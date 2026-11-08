"""Dữ liệu MINH HỌA cho Thư viện thành phố Cần Thơ theo cấu trúc Bộ biểu 19-10-2026.

Số liệu chỉ để làm quen phần mềm; đơn vị phải thay bằng số liệu thực tế đã được kiểm chứng.
"""
from __future__ import annotations

from .calc import Calculator, fmt
from .forms import DEFAULT_KY, YEARS

UNIT = "Thư viện thành phố Cần Thơ"
QD = "QĐ quy định chức năng, nhiệm vụ của Thư viện TP Cần Thơ"
LTV = "Luật Thư viện 2019"
NGUON = "Dữ liệu kê khai theo CV 2342-CV/BTCTW (minh họa)"

# ma, ten, can_cu
A1 = [
    ("NV01", "Xây dựng, phát triển tài nguyên thông tin; thu thập, lưu giữ tài liệu địa chí", f"{LTV}, Điều 10, 24; {QD}"),
    ("NV02", "Xử lý tài liệu, xây dựng hệ thống tra cứu, cơ sở dữ liệu thư mục", f"{LTV}, Điều 25; {QD}"),
    ("NV03", "Tổ chức phục vụ người sử dụng thư viện tại chỗ, mượn về nhà", f"{LTV}, Điều 26, 27; {QD}"),
    ("NV04", "Phục vụ thiếu nhi; tổ chức hoạt động phát triển văn hóa đọc", f"{LTV}, Điều 10; {QD}"),
    ("NV05", "Xây dựng thư viện số, số hóa tài liệu, chuyển đổi số", f"{LTV}, Điều 12; {QD}"),
    ("NV06", "Luân chuyển tài liệu, hướng dẫn nghiệp vụ thư viện cơ sở", f"{LTV}, Điều 10; {QD}"),
    ("NV07", "Bảo quản, kiểm kê, thanh lọc tài liệu", f"{LTV}, Điều 28; {QD}"),
    ("NV08", "Quản lý, điều hành hoạt động của Thư viện", QD),
    ("NV09", "Hành chính, tổng hợp, tổ chức cán bộ, văn thư, lưu trữ", QD),
    ("NV10", "Quản lý tài chính, kế toán, tài sản", f"Luật Kế toán 2015; {QD}"),
    ("NV11", "Bảo vệ trụ sở, tài sản", f"Nghị định 111/2022/NĐ-CP; {QD}"),
]

# ma, ma_nv, ma_vt, ten, san_pham, dvt, chat_luong
A2 = [
    ("CV01", "NV01", "VT04", "Bổ sung tài liệu (mua, nhận lưu chiểu, tặng biếu)", "Tài liệu được bổ sung", "bản",
     "Đúng danh mục, đăng ký cá biệt đầy đủ"),
    ("CV02", "NV01", "VT04", "Sưu tầm, thu thập tài liệu địa chí", "Tài liệu địa chí", "tài liệu", ""),
    ("CV03", "NV02", "VT05", "Biên mục, phân loại, định từ khóa tài liệu", "Biểu ghi thư mục", "biểu ghi",
     "Chuẩn MARC21, DDC"),
    ("CV04", "NV03", "VT06", "Phục vụ bạn đọc tại phòng đọc", "Lượt bạn đọc được phục vụ", "lượt", ""),
    ("CV05", "NV03", "VT06", "Phục vụ mượn, trả tài liệu về nhà", "Lượt mượn trả", "lượt", ""),
    ("CV06", "NV03", "VT06", "Cấp, gia hạn thẻ thư viện", "Thẻ được cấp", "thẻ", ""),
    ("CV07", "NV04", "VT07", "Phục vụ bạn đọc thiếu nhi", "Lượt bạn đọc thiếu nhi", "lượt", ""),
    ("CV08", "NV04", "VT07", "Tổ chức sự kiện phát triển văn hóa đọc", "Sự kiện được tổ chức", "cuộc",
     "Có kế hoạch, báo cáo kết quả"),
    ("CV09", "NV05", "VT08", "Số hóa tài liệu địa chí", "Trang tài liệu số hóa", "trang", "Đạt chuẩn ảnh, có metadata"),
    ("CV10", "NV05", "VT08", "Quản trị phần mềm, website, thư viện số", "Tháng vận hành ổn định", "tháng", ""),
    ("CV11", "NV06", "VT09", "Luân chuyển tài liệu đến thư viện, điểm đọc cơ sở", "Lượt luân chuyển", "lượt", ""),
    ("CV12", "NV06", "VT09", "Hướng dẫn, kiểm tra nghiệp vụ thư viện cơ sở", "Đơn vị được hướng dẫn", "đơn vị", ""),
    ("CV13", "NV07", "VT10", "Bảo quản, kiểm kê, thanh lọc tài liệu", "Bản tài liệu được kiểm kê", "bản", ""),
    ("CV14", "NV09", "VT12", "Văn thư, lưu trữ, tổng hợp báo cáo", "Văn bản đến, đi", "văn bản", "Đúng thể thức, thời hạn"),
    ("CV15", "NV09", "VT12", "Tổ chức cán bộ, thi đua – khen thưởng", "Hồ sơ, báo cáo", "hồ sơ", ""),
    ("CV16", "NV10", "VT11", "Kế toán, quản lý tài chính, tài sản", "Chứng từ kế toán", "chứng từ", "Đúng chế độ kế toán"),
    ("CV17", "NV08", "VT01", "Chỉ đạo, điều hành chung hoạt động Thư viện", "Kế hoạch, văn bản chỉ đạo", "văn bản", ""),
    ("CV18", "NV08", "VT02", "Chỉ đạo lĩnh vực được phân công", "Văn bản chỉ đạo lĩnh vực", "văn bản", ""),
    ("CV19", "NV08", "VT03", "Quản lý, điều hành phòng chuyên môn", "Kế hoạch, báo cáo phòng", "báo cáo", ""),
    ("CV20", "NV11", "VT13", "Bảo vệ trụ sở, tài sản 24/7", "Ca trực", "ca", "Không để xảy ra mất an toàn"),
]

