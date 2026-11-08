"""Lưu trữ dữ liệu bằng SQLite (một tệp .vtvl cho mỗi hồ sơ rà soát)."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
from datetime import datetime

SCHEMA_VERSION = 1

DEFAULT_META = {
    "ten_don_vi": "Thư viện thành phố Cần Thơ",
    "co_quan_chu_quan": "Sở Văn hóa, Thể thao và Du lịch thành phố Cần Thơ",
    "dia_chi": "Thành phố Cần Thơ",
    "nguoi_dung_dau": "",
    "chuc_vu_nguoi_dung_dau": "Giám đốc",
    "nguoi_lap": "",
    "dien_thoai": "",
    "ky_ra_soat": "Rà soát theo Hướng dẫn số 7-HD/BTCTW - phương án 2027 - 2031",
    "ky_thong_ke": "01/10/2025 - 30/9/2026",
    "ngay_chot": "30/9/2026",
    "bc_giao": "",
    "quy_gio": "1904",
}


def app_data_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    path = os.path.join(base, "QL-VTVL")
    os.makedirs(path, exist_ok=True)
    return path


class Project:
    """Một hồ sơ rà soát vị trí việc làm."""

    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._listeners = []
        self._init()

    # ------------------------------------------------------------------ setup
    def _init(self):
        c = self.conn
        c.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT)")
        c.execute(
            "CREATE TABLE IF NOT EXISTS rows(id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " form TEXT NOT NULL, ord INTEGER NOT NULL, data TEXT NOT NULL)"
        )
        c.execute("CREATE INDEX IF NOT EXISTS ix_rows_form ON rows(form, ord)")
        if self.get_meta("schema") is None:
            for k, v in DEFAULT_META.items():
                self.set_meta(k, v, notify=False)
            self.set_meta("schema", str(SCHEMA_VERSION), notify=False)
            self.set_meta("created", datetime.now().isoformat(timespec="seconds"), notify=False)
        c.commit()

    def close(self):
        try:
            self.conn.commit()
            self.conn.close()
        except sqlite3.Error:
            pass

    # -------------------------------------------------------------- listeners
    def subscribe(self, fn):
        self._listeners.append(fn)

    def _notify(self, form):
        for fn in list(self._listeners):
            fn(form)

    # ------------------------------------------------------------------- meta
    def get_meta(self, key, default=None):
        r = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return r[0] if r else default

    def set_meta(self, key, value, notify=True):
        self.conn.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )
        self.conn.commit()
        if notify:
            self._notify("meta")

    def meta(self) -> dict:
        d = dict(DEFAULT_META)
        d.update({r[0]: r[1] for r in self.conn.execute("SELECT key,value FROM meta")})
        return d

    def quy_gio(self) -> float:
        try:
            v = float(str(self.get_meta("quy_gio", "1904")).replace(",", "."))
            return v if v > 0 else 1904.0
        except ValueError:
            return 1904.0

    # ------------------------------------------------------------------- rows
    def rows(self, form: str) -> list[dict]:
        out = []
        for r in self.conn.execute(
            "SELECT id, data FROM rows WHERE form=? ORDER BY ord, id", (form,)
        ):
            d = json.loads(r["data"])
            d["_id"] = r["id"]
            out.append(d)
        return out

    def count(self, form: str) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM rows WHERE form=?", (form,)).fetchone()[0]

    def add_row(self, form: str, data: dict | None = None, notify=True) -> int:
        data = {k: v for k, v in (data or {}).items() if not k.startswith("_")}
        mx = self.conn.execute("SELECT COALESCE(MAX(ord),0) FROM rows WHERE form=?", (form,)).fetchone()[0]
        cur = self.conn.execute(
            "INSERT INTO rows(form, ord, data) VALUES(?,?,?)",
            (form, mx + 1, json.dumps(data, ensure_ascii=False)),
        )
        self.conn.commit()
        if notify:
            self._notify(form)
        return cur.lastrowid

    def update_row(self, row_id: int, data: dict, notify=True):
        r = self.conn.execute("SELECT form, data FROM rows WHERE id=?", (row_id,)).fetchone()
        if not r:
            return
        cur = json.loads(r["data"])
        cur.update({k: v for k, v in data.items() if not k.startswith("_")})
        self.conn.execute("UPDATE rows SET data=? WHERE id=?", (json.dumps(cur, ensure_ascii=False), row_id))
        self.conn.commit()
        if notify:
            self._notify(r["form"])

    def delete_rows(self, form: str, ids):
        self.conn.executemany("DELETE FROM rows WHERE id=?", [(i,) for i in ids])
        self.conn.commit()
        self._notify(form)

    def move_row(self, form: str, row_id: int, delta: int):
        ids = [r["_id"] for r in self.rows(form)]
        if row_id not in ids:
            return
        i = ids.index(row_id)
        j = max(0, min(len(ids) - 1, i + delta))
        if i == j:
            return
        ids.insert(j, ids.pop(i))
        self.conn.executemany("UPDATE rows SET ord=? WHERE id=?", [(n, rid) for n, rid in enumerate(ids, 1)])
        self.conn.commit()
        self._notify(form)

    def replace_rows(self, form: str, rows: list[dict]):
        self.conn.execute("DELETE FROM rows WHERE form=?", (form,))
        for n, d in enumerate(rows, 1):
            d = {k: v for k, v in d.items() if not k.startswith("_")}
            self.conn.execute(
                "INSERT INTO rows(form, ord, data) VALUES(?,?,?)",
                (form, n, json.dumps(d, ensure_ascii=False)),
            )
        self.conn.commit()
        self._notify(form)

    def rename_key(self, form_codes_cols, old: str, new: str):
        """Cập nhật mã tham chiếu ở các biểu phụ thuộc khi đổi mã."""
        if not old or old == new:
            return
        for form, col in form_codes_cols:
            for r in self.rows(form):
                if r.get(col) == old:
                    self.update_row(r["_id"], {col: new}, notify=False)
            self._notify(form)

    # ----------------------------------------------------------------- backup
    def backup(self, dest: str):
        self.conn.commit()
        b = sqlite3.connect(dest)
        with b:
            self.conn.backup(b)
        b.close()


def copy_project(src: str, dest: str):
    shutil.copyfile(src, dest)
