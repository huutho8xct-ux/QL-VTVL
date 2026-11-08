"""Dữ liệu minh họa cho Thư viện thành phố Cần Thơ.

Số liệu chỉ mang tính MINH HỌA để làm quen phần mềm; đơn vị cần thay bằng số liệu thực tế
đã được xác nhận.
"""
from __future__ import annotations

from .calc import Calculator, fmt

QD = "Quyết định quy định chức năng, nhiệm vụ, quyền hạn và cơ cấu tổ chức của Thư viện TP Cần Thơ"
LTV = "Luật Thư viện 2019"

P_BGD = "Ban Giám đốc"
P_HC = "Phòng Hành chính - Tổng hợp"
P_NV = "Phòng Nghiệp vụ"
P_PV = "Phòng Phục vụ bạn đọc"
P_TS = "Phòng Thông tin - Thư viện số"
P_TN = "Phòng Thiếu nhi"
P_CS = "Phòng Hoạt động cơ sở"

A1 = [
    ("NV01", "Xây dựng, phát triển tài nguyên thông tin; thu thập, lưu giữ tài liệu địa chí Cần Thơ",
     f"{LTV} (Điều 10, Điều 24); {QD}", "Chuyên môn, nghiệp vụ thư viện", P_NV),
    ("NV02", "Xử lý tài liệu, xây dựng hệ thống tra cứu, cơ sở dữ liệu thư mục",
     f"{LTV} (Điều 25); {QD}", "Chuyên môn, nghiệp vụ thư viện", P_NV),
    ("NV03", "Tổ chức phục vụ người sử dụng thư viện tại chỗ, mượn về nhà",
     f"{LTV} (Điều 26, Điều 27); {QD}", "Chuyên môn, nghiệp vụ thư viện", P_PV),
    ("NV04", "Phục vụ thiếu nhi; tổ chức hoạt động phát triển văn hóa đọc",
     f"{LTV} (Điều 10); Đề án phát triển văn hóa đọc; {QD}", "Chuyên môn, nghiệp vụ thư viện", P_TN),
    ("NV05", "Xây dựng thư viện số, số hóa tài liệu, ứng dụng công nghệ thông tin, chuyển đổi số",
     f"{LTV} (Điều 12); Chương trình chuyển đổi số ngành thư viện; {QD}",
     "Chuyên môn, nghiệp vụ thư viện", P_TS),
    ("NV06", "Luân chuyển tài liệu, hướng dẫn nghiệp vụ cho thư viện cơ sở trên địa bàn",
     f"{LTV} (Điều 10); {QD}", "Chuyên môn, nghiệp vụ thư viện", P_CS),
    ("NV07", "Bảo quản, kiểm kê, thanh lọc tài liệu", f"{LTV} (Điều 28); {QD}",
     "Chuyên môn, nghiệp vụ thư viện", P_NV),
    ("NV08", "Quản lý, điều hành hoạt động của Thư viện", f"{QD}", "Tham mưu, quản lý", P_BGD),
    ("NV09", "Hành chính, tổng hợp, tổ chức cán bộ, văn thư, lưu trữ", f"{QD}",
     "Chuyên môn dùng chung", P_HC),
    ("NV10", "Quản lý tài chính, kế toán, tài sản", f"Luật Kế toán 2015; {QD}",
     "Chuyên môn dùng chung", P_HC),
    ("NV11", "Bảo vệ, phục vụ, vệ sinh trụ sở", f"Nghị định 111/2022/NĐ-CP; {QD}",
     "Hỗ trợ, phục vụ", P_HC),
]

