# H03 — Vị trí hệ thống và vòng đời

    [Host/control logic]
       TX/START ──> [H03 core + TT wrapper] ── SCLK/MOSI/CS ──> [SPI sensor]
       RX/DONE <── [H03 core + TT wrapper] <──── MISO ───────── [SPI sensor]
                      ↑ clk/rst_n/ena

H03 là phần số tuần tự. Cảm biến có thể bao gồm phần tử analog, ADC và giao tiếp SPI; dự án không thiết kế các phần analog đó.

Lõi cung cấp BUSY/DONE; wrapper phân bổ RX trên hai nhóm cổng để tránh uio0/1 tranh chấp. ui_in dùng TX8; uio0/1 là START/MISO; uo0/1/2 là SCLK/MOSI/CS; uo7:3=RX4:0; uio4:2=RX7:5; uio5/6=BUSY/DONE. Cổng clk/rst_n/ena thuộc hạ tầng riêng. Tổng 23 chân người dùng.

ena=0 ngăn nhận START mới. Frame đã nhận hoàn tất bình thường, tránh một giao dịch SPI bị cắt khi enable hạ. Reset mới hủy frame.

Vòng đời hồ sơ:

    Charter → Spec/pin map → RTL → Self-checking regression → Synthesis
       → Floorplan/placement/CTS/routing → STA/DRC/LVS/antenna → GDS
       → Giải thích báo cáo, nêu giới hạn → CI/artifacts và báo cáo

Các mũi tên mô tả quy trình. Trạng thái từng bước lấy từ run thật, không từ sơ đồ. GDS ở mức macro không tự chứng minh đã tích hợp vào shuttle Tiny Tapeout.

