# H03 — Bối cảnh ứng dụng

H03 là khối số tuần tự làm SPI master mode 0 trong hệ thống đọc cảm biến gia tốc của thiết bị đeo tay. Tầng điều khiển cung cấp byte TX/START; H03 sinh CS/SCLK/MOSI, lấy MISO và trả byte RX/DONE.

    Điều khiển số ── TX/START ──> H03 ── SCLK/MOSI/CS ──> Cảm biến SPI
    Điều khiển số <── RX/DONE ─── H03 <──── MISO ───────── Cảm biến SPI

| Thành phần | Phân loại | Vai trò |
|---|---|---|
| Phần tử cảm biến | Analog hoặc mixed-signal | Chuyển gia tốc thành số đo |
| Giao tiếp số của cảm biến | Digital | Thực hiện SPI |
| H03 | Digital, tuần tự | FSM, divider, TX/RX shift register, thanh ghi kết quả |
| Điều khiển và xử lý dữ liệu | Digital | Phát yêu cầu, chốt và xử lý kết quả |

Phân loại tuần tự dựa trực tiếp trên các thanh ghi cập nhật ở cạnh clk. Số FF thực tế phải đọc từ synthesis của run hiện tại, không suy từ ước lượng Charter.

Lõi nhả CS sau mỗi byte. Cảm biến cần byte địa chỉ và nhiều byte dữ liệu dưới một CS thấp cần mở rộng ngoài phạm vi H03. Chưa chọn cảm biến/bo mạch cụ thể nên chưa thể kết luận SCLK và timing điện tương thích phần cứng thật.