# ma_cv, so_sp, phut/SP, tt_tg, nguon_tg, gio_bo_sung
B1 = [
    ("CV01", 6000, 15, "Kiểm đếm, ước lượng thực tế", "Bấm giờ mẫu 30 bản, 3/2026", None),
    ("CV02", 350, 120, "Kiểm đếm, ước lượng thực tế", "Sổ theo dõi sưu tầm", None),
    ("CV03", 7000, 27, "Kiểm đếm, ước lượng thực tế", "Thống kê phần mềm quản lý thư viện", 36),
    ("CV04", 85000, 3, "Kiểm đếm, ước lượng thực tế", "Khảo sát mẫu 2 tuần", None),
    ("CV05", 60000, 3.6, "Kiểm đếm, ước lượng thực tế", "Nhật ký phần mềm mượn trả", None),
    ("CV06", 2500, 18, "Kiểm đếm, ước lượng thực tế", "Bấm giờ mẫu 50 thẻ", None),
    ("CV07", 40000, 3.6, "Kiểm đếm, ước lượng thực tế", "Khảo sát mẫu 2 tuần", None),
    ("CV08", 48, 2400, "Kiểm đếm, ước lượng thực tế", "Hồ sơ tổ chức sự kiện", None),
    ("CV09", 60000, 3, "Kiểm đếm, ước lượng thực tế", "Nhật ký máy quét", None),
    ("CV10", 12, 9000, "Kiểm đếm, ước lượng thực tế", "Nhật ký vận hành hệ thống", None),
    ("CV11", 120, 1080, "Kiểm đếm, ước lượng thực tế", "Sổ luân chuyển", None),
    ("CV12", 45, 1800, "Kiểm đếm, ước lượng thực tế", "Báo cáo hướng dẫn cơ sở", None),
    ("CV13", 150000, 0.9, "Kiểm đếm, ước lượng thực tế", "Biên bản kiểm kê", None),
    ("CV14", 3200, 30, "Kiểm đếm, ước lượng thực tế", "Sổ văn bản đến, đi", None),
    ("CV15", 180, 480, "Kiểm đếm, ước lượng thực tế", "Hồ sơ tổ chức cán bộ", None),
    ("CV16", 2600, 42, "Kiểm đếm, ước lượng thực tế", "Sổ chứng từ kế toán", 120),
]

# ma_cv, loai, cong_doan, sp, phut_truoc, phut_sau, gio_moi, nguon
B2 = [
    ("CV05", "Số hóa", "Mượn trả tự động RFID tại quầy tự phục vụ", 24000, 3.6, 1.35, None,
     "Báo cáo vận hành hệ thống RFID từ 01/2026"),
    ("CV03", "Cải tiến quy trình", "Biên mục sao chép từ CSDL liên thông", 2100, 27, 8.4, None,
     "Thống kê biểu ghi sao chép trên phần mềm"),
    ("CV09", "Công việc mới phát sinh", "Kiểm soát chất lượng, gắn metadata dữ liệu số", None, None, None, 600,
     "Kế hoạch số hóa được phê duyệt"),
    ("CV08", "Xã hội hóa", "Đồng tổ chức sự kiện với trường học, doanh nghiệp", 12, 2400, 800, None,
     "Biên bản phối hợp tổ chức"),
]

