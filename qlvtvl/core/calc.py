"""Tính toán tự động giữa các biểu."""
from __future__ import annotations

import re
from collections import defaultdict

from .forms import DEFAULT_QUY_GIO, YEARS


def num(v, default=0.0) -> float:
    """Chuyển giá trị nhập thành số (chấp nhận dấu phẩy thập phân kiểu Việt Nam)."""
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "")
    if not s:
        return default
    # "1.904" kiểu VN (dấu chấm phân cách nghìn) hoặc "1,5" (dấu phẩy thập phân)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return default


def has_num(v) -> bool:
    return v is not None and str(v).strip() != "" and num(v, None) is not None


def fmt(v, digits=2) -> str:
    """Định dạng số theo kiểu Việt Nam: 1.904,25"""
    if v is None or v == "":
        return ""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if abs(f - round(f)) < 1e-9:
        s = f"{int(round(f)):,}"
    else:
        s = f"{f:,.{digits}f}".rstrip("0").rstrip(".")
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def parse_cv_list(text) -> list[tuple[str, float]]:
    """'CV01, CV02*0.5, CV03 (30%)' -> [('CV01',1.0), ('CV02',0.5), ('CV03',0.3)]"""
    out = []
    if not text:
        return out
    for part in re.split(r"[;,\n]+", str(text)):
        part = part.strip()
        if not part:
            continue
        share = 1.0
        m = re.match(r"^(.+?)\s*\(\s*([\d.,]+)\s*%\s*\)$", part)
        if m:
            part, share = m.group(1).strip(), num(m.group(2)) / 100
        else:
            m = re.match(r"^(.+?)\s*[*x×]\s*([\d.,]+)\s*(%?)$", part)
            if m:
                share = num(m.group(2))
                if m.group(3) or share > 1:
                    share /= 100
                part = m.group(1).strip()
        out.append((part, share))
    return out


def format_cv_list(items) -> str:
    parts = []
    for code, share in items:
        if abs(share - 1.0) < 1e-9:
            parts.append(code)
        else:
            parts.append(f"{code}*{fmt(share, 3).replace(',', '.')}")
    return ", ".join(parts)


class Calculator:
    def __init__(self, project):
        self.p = project
        self.refresh()

    def refresh(self):
        p = self.p
        self.default_quy = p.quy_gio() if p else DEFAULT_QUY_GIO
        self.a1 = {r.get("ma", ""): r for r in p.rows("A1") if r.get("ma")}
        self.a2 = {r.get("ma", ""): r for r in p.rows("A2") if r.get("ma")}
        self.c1 = {r.get("ma", ""): r for r in p.rows("C1") if r.get("ma")}
        self.b1_hours = defaultdict(float)
        for r in p.rows("B1"):
            self.b1_hours[r.get("ma_cv", "")] += num(r.get("so_luong")) * num(r.get("gio_sp"))
        self.b2_delta = defaultdict(float)
        for r in p.rows("B2"):
            self.b2_delta[r.get("ma_cv", "")] += num(r.get("gio_thay_doi"))
        self.c3 = {}
        self.cv_assign = defaultdict(float)
        for r in p.rows("C3"):
            vt = r.get("ma_vt", "")
            if vt:
                self.c3[vt] = r
            for code, share in parse_cv_list(r.get("ds_cv")):
                self.cv_assign[code] += share
        self.d1 = {r.get("ma_vt", ""): r for r in p.rows("D1") if r.get("ma_vt")}

    # ------------------------------------------------------------ C3 helpers
    def c3_values(self, r: dict) -> dict:
        b1 = b2 = 0.0
        for code, share in parse_cv_list(r.get("ds_cv")):
            b1 += self.b1_hours.get(code, 0.0) * share
            b2 += self.b2_delta.get(code, 0.0) * share
        can = max(0.0, b1 + b2)
        quy = num(r.get("quy_gio"), 0) or self.default_quy
        quy_doi = can / quy if quy else 0.0
        return {"gio_b1": b1, "gio_b2": b2, "gio_can": can, "quy": quy, "nguoi_quy_doi": quy_doi}

    def need(self, ma_vt: str) -> float:
        """Số người cần bố trí của một VTVL (ưu tiên số được đơn vị xác định)."""
        r = self.c3.get(ma_vt)
        if not r:
            return 0.0
        if has_num(r.get("nguoi_can")):
            return num(r.get("nguoi_can"))
        pp = str(r.get("phuong_phap", ""))
        if pp.startswith("PP2"):
            return self.c3_values(r)["nguoi_quy_doi"]
        return num(r.get("nguoi_dinh_muc"))

    def suggested_need(self, r: dict) -> float:
        pp = str(r.get("phuong_phap", ""))
        if pp.startswith("PP2"):
            return self.c3_values(r)["nguoi_quy_doi"]
        if pp.startswith("Kết hợp"):
            return self.c3_values(r)["nguoi_quy_doi"] + num(r.get("nguoi_dinh_muc"))
        return num(r.get("nguoi_dinh_muc"))

    def existing(self, ma_vt: str) -> float:
        r = self.d1.get(ma_vt)
        if not r:
            return 0.0
        return num(r.get("vien_chuc")) + num(r.get("hop_dong"))

    # --------------------------------------------------------- generic value
    def value(self, form: str, r: dict, key: str):
        if form == "B1":
            if key == "ten_cv":
                return self.a2.get(r.get("ma_cv", ""), {}).get("ten", "")
            if key == "tong_gio":
                return num(r.get("so_luong")) * num(r.get("gio_sp"))
        if form == "B2" and key == "ten_cv":
            return self.a2.get(r.get("ma_cv", ""), {}).get("ten", "")
        if form in ("C2", "C3", "D1", "D2") and key == "ten_vt":
            return self.c1.get(r.get("ma_vt", ""), {}).get("ten", "")
        if form == "C3" and key in ("gio_b1", "gio_b2", "gio_can", "nguoi_quy_doi"):
            return self.c3_values(r)[key]
        if form in ("D1", "D2") and key == "nguoi_can":
            return self.need(r.get("ma_vt", ""))
        if form == "D1":
            hc = num(r.get("vien_chuc")) + num(r.get("hop_dong"))
            if key == "hien_co":
                return hc
            if key == "chenh_lech":
                return hc - self.need(r.get("ma_vt", ""))
        if form == "D2" and key == "hien_co":
            return self.existing(r.get("ma_vt", ""))
        return r.get(key, "")

    # ------------------------------------------------------------- summary
    def summary(self) -> dict:
        p = self.p
        vts = list(self.c1.keys())
        need = sum(self.need(v) for v in vts)
        existing = sum(self.existing(v) for v in vts)
        giao = sum(num(r.get("giao")) for r in p.rows("D1"))
        hours = sum(self.b1_hours.values())
        delta = sum(self.b2_delta.values())
        by_group = defaultdict(lambda: {"vt": 0, "need": 0.0, "existing": 0.0})
        for v, r in self.c1.items():
            g = r.get("nhom") or "Chưa phân nhóm"
            by_group[g]["vt"] += 1
            by_group[g]["need"] += self.need(v)
            by_group[g]["existing"] += self.existing(v)
        plan = {y: 0.0 for y in YEARS}
        for r in p.rows("D2"):
            for y in YEARS:
                plan[y] += num(r.get(f"y{y}"))
        return {
            "nv": p.count("A1"), "cv": p.count("A2"), "vt": len(vts),
            "hours": hours, "delta": delta, "need": need, "existing": existing,
            "giao": giao, "diff": existing - need, "by_group": dict(by_group), "plan": plan,
        }
