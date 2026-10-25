# H03 — Sơ đồ khối

    TX/START ──> [Nạp TX/bit đầu] ──> [TX shift] ──> MOSI
                        ↑                 ↑
    clk/reset ──> [FSM IDLE/TRANSFER/FINISH] ──> CS/BUSY/DONE
                        ↓                 ↓
                 [half_count/tick] ──> SCLK đăng ký
                                          ↓ sample-enable
    MISO ─────────────────────────> [RX shift] ──> [RX result] ──> RX

Các đường là enable/dữ liệu trong cùng miền clk. Đầu ra SCLK không làm clock của shift register nội bộ. Divider tạo half_tick; FSM quyết định nâng/hạ SCLK, nạp/shift và hoàn tất.

TX/RX shift 8 bit độc lập giúp quan sát song công; RX result giữ byte hoàn chỉnh trong khi nhận frame kế. Số thanh ghi khai báo không bằng số FF sau synthesis vì hằng/bit không dùng có thể bị tối ưu và FSM có thể đổi mã. Chỉ báo FF từ netlist/thống kê của run tương ứng.

Wrapper tt_um_h03_spi_mode0 chỉ ánh xạ chân và gate START bởi ena; không thay thuật toán SPI.

