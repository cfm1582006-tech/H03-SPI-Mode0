# H03 — Giao diện và chân Tiny Tapeout

Ngày cập nhật: 25/10/2026. Bảng được đối chiếu với RTL, không phải bảng tự động sinh.

| Tín hiệu lõi | Chiều | Bit | Nghĩa và điều kiện |
|---|---|---:|---|
| clk | vào | 1 | Clock hệ thống, lấy mẫu cạnh lên |
| rst_n | vào | 1 | Reset đồng bộ active-low; lấy mẫu thấp ≥1 cạnh clk |
| start | vào | 1 | Yêu cầu theo mức, nhận ở IDLE; giữ cao kích lại |
| tx_data | vào | 8 | Byte TX, chốt tại nhận START |
| miso | vào | 1 | Dữ liệu slave ổn định trước cạnh lấy mẫu |
| mosi | ra | 1 | Bit đầu tại CS xuống, bit sau tại SCLK xuống |
| sclk | ra | 1 | Clock SPI đăng ký, nghỉ thấp |
| cs_n | ra | 1 | Chip select active-low bao trọn tám SCLK |
| rx_data | ra | 8 | RX hợp lệ khi DONE; giữ tới hoàn tất/reset |
| busy | ra | 1 | Cao từ nhận lệnh tới hoàn tất |
| done | ra | 1 | Xung hoàn tất dài một clk |

Lõi có 12 bit vào gồm clk/reset và 13 bit ra. Ngân sách chân người dùng Tiny Tapeout loại clk/rst_n vì là cổng hạ tầng riêng: 10 bit vào +13 bit ra=23/24. Kết luận cũ 25>24 là đếm nhầm clock/reset.

Charter gán uio[0] cho START, uio[1] cho MISO và đồng thời toàn bộ uio cho RX. uio_in/uio_out dùng chung chân vật lý nên wrapper phân bổ lại:

| Cổng wrapper tt_um_h03_spi_mode0 | Chức năng |
|---|---|
| ui_in[7:0] | TX[7:0] |
| uio_in[0] | START |
| uio_in[1] | MISO |
| uo_out[0] | SCLK |
| uo_out[1] | MOSI |
| uo_out[2] | CS_n |
| uo_out[7:3] | RX[4:0] |
| uio_out[4:2] | RX[7:5] |
| uio_out[5] | BUSY |
| uio_out[6] | DONE |
| uio[7] | Dự phòng, không lái |
| clk/rst_n/ena | Cổng hạ tầng Tiny Tapeout |

uio_oe=8'b01111100 (0x7c); RX={uio_out[4:2],uo_out[7:3]}. ena chỉ gate START; frame đang chạy không bị cắt. BUSY/DONE là phần mở rộng hữu ích so với Charter. Chân chưa dùng được lái dữ liệu 0 và không bật output-enable.

Có wrapper và GDS ở mức khối chưa tự chứng minh tích hợp toàn bộ shuttle/template Tiny Tapeout; muốn khẳng định CI template đạt phải có run/commit tương ứng.