# ma, ma_nv, ten, cong_doan, san_pham, dvt, don_vi, tan_suat
A2 = [
    ("CV01", "NV01", "Bổ sung tài liệu (mua, nhận nộp lưu chiểu, tặng biếu)",
     "Khảo sát nhu cầu; lập danh mục; nhận, kiểm tra; đăng ký cá biệt", "Tài liệu được bổ sung", "bản",
     P_NV, "Thường xuyên"),
    ("CV02", "NV01", "Sưu tầm, thu thập tài liệu địa chí", "Khảo sát; sưu tầm; xử lý sơ bộ",
     "Tài liệu địa chí", "tài liệu", P_NV, "Thường xuyên"),
    ("CV03", "NV02", "Biên mục, phân loại, định từ khóa tài liệu",
     "Phân loại DDC; biên mục MARC21; định từ khóa; kiểm tra", "Biểu ghi thư mục", "biểu ghi", P_NV,
     "Thường xuyên"),
    ("CV04", "NV03", "Phục vụ bạn đọc tại phòng đọc", "Hướng dẫn; tìm tài liệu; xếp giá",
     "Lượt bạn đọc được phục vụ", "lượt", P_PV, "Thường xuyên"),
    ("CV05", "NV03", "Phục vụ mượn, trả tài liệu về nhà", "Kiểm tra thẻ; ghi mượn/trả; nhắc trả",
     "Lượt mượn trả", "lượt", P_PV, "Thường xuyên"),
    ("CV06", "NV03", "Cấp, gia hạn thẻ thư viện", "Tiếp nhận; nhập dữ liệu; in thẻ",
     "Thẻ được cấp", "thẻ", P_PV, "Thường xuyên"),
    ("CV07", "NV04", "Phục vụ bạn đọc thiếu nhi", "Hướng dẫn; kể chuyện; xếp giá",
     "Lượt bạn đọc thiếu nhi", "lượt", P_TN, "Thường xuyên"),
    ("CV08", "NV04", "Tổ chức sự kiện, hoạt động phát triển văn hóa đọc",
     "Lập kế hoạch; chuẩn bị; tổ chức; báo cáo", "Sự kiện được tổ chức", "cuộc", P_TN, "Định kỳ"),
    ("CV09", "NV05", "Số hóa tài liệu (ưu tiên tài liệu địa chí)", "Chọn lọc; quét; xử lý ảnh; tạo metadata",
     "Trang tài liệu số hóa", "trang", P_TS, "Thường xuyên"),
    ("CV10", "NV05", "Quản trị hệ thống phần mềm, website, thư viện số", "Vận hành; sao lưu; cập nhật",
     "Tháng vận hành ổn định", "tháng", P_TS, "Thường xuyên"),
    ("CV11", "NV06", "Luân chuyển tài liệu đến thư viện, điểm bưu điện văn hóa xã",
     "Chọn sách; đóng gói; vận chuyển; thu hồi", "Lượt luân chuyển", "lượt", P_CS, "Định kỳ"),
    ("CV12", "NV06", "Hướng dẫn, kiểm tra nghiệp vụ thư viện cơ sở", "Khảo sát; tập huấn; báo cáo",
     "Đơn vị được hướng dẫn", "đơn vị", P_CS, "Định kỳ"),
    ("CV13", "NV07", "Bảo quản, kiểm kê, thanh lọc tài liệu", "Vệ sinh; tu bổ; kiểm kê; lập danh mục thanh lọc",
     "Bản tài liệu được kiểm kê, bảo quản", "bản", P_NV, "Định kỳ"),
    ("CV14", "NV09", "Văn thư, lưu trữ, tổng hợp báo cáo", "Tiếp nhận; trình; phát hành; lưu",
     "Văn bản đến, đi", "văn bản", P_HC, "Thường xuyên"),
    ("CV17", "NV08", "Chỉ đạo, điều hành, kiểm tra hoạt động của Thư viện", "Xây dựng kế hoạch; chỉ đạo; kiểm tra; sơ kết",
     "Kế hoạch, văn bản chỉ đạo", "văn bản", P_BGD, "Thường xuyên"),
    ("CV18", "NV11", "Bảo vệ trụ sở, tài sản 24/7", "Trực ca; tuần tra; phòng cháy chữa cháy",
     "Ca trực", "ca", P_HC, "Thường xuyên"),
    ("CV15", "NV09", "Tổ chức cán bộ, thi đua - khen thưởng, tổng hợp", "Tham mưu; lập hồ sơ; báo cáo",
     "Hồ sơ, báo cáo", "hồ sơ", P_HC, "Thường xuyên"),
    ("CV16", "NV10", "Kế toán, quản lý tài chính, tài sản", "Lập dự toán; chứng từ; quyết toán",
     "Chứng từ kế toán", "chứng từ", P_HC, "Thường xuyên"),
]

