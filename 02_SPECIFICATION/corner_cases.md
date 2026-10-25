# H03 — Ca biên và lỗi cần bắt

| Ca | Lỗi cần bắt |
|---|---|
| TX=00, FF | MOSI kẹt cao/thấp, đếm bit theo biến đổi dữ liệu |
| TX=A5,55,AA | MOSI đổi sai cạnh, lỗi mẫu lặp |
| TX=01,80 với RX độc lập | Đảo bit order bị byte đối xứng che |
| Quét đủ giá trị byte | Sai bit hoặc lỗi phụ thuộc mẫu |
| H=1 | Sai pha tại tốc độ chia nhanh nhất |
| H=3,5 | Comparator/counter sai ở H không lũy thừa hai |
| Cả hai bit order | Nhánh LSB chưa được test trong TB cũ |
| TX đổi sau nhận lệnh | Không chốt TX |
| START xung khi bận | Xếp hàng/phát thêm frame ngoài ý muốn |
| START giữ cao | Hiểu nhầm giao diện mức thành bắt cạnh |
| Reset tại pha SCLK cao/thấp/gần cuối | BUSY/CS kẹt, DONE giả, RX dở dang |
| Frame sau reset | Counter/shift register chưa khởi tạo đúng |
| RX giữ qua frame và idle | Rò dữ liệu chưa nhận đủ |
| State không hợp lệ | FSM bị kẹt, bus không nhả |
| H=0/âm | Cấu hình không hợp lệ vẫn mô phỏng như H=1 |
| Wrapper ena=0/ena hạ khi bận | Nhận nhầm lệnh hoặc cắt frame |
| Mutation MOSI/RX/độ dài frame | Checker bỏ sót lỗi |

Slave model nạp MISO bit đầu tại CS xuống, đổi bit sau ở SCLK xuống. Lái MISO tại SCLK lên có thể tạo race/trễ bit; không sửa DUT để khớp slave model sai.

TB cũ ở 05_VERIFICATION/testbench chỉ kiểm một phần số cạnh/nhả CS, không so byte RX/MOSI. “TB completed” là lịch sử, không chứng minh đầy đủ SPI. Regression mới ở verification/ là cổng chính.

