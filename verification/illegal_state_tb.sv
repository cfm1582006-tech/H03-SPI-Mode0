`timescale 1ns/1ps
// Fault injection verifies the specified RTL recovery path; it does not claim
// single-event-upset hardening or gate-level fault coverage.
module illegal_state_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0, start = 0;
    wire sclk, cs_n, busy, done, mosi;
    wire [7:0] rx_data;
    h03_spi_master dut (.clk(clk), .rst_n(rst_n), .start(start),
        .tx_data(8'h96), .miso(1'b1), .mosi(mosi), .sclk(sclk),
        .cs_n(cs_n), .rx_data(rx_data), .busy(busy), .done(done));
    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1; start = 1;
        @(negedge clk); start = 0;
        wait (done === 1'b1);
        @(negedge clk);
        if (rx_data !== 8'hFF) $fatal(1, "Probe prerequisite RX mismatch");
        start = 1;
        @(negedge clk); start = 0;
        wait (sclk === 1'b1);
        // Force the packed bits to inject an otherwise invalid enum encoding.
        // A whole-enum assignment requires a cast rejected by some Icarus builds.
        @(negedge clk);
        force dut.state[0] = 1'b1;
        force dut.state[1] = 1'b1;
        @(posedge clk); #1;
        if ({busy, cs_n, sclk, done, mosi} !== 5'b01000 || rx_data !== 8'hFF)
            $fatal(1, "Illegal-state recovery did not release bus/retain RX");
        release dut.state[0];
        release dut.state[1];
        repeat (2) @(negedge clk);
        if ({busy, cs_n, sclk, done} !== 4'b0100)
            $fatal(1, "Illegal-state recovery did not remain idle");
        start = 1;
        @(negedge clk); start = 0;
        wait (done === 1'b1);
        #1;
        if (rx_data !== 8'hFF || cs_n !== 1'b1 || busy !== 1'b0)
            $fatal(1, "Post-recovery frame failed");
        $display("ILLEGAL_STATE_RECOVERY PASS");
        $finish;
    end
    initial begin
        #10000;
        $fatal(1, "Illegal-state recovery timeout");
    end
endmodule