# ma_cv, so_luong, gio_sp, nguon
B1 = [
    ("CV01", 6000, 0.25, "Dữ liệu phần mềm quản lý thư viện"),
    ("CV02", 350, 2.0, "Sổ sách, hồ sơ lưu trữ"),
    ("CV03", 7000, 0.45, "Dữ liệu phần mềm quản lý thư viện"),
    ("CV04", 85000, 0.05, "Báo cáo thống kê định kỳ"),
    ("CV05", 60000, 0.06, "Dữ liệu phần mềm quản lý thư viện"),
    ("CV06", 2500, 0.3, "Dữ liệu phần mềm quản lý thư viện"),
    ("CV07", 40000, 0.06, "Báo cáo thống kê định kỳ"),
    ("CV08", 48, 40, "Báo cáo thống kê định kỳ"),
    ("CV09", 60000, 0.05, "Định mức kinh tế - kỹ thuật"),
    ("CV10", 12, 150, "Khảo sát, bấm giờ thực tế"),
    ("CV11", 120, 18, "Sổ sách, hồ sơ lưu trữ"),
    ("CV12", 45, 30, "Báo cáo thống kê định kỳ"),
    ("CV13", 150000, 0.015, "Định mức kinh tế - kỹ thuật"),
    ("CV14", 3200, 0.5, "Dữ liệu phần mềm quản lý thư viện"),
    ("CV15", 180, 8, "Sổ sách, hồ sơ lưu trữ"),
    ("CV16", 2600, 0.7, "Sổ sách, hồ sơ lưu trữ"),
    ("CV17", 300, 8, "Sổ sách, hồ sơ lưu trữ"),
    ("CV18", 1095, 8, "Sổ sách, hồ sơ lưu trữ"),
]

B2 = [
    ("CV05", "Chuyển đổi số", "Mượn trả tự động bằng RFID, máy tự mượn trả", 40, -900, 2027,
     "Kế hoạch chuyển đổi số của Thư viện"),
    ("CV03", "Chuyển đổi số", "Biên mục sao chép từ cơ sở dữ liệu liên thông", 30, -650, 2027,
     "Kết quả thử nghiệm năm 2026"),
    ("CV09", "Nhiệm vụ mới phát sinh", "Tăng khối lượng số hóa tài liệu địa chí sau hợp nhất tỉnh", 100, 600,
     2027, "Kế hoạch số hóa giai đoạn 2027 - 2031"),
    ("CV08", "Xã hội hóa", "Phối hợp doanh nghiệp, trường học đồng tổ chức sự kiện", 25, -320, 2027,
     "Biên bản phối hợp"),
]

# ma, ten, nhom, chuc_danh, ma_cdnn, don_vi, loai_hinh
C1 = [
    ("VT01", "Giám đốc", "Lãnh đạo, quản lý", "Thư viện viên hạng II trở lên", "V.10.02.06", P_BGD, "Viên chức"),
    ("VT02", "Phó Giám đốc", "Lãnh đạo, quản lý", "Thư viện viên hạng II trở lên", "V.10.02.06", P_BGD,
     "Viên chức"),
    ("VT03", "Trưởng phòng và tương đương", "Lãnh đạo, quản lý", "Thư viện viên hạng III trở lên",
     "V.10.02.07", "Các phòng", "Viên chức"),
    ("VT04", "Phát triển tài nguyên thông tin", "Chức danh nghề nghiệp chuyên ngành", "Thư viện viên hạng III",
     "V.10.02.07", P_NV, "Viên chức"),
    ("VT05", "Xử lý tài liệu, xây dựng hệ thống tra cứu", "Chức danh nghề nghiệp chuyên ngành",
     "Thư viện viên hạng III", "V.10.02.07", P_NV, "Viên chức"),
    ("VT06", "Phục vụ người sử dụng thư viện", "Chức danh nghề nghiệp chuyên ngành", "Thư viện viên hạng IV",
     "V.10.02.08", P_PV, "Viên chức"),
    ("VT07", "Phục vụ thiếu nhi, phát triển văn hóa đọc", "Chức danh nghề nghiệp chuyên ngành",
     "Thư viện viên hạng III", "V.10.02.07", P_TN, "Viên chức"),
    ("VT08", "Thư viện số, số hóa và công nghệ thông tin", "Chức danh nghề nghiệp chuyên ngành",
     "Thư viện viên hạng III", "V.10.02.07", P_TS, "Viên chức"),
    ("VT09", "Hoạt động thư viện cơ sở, luân chuyển tài liệu", "Chức danh nghề nghiệp chuyên ngành",
     "Thư viện viên hạng III", "V.10.02.07", P_CS, "Viên chức"),
    ("VT10", "Bảo quản tài liệu", "Chức danh nghề nghiệp chuyên ngành", "Thư viện viên hạng IV",
     "V.10.02.08", P_NV, "Viên chức"),
    ("VT11", "Kế toán", "Chuyên môn dùng chung", "Kế toán viên", "06.031", P_HC, "Viên chức"),
    ("VT12", "Hành chính - tổng hợp, văn thư", "Chuyên môn dùng chung", "Chuyên viên/Văn thư viên",
     "01.003", P_HC, "Viên chức"),
    ("VT13", "Bảo vệ", "Hỗ trợ, phục vụ", "Nhân viên bảo vệ", "", P_HC, "Hợp đồng lao động (NĐ 111/2022)"),
]