# ma, ten, loai_nl, pp, nguoi_pp1, so_nguoi_hien_co
C1 = [
    ("VT01", "Giám đốc", "Viên chức", "PP1", 1, 1),
    ("VT02", "Phó Giám đốc", "Viên chức", "PP1", 2, 2),
    ("VT03", "Trưởng phòng và tương đương", "Viên chức", "PP1", 6, 6),
    ("VT04", "Phát triển tài nguyên thông tin", "Viên chức", "PP2", None, 2),
    ("VT05", "Xử lý tài liệu, xây dựng hệ thống tra cứu", "Viên chức", "PP2", None, 2),
    ("VT06", "Phục vụ người sử dụng thư viện", "Viên chức", "PP2", None, 5),
    ("VT07", "Phục vụ thiếu nhi, phát triển văn hóa đọc", "Viên chức", "PP2", None, 2),
    ("VT08", "Thư viện số, số hóa và công nghệ thông tin", "Viên chức", "PP2", None, 1),
    ("VT09", "Hoạt động thư viện cơ sở, luân chuyển tài liệu", "Viên chức", "PP2", None, 2),
    ("VT10", "Bảo quản tài liệu", "Viên chức", "PP2", None, 1),
    ("VT11", "Kế toán", "Viên chức", "PP2", None, 1),
    ("VT12", "Hành chính – tổng hợp, văn thư", "Viên chức", "PP2", None, 2),
    ("VT13", "Bảo vệ", "Hợp đồng lao động", "PP1", 3, 3),
]

PP1_NOTE = {
    "VT01": "Theo cơ cấu tổ chức: 01 người đứng đầu.",
    "VT02": "Theo phân công lĩnh vực; không mặc nhiên bố trí đủ số cấp phó tối đa.",
    "VT03": "06 phòng theo cơ cấu tổ chức được phê duyệt.",
    "VT13": "Yêu cầu hiện diện 24/7 theo 3 ca; xem xét thuê dịch vụ theo NĐ 111/2022.",
}
# biến động dự báo: ma_vt -> {năm: (biến động, nội dung)}
FORECAST = {
    "VT08": {2028: (0.5, "Tăng khối lượng số hóa tài liệu địa chí theo kế hoạch 2027–2031")},
    "VT06": {2029: (-0.5, "Mở rộng mượn trả tự động RFID toàn bộ phòng đọc")},
}


