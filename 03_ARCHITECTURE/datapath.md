# H03 — Datapath

| Thành phần | Vai trò |
|---|---|
| tx_shift[7:0] | Giữ byte TX đã chốt; dịch theo bit order |
| rx_shift[7:0] | Tích lũy tám bit MISO |
| rx_data[7:0] | Giữ byte RX hoàn chỉnh, cập nhật cùng DONE |
| half_count[HCW−1:0] | Đếm H chu kỳ clk cho mỗi pha SCLK |
| edge_count[3:0] | Đếm số cạnh lên/sample đã thực hiện, 0…8 |
| state | IDLE, TRANSFER, FINISH |
| SCLK/MOSI/CS/BUSY/DONE | Đầu ra đăng ký |

MSB-first nạp bit đầu TX[7], sau đó phát bit tx_shift[6] trước phép dịch trái. RX shift trái, chèn MISO ở bit 0. LSB-first nạp TX[0], phát tx_shift[1] trước phép dịch phải; RX shift phải, chèn MISO ở bit 7.

MISO lấy mẫu đồng thời với cạnh clk tạo SCLK lên; slave phải chuẩn bị MISO từ pha trước. Testbench phải nạp bit đầu ở CS xuống và cập nhật bit sau ở SCLK xuống.

Tách rx_shift/rx_data tốn thanh ghi nhưng tránh để tầng ngoài thấy byte đang dở. Không có FIFO hoặc byte counter. Cell/FF/power chỉ được kết luận sau synthesis/STA run hiện tại.