# ma_vt, phuong_phap, ds_cv, nguoi_dinh_muc, giai_trinh
C3 = [
    ("VT01", "PP1 - Cơ cấu, định mức", "CV17*0.4", 1, "Theo cơ cấu tổ chức: 01 Giám đốc."),
    ("VT02", "PP1 - Cơ cấu, định mức", "CV17*0.6", 2, "Theo quy định số lượng cấp phó của đơn vị sự nghiệp."),
    ("VT03", "PP1 - Cơ cấu, định mức", "", 6, "06 phòng chuyên môn theo cơ cấu tổ chức (trưởng phòng)."),
    ("VT04", "PP2 - Khối lượng, thời gian", "CV01, CV02", None, ""),
    ("VT05", "PP2 - Khối lượng, thời gian", "CV03", None, ""),
    ("VT06", "PP2 - Khối lượng, thời gian", "CV04, CV05, CV06", None, ""),
    ("VT07", "PP2 - Khối lượng, thời gian", "CV07, CV08", None, ""),
    ("VT08", "PP2 - Khối lượng, thời gian", "CV09, CV10", None, ""),
    ("VT09", "PP2 - Khối lượng, thời gian", "CV11, CV12", None, ""),
    ("VT10", "PP2 - Khối lượng, thời gian", "CV13", None, ""),
    ("VT11", "PP2 - Khối lượng, thời gian", "CV16", None, ""),
    ("VT12", "PP2 - Khối lượng, thời gian", "CV14, CV15", None, ""),
    ("VT13", "PP1 - Cơ cấu, định mức", "CV18", 3,
     "Bảo vệ 24/7 theo ca (3 ca/ngày); xem xét thuê dịch vụ theo NĐ 111/2022."),
]

# ma_vt: (vien_chuc, hop_dong, giao, kinh_phi)
D1 = {
    "VT01": (1, 0, 1), "VT02": (2, 0, 2), "VT03": (6, 0, 6), "VT04": (2, 0, 2), "VT05": (2, 0, 2),
    "VT06": (5, 0, 6), "VT07": (2, 1, 2), "VT08": (1, 0, 1), "VT09": (2, 0, 2), "VT10": (1, 0, 1),
    "VT11": (1, 0, 1), "VT12": (2, 0, 2), "VT13": (0, 3, 0),
}


