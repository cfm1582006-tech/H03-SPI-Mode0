# H03 — FSM và khôi phục

    reset ───────────────────────────────> IDLE
    IDLE ── start=1 / chốt TX, CS=0 ─────> TRANSFER
    TRANSFER ── half_tick, SCLK xuống #8 ─> FINISH
    FINISH ── RX=result, DONE=1, CS=1 ────> IDLE
    mã không hợp lệ ── hủy frame ────────> IDLE

IDLE tự lặp khi START=0. TRANSFER tự lặp trên từng clk cho tới cạnh xuống SCLK thứ 8. FINISH kéo dài đúng một clk. Cần phân biệt “state đã là FINISH” và “tác vụ nhánh FINISH đã chạy”: sau cạnh xuống #8, CS vẫn thấp, BUSY cao; một clk sau mới hoàn tất.

Bản gốc dùng enum 2 bit cho ba trạng thái và không có default. Trong RTL, nếu nạp mã 2'b11 ngoài diễn tiến bình thường, thanh ghi điều khiển có thể bị giữ vô hạn. Bản cải tiến thêm default để nhả CS, hạ SCLK/BUSY, xóa bộ đếm/dịch, giữ RX trước, không phát DONE và trở về IDLE.

Mã không hợp lệ không tự xuất hiện trong mô phỏng bình thường sau reset. Fault-injection là kiểm bổ sung của hành vi RTL, không phải chứng minh full fault tolerance của netlist sau Yosys; công cụ có thể mã hóa/tối ưu FSM khác. Không tuyên bố formal verification hoặc chống bức xạ từ thử nghiệm này.

Reset là đồng bộ active-low. Nếu clk dừng, reset thấp chưa đảm bảo lập tức nhả CS.

