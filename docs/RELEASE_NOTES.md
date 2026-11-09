## Hệ thống nhập liệu vị trí việc làm – Thư viện thành phố Cần Thơ

Phần mềm rà soát vị trí việc làm, xác định nhu cầu nhân lực và xây dựng phương án biên chế 2027 – 2031 theo **Hướng dẫn số 7-HD/BTCTW ngày 19/10/2026** và **Bộ biểu Excel 19-10-2026**. Chạy **hoàn toàn offline** trên Windows.

### Tải về (mục Assets bên dưới)
| Tệp | Dùng khi |
|---|---|
| `CaiDat_QL-VTVL_<phiên bản>.exe` | **Cài đặt** (khuyên dùng): tạo biểu tượng ở màn hình nền, menu Start, mở tệp `.vtvl` bằng nhấp đúp |
| `QL-VTVL_portable.zip` | Không muốn cài: giải nén rồi chạy `QL-VTVL.exe` |
| `SHA256SUMS.txt` | Mã kiểm tra tính toàn vẹn của các tệp trên |

### Yêu cầu
Windows 10/11 64-bit. Không cần Internet, Python, Office hay quyền quản trị: nếu không có quyền quản trị, phần mềm cài cho riêng tài khoản đang dùng.

### Cài đặt
1. Tải `CaiDat_QL-VTVL_<phiên bản>.exe`. Có thể chép qua USB sang máy không có mạng.
2. Nhấp đúp để cài. Windows SmartScreen có thể cảnh báo vì phần mềm nội bộ chưa ký số: chọn **More info → Run anyway**.
3. Mở **QL-VTVL**, chọn *Mở hồ sơ có dữ liệu minh họa* để làm quen, hoặc *Tạo hồ sơ mới*.

### Kiểm tra tệp tải về (tùy chọn)
Mở PowerShell tại thư mục chứa tệp và chạy:
```
Get-FileHash .\CaiDat_QL-VTVL_*.exe -Algorithm SHA256
```
So sánh kết quả với dòng tương ứng trong `SHA256SUMS.txt`.

### Chức năng chính
- **Kê khai:** Trang làm việc; Hồ sơ của đơn vị; Hồ sơ; Nhập 09 biểu (đúng cột, công thức, cảnh báo của Bộ biểu); Lỗi và giải trình; Nhập từ Excel; Kiểm tra và gửi; Lịch sử hồ sơ.
- **Nhập từ Excel 4 bước** (Chọn tệp → Kiểm tra tệp → Xem kết quả → Kết chuyển): báo lỗi đến từng ô kèm cách xử lý; kiểm tra trùng với hồ sơ; tải về tệp kết quả có cột báo lỗi; tải biểu mẫu chuẩn; hoàn tác được.
- **Xuất vào Bộ biểu Excel chính thức** (tự sửa các công thức lỗi của bản phát hành 19-10-2026), báo cáo thuyết minh Word, **đóng gói hồ sơ .zip** có đánh số phiên bản.
- **Đơn vị:** tổng hợp hồ sơ cấp dưới. **Ứng dụng:** đồng bộ bằng gói dữ liệu, sao lưu/khôi phục, giao diện sáng/tối.

### Lưu ý
- Dữ liệu chỉ lưu trên máy: tệp hồ sơ `.vtvl`; bản sao lưu ở `%APPDATA%\QL-VTVL\SaoLuu`.
- Dữ liệu minh họa không phải số liệu chính thức của Thư viện.
- Hướng dẫn chi tiết: xem `README.md` của kho mã.
