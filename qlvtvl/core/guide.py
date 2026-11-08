"""Nội dung hướng dẫn 08 bước (trích Mục II Hướng dẫn số 7-HD/BTCTW ngày 19/10/2026) và căn cứ pháp lý."""
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
        1, "Rà soát chức năng, nhiệm vụ và dữ liệu đã kê khai", "Chức năng, nhiệm vụ", ("A1",),
        """<p>Đối chiếu quy định còn hiệu lực và dữ liệu đã xác nhận (Công văn 1972, 2209, 2342-CV/BTCTW).
        Phân loại nhiệm vụ: <b>tiếp tục thực hiện, mới tiếp nhận, đã chuyển giao, không còn thực hiện</b>;
        xác định chủ thể chủ trì, phối hợp và chịu trách nhiệm cuối cùng.</p>
        <ul>
        <li>Mã nhiệm vụ xác định loại nhiệm vụ; phân biệt số loại nhiệm vụ với số lượt giao thực hiện.
        Giữ mã đã dùng; nhiệm vụ chưa có trong danh mục ghi “đề xuất bổ sung”, kèm căn cứ, mã tạm.</li>
        <li>Đồng thời rà soát VTVL đã phê duyệt: giữ nguyên, cập nhật bản mô tả hoặc kiến nghị sửa đổi;
        không tự sửa danh mục đã phê duyệt.</li>
        <li>Chỉ cập nhật phần thay đổi, còn thiếu hoặc chưa kiểm chứng; không kê khai lại số liệu đã xác nhận.</li>
        </ul>
        <p><i>Kết quả: danh mục nhiệm vụ có mã, căn cứ, trạng thái, nguồn dữ liệu. Tham khảo Phụ lục I, IV, V.</i></p>""",
    ),
    Step(
        2, "Xác định công việc, công đoạn và sản phẩm", "Công việc, sản phẩm", ("A2",),
        """<p><b>Nhiệm vụ</b> là nội dung được giao; <b>công việc</b> là phần việc để thực hiện nhiệm vụ;
        <b>sản phẩm</b> là kết quả có thể xác nhận; <b>vị trí việc làm</b> là nhóm công việc ổn định gắn với
        sản phẩm, trách nhiệm và năng lực.</p>
        <ul>
        <li>Với mỗi nhiệm vụ: xác định công việc, sản phẩm, đơn vị tính, yêu cầu chất lượng, VTVL chịu trách nhiệm.</li>
        <li>Không tách thao tác nhỏ thành nhiệm vụ hoặc vị trí riêng; không đếm một sản phẩm nhiều lần.</li>
        <li>Ví dụ thư viện: biên mục tài liệu (biểu ghi), phục vụ bạn đọc (lượt), luân chuyển sách (lượt),
        số hóa tài liệu địa chí (trang), tổ chức sự kiện văn hóa đọc (cuộc)...</li>
        </ul>
        <p><i>Kết quả: danh mục công việc, sản phẩm gắn nhiệm vụ và VTVL. Tham khảo Phụ lục I, II, V.</i></p>""",
    ),
    Step(
        3, "Xác định số lượng sản phẩm và thời gian thực hiện", "Khối lượng, thời gian", ("B1", "DM"),
        """<p><b>Kỳ thống kê 12 tháng: 01/10/2025 – 30/9/2026.</b> Không lấy một tháng bất thường làm đại diện
        cả năm; không tự nhân số liệu ngắn kỳ thành 12 tháng.</p>
        <ul>
        <li>Thời gian xác định theo thứ tự: định mức chuyên ngành còn hiệu lực (ví dụ Thông tư 07/2023/TT-BVHTTDL
        cho dịch vụ thư viện); thời gian tham chiếu đã kiểm chứng; số liệu thực đo, khảo sát mẫu có nguồn.</li>
        <li>Tính <b>giờ lao động thực tế</b>, không tính thời gian chờ hay thời hạn giải quyết.
        Ví dụ: 300 hồ sơ × 30 phút = 150 giờ.</li>
        <li>Giờ bổ sung (rà soát định kỳ, phối hợp, đào tạo...) chỉ ghi nếu chưa tính trong giờ sản phẩm.
        <b>Không cộng tỷ lệ 10–15% hoặc hệ số cố định</b> cho phần chưa đo.</li>
        <li>Dữ liệu thiếu căn cứ: cột Cảnh báo ≠ ĐẠT, không được chuyển sang C3.</li>
        </ul>
        <p><i>Tham khảo Phụ lục III, V. Tab “Danh mục sản phẩm” chứa phút chuẩn do cơ quan chuyên ngành xác nhận.</i></p>""",
    ),
    Step(
        4, "Xác định thay đổi do chuyển đổi số, tự chủ, thuê dịch vụ và xã hội hóa", "Tác động B2",
        ("B2", "B2TH"),
        """<p>Ghi công đoạn thực tế thay đổi; đo số lượng áp dụng, thời gian trước và sau, phần giờ thực giảm
        và công việc mới tăng (quản lý dữ liệu, giám sát dịch vụ, kiểm soát chất lượng...). <b>Chỉ ghi tác động có
        bằng chứng.</b></p>
        <ul>
        <li>Chọn một trong hai cách: (1) dùng thời gian trước thay đổi rồi cộng, trừ tác động (“Trước thay đổi,
        có điều chỉnh”); hoặc (2) dùng thời gian đã đo sau thay đổi (“Đã đo sau thay đổi – không trừ”).</li>
        <li>Không giảm giờ chỉ vì có phần mềm, thủ tục trực tuyến hay khả năng thuê dịch vụ. Đổi nguồn kinh phí
        hoặc chuyển sang tự chủ không đương nhiên làm giảm công việc.</li>
        <li>Dòng “Ước lượng tham khảo” không vào phép tính. Bảng tổng hợp tự động chuyển giờ tác động ròng sang C3.</li>
        </ul>""",
    ),
    Step(
        5, "Đối chiếu, hoàn thiện danh mục vị trí việc làm, bản mô tả và khung năng lực", "Danh mục VTVL",
        ("C1", "C2"),
        """<p>Đối chiếu từng VTVL với chức năng, nhiệm vụ, công việc và sản phẩm: <b>tiếp tục sử dụng, cần cập
        nhật, đề nghị bổ sung, sửa đổi hoặc bãi bỏ</b> theo thẩm quyền. Một vị trí không đồng nghĩa một người hay
        một biên chế.</p>
        <ul>
        <li>Viên chức áp dụng mẫu bản mô tả, khung năng lực tại <b>Phụ lục IV Nghị định 232/2026/NĐ-CP</b>;
        chức danh nghề nghiệp thư viện theo quy định chuyên ngành còn hiệu lực.</li>
        <li>C1 xác định quỹ giờ PP2: chế độ phổ biến 40 giờ/tuần dùng mức chung 1.904 giờ; chế độ đặc thù
        (ca, kíp, trực...) phải có giờ riêng đã kiểm chứng và căn cứ.</li>
        <li>C2 ghi tóm tắt trách nhiệm, năng lực và địa chỉ lưu bản mô tả; không sao chép toàn bộ hồ sơ.</li>
        <li>Đơn vị sự nghiệp: phân biệt viên chức, hợp đồng lao động và nhân sự chế độ khác.</li>
        </ul>""",
    ),
    Step(
        6, "Xác định số người cần thiết theo từng vị trí việc làm", "Nhu cầu nhân lực", ("C3",),
        """<ul>
        <li><b>PP1</b> – theo cơ cấu, chức danh, định mức bố trí hoặc yêu cầu hiện diện được quy định
        (ví dụ: 01 người đứng đầu). Giới hạn số cấp phó tối đa không phải yêu cầu bố trí đủ.</li>
        <li><b>PP2</b> – theo khối lượng và thời gian đo được: <i>Người quy đổi = Giờ ròng ÷ Quỹ giờ</i>.
        Quỹ giờ kỳ gốc = (261 − 11 ngày lễ, Tết − 12 ngày phép) × 8 = <b>1.904 giờ</b>.</li>
        <li><b>PP3</b> – thẩm định theo sản phẩm, tiến độ, trách nhiệm đối với công việc khó chuẩn hóa thời gian;
        phải có hồ sơ giải trình, thẩm định.</li>
        </ul>
        <p>Ví dụ: 3.000 − 500 − 100 + 200 = 2.600 giờ; 2.600 ÷ 1.904 ≈ 1,366 người – <b>không tự làm tròn thành
        02 biên chế</b>. Không làm tròn tăng từng dòng rồi cộng thành nhu cầu chung. Một vị trí có thể dùng nhiều
        phương pháp cho các phần việc khác nhau nhưng không cộng trùng.</p>""",
    ),
    Step(
        7, "Đối chiếu nguồn nhân lực hiện có và xây dựng phương án biên chế", "Đối chiếu, phương án",
        ("D1", "DB", "D2"),
        """<p>Nhân lực hiện có <b>chốt tại ngày 30/9/2026</b>. Đối chiếu nhu cầu với nhân lực hiện có trên cùng kỳ,
        phạm vi, đơn vị tính; phân biệt người quy đổi, số người và chỉ tiêu biên chế.</p>
        <ul>
        <li><b>D1</b>: mỗi người một mã nguồn lực; phân bổ giờ cho VTVL và việc khác, không vượt quỹ giờ.</li>
        <li><b>Dự báo 2027–2031</b>: biến động từng năm so với C3 (nhập 0 nếu không đổi), có căn cứ.</li>
        <li><b>D2</b>: phương án từng năm – số người có thể bố trí, điều chuyển/bố trí lại, đề nghị điều chỉnh.
        Trước khi đề nghị tăng phải xem xét bố trí lại, kiêm nhiệm, dùng chung, công nghệ, thuê dịch vụ.</li>
        <li>Viên chức phân biệt nguồn ngân sách và nguồn thu; không nhân tỷ lệ tăng, giảm cố định.</li>
        </ul>""",
    ),
    Step(
        8, "Kiểm tra, xác nhận và gửi kết quả", "Kiểm tra, xuất hồ sơ", (),
        """<p>Phần mềm kiểm tra theo đúng cột cảnh báo của bộ biểu và Phụ lục VI. Kết quả kiểm tra tự động
        <b>không thay thế</b> trách nhiệm xác nhận nghiệp vụ; người đứng đầu chịu trách nhiệm về dữ liệu gốc.</p>
        <ul>
        <li><b>Xuất vào Bộ biểu Excel chính thức</b> (Bộ biểu VTVL 19-10-2026, giữ nguyên công thức) để gửi
        theo đầu mối quy định.</li>
        <li>Xuất báo cáo thuyết minh (Word) kèm danh sách nội dung chưa đủ căn cứ.</li>
        <li>Mốc tiến độ: trước 10/11/2026 gửi dữ liệu ban đầu; trước 20/11/2026 hoàn thành nhu cầu nhân lực và
        phương án biên chế 2027–2031.</li>
        </ul>""",
    ),
)

