# H03 — Tiêu chí chấp nhận

Ngày cập nhật: 25/10/2026. Bảng này định nghĩa cổng kiểm tra; trạng thái thực tế lấy từ báo cáo run mới. Không kế thừa dấu PASS trong ZIP cũ cho mã đã cải tiến.

| Cổng | Điều kiện đạt |
|---|---|
| Giao diện | Mỗi cổng có chiều, độ rộng, mức tích cực và điều kiện hợp lệ; ánh xạ Tiny Tapeout không tranh chấp chân |
| Build | Biên dịch mã thoát 0; mọi binary sinh từ nguồn/hash của lần chạy hiện tại |
| SPI | 8 cạnh lên và 8 cạnh xuống; CPOL=0; MOSI đúng từng bit; RX đúng byte độc lập |
| Timing chức năng | Nửa SCLK đúng H clk; START→DONE=16H+1; CS thấp ở cạnh xuống thứ 8 |
| Bắt tay | START khi bận không xếp hàng; giữ cao kích lại ở IDLE; DONE một clk |
| Reset | Reset đồng bộ đưa CS=1/SCLK=0/BUSY=0/DONE=0/RX=0 ở cạnh clk kế; frame mới chạy lại được |
| Tham số và FSM | H<1 bị từ chối; mã FSM không hợp lệ được khôi phục theo đặc tả |
| Phạm vi test | Đủ 00/FF/A5, ca bổ sung có lý do, H=1 và H không lũy thừa 2, cả hai bit order |
| Độ tin cậy checker | Các mutation bị phát hiện; baseline cùng checker đạt |
| Wrapper | Mapping 0x7c đúng; ena chặn nhận lệnh mới nhưng không cắt frame đã nhận |
| Synthesis | Không lỗi cấu trúc hoặc latch ngoài ý muốn; lưu netlist và thống kê cùng nguồn |
| Physical flow | Hoàn tất bước bật trong config; có GDS và kiểm DRC/LVS/antenna/timing reports |
| Báo cáo | Mỗi số liệu dẫn đúng file/run/corner/đơn vị; công suất ghi là ước lượng với giả định hoạt động |
| CI | Workflow có thể chạy; chỉ gọi CI đạt sau khi có URL run và commit tương ứng |

GDS tồn tại không tự chứng minh chức năng, timing hoặc DRC/LVS sạch. Flow đạt trong phạm vi học phần không có nghĩa là chế tạo, tape-out hay sẵn sàng sản xuất.

