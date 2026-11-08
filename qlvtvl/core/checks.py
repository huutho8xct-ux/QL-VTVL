"""Kiểm tra, xác nhận dữ liệu (Bước 8, Phụ lục VI) – dựa trên các cột cảnh báo của bộ biểu và liên kết giữa biểu."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .calc import DAT, Calculator, blank, s
from .forms import FORMS, INPUT_FORMS, YEARS

ERROR, WARNING, INFO = "Lỗi", "Cảnh báo", "Lưu ý"
ORDER = {ERROR: 0, WARNING: 1, INFO: 2}

# cột cảnh báo tự động của từng biểu và giá trị được coi là đạt
WARN_COLS = {
    "B1": ("canh_bao", "ma_cv", {DAT}),
    "B2": ("kiem_tra", "ma_cv", {DAT}),
    "C1": ("kt_quy_gio", "ma", {DAT}),
    "C3": ("canh_bao", "ma_vt", {DAT}),
    "D1": ("canh_bao", "ma_nl", {"Đạt"}),
    "DB": ("kiem_tra", "ma_vt", {DAT}),
    "D2": ("canh_bao", "ma_vt", {"ĐÃ THẨM ĐỊNH", "ĐÃ QUYẾT ĐỊNH"}),
}
INFO_VALUES = {"THAM KHẢO – KHÔNG TÍNH", "ĐANG XÂY DỰNG", "SẴN SÀNG THẨM ĐỊNH", "CHỜ XÁC NHẬN NGHIỆP VỤ"}
REQUIRED_NONEMPTY = ("A1", "A2", "B1", "C1", "C2", "C3", "D1", "DB", "D2")


@dataclass
class Issue:
    level: str
    form: str
    ref: str
    message: str
    row_id: int | None = None


def run_checks(project, calc: Calculator | None = None) -> list[Issue]:
    calc = calc or Calculator(project)
    R = calc.rows
    issues: list[Issue] = []

    def add(level, form, ref, msg, rid=None):
        issues.append(Issue(level, form, ref, msg, rid))

    # ---- biểu trống, sức chứa, trường bắt buộc, trùng mã, mã tham chiếu
    refs = {"A1": calc.a1, "A2": calc.a2, "C1": calc.c1, "DM": calc.dm}
    for code in INPUT_FORMS:
        form = FORMS[code]
        rows = R[code]
        if not rows:
            if code in REQUIRED_NONEMPTY:
                add(ERROR, code, "", f"Biểu {code} – {form.title} chưa có dữ liệu.")
            continue
        if len(rows) > form.capacity:
            add(WARNING, code, "", f"Biểu {code} có {len(rows)} dòng, vượt sức chứa {form.capacity} dòng của bộ biểu "
                                   "Excel; báo đầu mối hỗ trợ kỹ thuật để mở rộng có kiểm soát.")
        if form.key_col:
            cnt = Counter(s(r.get(form.key_col)) for r in rows)
            for k, n in cnt.items():
                if k and n > 1:
                    add(ERROR, code, k, f"Mã '{k}' bị trùng {n} lần trong biểu {code}.")
        for i, r in enumerate(rows, 1):
            ref = s(r.get(form.key_col or "ma_cv") or r.get("ma_vt")) or f"dòng {i}"
            missing = [c.label for c in form.columns if c.required and c.kind != "calc" and blank(r.get(c.key))]
            if missing:
                add(WARNING, code, ref, "Chưa nhập: " + "; ".join(missing) + ".", r["_id"])
            for c in form.columns:
                if c.kind == "ref" and s(r.get(c.key)) and s(r.get(c.key)) not in refs[c.ref]:
                    add(ERROR, code, ref, f"{c.label} '{r.get(c.key)}' chưa có ở biểu {c.ref}.", r["_id"])

    # ---- cảnh báo tự động của bộ biểu
    for code, (col, keycol, ok) in WARN_COLS.items():
        infos = Counter()
        for r in R[code]:
            w = calc.v.get(r["_id"], {}).get(col, "")
            if w and w not in ok:
                if w in INFO_VALUES:
                    infos[w] += 1
                    continue
                lvl = ERROR if w.startswith("TRÙNG") else WARNING
                ref = s(r.get(keycol)) + (f" {s(r.get('nam'))}" if code in ("DB", "D2") else "")
                add(lvl, code, ref, f"{FORMS[code].col(col).label}: {w}", r["_id"])
        for w, n in infos.items():
            add(INFO, code, f"{n} dòng", f"{FORMS[code].col(col).label}: {w}")
    for t in calc.b2th:
        if t["canh_bao"] != DAT:
            add(INFO, "B2TH", t["ma_cv"], f"B2 tổng hợp: {t['canh_bao']}")

    # ---- liên kết giữa các biểu
    cv_by_nv = {s(r.get("ma_nv")) for r in R["A2"]}
    for r in R["A1"]:
        if s(r.get("ma")) and s(r.get("trang_thai")) in ("Tiếp tục thực hiện", "Mới tiếp nhận") \
                and s(r.get("ma")) not in cv_by_nv:
            add(WARNING, "A1", s(r.get("ma")), "Nhiệm vụ chưa được phân rã thành công việc ở Biểu A2.", r["_id"])
    b1_cv = {s(r.get("ma_cv")) for r in R["B1"]}
    for r in R["A2"]:
        cv, vt = s(r.get("ma")), s(r.get("ma_vt"))
        c3 = calc.c3.get(vt)
        if cv and cv not in b1_cv and c3 is not None and "PP2" in s(c3.get("pp")):
            add(WARNING, "A2", cv, f"Công việc thuộc {vt} (PP2) chưa có khối lượng, thời gian ở Biểu B1.", r["_id"])
    sets = {code: {s(r.get("ma_vt")) for r in R[code]} for code in ("A2", "C2", "C3", "D1")}
    d2_years = Counter(s(r.get("ma_vt")) for r in R["D2"])
    for r in R["C1"]:
        vt = s(r.get("ma"))
        if not vt or s(r.get("trang_thai")) == "Đề nghị bãi bỏ":
            continue
        for code, msg in (("C2", "mô tả trách nhiệm, năng lực"), ("C3", "xác định nhu cầu nhân lực")):
            if vt not in sets[code]:
                add(WARNING, code, vt, f"Vị trí {vt} chưa có {msg} (Biểu {code}).")
        if vt not in sets["A2"]:
            add(INFO, "A2", vt, f"Vị trí {vt} chưa được gắn công việc nào ở Biểu A2.")
        if d2_years[vt] < len(YEARS):
            add(INFO, "D2", vt, f"Vị trí {vt} mới có {d2_years[vt]}/{len(YEARS)} năm phương án 2027 - 2031.")
    for r in R["C3"]:
        vt = s(r.get("ma_vt"))
        o = calc.v[r["_id"]]
        if o.get("nguoi_qd") not in ("", None) and r.get("nguoi_can") not in (None, ""):
            try:
                diff = float(r.get("nguoi_can")) - calc.suggested_need(r)
            except (TypeError, ValueError):
                diff = 0
            if diff >= 0.5 and not s(r.get("giai_trinh")):
                add(WARNING, "C3", vt, "Người cần bố trí cao hơn kết quả tính: không làm tròn tăng cơ học, "
                                       "cần giải trình.", r["_id"])
    if not R["B2"]:
        add(INFO, "B2", "", "Chưa kê khai tác động chuyển đổi số, tự chủ, thuê dịch vụ, xã hội hóa (chỉ kê khai khi "
                            "có tác động thực tế có bằng chứng).")
    meta = project.meta()
    for key, label in (("nguoi_dung_dau", "họ tên người đứng đầu"), ("nguoi_lap", "họ tên người lập biểu")):
        if not s(meta.get(key)):
            add(INFO, "TT", "Thông tin", f"Chưa nhập {label}.")
    if abs(calc.quy - 1904) > 0.01:
        add(WARNING, "TT", "Quỹ giờ", "Quỹ giờ PP2 khác mức tham chiếu 1.904 giờ – tham số này do cơ quan chủ trì "
                                     "quản lý (DM_THAM_SO).")

    form_rank = {c: i for i, c in enumerate(("TT",) + tuple(FORMS))}
    issues.sort(key=lambda i: (ORDER[i.level], form_rank.get(i.form, 99)))
    return issues


def step_status(project, calc: Calculator | None = None) -> dict[int, str]:
    """Trạng thái từng bước: 'done' | 'partial' | 'empty'."""
    from .guide import STEPS

    calc = calc or Calculator(project)
    issues = run_checks(project, calc)
    bad = {i.form for i in issues if i.level in (ERROR, WARNING)}
    out = {}
    for st in STEPS:
        forms = [f for f in st.forms if not FORMS[f].virtual]
        if not forms:
            has_err = any(i.level == ERROR for i in issues)
            out[st.no] = "done" if calc.rows["D2"] and not has_err and not bad else (
                "partial" if calc.rows["A1"] else "empty")
            continue
        main = [f for f in forms if f not in ("DM", "B2")] or forms
        counts = [len(calc.rows[f]) for f in forms]
        if not any(counts):
            out[st.no] = "empty"
        elif all(len(calc.rows[f]) for f in main) and not (bad & set(forms)):
            out[st.no] = "done"
        else:
            out[st.no] = "partial"
    return out
