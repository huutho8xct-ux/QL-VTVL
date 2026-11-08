"""Đặc tả 09 biểu nghiệp vụ theo Hướng dẫn 07-HD/BTCTW (19/10/2026).

Mỗi biểu gồm danh sách cột. Kiểu cột:
  text     - văn bản một dòng
  memo     - văn bản nhiều dòng
  int      - số nguyên
  float    - số thực
  choice   - chọn trong danh sách ``options``
  ref      - tham chiếu mã của biểu khác (``ref`` = mã biểu)
  multiref - danh sách mã công việc (có thể kèm tỷ lệ, ví dụ "CV01, CV02*0.5")
  calc     - cột tính tự động, chỉ đọc
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Col:
    key: str
    label: str
    kind: str = "text"
    width: int = 140
    options: tuple = ()
    ref: str = ""
    required: bool = False
    tip: str = ""


@dataclass(frozen=True)
class Form:
    code: str
    title: str
    step: int
    columns: tuple
    key_col: str = ""
    note: str = ""
    sync_from: str = ""  # biểu nguồn để tạo dòng tự động (theo mã VTVL)

    def col(self, key: str) -> Col:
        for c in self.columns:
            if c.key == key:
                return c
        raise KeyError(key)

    @property
    def editable_columns(self):
        return [c for c in self.columns if c.kind != "calc"]


NHOM_NHIEM_VU = (
    "Tham mưu, quản lý",
    "Chuyên môn, nghiệp vụ thư viện",
    "Chuyên môn dùng chung",
    "Hỗ trợ, phục vụ",
)
TINH_TRANG_NV = ("Giữ nguyên", "Bổ sung mới", "Điều chỉnh", "Đề nghị bãi bỏ")
TAN_SUAT = ("Thường xuyên", "Định kỳ", "Theo mùa vụ", "Đột xuất")
NGUON_XAC_NHAN = (
    "Sổ sách, hồ sơ lưu trữ",
    "Dữ liệu phần mềm quản lý thư viện",
    "Báo cáo thống kê định kỳ",
    "Khảo sát, bấm giờ thực tế",
    "Định mức kinh tế - kỹ thuật",
    "Ước tính (cần bổ sung minh chứng)",
)
YEU_TO_B2 = (
    "Chuyển đổi số",
    "Tự chủ tài chính",
    "Thuê dịch vụ",
    "Xã hội hóa",
    "Thay đổi quy trình",
    "Nhiệm vụ mới phát sinh",
)
NHOM_VTVL = (
    "Lãnh đạo, quản lý",
    "Chức danh nghề nghiệp chuyên ngành",
    "Chuyên môn dùng chung",
    "Hỗ trợ, phục vụ",
)
LOAI_HINH = ("Viên chức", "Hợp đồng lao động (NĐ 111/2022)", "Kiêm nhiệm")
TINH_TRANG_VTVL = (
    "Tiếp tục sử dụng",
    "Cần điều chỉnh",
    "Tích hợp",
    "Đề nghị bổ sung",
    "Đề nghị bãi bỏ",
)
PHUONG_PHAP = (
    "PP2 - Khối lượng, thời gian",
    "PP1 - Cơ cấu, định mức",
    "PP3 - Thẩm định sản phẩm",
    "Kết hợp",
)
NGUON_KINH_PHI = (
    "Ngân sách nhà nước",
    "Nguồn thu sự nghiệp",
    "Hỗn hợp",
)

YEARS = (2027, 2028, 2029, 2030, 2031)

A1 = Form(
    "A1", "Danh mục nhiệm vụ", 1,
    (
        Col("ma", "Mã nhiệm vụ", "text", 95, required=True, tip="Ví dụ: NV01"),
        Col("ten", "Tên nhiệm vụ", "memo", 320, required=True),
        Col("can_cu", "Căn cứ pháp lý (văn bản, điều, khoản)", "memo", 240, required=True),
        Col("nhom", "Nhóm nhiệm vụ", "choice", 190, NHOM_NHIEM_VU, required=True),
        Col("don_vi", "Phòng/bộ phận chủ trì", "text", 170, required=True),
        Col("tinh_trang", "Kết quả rà soát", "choice", 130, TINH_TRANG_NV, required=True),
        Col("ghi_chu", "Ghi chú", "memo", 180),
    ),
    key_col="ma",
    note="Liệt kê đầy đủ nhiệm vụ theo quyết định chức năng, nhiệm vụ còn hiệu lực; "
         "không xuất phát từ người hiện có.",
)

A2 = Form(
    "A2", "Công việc và sản phẩm", 2,
    (
        Col("ma", "Mã công việc", "text", 95, required=True, tip="Ví dụ: CV01"),
        Col("ma_nv", "Thuộc nhiệm vụ", "ref", 105, ref="A1", required=True),
        Col("ten", "Tên công việc", "memo", 280, required=True),
        Col("cong_doan", "Các công đoạn chính", "memo", 240),
        Col("san_pham", "Sản phẩm đầu ra", "memo", 200, required=True),
        Col("dvt", "Đơn vị tính", "text", 100, required=True),
        Col("don_vi", "Phòng/bộ phận thực hiện", "text", 160, required=True),
        Col("tan_suat", "Tần suất", "choice", 120, TAN_SUAT),
        Col("ghi_chu", "Ghi chú", "memo", 160),
    ),
    key_col="ma",
    note="Từ mỗi nhiệm vụ xác định công việc, công đoạn chính, sản phẩm và đơn vị chịu trách nhiệm.",
)

B1 = Form(
    "B1", "Khối lượng và thời gian thực hiện công việc", 3,
    (
        Col("ma_cv", "Mã công việc", "ref", 105, ref="A2", required=True),
        Col("ten_cv", "Tên công việc", "calc", 240),
        Col("so_luong", "Số lượng sản phẩm/năm", "float", 130, required=True),
        Col("gio_sp", "Thời gian lao động trực tiếp/1 SP (giờ)", "float", 150, required=True,
            tip="Chỉ tính thời gian người thực sự làm, không tính thời hạn trả kết quả, thời gian chờ"),
        Col("tong_gio", "Tổng giờ/năm", "calc", 110),
        Col("ky", "Kỳ số liệu", "text", 110, tip="Ví dụ: 2024-2025 (bình quân)"),
        Col("nguon", "Nguồn xác nhận", "choice", 210, NGUON_XAC_NHAN, required=True),
        Col("ghi_chu", "Ghi chú", "memo", 160),
    ),
    key_col="ma_cv",
    note="Ghi số sản phẩm thực tế, thời gian lao động trực tiếp và nguồn xác nhận trong kỳ.",
)

B2 = Form(
    "B2", "Tác động của chuyển đổi số, tự chủ, thuê dịch vụ và xã hội hóa", 4,
    (
        Col("ma_cv", "Mã công việc", "ref", 105, ref="A2", required=True),
        Col("ten_cv", "Tên công việc", "calc", 220),
        Col("yeu_to", "Yếu tố tác động", "choice", 160, YEU_TO_B2, required=True),
        Col("mo_ta", "Công đoạn thay đổi thực tế", "memo", 240, required=True),
        Col("ty_le", "Tỷ lệ áp dụng (%)", "float", 100),
        Col("gio_thay_doi", "Giờ tăng (+)/giảm (−) mỗi năm", "float", 140, required=True),
        Col("nam_ap_dung", "Năm bắt đầu áp dụng", "int", 110),
        Col("can_cu", "Căn cứ, minh chứng", "memo", 200),
    ),
    note="Chỉ ghi công đoạn thực tế thay đổi, đo số lượng áp dụng và thời gian; "
         "số âm là giờ giảm, số dương là giờ tăng.",
)

C1 = Form(
    "C1", "Danh mục vị trí việc làm", 5,
    (
        Col("ma", "Mã VTVL", "text", 95, required=True, tip="Ví dụ: VT01"),
        Col("ten", "Tên vị trí việc làm", "memo", 240, required=True),
        Col("nhom", "Nhóm vị trí việc làm", "choice", 210, NHOM_VTVL, required=True),
        Col("chuc_danh", "Chức danh nghề nghiệp/hạng tương ứng", "text", 210, required=True),
        Col("ma_cdnn", "Mã số CDNN", "text", 100),
        Col("don_vi", "Phòng/bộ phận", "text", 150, required=True),
        Col("loai_hinh", "Loại hình", "choice", 170, LOAI_HINH, required=True),
        Col("tinh_trang", "Kết quả rà soát", "choice", 140, TINH_TRANG_VTVL, required=True),
        Col("can_cu", "Căn cứ", "memo", 200),
    ),
    key_col="ma",
    note="Đối chiếu từng vị trí với chức năng, nhiệm vụ, công việc và sản phẩm để phân nhóm: "
         "tiếp tục sử dụng, cần điều chỉnh, tích hợp, đề nghị bổ sung hoặc bãi bỏ.",
)

C2 = Form(
    "C2", "Bản mô tả công việc và khung năng lực", 5,
    (
        Col("ma_vt", "Mã VTVL", "ref", 95, ref="C1", required=True),
        Col("ten_vt", "Tên VTVL", "calc", 200),
        Col("muc_tieu", "Mục tiêu vị trí", "memo", 220, required=True),
        Col("cong_viec", "Công việc chủ yếu", "memo", 260, required=True),
        Col("trinh_do", "Trình độ đào tạo", "text", 150, required=True),
        Col("chuyen_nganh", "Chuyên ngành", "text", 170),
        Col("boi_duong", "Bồi dưỡng, chứng chỉ", "memo", 180),
        Col("kinh_nghiem", "Kinh nghiệm", "text", 140),
        Col("nl_chung", "Năng lực chung", "memo", 200),
        Col("nl_chuyen_mon", "Năng lực chuyên môn", "memo", 200, required=True),
        Col("nl_quan_ly", "Năng lực quản lý", "memo", 180),
    ),
    key_col="ma_vt",
    sync_from="C1",
)

C3 = Form(
    "C3", "Xác định nhu cầu nhân lực", 6,
    (
        Col("ma_vt", "Mã VTVL", "ref", 95, ref="C1", required=True),
        Col("ten_vt", "Tên VTVL", "calc", 200),
        Col("phuong_phap", "Phương pháp", "choice", 190, PHUONG_PHAP, required=True),
        Col("ds_cv", "Công việc đảm nhận (mã CV, tỷ lệ)", "multiref", 210, ref="A2",
            tip="Nhấp đúp để chọn. Ví dụ: CV01, CV02*0.5 (đảm nhận 50% CV02)"),
        Col("gio_b1", "Giờ từ B1", "calc", 90),
        Col("gio_b2", "Giờ điều chỉnh B2", "calc", 100),
        Col("gio_can", "Tổng giờ cần thiết", "calc", 105),
        Col("quy_gio", "Quỹ giờ/người/năm", "float", 105,
            tip="Mặc định 1.904 giờ (40 giờ/tuần); chỉ dùng mức đặc thù khi đã được xác nhận"),
        Col("nguoi_quy_doi", "Số người quy đổi (PP2)", "calc", 110),
        Col("nguoi_dinh_muc", "Số người theo định mức/thẩm định (PP1/PP3)", "float", 150),
        Col("nguoi_can", "Số người cần bố trí", "float", 110, required=True),
        Col("giai_trinh", "Giải trình", "memo", 240),
    ),
    key_col="ma_vt",
    sync_from="C1",
    note="Số người quy đổi = Tổng giờ cần thiết ÷ Quỹ giờ của 1 người/năm. "
         "Không làm tròn cơ học; nhu cầu tính được không tự động trở thành biên chế.",
)

D1 = Form(
    "D1", "Đối chiếu nguồn nhân lực hiện có", 7,
    (
        Col("ma_vt", "Mã VTVL", "ref", 95, ref="C1", required=True),
        Col("ten_vt", "Tên VTVL", "calc", 200),
        Col("nguoi_can", "Số người cần (C3)", "calc", 100),
        Col("vien_chuc", "Viên chức hiện có", "float", 100),
        Col("hop_dong", "Hợp đồng lao động hiện có", "float", 120),
        Col("hien_co", "Tổng hiện có", "calc", 90),
        Col("chenh_lech", "Chênh lệch (+ thừa / − thiếu)", "calc", 130),
        Col("giao", "Số lượng người làm việc được giao", "float", 140),
        Col("kinh_phi", "Nguồn kinh phí", "choice", 160, NGUON_KINH_PHI),
        Col("giai_trinh", "Giải trình", "memo", 220),
    ),
    key_col="ma_vt",
    sync_from="C1",
    note="Đối chiếu cùng kỳ, cùng phạm vi, cùng đơn vị tính. Nhân lực hiện có chỉ dùng để đối chiếu, "
         "không làm đầu vào xác định vị trí việc làm.",
)

D2 = Form(
    "D2", "Phương án biên chế giai đoạn 2027 - 2031", 7,
    (
        Col("ma_vt", "Mã VTVL", "ref", 95, ref="C1", required=True),
        Col("ten_vt", "Tên VTVL", "calc", 200),
        Col("nguoi_can", "Số người cần (C3)", "calc", 95),
        Col("hien_co", "Hiện có (D1)", "calc", 85),
    )
    + tuple(Col(f"y{y}", f"Năm {y}", "float", 80) for y in YEARS)
    + (
        Col("dieu_chuyen", "Điều chuyển, tinh giản, bố trí lại", "memo", 200),
        Col("de_nghi", "Đề nghị", "memo", 180),
        Col("giai_trinh", "Giải trình", "memo", 220),
    ),
    key_col="ma_vt",
    sync_from="C1",
    note="Lộ trình số người làm việc từng năm của giai đoạn 2027 - 2031.",
)

FORMS = {f.code: f for f in (A1, A2, B1, B2, C1, C2, C3, D1, D2)}
FORM_ORDER = ("A1", "A2", "B1", "B2", "C1", "C2", "C3", "D1", "D2")

DEFAULT_QUY_GIO = 1904.0

# Danh mục căn cứ pháp lý (không thuộc 09 biểu, người dùng có thể cập nhật)
CC = Form(
    "CC", "Căn cứ pháp lý", 0,
    (
        Col("so_hieu", "Số, ký hiệu văn bản", "text", 220, required=True),
        Col("ngay", "Ngày ban hành", "text", 110),
        Col("co_quan", "Cơ quan ban hành", "text", 180),
        Col("trich_yeu", "Trích yếu / nội dung áp dụng", "memo", 520),
        Col("hieu_luc", "Tình trạng", "choice", 130, ("Đang áp dụng", "Hết hiệu lực", "Dự thảo")),
    ),
    key_col="so_hieu",
)
ALL_FORMS = dict(FORMS, CC=CC)