def load_sample(project):
    for ma, ten, cc, nhom, dv in A1:
        project.add_row("A1", dict(ma=ma, ten=ten, can_cu=cc, nhom=nhom, don_vi=dv, tinh_trang="Giữ nguyên"),
                        notify=False)
    for ma, nv, ten, cd, sp, dvt, dv, ts in A2:
        project.add_row("A2", dict(ma=ma, ma_nv=nv, ten=ten, cong_doan=cd, san_pham=sp, dvt=dvt, don_vi=dv,
                                   tan_suat=ts), notify=False)
    for cv, sl, g, nguon in B1:
        project.add_row("B1", dict(ma_cv=cv, so_luong=sl, gio_sp=g, ky="Bình quân 2024 - 2026", nguon=nguon),
                        notify=False)
    for cv, yt, mt, tl, gio, nam, cc in B2:
        project.add_row("B2", dict(ma_cv=cv, yeu_to=yt, mo_ta=mt, ty_le=tl, gio_thay_doi=gio, nam_ap_dung=nam,
                                   can_cu=cc), notify=False)
    for ma, ten, nhom, cd, mcd, dv, lh in C1:
        project.add_row("C1", dict(ma=ma, ten=ten, nhom=nhom, chuc_danh=cd, ma_cdnn=mcd, don_vi=dv,
                                   loai_hinh=lh, tinh_trang="Tiếp tục sử dụng",
                                   can_cu="Thông tư 10/2023/TT-BVHTTDL" if nhom != "Hỗ trợ, phục vụ"
                                   else "Nghị định 111/2022/NĐ-CP"), notify=False)
        project.add_row("C2", dict(
            ma_vt=ma,
            muc_tieu=f"Bảo đảm thực hiện hiệu quả nhiệm vụ: {ten.lower()}.",
            cong_viec="Theo danh mục công việc đảm nhận tại Biểu C3.",
            trinh_do="Đại học trở lên" if nhom != "Hỗ trợ, phục vụ" else "Tốt nghiệp THPT",
            chuyen_nganh="Thư viện - Thông tin hoặc phù hợp" if "chuyên ngành" in nhom or "Lãnh đạo" in nhom
            else "Phù hợp vị trí",
            boi_duong="Bồi dưỡng tiêu chuẩn chức danh nghề nghiệp" if nhom != "Hỗ trợ, phục vụ" else "",
            nl_chung="Đạo đức công vụ; giao tiếp; làm việc nhóm; ứng dụng công nghệ số",
            nl_chuyen_mon=f"Nắm vững nghiệp vụ {ten.lower()}",
            nl_quan_ly="Lập kế hoạch, tổ chức, điều hành" if nhom == "Lãnh đạo, quản lý" else "",
        ), notify=False)
    for vt, pp, ds, dm, gt in C3:
        project.add_row("C3", dict(ma_vt=vt, phuong_phap=pp, ds_cv=ds, nguoi_dinh_muc=dm, giai_trinh=gt),
                        notify=False)

    # Số người cần bố trí: lấy kết quả tính, làm tròn đến 0,5 gần nhất (không làm tròn lên cơ học)
    calc = Calculator(project)
    for r in project.rows("C3"):
        sug = calc.suggested_need(r)
        chosen = round(sug * 2) / 2
        note = r.get("giai_trinh") or (
            f"Kết quả quy đổi {fmt(sug, 3)} người; đề xuất {fmt(chosen)} người, phần lẻ bố trí kiêm nhiệm.")
        project.update_row(r["_id"], dict(nguoi_can=chosen, giai_trinh=note), notify=False)

    calc = Calculator(project)
    for vt, (vc, hd, giao) in D1.items():
        need = calc.need(vt)
        diff = vc + hd - need
        gt = ""
        if abs(diff) >= 0.5:
            gt = ("Bố trí lại, tinh giản theo lộ trình." if diff > 0
                  else "Bổ sung qua tuyển dụng hoặc điều chuyển nội bộ.")
        project.add_row("D1", dict(ma_vt=vt, vien_chuc=vc, hop_dong=hd, giao=giao,
                                   kinh_phi="Ngân sách nhà nước", giai_trinh=gt), notify=False)
        cur = vc + hd
        row = dict(ma_vt=vt)
        for i, y in enumerate((2027, 2028, 2029, 2030, 2031)):
            # tiến dần từ hiện có đến nhu cầu trong 5 năm
            v = cur + (need - cur) * (i + 1) / 5
            row[f"y{y}"] = round(v * 2) / 2
        row["dieu_chuyen"] = "Giữ ổn định" if abs(diff) < 0.5 else (
            "Tinh giản, bố trí lại" if diff > 0 else "Tuyển dụng bổ sung")
        row["giai_trinh"] = "Lộ trình điều chỉnh dần theo nhu cầu đã xác định tại Biểu C3."
        project.add_row("D2", row, notify=False)
    project.set_meta("du_lieu_mau", "1")


def ensure_defaults(project):
    """Tạo danh mục căn cứ pháp lý mặc định cho hồ sơ mới."""
    from .guide import LEGAL_BASES

    if project.count("CC") == 0 and project.get_meta("cc_seeded") != "1":
        for so, ngay, cq, ty in LEGAL_BASES:
            project.add_row("CC", dict(so_hieu=so, ngay=ngay, co_quan=cq, trich_yeu=ty,
                                       hieu_luc="Đang áp dụng"), notify=False)
        project.set_meta("cc_seeded", "1", notify=False)
