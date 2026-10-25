# H03 — Cách đọc kết quả kiểm chứng

Báo cáo bản cải tiến ngày 25/10/2026. Tệp này chỉ mô tả nguồn bằng chứng; các số đếm/PASS cuối lấy từ summary/results JSON của run mới và báo cáo tổng hợp trong docs/.

## Nguồn lịch sử

Testbench gốc kiểm rất ít: hoàn thành mô phỏng, đếm cạnh và CS cuối frame. Nó không kiểm byte MOSI/RX đầy đủ; slave model lái MISO tại cạnh lấy mẫu có thể tạo race hoặc sai pha. Vì vậy “H03 TB completed” không chứng minh song công đúng. Các log gốc đã đặt trong historical_logs/ và gắn nhãn lịch sử.

Mô hình Python cũ kiểm quy ước bit bằng chính các hàm Python, không so với DUT theo chu kỳ. 5000 vector của mô hình này không phải 5000 ca RTL.

## Bằng chứng cho bản mới

Runner mới ghi compiler/simulator exit code, source hash, cấu hình và từng ca. Chỉ chấp nhận clean compile và checker không báo lỗi. Xem scripts/run_regression.py và verification/. Không đưa con số 156 cell/36 FF/1,9 ns của tài liệu cũ vào kết quả mới.

## Trả lời các câu kỹ thuật

CS xuống tại E(0), trước SCLK lên #1 ở E(H). CS lên tại E(16H+1), sau SCLK xuống #8 ở E(16H). Hai mốc và đúng tám xung phải được kiểm trên VCD thật của run.

Mode 0: SCLK nghỉ thấp, lấy MISO khi SCLK lên; MOSI bit đầu nạp khi CS xuống và bit sau phát ở cạnh xuống. Khoảng ổn định MOSI danh định H*T_clk; phải trừ timing điện để kết luận setup margin ở slave thực.

Song công dùng tám SCLK để chuyển một byte mỗi chiều đồng thời. Nếu tách truyền rồi nhận hai pha cùng tốc độ thì phần bit-clock cần 16 SCLK, chưa tính overhead giao dịch. Đây là so sánh định lượng về giao thức, không phải số công suất đo được.

## Giới hạn

Mô phỏng RTL zero-delay không chứng minh CDC/analog timing/board timing, glitch sau P&R hoặc mọi trạng thái đầu vào. LVS không thay formal equivalence RTL→netlist. DRC/LVS sạch theo bộ rule hiện tại không có nghĩa sign-off công nghiệp. CI chỉ được gọi đã chạy khi có URL run/commit thật.