def load_sample(project):
    for ma, ten, cc in A1:
        project.add_row("A1", dict(ma=ma, ten=ten, co_quan=UNIT, can_cu=cc, ky=DEFAULT_KY,
                                   trang_thai="Tiếp tục thực hiện", nguon=NGUON), notify=False)
    for ma, nv, vt, ten, sp, dvt, cl in A2:
        project.add_row("A2", dict(ma=ma, ma_nv=nv, ma_vt=vt, ten=ten, san_pham=sp, dvt=dvt, chat_luong=cl,
                                   can_cu=f"Kế hoạch công tác năm; {QD}"), notify=False)
    for cv, sl, phut, tt, ntg, extra in B1:
        project.add_row("B1", dict(ma_cv=cv, so_sp=sl, phut_do=phut, gio_bo_sung=extra,
                                   nguon_sl="Báo cáo thống kê kỳ 01/10/2025 - 30/9/2026", nguon_tg=ntg, tt_tg=tt,
                                   ky=DEFAULT_KY), notify=False)
    for cv, loai, cd, sp, ft, fs, moi, ng in B2:
        project.add_row("B2", dict(ma_cv=cv, loai=loai, cong_doan=cd, sp_ap_dung=sp, phut_truoc=ft, phut_sau=fs,
                                   gio_moi=moi, nguon=ng, ky=DEFAULT_KY, co_so="Trước thay đổi, có điều chỉnh",
                                   trang_thai="Đã kiểm chứng", doi_chieu="Đã đối chiếu"), notify=False)
    for ma, ten, loai, pp, n1, _ in C1:
        project.add_row("C1", dict(ma=ma, ten=ten, loai_nl=loai, quyet_dinh="QĐ phê duyệt danh mục VTVL (minh họa)",
                                   can_cu_quy_gio="Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ "
                                                  "làm việc", trang_thai="Tiếp tục sử dụng",
                                   che_do="Phổ biến (40 giờ/tuần)"), notify=False)
        lead = ma in ("VT01", "VT02", "VT03")
        project.add_row("C2", dict(
            ma_vt=ma, trach_nhiem=f"Chịu trách nhiệm về kết quả: {ten.lower()}.",
            nl_chung="Đạo đức nghề nghiệp; giao tiếp; phối hợp; năng lực số (mức 3)",
            chuyen_mon="Nghiệp vụ thư viện – thông tin (mức 3–4)" if loai == "Viên chức" else "Nghiệp vụ bảo vệ",
            lanh_dao="Hoạch định, tổ chức, kiểm tra (mức 4)" if lead else "",
            can_cu="Phụ lục IV Nghị định 232/2026/NĐ-CP",
            nguon_mo_ta=f"HoSo_VTVL/{ma}_MoTa_KhungNangLuc.docx"), notify=False)
        project.add_row("C3", dict(ma_vt=ma, pp=pp, nguoi_pp1=n1, trang_thai="Đã kiểm chứng",
                                   giai_trinh=PP1_NOTE.get(ma, "")), notify=False)

    # C3: kết luận số người cần bố trí (PP2 làm tròn đến 0,5 gần nhất, không làm tròn tăng cơ học)
    calc = Calculator(project)
    for r in project.rows("C3"):
        sug = calc.suggested_need(r)
        chosen = round(sug * 2) / 2
        note = r.get("giai_trinh") or (f"Giờ ròng ÷ 1.904 = {fmt(sug, 3)} người quy đổi; bố trí {fmt(chosen)} "
                                       "người, phần lẻ kiêm nhiệm/dùng chung trong phòng.")
        project.update_row(r["_id"], dict(nguoi_can=chosen, giai_trinh=note), notify=False)

    # D1: mỗi người một mã nguồn lực
    n = 0
    for ma, _, loai, _, _, cnt in C1:
        for _ in range(cnt):
            n += 1
            project.add_row("D1", dict(ma_nl=f"NL{n:03d}", ma_vt=ma, loai_nl=loai, gio_vtvl=1904, gio_khac=0,
                                       noi_bc=UNIT, nguon="Hồ sơ nhân sự chốt 30/9/2026",
                                       trang_thai="Đã kiểm chứng"), notify=False)

    # Dự báo 2027–2031
    for ma, *_ in C1:
        acc, note = 0.0, "Không đổi so với năm cơ sở"
        for y in YEARS:
            if y in FORECAST.get(ma, {}):
                d, note = FORECAST[ma][y]
                acc += d
            project.add_row("DB", dict(ma_vt=ma, nam=str(y), bien_dong=acc, noi_dung=note,
                                       can_cu="Kế hoạch phát triển Thư viện 2027–2031 (minh họa)",
                                       trang_thai="Đã kiểm chứng"), notify=False)

    # D2: phương án từng năm
    calc = Calculator(project)
    for ma, *_ in C1:
        avail = calc.existing(ma)[0]
        for y in YEARS:
            need = calc.forecast(ma, str(y))
            need = need if need != "" else 0
            de_nghi = need - avail
            if abs(de_nghi) < 0.5:
                dc, gt = "Giữ ổn định", "Nhân lực hiện có đáp ứng nhu cầu."
            elif de_nghi > 0:
                dc, gt = "Bố trí lại nội bộ trước khi đề nghị", "Còn thiếu sau khi đã xem xét bố trí lại, kiêm nhiệm."
            else:
                dc, gt = "Điều chuyển sang vị trí còn thiếu", "Dư so với nhu cầu, điều chuyển nội bộ."
            project.add_row("D2", dict(ma_vt=ma, nam=str(y), co_the_bt=avail, dieu_chuyen=dc, de_nghi=round(de_nghi, 3),
                                       giai_trinh=gt, trang_thai="Đã hoàn thành ở đơn vị"), notify=False)
    project.set_meta("du_lieu_mau", "1", notify=False)
    project.set_meta("bc_giao", "28", notify=False)


def ensure_defaults(project):
    """Tạo danh mục căn cứ pháp lý mặc định cho hồ sơ mới."""
    from .guide import LEGAL_BASES

    if project.count("CC") == 0 and project.get_meta("cc_seeded") != "1":
        for so, ngay, cq, ty in LEGAL_BASES:
            project.add_row("CC", dict(so_hieu=so, ngay=ngay, co_quan=cq, trich_yeu=ty,
                                       hieu_luc="Đang áp dụng"), notify=False)
        project.set_meta("cc_seeded", "1", notify=False)
