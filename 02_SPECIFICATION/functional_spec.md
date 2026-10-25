# H03 — Đặc tả chức năng

Ngày cập nhật: 25/10/2026. Lõi h03_spi_master truyền và nhận đồng thời 8 bit qua một SPI slave, CPOL=0/CPHA=0. H=HALF_CYCLES là số nguyên ≥1; MSB_FIRST=1 mặc định, 0 chọn LSB-first. Mọi logic nội bộ dùng cạnh lên clk; sclk là đầu ra đăng ký, không làm clock nội bộ.

## Nhận yêu cầu và hoàn tất

START được lấy mẫu **theo mức** ở IDLE. Cạnh nhận lệnh chốt TX, hạ CS, bật BUSY, đưa bit TX đầu tiên lên MOSI. START ở TRANSFER/FINISH không được xếp hàng. Nếu START còn cao khi về IDLE, lõi bắt đầu frame mới ở cạnh nhận lệnh kế tiếp. Đây không phải giao diện bắt cạnh lên START.

RX giữ kết quả trước trong suốt frame mới và cập nhật cùng DONE. DONE là xung đúng một clk. MOSI ngoài CS thấp không mang dữ liệu hợp lệ, có thể giữ bit cuối.

Gọi cạnh nhận lệnh E(0); bảng xét sau cập nhật nonblocking:

| Mốc | Chu kỳ clk | Hành vi |
|---|---:|---|
| Nhận START | 0 | CS=0, BUSY=1, SCLK=0, MOSI=bit đầu |
| SCLK lên thứ k | (2k−1)H, k=1…8 | Lấy mẫu MISO; MOSI đã ổn định |
| SCLK xuống thứ k | 2kH, k=1…7 | Đưa bit MOSI kế tiếp |
| SCLK xuống #8 | 16H | SCLK=0; CS thấp; MOSI giữ bit cuối; state=FINISH |
| Hoàn tất | 16H+1 | CS=1, BUSY=0, RX cập nhật, DONE=1; state=IDLE |
| Frame tiếp nếu START giữ cao | 16H+2 | Nhận lệnh; DONE=0 |

f_SCLK=f_clk/(2H). START→DONE=(16H+1)T_clk; khoảng giữa hai lần nhận START khi giữ cao=(16H+2)T_clk.

## Thứ tự bit

MSB-first: MOSI TX[7]…TX[0], thu MISO bằng dịch trái và chèn bit thấp. LSB-first: MOSI TX[0]…TX[7], thu bằng dịch phải và chèn bit cao. Sau tám lần lấy mẫu, RX là byte chuẩn ở cả hai chế độ.

## Reset và khôi phục trạng thái

rst_n là reset đồng bộ active-low: có hiệu lực tại cạnh lên clk. Reset giữa frame hủy frame, đưa SCLK=0, CS=1, MOSI=0, BUSY=DONE=0 và xóa RX/các thanh ghi nội bộ; không phát DONE cho frame hủy.

Bản cải tiến từ chối H<1 bằng lỗi khởi tạo. Nhánh default của FSM hủy frame nếu mã state không hợp lệ, đưa bus về idle, xóa bộ đếm/dịch, giữ RX đã hoàn tất và không phát DONE. Đây là kiểm soát ở RTL; không tự chứng minh khả năng chống lỗi bức xạ/metastability ở netlist vật lý.

Khi không reset và frame bình thường: CS thấp kéo theo BUSY cao; mỗi frame đúng 8 cạnh lên/xuống; MOSI đổi lúc nhận lệnh hoặc cạnh xuống #1…7; RX chỉ đổi cùng DONE. Reset/hủy frame là ngoại lệ có chủ đích của bất biến số cạnh.

## Điều kiện môi trường

START/TX/reset thỏa setup/hold theo clk. MISO do slave trả theo SCLK nên cần ngân sách trễ vòng và timing ngoài chip; zero-delay simulation không chứng minh timing điện. Không tự thêm bộ đồng bộ MISO hai tầng vì độ trễ có thể lệch bit, nhất là H=1.

Wrapper tt_um_h03_spi_mode0 giữ nguyên hợp đồng của lõi. ena chỉ chặn nhận START mới; frame đã nhận được truyền tới hết dù ena hạ. Mapping và cổng hạ tầng ở interface.md.

