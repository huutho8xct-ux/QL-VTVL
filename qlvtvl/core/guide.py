"""Nội dung hướng dẫn 08 bước và danh mục căn cứ pháp lý."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    no: int
    title: str
    short: str
    forms: tuple
    guide: str


STEPS = (
    Step(
        1, "Rà soát chức năng, nhiệm vụ", "Chức năng, nhiệm vụ", ("A1",),
        """<p><b>Mục đích:</b> xác định đầy đủ, chính xác các nhiệm vụ của Thư viện thành phố
        theo quy định còn hiệu lực.</p>
        <ul>
        <li>Đối chiếu Quyết định quy định chức năng, nhiệm vụ, quyền hạn và cơ cấu tổ chức của
        Thư viện; Luật Thư viện 2019 và các văn bản hướng dẫn; dữ liệu đã kê khai, đã xác nhận.</li>
        <li>Mỗi nhiệm vụ ghi rõ <b>căn cứ pháp lý</b> (văn bản, điều, khoản) và phòng chủ trì.</li>
        <li>Đánh dấu kết quả rà soát: giữ nguyên, bổ sung mới, điều chỉnh, đề nghị bãi bỏ.</li>
        <li><b>Không</b> xác định nhiệm vụ xuất phát từ người hiện có, ngạch, mức lương
        hoặc số biên chế đã giao.</li>
        </ul>""",
    ),
    Step(
        2, "Xác định công việc và sản phẩm", "Công việc, sản phẩm", ("A2",),
        """<p>Từ mỗi nhiệm vụ ở Biểu A1, xác định <b>công việc, công đoạn chính, sản phẩm đầu ra
        và đơn vị chịu trách nhiệm</b>.</p>
        <ul>
        <li>Ví dụ nghiệp vụ thư viện: bổ sung tài liệu, biên mục, phân loại; phục vụ bạn đọc
        tại chỗ, mượn về nhà; luân chuyển sách cơ sở; số hóa tài liệu địa chí; tổ chức sự kiện
        phát triển văn hóa đọc; hướng dẫn nghiệp vụ cho thư viện cơ sở...</li>
        <li>Sản phẩm phải đo đếm được và có đơn vị tính (biểu ghi, lượt bạn đọc, trang số hóa,
        cuộc, lớp, báo cáo...).</li>
        <li>Mỗi công việc phải gắn với một nhiệm vụ trong Biểu A1.</li>
        </ul>""",
    ),
    Step(
        3, "Xác định khối lượng, thời gian thực hiện", "Khối lượng, thời gian", ("B1",),
        """<p>Với mỗi công việc ở Biểu A2, ghi <b>số sản phẩm thực tế/năm</b>,
        <b>thời gian lao động trực tiếp</b> cho một sản phẩm và <b>nguồn xác nhận</b>.</p>
        <ul>
        <li>Phân biệt thời gian người thực sự làm với thời hạn trả kết quả và thời gian chờ.</li>
        <li>Ưu tiên số liệu từ phần mềm quản lý thư viện, sổ sách, báo cáo thống kê; định mức
        kinh tế - kỹ thuật (Thông tư 07/2023/TT-BVHTTDL); khảo sát bấm giờ.</li>
        <li>Nên lấy bình quân nhiều năm để loại trừ biến động ngắn hạn.</li>
        <li>Phần mềm tự tính: <i>Tổng giờ = Số lượng × Giờ/1 sản phẩm</i>.</li>
        </ul>""",
    ),
    Step(
        4, "Đánh giá tác động chuyển đổi số, tự chủ, thuê dịch vụ, xã hội hóa", "Yếu tố tác động",
        ("B2",),
        """<p>Xác định các <b>công đoạn thực tế thay đổi</b>, đo số lượng áp dụng và thời gian
        tăng/giảm.</p>
        <ul>
        <li>Chuyển đổi số: mượn trả tự động (RFID), biên mục sao chép, thư viện số, tra cứu trực tuyến...</li>
        <li>Thuê dịch vụ: vệ sinh, bảo vệ, bảo trì; Xã hội hóa: sự kiện, tài trợ...</li>
        <li>Tự chủ tài chính, thay đổi quy trình hoặc nhiệm vụ mới phát sinh.</li>
        <li>Ghi <b>số âm</b> cho giờ giảm, <b>số dương</b> cho giờ tăng; kèm minh chứng.</li>
        </ul>""",
    ),
    Step(
        5, "Rà soát danh mục vị trí việc làm, mô tả công việc và khung năng lực", "Danh mục VTVL",
        ("C1", "C2"),
        """<p>Đối chiếu từng vị trí việc làm với chức năng, nhiệm vụ, công việc và sản phẩm.
        Phân nhóm: <b>tiếp tục sử dụng, cần điều chỉnh, tích hợp, đề nghị bổ sung hoặc bãi bỏ</b>.</p>
        <ul>
        <li>Nhóm vị trí: lãnh đạo, quản lý; chức danh nghề nghiệp chuyên ngành thư viện
        (Thông tư 10/2023/TT-BVHTTDL, Thông tư 02/2022/TT-BVHTTDL); chuyên môn dùng chung
        (kế toán, hành chính, văn thư...); hỗ trợ, phục vụ (Nghị định 111/2022/NĐ-CP).</li>
        <li>Một vị trí việc làm <b>không đồng nghĩa</b> với một người hoặc một biên chế.</li>
        <li>Biểu C2: lập bản mô tả công việc và khung năng lực cho từng vị trí
        (nút <i>Đồng bộ từ C1</i> tạo sẵn dòng cho mọi vị trí).</li>
        </ul>""",
    ),
    Step(
        6, "Xác định nhu cầu nhân lực theo vị trí việc làm", "Nhu cầu nhân lực", ("C3",),
        """<p>Chọn phương pháp phù hợp với tính chất công việc:</p>
        <ul>
        <li><b>PP1</b> – công việc theo cơ cấu, chức danh hoặc định mức bố trí đã được quy định
        (ví dụ: Giám đốc, Phó Giám đốc, kế toán trưởng).</li>
        <li><b>PP2</b> – tính theo khối lượng và thời gian lao động đo được:
        <i>Số người quy đổi = Tổng giờ cần thiết ÷ Quỹ giờ 1 người/năm</i>
        (mặc định <b>1.904 giờ</b>: 40 giờ/tuần, 5 ngày/tuần, trừ nghỉ lễ, 12 ngày phép).</li>
        <li><b>PP3</b> – thẩm định theo sản phẩm, tiến độ, trách nhiệm đối với công việc khó
        chuẩn hóa thời gian.</li>
        </ul>
        <p>Ví dụ: 2.600 giờ ÷ 1.904 ≈ 1,366 người – <b>không làm tròn cơ học thành 2</b>;
        phần lẻ được xem xét kiêm nhiệm, tích hợp. PP1/PP3 ghi số người và giải trình,
        không gán số giờ giả định.</p>""",
    ),
    Step(
        7, "Đối chiếu nhân lực hiện có, xây dựng phương án biên chế", "Đối chiếu, phương án",
        ("D1", "D2"),
        """<p><b>Biểu D1:</b> đối chiếu nhu cầu với nhân lực hiện có cùng kỳ, cùng phạm vi, cùng
        đơn vị tính; phân biệt viên chức, hợp đồng lao động và nguồn kinh phí; không gộp với
        biên chế công chức của cơ quan quản lý.</p>
        <p><b>Biểu D2:</b> xây dựng lộ trình từng năm 2027 - 2031: số người có thể bố trí,
        điều chuyển, tinh giản, bố trí lại, đề nghị và giải trình.</p>
        <ul><li>Kết quả rà soát <b>không tự động</b> làm tăng biên chế, không tự động thay đổi
        lương, phụ cấp khi chưa có quy định mới.</li></ul>""",
    ),
    Step(
        8, "Kiểm tra, xác nhận và gửi kết quả", "Kiểm tra, xuất báo cáo", (),
        """<p>Phần mềm tự động kiểm tra tính đầy đủ, logic và liên kết giữa các biểu.
        Xử lý hết các lỗi (đỏ), xem xét các cảnh báo (vàng) trước khi xuất.</p>
        <ul>
        <li>Xuất <b>Bộ 09 biểu</b> ra Excel để gửi cơ quan quản lý (Sở Văn hóa, Thể thao và
        Du lịch; Sở Nội vụ).</li>
        <li>Xuất <b>Báo cáo thuyết minh</b> ra Word.</li>
        <li>Người đứng đầu đơn vị chịu trách nhiệm về tính chính xác của dữ liệu.</li>
        <li>Năm đầu rà soát theo quý; cập nhật khi thay đổi lớn về chức năng, nhiệm vụ,
        tổ chức, quy trình, công nghệ.</li>
        </ul>""",
    ),
)

LEGAL_BASES = (
    ("Hướng dẫn 07-HD/BTCTW", "19/10/2026", "Ban Tổ chức Trung ương",
     "Rà soát, hoàn thiện vị trí việc làm, xác định nhu cầu nhân lực và xây dựng phương án "
     "biên chế trong hệ thống chính trị giai đoạn 2027 - 2031 (08 bước, 09 biểu nghiệp vụ)."),
    ("Kế hoạch 71-KH/BTCTW", "2026", "Ban Tổ chức Trung ương",
     "Xây dựng cơ sở dữ liệu vị trí việc làm gắn với phương án giao biên chế giai đoạn 2027 - 2031."),
    ("Luật Viên chức số 129/2025/QH15", "10/12/2025", "Quốc hội",
     "Quản lý viên chức theo vị trí việc làm."),
    ("Luật Cán bộ, công chức số 80/2025/QH15", "24/6/2025", "Quốc hội",
     "Quản lý cán bộ, công chức theo vị trí việc làm."),
    ("Nghị định 106/2020/NĐ-CP", "10/9/2020", "Chính phủ",
     "Vị trí việc làm và số lượng người làm việc trong đơn vị sự nghiệp công lập "
     "(tiếp tục áp dụng trong thời gian chờ Nghị định hướng dẫn Luật Viên chức 2025)."),
    ("Quy định 70-QĐ/TW", "18/7/2022", "Bộ Chính trị",
     "Quản lý biên chế của hệ thống chính trị."),
    ("Luật Thư viện số 46/2019/QH14", "21/11/2019", "Quốc hội",
     "Hoạt động thư viện; nhiệm vụ của thư viện công cộng cấp tỉnh."),
    ("Thông tư 10/2023/TT-BVHTTDL", "2023", "Bộ VHTTDL",
     "Vị trí việc làm lãnh đạo, quản lý và chức danh nghề nghiệp chuyên ngành trong đơn vị sự "
     "nghiệp công lập thuộc lĩnh vực văn hóa, thể thao và du lịch."),
    ("Thông tư 02/2022/TT-BVHTTDL", "2022", "Bộ VHTTDL",
     "Mã số, tiêu chuẩn chức danh nghề nghiệp, xếp lương viên chức chuyên ngành thư viện."),
    ("Thông tư 07/2023/TT-BVHTTDL", "2023", "Bộ VHTTDL",
     "Tiêu chí, định mức kinh tế - kỹ thuật dịch vụ sự nghiệp công lĩnh vực thư viện."),
    ("Thông tư 12/2022/TT-BNV", "30/12/2022", "Bộ Nội vụ",
     "Vị trí việc làm chuyên môn dùng chung (hành chính, tổng hợp, văn thư, lưu trữ...)."),
    ("Thông tư 29/2022/TT-BTC", "2022", "Bộ Tài chính",
     "Vị trí việc làm chuyên ngành kế toán."),
    ("Nghị định 111/2022/NĐ-CP", "30/12/2022", "Chính phủ",
     "Hợp đồng đối với một số loại công việc hỗ trợ, phục vụ trong đơn vị sự nghiệp công lập."),
)

DISCLAIMER = (
    "Danh mục căn cứ được tổng hợp tại thời điểm phát hành phần mềm. Người sử dụng cần đối chiếu "
    "văn bản gốc và cập nhật khi có văn bản mới thay thế (có thể sửa ngay trong phần mềm)."
)
