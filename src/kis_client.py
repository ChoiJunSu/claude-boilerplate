"""한국투자증권 OpenAPI (모의투자) REST client.

Only the calls the bot needs: OAuth token (file-cached), current price, daily
candles, balance, cash order. The KIS HTTP boundary is an edge — we validate
rt_cd here and raise loudly on failure.
"""

import json
import time
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests

import config
import market_data as md


@dataclass
class OrderResult:
    ok: bool
    order_no: str
    message: str


class KisError(RuntimeError):
    pass


class KisClient:
    def __init__(self, settings: config.Settings):
        self.s = settings
        self.session = requests.Session()
        self._token = None
        self._token_expiry = 0.0

    # --- auth ---------------------------------------------------------------
    def _load_cached_token(self) -> bool:
        try:
            with open(config.TOKEN_CACHE_PATH) as f:
                data = json.load(f)
        except (OSError, ValueError):
            return False
        if data.get("expiry", 0) - 600 > time.time():
            self._token = data["access_token"]
            self._token_expiry = data["expiry"]
            return True
        return False

    def _token_header(self) -> str:
        if self._token and self._token_expiry - 600 > time.time():
            return self._token
        if self._load_cached_token():
            return self._token
        # Issue a fresh token. Mock issuance is rate-limited (~1/min) so we
        # cache it to disk and reuse across runs.
        resp = self.session.post(
            f"{config.BASE_URL}/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": self.s.app_key,
                "appsecret": self.s.app_secret,
            },
            timeout=10,
        )
        body = resp.json()
        if "access_token" not in body:
            raise KisError(f"token issue failed: {body}")
        self._token = body["access_token"]
        self._token_expiry = time.time() + int(body.get("expires_in", 86400))
        with open(config.TOKEN_CACHE_PATH, "w") as f:
            json.dump({"access_token": self._token, "expiry": self._token_expiry}, f)
        os.chmod(config.TOKEN_CACHE_PATH, 0o600)
        return self._token

    def _headers(self, tr_id: str, extra: dict | None = None) -> dict:
        h = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._token_header()}",
            "appkey": self.s.app_key,
            "appsecret": self.s.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }
        if extra:
            h.update(extra)
        return h

    def _hashkey(self, body: dict) -> str:
        resp = self.session.post(
            f"{config.BASE_URL}/uapi/hashkey",
            headers={
                "content-type": "application/json; charset=utf-8",
                "appkey": self.s.app_key,
                "appsecret": self.s.app_secret,
            },
            data=json.dumps(body),
            timeout=10,
        )
        return resp.json().get("HASH", "")

    # --- quotations ---------------------------------------------------------
    def get_price(self, code: str, name: str = "") -> md.PriceSnapshot:
        resp = self.session.get(
            f"{config.BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=self._headers(config.TR_PRICE),
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
            timeout=10,
        )
        body = resp.json()
        if body.get("rt_cd") != "0":
            raise KisError(f"price[{code}] failed: {body.get('msg1', body)}")
        return md.parse_price(code, name, body["output"])

    def get_daily(self, code: str) -> list:
        """Recent daily candles. Optional context — degrade to [] on failure."""
        end = datetime.now()
        start = end - timedelta(days=14)
        try:
            resp = self.session.get(
                f"{config.BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                headers=self._headers(config.TR_DAILY),
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": code,
                    "FID_INPUT_DATE_1": start.strftime("%Y%m%d"),
                    "FID_INPUT_DATE_2": end.strftime("%Y%m%d"),
                    "FID_PERIOD_DIV_CODE": "D",
                    "FID_ORG_ADJ_PRC": "0",
                },
                timeout=10,
            )
            return md.parse_candles(resp.json().get("output2", []))
        except (requests.RequestException, ValueError):
            return []

    # --- trading ------------------------------------------------------------
    def get_balance(self) -> md.Balance:
        resp = self.session.get(
            f"{config.BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance",
            headers=self._headers(config.TR_BALANCE),
            params={
                "CANO": self.s.account_no,
                "ACNT_PRDT_CD": self.s.account_product,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "00",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            timeout=10,
        )
        body = resp.json()
        if body.get("rt_cd") != "0":
            raise KisError(f"balance failed: {body.get('msg1', body)}")
        return md.parse_balance(body.get("output1", []), body.get("output2", []))

    def place_order(self, code: str, side: str, qty: int) -> OrderResult:
        """Market order (ORD_DVSN=01). side is 'buy' or 'sell'."""
        tr_id = config.TR_ORDER_BUY if side == "buy" else config.TR_ORDER_SELL
        body = {
            "CANO": self.s.account_no,
            "ACNT_PRDT_CD": self.s.account_product,
            "PDNO": code,
            "ORD_DVSN": "01",   # 시장가
            "ORD_QTY": str(qty),
            "ORD_UNPR": "0",    # 시장가는 0
        }
        resp = self.session.post(
            f"{config.BASE_URL}/uapi/domestic-stock/v1/trading/order-cash",
            headers=self._headers(tr_id, {"hashkey": self._hashkey(body)}),
            data=json.dumps(body),
            timeout=10,
        )
        b = resp.json()
        ok = b.get("rt_cd") == "0"
        return OrderResult(
            ok=ok,
            order_no=(b.get("output") or {}).get("ODNO", ""),
            message=b.get("msg1", str(b)),
        )
