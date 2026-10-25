# H03 — Phạm vi và bàn giao

Ngày cập nhật: 25/10/2026. Áp dụng phiếu H03/B2 tại docs/REFERENCE_CHARTER_H03.html. Phiếu này đưa RTL-to-GDSII vào phạm vi; diễn giải cũ gọi flow vật lý là tự nguyện đã được sửa.

Trong phạm vi: đặc tả SPI mode 0 một byte, RTL, testbench tự kiểm, waveform có chú thích, flow RTL-to-GDSII, đọc synthesis/STA/power/DRC/LVS/layout, báo cáo và hồ sơ tái lập. Wrapper Tiny Tapeout giải quyết xung đột chân của Charter và được kiểm riêng với lõi.

Ngoài phạm vi chức năng: mode 1/2/3, nhiều slave, DMA, FIFO và truyền nhiều byte dưới cùng CS. Ngoài phạm vi học phần: chế tạo chip, tape-out, sign-off công nghiệp hoặc khẳng định sẵn sàng sản xuất.

| Nội dung | Vị trí |
|---|---|
| Yêu cầu và tiêu chí | 01_REQUIREMENT/ |
| Hợp đồng tín hiệu, timing, tham số | 02_SPECIFICATION/ |
| Sơ đồ và giải thích mạch | 03_ARCHITECTURE/ |
| RTL chuẩn để build | 04_IMPLEMENTATION/rtl/ |
| Kiểm chứng mới | verification/, scripts/run_regression.py |
| Flow và scripts tái lập | flow/, scripts/ |
| Báo cáo và thay đổi | docs/ |
| Bản nguồn đối chiếu | 08_ORIGINAL_SOURCE/ |

05_VERIFICATION ghi kế hoạch và sự khác nhau giữa testbench cũ/regression mới. Log cũ là lịch sử, không dùng để tuyên bố bản cải tiến đã PASS.


