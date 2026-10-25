# H03 — Assertion và checker

Các kiểm tra thực thi chính nằm trong verification/h03_spi_regression_tb.sv: mức idle/reset, không X/Z sau reset, bit MOSI, byte RX, tám cạnh lên/xuống, divider/pha, CS bao trọn, DONE một clk và RX giữ ổn định.

properties.sv trong testbench/ là bản cũ chứa SVA dưới macro H03_SVA. Không tính các property này đã chạy nếu macro tắt hoặc simulator không hỗ trợ. File hiện có không thay thế checker độc lập và không phải formal proof.

Nếu dùng simulator hỗ trợ SVA, cần wrapper/bind/module hợp lệ và một lệnh chạy riêng có log. Kết luận “không có assertion vi phạm” chỉ có nghĩa với những assertion thật sự được compile và thực thi.

