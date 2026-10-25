# H03 — Mốc waveform và khoảng setup

Waveform minh họa bằng mốc chu kỳ; ảnh báo cáo phải trích VCD thật:

    E(0): CS xuống, MOSI bit đầu
    E(H): SCLK lên #1, sample MISO #1
    E(2H): SCLK xuống #1, MOSI bit tiếp
    ...
    E(15H): SCLK lên #8, sample MISO #8
    E(16H): SCLK xuống #8, giữ MOSI cuối, CS vẫn thấp
    E(16H+1): CS lên, RX cập nhật, DONE=1
    E(16H+2): DONE=0; có thể nhận frame mới

Hai mốc để chứng minh CS bao trọn tám SCLK: CS xuống tại E(0), trước SCLK lên #1 tại E(H); CS lên tại E(16H+1), sau SCLK xuống #8 tại E(16H). Số cạnh phải đếm từ VCD/checker, không dựa vào hình vẽ sơ lược.

Khoảng MOSI ổn định danh định trước sample là H*T_clk cho cả bit đầu và bit sau. Với H=4/T_clk=10 ns, khoảng danh định 40 ns. Đây là thời gian giữa mốc RTL, chưa trừ clock-to-Q/pad/wire/skew và setup slave. Phải gọi đúng là khoảng setup danh định, không phải biên setup đã xác minh trên bo mạch.

MOSI không bắt buộc đổi ở mọi cạnh xuống: hai bit bằng nhau thì mức giữ nguyên. A5 cũng có cặp 00 và 11, nên không được mô tả “đổi ở mọi biên”. Checker so từng bit, không suy số bit từ số transition MOSI.

