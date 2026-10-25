module h03_spi_master_tb;
    localparam int HC=2;

    logic clk=0,rst_n=0,start=0;
    logic [7:0] tx_data=8'h96;
    logic miso;
    logic mosi,sclk,cs_n,busy,done;
    logic [7:0] rx_data;

    h03_spi_master #(.HALF_CYCLES(HC),.MSB_FIRST(1'b1)) dut(
        .clk(clk),.rst_n(rst_n),.start(start),.tx_data(tx_data),
        .miso(miso),.mosi(mosi),.sclk(sclk),.cs_n(cs_n),
        .rx_data(rx_data),.busy(busy),.done(done));

    always #5 clk=~clk;

    logic [7:0] slave_bits=8'h3C;
    integer rise_count=0;
    integer fall_count=0;
    integer rx_i=0;

    always @(posedge sclk) begin
        rise_count = rise_count + 1;
        if (rx_i < 8)
            miso = slave_bits[7-rx_i];
    end

    always @(negedge sclk) begin
        fall_count = fall_count + 1;
        rx_i = rx_i + 1;
    end

    initial begin
        miso=1'b0;
        repeat(2) @(posedge clk);
        rst_n=1;

        @(negedge clk);
        start=1;
        @(negedge clk);
        start=0;

        wait(done);
        assert(rise_count==8) else $fatal(1,"Expected 8 rising edges");
        assert(fall_count>=8) else $fatal(1,"Expected falling edges");
        assert(cs_n==1'b1) else $fatal(1,"CS not released");

        $display("H03 TB completed");
        $finish;
    end
endmodule
