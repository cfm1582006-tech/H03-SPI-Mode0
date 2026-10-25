module h03_spi_master #(
    parameter int HALF_CYCLES = 4,
    parameter bit MSB_FIRST   = 1'b1
) (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       start,
    input  logic [7:0] tx_data,
    input  logic       miso,
    output logic       mosi,
    output logic       sclk,
    output logic       cs_n,
    output logic [7:0] rx_data,
    output logic       busy,
    output logic       done
);

    localparam int HCW = (HALF_CYCLES <= 1) ? 1 : $clog2(HALF_CYCLES);

    logic [HCW-1:0] half_count;
    logic [3:0] edge_count;
    logic [7:0] tx_shift;
    logic [7:0] rx_shift;

    typedef enum logic [1:0] {IDLE, TRANSFER, FINISH} state_t;
    state_t state;

    wire half_tick = (HALF_CYCLES <= 1) || (half_count == HALF_CYCLES-1);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            half_count <= '0;
            edge_count <= '0;
            tx_shift   <= '0;
            rx_shift   <= '0;
            rx_data    <= '0;
            mosi       <= 1'b0;
            sclk       <= 1'b0;
            cs_n       <= 1'b1;
            busy       <= 1'b0;
            done       <= 1'b0;
            state      <= IDLE;
        end else begin
            done <= 1'b0;

            case (state)
                IDLE: begin
                    sclk <= 1'b0;
                    cs_n <= 1'b1;
                    busy <= 1'b0;
                    half_count <= '0;
                    edge_count <= '0;

                    if (start) begin
                        busy <= 1'b1;
                        cs_n <= 1'b0;
                        tx_shift <= tx_data;
                        rx_shift <= '0;
                        edge_count <= '0;
                        mosi <= MSB_FIRST ? tx_data[7] : tx_data[0];
                        state <= TRANSFER;
                    end
                end

                TRANSFER: begin
                    busy <= 1'b1;

                    if (half_tick) begin
                        half_count <= '0;

                        if (sclk == 1'b0) begin
                            // Rising edge: mode-0 sample edge.
                            sclk <= 1'b1;
                            rx_shift <= MSB_FIRST
                                      ? {rx_shift[6:0],miso}
                                      : {miso,rx_shift[7:1]};
                            edge_count <= edge_count + 1'b1;
                        end else begin
                            // Falling edge: mode-0 data-update edge.
                            sclk <= 1'b0;

                            if (edge_count == 8) begin
                                state <= FINISH;
                            end else begin
                                if (MSB_FIRST) begin
                                    tx_shift <= {tx_shift[6:0],1'b0};
                                    mosi <= tx_shift[6];
                                end else begin
                                    tx_shift <= {1'b0,tx_shift[7:1]};
                                    mosi <= tx_shift[1];
                                end
                            end
                        end
                    end else begin
                        half_count <= half_count + 1'b1;
                    end
                end

                FINISH: begin
                    sclk <= 1'b0;
                    cs_n <= 1'b1;
                    busy <= 1'b0;
                    rx_data <= rx_shift;
                    done <= 1'b1;
                    state <= IDLE;
                end
            endcase
        end
    end
endmodule
