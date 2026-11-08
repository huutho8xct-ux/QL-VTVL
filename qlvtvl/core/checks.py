"""Kiểm tra tính đầy đủ, logic và liên kết giữa các biểu (Bước 8)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .calc import Calculator, fmt, has_num, num, parse_cv_list
from .forms import FORM_ORDER, FORMS, YEARS

ERROR, WARNING, INFO = "Lỗi", "Cảnh báo", "Lưu ý"


@dataclass
class Issue:
    level: str
    form: str
    ref: str
    message: str
    row_id: int | None = None


def run_checks(project) -> list[Issue]:
    calc = Calculator(project)
    issues: list[Issue] = []

    def add(level, form, ref, msg, rid=None):
        issues.append(Issue(level, form, ref, msg, rid))

    rows = {code: project.rows(code) for code in FORM_ORDER}

    # ---- thiếu dữ liệu bắt buộc & mã trùng
    for code in FORM_ORDER:
        form = FORMS[code]
        if not rows[code]:
            add(ERROR, code, "", f"Biểu {code} - {form.title} chưa có dữ liệu.")
            continue
        if form.key_col:
            cnt = Counter(str(r.get(form.key_col, "")).strip() for r in rows[code])
            for k, n in cnt.items():
                if k and n > 1:
                    add(ERROR, code, k, f"Mã '{k}' bị trùng {n} lần trong biểu {code}.")
        for i, r in enumerate(rows[code], 1):
            ref = str(r.get(form.key_col or "ma", "") or f"dòng {i}")
            missing = [c.label for c in form.columns
                       if c.required and c.kind != "calc" and str(r.get(c.key, "")).strip() == ""]
            if missing:
                add(WARNING, code, ref, "Chưa nhập: " + "; ".join(missing) + ".", r["_id"])
            for c in form.columns:
                if c.kind == "ref" and r.get(c.key):
                    target = {"A1": calc.a1, "A2": calc.a2, "C1": calc.c1}[c.ref]
                    if r[c.key] not in target:
                        add(ERROR, code, ref,
                            f"{c.label} '{r[c.key]}' không tồn tại trong biểu {c.ref}.", r["_id"])

    # ---- liên kết A1 -> A2
    nv_has_cv = {r.get("ma_nv") for r in rows["A2"]}
    for r in rows["A1"]:
        if r.get("ma") and r.get("tinh_trang") != "Đề nghị bãi bỏ" and r["ma"] not in nv_has_cv:
            add(WARNING, "A1", r["ma"], "Nhiệm vụ chưa được cụ thể hóa thành công việc ở Biểu A2.", r["_id"])

    # ---- A2 -> B1, phân công
    b1_cv = {r.get("ma_cv") for r in rows["B1"]}
    for r in rows["A2"]:
        cv = r.get("ma")
        if not cv:
            continue
        if cv not in b1_cv:
            add(WARNING, "A2", cv, "Công việc chưa có khối lượng, thời gian ở Biểu B1.", r["_id"])
        share = calc.cv_assign.get(cv, 0.0)
        if share == 0:
            add(WARNING, "C3", cv, f"Công việc {cv} chưa được giao cho vị trí việc làm nào (Biểu C3).")
        elif share > 1.0001:
            add(ERROR, "C3", cv,
                f"Công việc {cv} được phân bổ {fmt(share * 100)}% (> 100%) cho các vị trí việc làm.")
        elif share < 0.9999:
            add(INFO, "C3", cv, f"Công việc {cv} mới được phân bổ {fmt(share * 100)}% cho các vị trí.")

    # ---- B1
    for r in rows["B1"]:
        ref = r.get("ma_cv", "")
        if has_num(r.get("gio_sp")) and num(r.get("gio_sp")) < 0:
            add(ERROR, "B1", ref, "Thời gian/1 sản phẩm không được âm.", r["_id"])
        if has_num(r.get("so_luong")) and num(r.get("so_luong")) < 0:
            add(ERROR, "B1", ref, "Số lượng sản phẩm không được âm.", r["_id"])
        if str(r.get("nguon", "")).startswith("Ước tính"):
            add(INFO, "B1", ref, "Số liệu ước tính: cần bổ sung minh chứng trước khi gửi.", r["_id"])

    # ---- B2
    for r in rows["B2"]:
        cv = r.get("ma_cv", "")
        if not str(r.get("can_cu", "")).strip():
            add(INFO, "B2", cv, "Nên ghi căn cứ, minh chứng cho mức tăng/giảm thời gian.", r["_id"])
        if cv in calc.b1_hours and calc.b1_hours[cv] + calc.b2_delta[cv] < 0:
            add(ERROR, "B2", cv, "Tổng giờ giảm vượt quá tổng giờ của công việc ở B1.", r["_id"])

    # ---- C1 -> C2, C3, D1, D2
    sets = {code: {r.get("ma_vt") for r in rows[code]} for code in ("C2", "C3", "D1", "D2")}
    for r in rows["C1"]:
        vt = r.get("ma")
        if not vt:
            continue
        if r.get("tinh_trang") == "Đề nghị bãi bỏ":
            continue
        for code, msg in (("C2", "bản mô tả công việc, khung năng lực"),
                          ("C3", "xác định nhu cầu nhân lực"),
                          ("D1", "đối chiếu nhân lực hiện có"),
                          ("D2", "phương án biên chế 2027 - 2031")):
            if vt not in sets[code]:
                add(WARNING, code, vt, f"Vị trí {vt} chưa có {msg} (Biểu {code}).")
        if r.get("tinh_trang") in ("Cần điều chỉnh", "Tích hợp", "Đề nghị bổ sung") \
                and not str(r.get("can_cu", "")).strip():
            add(WARNING, "C1", vt, f"Vị trí '{r.get('tinh_trang')}' cần ghi căn cứ, lý do.", r["_id"])

    # ---- C3
    for r in rows["C3"]:
        vt = r.get("ma_vt", "")
        pp = str(r.get("phuong_phap", ""))
        v = calc.c3_values(r)
        if pp.startswith("PP2"):
            if not parse_cv_list(r.get("ds_cv")):
                add(ERROR, "C3", vt, "Phương pháp PP2 nhưng chưa chọn công việc đảm nhận.", r["_id"])
            elif v["gio_can"] <= 0:
                add(ERROR, "C3", vt, "Phương pháp PP2 nhưng tổng giờ cần thiết bằng 0.", r["_id"])
            for code, _ in parse_cv_list(r.get("ds_cv")):
                if code not in calc.a2:
                    add(ERROR, "C3", vt, f"Mã công việc '{code}' không có trong Biểu A2.", r["_id"])
        if pp.startswith(("PP1", "PP3")) and not str(r.get("giai_trinh", "")).strip():
            add(WARNING, "C3", vt, f"{pp[:3]} cần có hồ sơ giải trình (không gán số giờ giả định).", r["_id"])
        if pp.startswith(("PP1", "PP3")) and not has_num(r.get("nguoi_dinh_muc")) \
                and not has_num(r.get("nguoi_can")):
            add(WARNING, "C3", vt, "Chưa nhập số người theo định mức/thẩm định.", r["_id"])
        if has_num(r.get("quy_gio")) and abs(num(r.get("quy_gio")) - calc.default_quy) > 0.01 \
                and not str(r.get("giai_trinh", "")).strip():
            add(WARNING, "C3", vt, "Dùng quỹ giờ đặc thù khác mức chung: cần giải trình căn cứ xác nhận.",
                r["_id"])
        if has_num(r.get("nguoi_can")):
            sug = calc.suggested_need(r)
            chosen = num(r.get("nguoi_can"))
            if sug > 0 and chosen - sug >= 0.5 and not str(r.get("giai_trinh", "")).strip():
                add(WARNING, "C3", vt,
                    f"Số người cần bố trí ({fmt(chosen)}) cao hơn kết quả tính ({fmt(sug, 3)}): "
                    "không làm tròn cơ học, cần giải trình.", r["_id"])
            if chosen < 0:
                add(ERROR, "C3", vt, "Số người cần bố trí không được âm.", r["_id"])

    # ---- D1
    for r in rows["D1"]:
        vt = r.get("ma_vt", "")
        diff = calc.value("D1", r, "chenh_lech")
        if abs(diff) >= 0.5 and not str(r.get("giai_trinh", "")).strip():
            word = "thừa" if diff > 0 else "thiếu"
            add(WARNING, "D1", vt, f"Vị trí {word} {fmt(abs(diff))} người: cần giải trình.", r["_id"])
        if not r.get("kinh_phi"):
            add(INFO, "D1", vt, "Chưa xác định nguồn kinh phí chi trả.", r["_id"])

    # ---- D2
    for r in rows["D2"]:
        vt = r.get("ma_vt", "")
        need = calc.need(vt)
        vals = [num(r.get(f"y{y}")) for y in YEARS if has_num(r.get(f"y{y}"))]
        if not vals:
            add(WARNING, "D2", vt, "Chưa xây dựng lộ trình các năm 2027 - 2031.", r["_id"])
            continue
        if max(vals) - need >= 0.5 and not str(r.get("giai_trinh", "")).strip():
            add(WARNING, "D2", vt,
                f"Phương án có năm vượt nhu cầu ({fmt(max(vals))} > {fmt(need, 3)}): cần giải trình.", r["_id"])

    # ---- tổng
    s = calc.summary()
    giao = s["giao"]
    plan_2027 = s["plan"].get(2027, 0)
    if giao and plan_2027 - giao >= 0.5:
        add(INFO, "D2", "Tổng",
            f"Phương án năm 2027 ({fmt(plan_2027)}) cao hơn số lượng người làm việc được giao ({fmt(giao)}). "
            "Nhu cầu tính được không tự động trở thành biên chế.")
    meta = project.meta()
    if not meta.get("nguoi_dung_dau", "").strip():
        add(INFO, "TT", "Thông tin", "Chưa nhập họ tên người đứng đầu (ký xác nhận).")
    if not meta.get("nguoi_lap", "").strip():
        add(INFO, "TT", "Thông tin", "Chưa nhập họ tên người lập biểu.")

    order = {ERROR: 0, WARNING: 1, INFO: 2}
    issues.sort(key=lambda i: (order[i.level], FORM_ORDER.index(i.form) if i.form in FORM_ORDER else 99))
    return issues


def step_status(project) -> dict[int, str]:
    """Trạng thái hoàn thành từng bước: 'done' | 'partial' | 'empty'."""
    from .guide import STEPS

    issues = run_checks(project)
    bad = {i.form for i in issues if i.level in (ERROR, WARNING)}
    out = {}
    for st in STEPS:
        if not st.forms:
            errs = [i for i in issues if i.level == ERROR]
            out[st.no] = "done" if project.count("D2") and not errs else (
                "partial" if project.count("A1") else "empty")
            continue
        counts = [project.count(f) for f in st.forms]
        if not any(counts):
            out[st.no] = "empty"
        elif all(counts) and not (bad & set(st.forms)):
            out[st.no] = "done"
        else:
            out[st.no] = "partial"
    return out
