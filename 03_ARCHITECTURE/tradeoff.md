# H03 — Các đánh đổi kiến trúc

| Quyết định | Lợi ích | Chi phí/giới hạn |
|---|---|---|
| Một miền clk, SCLK đăng ký | Điều khiển pha rõ, không tạo miền clock nội bộ mới | Timing IO SPI vẫn phải phân tích riêng |
| TX/RX shift riêng | Song công rõ ràng, dễ kiểm | Có thể tốn FF hơn thanh ghi dùng chung |
| RX result riêng | Byte ra giữ ổn định trong frame kế | Thêm 8 bit khai báo; synthesis quyết định cell thực tế |
| H compile-time | Logic nhỏ, dễ tham số hóa | Không đổi tốc độ runtime |
| MSB/LSB compile-time | Kiểm được cả hai thứ tự | Cấu hình synthesized phải ghi rõ |
| START theo mức | Logic nhỏ, truyền liên tiếp khi giữ cao | Tầng ngoài phải phát xung để tránh kích lại |
| Default FSM | Hủy lỗi và về idle tại RTL | Không tự chứng minh fault safety sau tối ưu |
| ena chỉ gate START | Không cắt giao dịch đang chạy | Không dừng ngay SCLK khi disable |
| Wrapper giữ BUSY/DONE | Quan sát hoàn tất dễ | Dùng 23/24 chân người dùng |

Các kiến trúc thay thế như shift register dùng chung, RX trực tiếp, giữ CS nhiều byte và FIFO chưa được tổng hợp trong bản này; không đưa số tiết kiệm FF/diện tích như kết quả đã đo. Truyền nhiều byte, DMA, nhiều slave và mode 1/2/3 nằm ngoài phạm vi chức năng hiện tại.

H lớn hơn giảm SCLK, tăng thời gian cho trễ vòng ngoài chip nhưng giảm thông lượng và có thể tăng độ rộng divider. Tốc độ phù hợp phải theo datasheet slave/board. Không có một tần số chung cho mọi cảm biến gia tốc.

