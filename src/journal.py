"""SQLite journal of every cycle's crowd read + contrarian decision + order."""

import sqlite3
from datetime import datetime, timezone

import config
from crowd import CrowdView
from market_data import PriceSnapshot
from strategy import Decision

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT,
    price INTEGER,
    change_pct REAL,
    crowd_urge TEXT,
    crowd_conviction INTEGER,
    crowd_emotion TEXT,
    crowd_one_liner TEXT,
    side TEXT,
    qty INTEGER,
    reason TEXT,
    order_no TEXT,
    status TEXT
);
"""


class Journal:
    def __init__(self, path: str = config.DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.execute(_SCHEMA)
        self.conn.commit()

    def record(
        self,
        snap: PriceSnapshot,
        view: CrowdView,
        decision: Decision,
        order_no: str,
        status: str,
    ) -> None:
        self.conn.execute(
            """INSERT INTO decisions
               (ts, code, name, price, change_pct, crowd_urge, crowd_conviction,
                crowd_emotion, crowd_one_liner, side, qty, reason, order_no, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                snap.code, snap.name, snap.price, snap.change_pct,
                view.urge, view.conviction, view.emotion, view.one_liner,
                decision.side, decision.qty, decision.reason, order_no, status,
            ),
        )
        self.conn.commit()
