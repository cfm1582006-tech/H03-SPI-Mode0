# Kiểm chứng SPI mode 0

Từ thư mục dự án, chạy bằng Python 3.9 trở lên, với `iverilog` và `vvp` trong PATH:

```bash
python3 scripts/run_regression.py --out evidence/regression --mutations
```

Thư mục đầu ra phải mới hoặc trống. Runner không tái sử dụng binary, không tiếp
tục mô phỏng sau lỗi compiler và không xem lỗi compile là một mutation bị phát hiện.
`summary.json` lưu SHA-256 nguồn, seed, phiên bản công cụ, từng lệnh, mã thoát và
kết quả. `test_results.csv` lưu từng ca. Các file `.vvp` là sản phẩm của lần chạy đó.

## Phạm vi

Mặc định kiểm 12 cấu hình: `HALF_CYCLES=1,2,3,4,5,8`, mỗi cấu hình kiểm cả hai
thứ tự bit. Tổng 6.320 ca gồm 5.548 frame hoàn chỉnh và 772 ca reset hủy frame.
Số ca từng cấu hình là `18 + 256 + 128 + 2*(16*H+1)`.

- Kiểm chân MOSI từng bit, byte RX độc lập với TX, pha cạnh và tần số SCLK,
  chính xác 8 cạnh lên/8 cạnh xuống, CS bao trọn frame, MOSI ổn định khi lấy mẫu.
- RX giữ byte trước đến DONE, DONE dài một chu kỳ, và bus không có X/Z sau reset.
- TX thay đổi ngay sau lúc nhận START để kiểm dữ liệu đã chốt.
- START khi busy, ở FINISH, và START giữ cao qua hai frame; đây là giao thức
  START theo mức khi IDLE, nên START giữ cao sẽ tự nhận frame tiếp theo.
- Mỗi hướng kiểm đủ 256 giá trị byte. Cặp RX được hoán vị bằng
  `(73*TX+41) mod 256`; bộ này **không** kiểm toàn bộ 65.536 cặp TX/RX.
- 128 cặp ngẫu nhiên xác định từ xorshift32 seed `0x1a2b3c4d`; có thể tái lập
  trên các simulator mà không phụ thuộc thuật toán `$urandom` của công cụ.
- Reset đồng bộ ở mọi offset từ 0 đến `16*H`, bao gồm các pha chia clock,
  bit đầu/cuối và lúc đã vào FINISH. Sau mỗi reset đều có frame phục hồi.
- Reset có ưu tiên cao hơn START; reset không đổi bus trước cạnh clk.

Ba probe ngoài số ca chính: ép trạng thái FSM bất hợp lệ và xác nhận phục hồi,
tham số `HALF_CYCLES=0` và `-1` phải bị từ chối khi mô phỏng. Probe ép FSM là
kiểm tra logic phục hồi RTL, không chứng minh khả năng chống lỗi vật lý.

Ba mutation thay RX bằng 0, ép bit MOSI đầu bằng 0, và kết thúc sau 7 bit phải
bị checker phát hiện qua compile thành công và mô phỏng trả lỗi do kiểm tra.

`sample_mode0.vcd` ở cấu hình H=2, MSB-first lưu phần directed test rồi tắt ghi
trước khi chạy exhaustive để giữ file nhỏ. Toàn bộ kiểm tra vẫn tiếp tục.

## Mô phỏng netlist

TB hỗ trợ macro `GATE_LEVEL` để bỏ parameter override khi instantiation, do
netlist đã cố định tham số tại tổng hợp. Khi dùng netlist phải chọn HC và ORDER
khớp cấu hình tổng hợp, kèm model cell của PDK. Các probe ép FSM/kiểm tham số
chỉ áp dụng RTL. Mô phỏng netlist không có SDF chỉ xác minh logic, không thay
thế STA hoặc mô phỏng có annotation trễ.

## Wrapper Tiny Tapeout

```bash
python3 scripts/run_wrapper_test.py --out evidence/wrapper_regression
```

`h03_wrapper_tb.sv` kiểm 78 ca: H=1,4,5 nhân hai thứ tự bit, 13 ca mỗi cấu
hình. Mô hình pad dùng tri-state để phát hiện tranh chấp trên START/MISO; kiểm
chính xác `uio_oe=0x7c`, RX chia qua hai nhóm chân, BUSY và DONE. Ca chức năng
bao gồm dữ liệu TX/RX khác nhau, ENA cấm nhận lệnh khi idle, bật ENA khi START
đang cao, hạ ENA sau khi nhận lệnh vẫn hoàn tất frame, START giữ cao nhưng ENA
thấp không tự nhận tiếp, hai frame liên tiếp nhận hai cặp byte khác nhau, START
khi busy và reset đồng bộ hủy frame rồi phục hồi. Wrapper TB cũng có macro
`GATE_LEVEL`; chọn HC/ORDER khớp tham số netlist khi dùng.
