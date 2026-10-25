# H03 — Tham số và cấu hình tái lập

| Tham số | Mặc định | Miền hợp lệ | Ảnh hưởng |
|---|---:|---|---|
| HALF_CYCLES | 4 | Số nguyên ≥1 | H clk cho mỗi nửa SCLK |
| MSB_FIRST | 1 | 0 hoặc 1 | Thứ tự bit cả TX/RX |

Tham số chốt lúc biên dịch/tổng hợp, không đổi runtime. HCW=max(1,ceil(log2(H))) giữ độ rộng hợp lệ ở H=1. Bản cải tiến kiểm H<1 và dùng comparator đúng độ rộng.

| H | SCLK nếu clk=100 MHz | START→DONE | Khoảng nhận lệnh khi giữ START |
|---:|---:|---:|---:|
| 1 | 50 MHz | 17 clk | 18 clk |
| 2 | 25 MHz | 33 clk | 34 clk |
| 3 | 16,6667 MHz | 49 clk | 50 clk |
| 4 | 12,5 MHz | 65 clk | 66 clk |
| 5 | 10 MHz | 81 clk | 82 clk |
| 8 | 6,25 MHz | 129 clk | 130 clk |

100 MHz là điều kiện phân tích/mô phỏng, chưa là tần số đã xác minh với slave/bo mạch thật.

Mọi số cell/FF/diện tích/timing/power cần top, H/ORDER, source hash, tool version, PDK/SCL/corner, SDC và run ID. Số 156 cell/36 FF/1,9 ns trong hồ sơ cũ không được dùng lại cho bản cải tiến. Dữ liệu cuối lấy từ artifact run mới, không điền sẵn trong đặc tả.

