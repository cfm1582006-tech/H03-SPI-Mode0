# H03 — Timing và giả định

Lõi có một miền clk; SCLK là đầu ra flip-flop. Clock 10 ns và IO delay là giả định ở mức khối, phải công bố khi báo số. SDC phải cùng config với run; không suy Fmax từ nghịch đảo một delay path đơn lẻ.

Mode 0: bit đầu MOSI có trước cạnh lên SCLK đầu; bit sau phát tại cạnh xuống và lấy mẫu ở cạnh lên kế. Trong RTL zero-delay, MOSI ổn định danh định H*T_clk cho mọi bit; H=4/T_clk=10 ns cho 40 ns.

40 ns không phải setup margin điện thực tế. Cần trừ chênh clock-to-Q MOSI/SCLK, pad, dây và yêu cầu setup/hold slave. Chiều MISO cần ngân sách vòng SCLK ra slave → clock-to-out slave → dây về → input pad → FF thu. Chưa có datasheet/board timing nên chưa thể xác nhận.

| Đại lượng | Công thức lý tưởng |
|---|---|
| Nửa SCLK | H*T_clk |
| Chu kỳ SCLK | 2H*T_clk |
| CS xuống → SCLK lên #1 | H*T_clk |
| SCLK xuống #8 → CS lên | T_clk |
| START → DONE | (16H+1)*T_clk |
| CS cao giữa hai frame giữ START | T_clk |

Reset đồng bộ có hiệu lực ở cạnh clk kế tiếp, không nhả bus tức thời. Reset/start/TX đều cần timing theo clk; không tự false-path reset đồng bộ. Mô phỏng chức năng không chứng minh glitch sau P&R hoặc SI/board timing.

