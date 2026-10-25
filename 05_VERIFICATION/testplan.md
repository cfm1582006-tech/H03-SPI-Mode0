# H03 — Kế hoạch kiểm chứng bản cải tiến

Ngày cập nhật: 25/10/2026. Cổng chính là verification/h03_spi_regression_tb.sv và scripts/run_regression.py. Kết quả thực tế nằm trong thư mục output do runner mới tạo, gồm source hash, phiên bản công cụ, lệnh, exit code, CSV và JSON.

| Lớp | Mục tiêu | Không suy ra |
|---|---|---|
| Mô hình Python cũ | Quy ước bit order và các công thức cơ bản | Không chứng minh RTL vì không nối DUT |
| RTL regression | MOSI từng bit, RX byte độc lập, tám chu kỳ, pha/divider/CS, START/reset | Không chứng minh độ trễ cổng/board |
| Mutation testing | Checker thật sự bắt được lỗi TX/RX/độ dài frame | Không phải độ phủ lỗi đầy đủ |
| Wrapper regression | Pin map/oe/ena đúng, không tranh chấp START/MISO | Không chứng minh template/shuttle CI |
| Synthesis/STA | Cấu trúc và timing theo SDC/corner cụ thể | Không chứng minh chức năng toàn bộ |
| DRC/LVS/antenna | Điều kiện kiểm vật lý của run | Không chứng minh silicon sẵn sàng sản xuất |
| Gate-level/SDF/formal | Chỉ coi đạt khi có run riêng | Không suy từ RTL hoặc LVS |

Ca bắt buộc Charter: TX=00,FF,A5; RX biết trước và độc lập TX; CS bao trọn tám SCLK. Ca bổ sung có mục đích ở 02_SPECIFICATION/corner_cases.md. Sweep H=1,2,3,4,5,8 và cả bit order; dữ liệu ngẫu nhiên có seed để tái lập, quét byte để giảm lỗ hổng mẫu.

Compiler lỗi làm run fail ngay. Không tái dùng vvp cũ sau compiler lỗi, không chuyển exit code lỗi thành thành công. Mỗi lần phải có thư mục kết quả mới và hash nguồn tương ứng.

TB cũ ở testbench/ và log trong historical_logs/ giữ để đối chiếu; không dùng làm acceptance gate. SVA cũ không được tính đã chạy chỉ vì file tồn tại hoặc được include với macro tắt.