LEGAL_BASES = (
    ("Kết luận số 107-KL/TW", "17/10/2026", "Bộ Chính trị",
     "Hoàn thiện hệ thống vị trí việc làm trong hệ thống chính trị gắn với xây dựng đội ngũ cán bộ và quản lý biên chế."),
    ("Hướng dẫn số 7-HD/BTCTW", "19/10/2026", "Ban Tổ chức Trung ương",
     "Rà soát, hoàn thiện vị trí việc làm, xác định nhu cầu nhân lực và xây dựng phương án biên chế trong hệ thống "
     "chính trị (08 bước, Phụ lục I–VIII, Bộ biểu Excel 19-10-2026)."),
    ("Hướng dẫn số 06-HD/BTCTW", "11/10/2026", "Ban Tổ chức Trung ương",
     "Vị trí việc làm khối cơ quan Đảng, Mặt trận Tổ quốc và tổ chức chính trị – xã hội."),
    ("Nghị định số 232/2026/NĐ-CP", "26/6/2026", "Chính phủ",
     "Vị trí việc làm viên chức (mẫu bản mô tả, khung năng lực tại Phụ lục IV)."),
    ("Nghị định số 361/2025/NĐ-CP", "31/12/2025", "Chính phủ",
     "Vị trí việc làm công chức (mẫu tại Phụ lục VI)."),
    ("Luật Viên chức số 129/2025/QH15", "10/12/2025", "Quốc hội",
     "Quản lý viên chức theo vị trí việc làm."),
    ("Công văn số 1972, 2209, 2342-CV/BTCTW", "2026", "Ban Tổ chức Trung ương",
     "Dữ liệu chức năng, nhiệm vụ, vị trí việc làm đã kê khai, xác nhận (kế thừa)."),
    ("Luật Thư viện số 46/2019/QH14", "21/11/2019", "Quốc hội",
     "Hoạt động thư viện; nhiệm vụ của thư viện công cộng cấp tỉnh."),
    ("Thông tư 07/2023/TT-BVHTTDL", "2023", "Bộ VHTTDL",
     "Tiêu chí, định mức kinh tế - kỹ thuật dịch vụ sự nghiệp công lĩnh vực thư viện (căn cứ thời gian B1)."),
    ("Bộ luật Lao động 2019 và quy định về thời giờ làm việc", "", "Quốc hội, Chính phủ",
     "Căn cứ quỹ giờ chung 1.904 giờ/người/năm (chế độ 40 giờ/tuần)."),
)

DISCLAIMER = (
    "Danh mục căn cứ tổng hợp từ Hướng dẫn số 7-HD/BTCTW, Bộ phụ lục và Cẩm nang kèm theo. Khi có văn bản mới, "
    "cập nhật tại đây và đối chiếu bản ký ban hành. Trường hợp Hướng dẫn chưa thống nhất với văn bản có hiệu lực "
    "của cấp có thẩm quyền thì thực hiện theo văn bản có hiệu lực."
)
