`timescale 1ns/1ps
module invalid_parameter_tb;
    parameter integer HC = 0;
    reg clk = 0;
    always #5 clk = ~clk;
    h03_spi_master #(.HALF_CYCLES(HC)) dut (
        .clk(clk), .rst_n(1'b0), .start(1'b0), .tx_data(8'h00), .miso(1'b0),
        .mosi(), .sclk(), .cs_n(), .rx_data(), .busy(), .done());
    initial begin
        #20;
        $display("INVALID_PARAMETER_WAS_ACCEPTED");
        $finish;
    end
endmodule
