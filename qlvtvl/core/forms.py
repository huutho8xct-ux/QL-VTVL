"""Đặc tả các biểu nghiệp vụ theo Bộ biểu Excel kèm Hướng dẫn 07-HD/BTCTW (phiên bản 19/10/2026).

Tên cột, thứ tự cột (``letter``), danh sách lựa chọn và quy tắc tính bám sát bộ biểu chính thức.
Kiểu cột:
  text / memo  - văn bản
  int / float  - số
  choice       - chọn trong ``options`` (theo trang DM_THAM_SO)
  ref          - mã tham chiếu biểu khác (``ref``)
  calc         - cột công thức tự động (ô xám trong bộ biểu), chỉ đọc
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Col:
    key: str
    label: str
    kind: str = "text"
    width: int = 130
    options: tuple = ()
    ref: str = ""
    required: bool = False
    tip: str = ""
    letter: str = ""  # cột trong bộ biểu Excel chính thức


@dataclass(frozen=True)
class Form:
    code: str
    title: str
    step: int
    columns: tuple
    key_col: str = ""
    note: str = ""
    sheet: str = ""          # tên trang tính trong bộ biểu chính thức
    virtual: bool = False    # biểu tổng hợp tự động (không nhập)
    capacity: int = 200      # số dòng dữ liệu của bộ biểu

    def col(self, key: str) -> Col:
        for c in self.columns:
            if c.key == key:
                return c
        raise KeyError(key)

    @property
    def input_columns(self):
        return [c for c in self.columns if c.kind != "calc"]


def _c(letter, key, label, kind="text", width=130, options=(), **kw):
    return Col(key, label, kind, width, options, letter=letter, **kw)


# ----------------------------------------------- danh sách lựa chọn (DM_THAM_SO)
TT_A1 = ("Tiếp tục thực hiện", "Mới tiếp nhận", "Đã chuyển giao", "Không còn thực hiện")
TT_B1 = ("Có định mức", "Kiểm đếm, ước lượng thực tế")
KIEM_CHUNG = ("Đã kiểm chứng", "Chưa kiểm chứng")
TT_B2CT = ("Đã kiểm chứng", "Chưa kiểm chứng", "Ước lượng tham khảo")
LOAI_TD = ("Số hóa", "Cải tiến quy trình", "Thuê dịch vụ/đặt hàng", "Tự chủ", "Xã hội hóa",
           "Công việc mới phát sinh")
CO_SO_B1 = ("Trước thay đổi, có điều chỉnh", "Đã đo sau thay đổi (không trừ)")
DOI_CHIEU = ("Chờ đối chiếu", "Đã đối chiếu")
TT_C1 = ("Tiếp tục sử dụng", "Cần cập nhật", "Đề nghị bổ sung", "Đề nghị sửa đổi", "Đề nghị bãi bỏ")
CHE_DO = ("Phổ biến (40 giờ/tuần)", "Đặc thù")
PP = ("PP1", "PP2", "PP3", "PP1+PP2", "PP1+PP3", "PP2+PP3", "PP1+PP2+PP3")
TT_C3 = ("Tính thử", "Chưa đủ dữ liệu", "Đã kiểm chứng", "Không áp dụng")
TT_D2 = ("Đang xây dựng", "Đã hoàn thành ở đơn vị", "Đã thẩm định", "Đã được quyết định")
YEARS = (2027, 2028, 2029, 2030, 2031)
LOAI_NL = ("Cán bộ", "Công chức", "Viên chức", "Hợp đồng lao động", "Khác")
NHOM = ("I", "II", "III", "IV", "V", "VI", "Không phân nhóm")
TT_DM = ("Đang kiểm chứng", "Đã xác nhận", "Không áp dụng")

DEFAULT_QUY_GIO = 1904.0
DEFAULT_KY = "01/10/2025 - 30/9/2026"

# ------------------------------------------------------------------- biểu
A1 = Form(
    "A1", "Danh mục nhiệm vụ", 1,
    (
        _c("A", "ma", "Mã nhiệm vụ", width=95, required=True,
           tip="Mã ổn định; giữ mã nguồn/mã đã xác nhận, nhiệm vụ mới dùng mã tạm. Không đổi mã theo thứ tự dòng."),
        _c("B", "ten", "Tên nhiệm vụ", "memo", 330, required=True,
           tip="Tên đầy đủ, đúng nội dung nhiệm vụ theo văn bản có hiệu lực."),
        _c("C", "co_quan", "Cơ quan", width=190, required=True,
           tip="Tên cơ quan/đơn vị trực tiếp thực hiện nhiệm vụ."),
        _c("D", "can_cu", "Căn cứ", "memo", 240, required=True,
           tip="Số, ký hiệu văn bản, điều/khoản giao nhiệm vụ. Không tự suy diễn căn cứ."),
        _c("E", "ky", "Kỳ", width=150, required=True, tip="Kỳ số liệu hoặc thời điểm chốt áp dụng."),
        _c("F", "trang_thai", "Trạng thái", "choice", 150, TT_A1, required=True),
        _c("G", "nguon", "Nguồn", "memo", 190, required=True,
           tip="Địa chỉ truy vết: công văn/tệp/trang tính/ô hoặc hồ sơ xác nhận."),
    ),
    key_col="ma", sheet="1. A1_NhiemVu",
    note="Ghi từng nhiệm vụ có mã, căn cứ, kỳ và nguồn để liên kết công việc. Nhiệm vụ “khác” chỉ ghi khi có "
         "công việc thực tế và căn cứ giao.",
)

A2 = Form(
    "A2", "Công việc và sản phẩm", 2,
    (
        _c("A", "ma", "Mã công việc", width=95, required=True, tip="Mỗi công việc một mã ổn định."),
        _c("B", "ma_nv", "Mã nhiệm vụ", "ref", 100, ref="A1", required=True),
        _c("C", "ma_vt", "Mã VTVL", "ref", 95, ref="C1", required=True,
           tip="VTVL thực hiện công việc (mã ở Biểu C1). B1, B2 tự lấy mã VTVL từ cột này."),
        _c("D", "ten", "Tên công việc", "memo", 280, required=True,
           tip="Động từ + đối tượng/kết quả, đủ rõ để xác định sản phẩm."),
        _c("E", "san_pham", "Sản phẩm", "memo", 200, required=True),
        _c("F", "dvt", "Đơn vị tính", width=100, required=True),
        _c("G", "chat_luong", "Chất lượng", "memo", 170, tip="Yêu cầu chất lượng/điều kiện nghiệm thu (nhập khi có)."),
        _c("H", "can_cu", "Căn cứ (nguồn)", "memo", 180, required=True),
    ),
    key_col="ma", sheet="2. A2_CongViec",
    note="Phân rã nhiệm vụ thành công việc, sản phẩm gắn với VTVL. Không tách thao tác nhỏ thành nhiệm vụ "
         "hoặc vị trí riêng; không đếm một sản phẩm nhiều lần.",
)

B1 = Form(
    "B1", "Khối lượng và thời gian thực hiện công việc", 3,
    (
        _c("A", "ma_cv", "Mã công việc", "ref", 100, ref="A2", required=True),
        _c("B", "ma_vt", "Mã VTVL", "calc", 80),
        _c("C", "so_sp", "Số SP/năm", "float", 95, tip="Số sản phẩm thực tế trong kỳ 12 tháng."),
        _c("D", "phut_do", "Trung bình phút/SP (đo thực tế)", "float", 115),
        _c("E", "gio_bo_sung", "Giờ bổ sung (công việc liên quan)", "float", 115,
           tip="Giờ/năm của công việc bổ trợ chưa tính trong phút/SP; không cộng trùng."),
        _c("F", "gio_sp", "Giờ SP (tính)", "calc", 90),
        _c("G", "gio_tong", "Giờ tổng (tính)", "calc", 95),
        _c("H", "nguon_sl", "Nguồn SL", "memo", 160, required=True),
        _c("I", "nguon_tg", "Nguồn thời gian", "memo", 170,
           tip="Bắt buộc khi chọn “Có định mức” (số, ngày, điều/khoản). Khi ước lượng: ghi cách đo."),
        _c("J", "tt_tg", "Trạng thái căn cứ thời gian", "choice", 175, TT_B1),
        _c("K", "ky", "Kỳ", width=140, required=True),
        _c("L", "ma_sp", "Mã SP trong danh mục", "ref", 105, ref="DM"),
        _c("M", "nhom", "Nhóm (tự tra)", "calc", 70),
        _c("N", "phut_chuan", "Phút/SP chuẩn (tự tra)", "calc", 90),
        _c("O", "xn_chuan", "Xác nhận chuẩn (tự tra)", "calc", 100),
        _c("P", "phut_tinh", "Phút/SP dùng để tính", "calc", 90),
        _c("Q", "nguon_tinh", "Nguồn thời gian dùng tính", "calc", 170),
        _c("R", "canh_bao", "Cảnh báo dữ liệu", "calc", 190),
        _c("S", "giai_trinh", "Giải trình khác chuẩn", "memo", 170),
    ),
    sheet="3. B1_KhoiLuong",
    note="Giờ SP = Số SP × Phút/SP ÷ 60 (chỉ tính khi Cảnh báo = ĐẠT); Giờ tổng = Giờ SP + Giờ bổ sung. "
         "Tính giờ lao động thực tế, không tính thời gian chờ hay thời hạn xử lý. Chỉ dòng ĐẠT được chuyển sang C3.",
)

DM = Form(
    "DM", "Danh mục sản phẩm dùng chung", 3,
    (
        _c("A", "ma", "Mã sản phẩm chuẩn", width=110, required=True),
        _c("B", "ten", "Tên/loại sản phẩm", "memo", 240, required=True),
        _c("C", "khoi", "Khối/ngành/lĩnh vực", width=150),
        _c("D", "nhom", "Nhóm I–VI (nếu áp dụng)", "choice", 120, NHOM),
        _c("E", "phut_chuan", "Phút/SP chuẩn", "float", 95),
        _c("F", "van_ban", "Văn bản/nguồn xác nhận", "memo", 200),
        _c("G", "trang_thai", "Trạng thái", "choice", 130, TT_DM),
        _c("H", "co_quan_xn", "Cơ quan xác nhận", width=160),
        _c("I", "ngay_hl", "Ngày hiệu lực", width=100),
        _c("J", "pham_vi", "Phạm vi áp dụng/ghi chú", "memo", 180),
    ),
    key_col="ma", sheet="11. DM_SAN_PHAM",
    note="Do cơ quan chuyên ngành/đầu mối quản lý (cơ sở chỉ đọc). Phút chuẩn “Đã xác nhận” được ưu tiên dùng tại B1.",
)

B2 = Form(
    "B2", "Tác động thực tế (B2 chi tiết)", 4,
    (
        _c("A", "ma_cv", "Mã công việc", "ref", 100, ref="A2", required=True),
        _c("B", "ma_vt", "Mã VTVL", "calc", 80),
        _c("C", "loai", "Loại tác động", "choice", 165, LOAI_TD, required=True),
        _c("D", "cong_doan", "Công đoạn", "memo", 200, required=True),
        _c("E", "sp_ap_dung", "SP áp dụng", "float", 90),
        _c("F", "phut_truoc", "Phút trước", "float", 80),
        _c("G", "phut_sau", "Phút sau", "float", 80),
        _c("H", "gio_giam", "Giờ giảm trực tiếp", "calc", 95),
        _c("I", "gio_moi", "Giờ việc mới", "float", 90),
        _c("J", "nguon", "Nguồn/bằng chứng", "memo", 170, required=True),
        _c("K", "ky", "Kỳ", width=130, required=True),
        _c("L", "co_so", "Cơ sở B1", "choice", 200, CO_SO_B1, required=True),
        _c("M", "trang_thai", "Trạng thái", "choice", 140, TT_B2CT, required=True),
        _c("N", "gio_giam_hl", "Giờ giảm hợp lệ", "calc", 95),
        _c("O", "gio_tang_hl", "Giờ tăng hợp lệ", "calc", 95),
        _c("P", "kiem_tra", "Kiểm tra", "calc", 190),
        _c("Q", "kp_truoc", "Kinh phí trước", width=110),
        _c("R", "kp_sau", "Kinh phí sau", width=110),
        _c("S", "doi_chieu", "Đối chiếu trùng/phạm vi (cán bộ xác nhận)", "choice", 150, DOI_CHIEU, required=True),
    ),
    sheet="4. B2_CT_TacDong",
    note="Chỉ ghi tác động có bằng chứng. Giờ giảm = SP áp dụng × (Phút trước − Phút sau) ÷ 60. Không giảm giờ chỉ vì "
         "có phần mềm; nếu B1 đã đo sau thay đổi thì không trừ lại.",
)

B2TH = Form(
    "B2TH", "Thay đổi công việc (B2 tổng hợp)", 4,
    (
        _c("A", "ma_cv", "Mã công việc", "calc", 100),
        _c("B", "ma_vt", "Mã VTVL", "calc", 90),
        _c("C", "giam_so_hoa", "Giờ giảm số hóa", "calc", 110),
        _c("D", "giam_khac", "Giờ giảm thuê/TCh/XHH", "calc", 130),
        _c("E", "gio_moi", "Giờ việc mới", "calc", 100),
        _c("F", "rong", "Giờ tác động ròng", "calc", 120),
        _c("G", "trang_thai", "Trạng thái", "calc", 150),
        _c("H", "so_dong", "Số dòng chi tiết", "calc", 100),
        _c("I", "canh_bao", "Cảnh báo", "calc", 300),
    ),
    sheet="5. B2_ThayDoi", virtual=True,
    note="Tự động tổng hợp từ B2 chi tiết (chỉ dòng ĐẠT). Giờ tác động ròng = Giờ việc mới − Giờ giảm; số âm là giảm giờ.",
)

C1 = Form(
    "C1", "Danh mục vị trí việc làm", 5,
    (
        _c("A", "ma", "Mã VTVL", width=90, required=True, tip="Mã theo danh mục/quyết định có thẩm quyền."),
        _c("B", "ten", "Tên VTVL", "memo", 250, required=True),
        _c("C", "loai_nl", "Loại nhân lực", "choice", 140, LOAI_NL, required=True),
        _c("D", "quyet_dinh", "Quyết định", "memo", 190, tip="Số, ký hiệu, ngày quyết định/danh mục phê duyệt VTVL."),
        _c("E", "gio_pp2", "Giờ chuẩn PP2", "calc", 90),
        _c("F", "can_cu_quy_gio", "Căn cứ xác định quỹ giờ", "memo", 210,
           tip="Chế độ phổ biến: “Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ làm việc”."),
        _c("G", "trang_thai", "Trạng thái", "choice", 150, TT_C1, required=True),
        _c("H", "gio_rieng", "Giờ riêng được xác nhận", "float", 100, tip="Chỉ nhập khi chế độ đặc thù có căn cứ."),
        _c("I", "xn_gio_rieng", "Xác nhận giờ riêng", "choice", 130, KIEM_CHUNG),
        _c("J", "che_do", "Chế độ làm việc", "choice", 170, CHE_DO, required=True),
        _c("K", "kt_quy_gio", "Kiểm tra quỹ giờ PP2", "calc", 150),
    ),
    key_col="ma", sheet="6. C1_VTVL",
    note="Rà soát VTVL: tiếp tục sử dụng, cần cập nhật, đề nghị bổ sung/sửa đổi/bãi bỏ. Một vị trí không đồng nghĩa "
         "một người hay một biên chế; không tạo vị trí từ người hoặc ngạch hiện có.",
)

C2 = Form(
    "C2", "Mô tả trách nhiệm và năng lực", 5,
    (
        _c("A", "ma_vt", "Mã VTVL", "ref", 90, ref="C1", required=True),
        Col("ten_vt", "Tên VTVL", "calc", 200),
        _c("B", "trach_nhiem", "Trách nhiệm", "memo", 250, required=True),
        _c("C", "nl_chung", "Năng lực chung", "memo", 210, required=True),
        _c("D", "chuyen_mon", "Chuyên môn", "memo", 220, required=True),
        _c("E", "lanh_dao", "Lãnh đạo", "memo", 170, tip="Nếu VTVL có chức năng quản lý; không áp dụng thì để trống."),
        _c("F", "can_cu", "Căn cứ", "memo", 190, required=True),
        _c("G", "nguon_mo_ta", "Nguồn bản mô tả", "memo", 190, required=True,
           tip="Mã hồ sơ, tên tệp hoặc đường dẫn nội bộ của bản mô tả, khung năng lực."),
    ),
    key_col="ma_vt", sheet="7. C2_NangLuc",
    note="Tóm tắt trách nhiệm, năng lực theo hồ sơ đã phê duyệt; ghi địa chỉ lưu bản mô tả, không sao chép toàn bộ. "
         "Viên chức áp dụng mẫu Phụ lục IV Nghị định 232/2026/NĐ-CP.",
)

C3 = Form(
    "C3", "Nhu cầu nhân lực", 6,
    (
        _c("A", "ma_vt", "Mã VTVL", "ref", 90, ref="C1", required=True),
        Col("ten_vt", "Tên VTVL", "calc", 190),
        _c("B", "pp", "Phương pháp", "choice", 105, PP, required=True),
        _c("C", "gio_b1", "Giờ B1", "calc", 85),
        _c("D", "gio_b2", "Giờ tác động B2", "calc", 95),
        _c("E", "gio_rong", "Giờ ròng", "calc", 85),
        _c("F", "gio_pp2", "Giờ PP2 (từ C1)", "calc", 85),
        _c("G", "nguoi_qd", "Người quy đổi PP2", "calc", 95),
        _c("H", "nguoi_pp1", "Người PP1", "float", 80),
        _c("I", "nguoi_pp3", "Người PP3 (ước lượng, cần giải trình)", "float", 120),
        _c("J", "nguoi_can", "Người cần bố trí", "float", 95,
           tip="Kết luận sau thẩm định; loại trùng phần việc giữa các phương pháp; không làm tròn tăng cơ học."),
        _c("K", "giai_trinh", "Nguồn/giải trình", "memo", 230),
        _c("L", "trang_thai", "Trạng thái", "choice", 130, TT_C3, required=True),
        _c("M", "canh_bao", "Cảnh báo", "calc", 200),
        _c("N", "b1_chua_dat", "Số dòng B1 chưa đạt", "calc", 90),
    ),
    key_col="ma_vt", sheet="8. C3_NhuCau",
    note="Người quy đổi PP2 = Giờ ròng ÷ Quỹ giờ (1.904). Ví dụ 2.600 ÷ 1.904 ≈ 1,366 người – không tự làm tròn "
         "thành 02 biên chế. PP1/PP3 ghi số người và giải trình, không gán giờ giả định.",
)

D1 = Form(
    "D1", "Nguồn nhân lực hiện có", 7,
    (
        _c("A", "ma_nl", "Mã nguồn lực", width=95, required=True,
           tip="Mã tham chiếu ổn định của người/nguồn lực; hạn chế ghi thông tin cá nhân."),
        _c("B", "ma_vt", "Mã VTVL", "ref", 90, ref="C1", required=True),
        _c("C", "loai_nl", "Loại nhân lực", "choice", 140, LOAI_NL, required=True),
        _c("D", "gio_qd", "Giờ quy đổi/năm (tự lấy)", "calc", 100),
        _c("E", "gio_vtvl", "Giờ dành cho VTVL", "float", 100, required=True),
        _c("F", "gio_khac", "Giờ việc khác", "float", 90, required=True, tip="Nhập 0 nếu không có."),
        _c("G", "noi_bc", "Nơi tính BC", width=170, required=True),
        _c("H", "nguon", "Nguồn", "memo", 160, required=True),
        _c("I", "trang_thai", "Trạng thái", "choice", 130, KIEM_CHUNG, required=True),
        _c("J", "canh_bao", "Cảnh báo", "calc", 140),
        _c("K", "gio_rieng", "Giờ riêng theo chế độ", "float", 100),
    ),
    key_col="ma_nl", sheet="9. D1_NhanLuc",
    note="Nhân lực hiện có chốt tại ngày 30/9/2026. Mỗi người một mã; tổng giờ của một người không vượt quỹ giờ. "
         "Ví dụ: 02 người mỗi người 50% giờ cho một vị trí = 1,0 người quy đổi nhưng vẫn là 02 người thực tế.",
)

DB = Form(
    "DB", "Dự báo nhu cầu 2027 – 2031", 7,
    (
        _c("A", "ma_vt", "Mã VTVL", "ref", 90, ref="C1", required=True),
        _c("B", "nam", "Năm", "choice", 70, tuple(str(y) for y in YEARS), required=True),
        _c("C", "bien_dong", "Biến động so C3 (+/− người)", "float", 110, required=True,
           tip="Nhập 0 nếu không đổi."),
        _c("D", "noi_dung", "Nội dung thay đổi / xác nhận không đổi", "memo", 230, required=True),
        _c("E", "can_cu", "Căn cứ nguồn và thời điểm", "memo", 200, required=True),
        _c("F", "trang_thai", "Trạng thái xác nhận", "choice", 130, KIEM_CHUNG, required=True),
        _c("G", "nguoi_c3", "Người C3 năm cơ sở", "calc", 95),
        _c("H", "nguoi_nam", "Người cần bố trí trong năm", "calc", 105),
        _c("I", "kiem_tra", "Kiểm tra, đối chiếu", "calc", 200),
        _c("J", "ghi_chu", "Ghi chú đầu mối", "memo", 160),
    ),
    sheet="DU_BAO_5_NAM", capacity=1000,
    note="Dự báo từng năm có căn cứ và giải trình; không dùng biên chế năm 2026 làm định mức, không nhân tỷ lệ cố định. "
         "Số người cần bố trí của năm = Người C3 (đã kiểm chứng) + Biến động.",
)

D2 = Form(
    "D2", "Phương án bố trí và biên chế 2027 – 2031", 7,
    (
        _c("A", "ma_vt", "Mã VTVL", "ref", 90, ref="C1", required=True),
        _c("B", "nam", "Năm", "choice", 70, tuple(str(y) for y in YEARS), required=True),
        _c("C", "nguoi_can_nam", "Số người cần bố trí trong năm phương án", "calc", 120),
        _c("D", "co_the_bt", "Số người có thể bố trí (cùng đơn vị tính)", "float", 120, required=True),
        _c("E", "bc_giao", "Biên chế được giao theo đúng cấp", "float", 110,
           tip="Chỉ ghi theo VTVL nếu quyết định phân bổ đến VTVL; nếu chỉ giao tổng thì không lặp ở từng dòng."),
        _c("F", "dieu_chuyen", "Điều chuyển/bố trí lại", "memo", 180),
        _c("G", "de_nghi", "Đề nghị điều chỉnh", "float", 100, required=True, tip="Có thể bằng 0."),
        _c("H", "giai_trinh", "Nguồn/giải trình", "memo", 220, required=True),
        _c("I", "trang_thai", "Trạng thái", "choice", 160, TT_D2, required=True),
        _c("J", "canh_bao", "Cảnh báo", "calc", 210),
        _c("K", "pp2_qd", "PP2: người quy đổi (tham khảo)", "calc", 105),
        _c("L", "c3_co_so", "Người cần bố trí C3 năm cơ sở (tham khảo)", "calc", 120),
        _c("M", "kiem_soat", "Kiểm soát cơ sở đối chiếu", "calc", 200),
        _c("N", "van_ban", "Văn bản thẩm định/quyết định (số, ngày, cơ quan)", "memo", 200),
    ),
    sheet="10. D2_PhuongAn",
    note="Trước khi đề nghị điều chỉnh phải xem xét bố trí lại, điều chuyển, kiêm nhiệm, dùng chung nhân lực, ứng dụng "
         "công nghệ, thuê dịch vụ. Kết quả tính không tự động làm tăng biên chế.",
)

FORMS = {f.code: f for f in (A1, A2, B1, DM, B2, B2TH, C1, C2, C3, D1, DB, D2)}
FORM_ORDER = ("A1", "A2", "B1", "DM", "B2", "B2TH", "C1", "C2", "C3", "D1", "DB", "D2")
INPUT_FORMS = tuple(c for c in FORM_ORDER if not FORMS[c].virtual)
# 09 biểu nghiệp vụ chính (B2 gồm chi tiết + tổng hợp)
NINE = ("A1", "A2", "B1", "B2", "C1", "C2", "C3", "D1", "D2")

# Danh mục căn cứ pháp lý (không thuộc bộ biểu, người dùng có thể cập nhật)
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
