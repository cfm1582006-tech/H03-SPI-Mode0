# H03 — Yêu cầu và truy vết

Phiên bản cải tiến: 25/10/2026. Nguồn yêu cầu hiện tại: docs/REFERENCE_CHARTER_H03.html, môn EEE703128, Bài kiểm tra số 2. Các yêu cầu thiết kế bổ sung được đánh dấu rõ, không gán nhầm thành nội dung nguyên văn của Charter.

| ID | Nguồn | Yêu cầu | Cách kiểm và bằng chứng |
|---|---|---|---|
| R01 | Charter §1, §4 | SPI master mode 0, CPOL=0, CPHA=0; 8 bit song công | Checker chân SCLK/MOSI/MISO/CS trong verification/ |
| R02 | Charter §5 | Bảng giao diện đầy đủ; giải quyết chân uio[0:1] bị gán trùng chiều | 02_SPECIFICATION/interface.md; wrapper và kiểm thử riêng |
| R03 | Charter §6 | Truyền 00, FF, A5; thu đồng thời byte biết trước; CS bao trọn 8 xung SCLK | Regression đối chiếu từng bit TX, cả byte RX và đúng 8 cạnh lên/xuống |
| R04 | Charter §6 | Ít nhất hai ca bổ sung, có ca biên và nêu lỗi cần bắt | Reset giữa frame, H=1, H không lũy thừa 2, START khi bận/giữ mức, TX đổi sau nhận lệnh |
| R05 | Charter §4.2 | Chứng minh cạnh phát/lấy mẫu và khoảng setup bằng waveform thật có chú thích | VCD của regression và hình trích từ đúng VCD đó |
| R06 | Charter §7–8 | Thực hiện flow RTL-to-GDSII, đọc synthesis/STA/power/DRC/LVS/layout | Log lần chạy mới, source hash, config, metrics và artifact của cùng run |
| R07 | Charter §8 M3 | Tổ chức repo, GitHub Actions/LibreLane và lưu artifacts hoặc nhật ký lỗi | Cấu hình CI có thể tái chạy; URL/commit/run chỉ điền sau khi có thật |
| R08 | Charter §1–2 | Giải thích FSM, divider, shift register và critical path/tài nguyên | 03_ARCHITECTURE/, báo cáo của lần chạy mới |
| R09 | Thiết kế bổ sung | START nhận theo mức ở IDLE; giữ cao sẽ kích lại | functional_spec.md, ca held START |
| R10 | Thiết kế bổ sung | Reset đồng bộ active-low hủy frame; RX chỉ cập nhật ở DONE/reset | Ca reset-abort và kiểm RX giữ ổn định |
| R11 | Thiết kế bổ sung | H nguyên ≥1; hỗ trợ MSB-first và LSB-first | Sweep tham số; cấu hình tổng hợp ghi rõ H/ORDER |
| R12 | Chất lượng bằng chứng | Compiler/simulator lỗi phải làm bước đó thất bại; không dùng binary cũ | Runner nghiêm ngặt, exit code, hash, thư mục kết quả riêng |
| R13 | Độ bền bổ sung | Mã FSM không hợp lệ hủy frame về IDLE, không DONE giả; giữ RX trước | Test fault injection ở RTL; không thay thế phân tích an toàn lỗi vật lý |

Quy mô 230–330 cell và 24–28 ô nhớ trong Charter là gợi ý phân tích, không phải số đo của thiết kế hiện tại. Số cell/FF phụ thuộc top, tham số, tối ưu và thư viện, phải lấy từ log thực tế.


