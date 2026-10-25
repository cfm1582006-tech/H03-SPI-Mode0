# H03 — Điều khiển

IDLE đặt SCLK thấp, CS cao, BUSY thấp, bộ đếm về 0. Khi START cao, chốt TX, xóa RX shift, đưa bit TX đầu, CS thấp/BUSY cao và sang TRANSFER.

TRANSFER tăng half_count cho tới H−1. Tại half_tick, xóa half_count. Nếu SCLK cũ=0: nâng SCLK, thu MISO, tăng edge_count. Nếu SCLK cũ=1: hạ SCLK; khi edge_count=8 thì sang FINISH; nếu chưa đủ thì shift TX và đưa bit kế.

FINISH chạy tại cạnh clk sau cạnh xuống SCLK thứ 8: CS cao, BUSY thấp, RX=result, DONE=1, state=IDLE. DONE mặc định xóa mỗi clk. Vì gán nonblocking, state nhìn thấy FINISH ngay sau cạnh xuống #8 nhưng CS vẫn thấp/BUSY cao cho tới cạnh clk kế.

Reset đồng bộ có ưu tiên cao nhất. Nhánh default khôi phục mã FSM không hợp lệ về idle và hủy giao dịch, giữ byte RX đã hoàn tất, không DONE giả.

START ở trạng thái bận không được ghi nhớ. START giữ cao có hiệu lực lại khi IDLE; để chỉ có một frame, tầng điều khiển phải hạ START trước lần IDLE kế tiếp.

