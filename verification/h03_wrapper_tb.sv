`timescale 1ns/1ps
module h03_wrapper_tb;
    parameter integer HC = 4;
    parameter bit ORDER = 1'b1;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0, ena = 0, start = 0, miso = 0;
    reg [7:0] ui_in = 0;
    reg unused_input = 0;
    wire [7:0] uo_out, uio_out, uio_oe;
    tri [7:0] uio_bus;
    assign uio_bus = {unused_input, 5'bzzzzz, miso, start};
    genvar pin;
    generate for (pin = 0; pin < 8; pin = pin+1) begin: pad_model
        assign uio_bus[pin] = uio_oe[pin] ? uio_out[pin] : 1'bz;
    end endgenerate
`ifdef GATE_LEVEL
    tt_um_h03_spi_mode0 dut (
`else
    tt_um_h03_spi_mode0 #(.HALF_CYCLES(HC), .MSB_FIRST(ORDER)) dut (
`endif
        .clk(clk), .rst_n(rst_n), .ena(ena), .ui_in(ui_in), .uo_out(uo_out),
        .uio_in(uio_bus), .uio_out(uio_out), .uio_oe(uio_oe));
    wire sclk = uo_out[0];
    wire mosi = uo_out[1];
    wire cs_n = uo_out[2];
    wire busy = uio_bus[5];
    wire done = uio_bus[6];
    wire [7:0] rx_data = {uio_bus[4:2], uo_out[7:3]};
    reg [7:0] slave_payload = 0, previous_rx = 0;
    integer slave_index = 0, selected_frames = 0, cases_passed = 0, csv;

    function automatic bit serial_bit(input reg [7:0] value, input integer index);
        serial_bit = ORDER ? value[7-index] : value[index];
    endfunction
    always @(negedge cs_n) if (rst_n === 1'b1) begin
        slave_index = 0;
        miso = serial_bit(slave_payload, 0);
        selected_frames = selected_frames+1;
    end
    always @(negedge sclk) if (cs_n === 1'b0 && rst_n === 1'b1 && slave_index < 7) begin
        slave_index = slave_index+1;
        miso = serial_bit(slave_payload, slave_index);
    end
    task automatic insist(input bit ok, input string message);
        if (!ok) $fatal(1, "WRAPPER FAIL HC=%0d ORDER=%0d t=%0t %s", HC, ORDER, $time, message);
    endtask
    task automatic check_pins;
        begin
            insist(uio_oe === 8'h7C, "OE must drive only RX[7:5], BUSY, DONE");
            insist(uio_out[7] === 1'b0 && uio_out[1:0] === 2'b00, "Unused output values");
            insist(uio_bus[0] === start && uio_bus[1] === miso,
                   "START/MISO pins must remain external inputs without contention");
            insist((^{uo_out,uio_out,uio_oe}) !== 1'bx, "Unknown wrapper output");
        end
    endtask
    task automatic log_pass(input string name, input reg [7:0] tx, input reg [7:0] rx);
        begin
            cases_passed = cases_passed+1;
            $fdisplay(csv,"%0d,%0d,%s,%02h,%02h,PASS",HC,ORDER,name,tx,rx);
            $display("WRAPPER CASE PASS HC=%0d ORDER=%0d %s", HC,ORDER,name);
        end
    endtask
    task automatic quiet(input integer clocks, input bit held_start);
        integer i, before_frames;
        begin
            before_frames = selected_frames;
            for (i=0; i<clocks; i=i+1) begin
                @(negedge clk); start = held_start; unused_input = ~unused_input;
                @(posedge clk); #1; check_pins();
                insist({busy,done,cs_n,sclk} === 4'b0010, "Idle/status pin mapping");
                insist(rx_data === previous_rx, "RX pin map/hold while idle");
            end
            insist(selected_frames == before_frames, "Unexpected frame while idle/disabled");
        end
    endtask
    // 0 normal; 1 drop ENA after acceptance; 2 hold START; 3 release START;
    // 4 hold START while dropping ENA; 5 pulse START repeatedly while busy.
    task automatic observe(input string name, input reg [7:0] tx,
                           input reg [7:0] rx, input integer mode);
        integer cycle, rises, falls;
        reg prev_sclk, prev_mosi, completed;
        begin
            check_pins();
            insist({busy,done,cs_n,sclk} === 4'b1000, "Admission/status pin mapping");
            insist(mosi === serial_bit(tx,0), "First MOSI bit pin");
            rises=0; falls=0; prev_sclk=sclk; prev_mosi=mosi; completed=0;
            for (cycle=1; cycle<=16*HC+3 && !completed; cycle=cycle+1) begin
                @(negedge clk);
                start = (mode == 2 || mode == 4 || (mode == 5 && cycle % 3 == 0));
                if (mode == 1 || mode == 4) ena = 0;
                ui_in = ~tx; unused_input = ~unused_input;
                @(posedge clk); #1; check_pins();
                if (!prev_sclk && sclk) begin
                    rises=rises+1;
                    insist(rises<=8 && cycle==(2*rises-1)*HC, "Sample edge count/phase");
                    insist(mosi === serial_bit(tx,rises-1), "MOSI byte through physical pin map");
                end
                if (prev_sclk && !sclk) begin
                    falls=falls+1;
                    insist(falls<=8 && cycle==2*falls*HC, "Launch edge count/phase");
                    insist(cs_n === 1'b0, "CS must cover final falling edge");
                end
                if (mosi !== prev_mosi)
                    insist(prev_sclk && !sclk && falls<8, "MOSI launch edge");
                if (done) begin
                    insist(cycle==16*HC+1 && rises==8 && falls==8, "DONE pin/latency");
                    insist({busy,cs_n,sclk} === 3'b010, "Completion pin mapping");
                    insist(rx_data === rx, "Split RX byte reconstruction");
                    previous_rx=rx; completed=1; log_pass(name,tx,rx);
                end else begin
                    insist(cycle<=16*HC && {busy,cs_n} === 2'b10, "Frame/status continuity");
                    insist(rx_data === previous_rx, "RX changed before DONE");
                end
                prev_sclk=sclk; prev_mosi=mosi;
            end
            insist(completed, "Wrapper frame timeout");
        end
    endtask
    task automatic frame(input string name,input reg [7:0] tx,input reg [7:0] rx,input integer mode);
        integer before_frames;
        begin
            before_frames=selected_frames;
            @(negedge clk); ena=1; start=1; ui_in=tx; slave_payload=rx;
            @(posedge clk); #1; observe(name,tx,rx,mode);
            quiet(2,0);
            insist(selected_frames==before_frames+1,"START while busy must not queue");
        end
    endtask
    initial begin
        csv=$fopen("cases.csv","w");
        insist(csv != 0,"Cannot open cases.csv");
        $fdisplay(csv,"half_cycles,msb_first,test,tx_hex,rx_hex,status");
        repeat(3) @(posedge clk); #1; check_pins();
        insist({busy,done,cs_n,sclk,mosi} === 5'b00100 && rx_data===8'h00,"Reset pin mapping");
        log_pass("reset_pin_map",0,0);
        @(negedge clk); rst_n=1;
        quiet(2,0);
        ena=0; quiet(5,1);
        log_pass("disabled_start_ignored",0,0);
        // START already high: enabling ENA admits a level-sensitive request.
        @(negedge clk); ena=1; ui_in=8'h73; slave_payload=8'h2E;
        @(posedge clk); #1; observe("enable_held_start",8'h73,8'h2E,3);
        quiet(2,0);
        frame("normal_A5_3C",8'hA5,8'h3C,0);
        frame("normal_96_C3",8'h96,8'hC3,0);
        frame("ena_drop_completes",8'h5A,8'hE7,1);
        frame("busy_start_pulses",8'h81,8'h7E,5);
        @(negedge clk); ena=1; start=1; ui_in=8'hD2; slave_payload=8'h27;
        @(posedge clk); #1; observe("held_start_first",8'hD2,8'h27,2);
        @(negedge clk); ui_in=8'h8F; slave_payload=8'hC1;
        @(posedge clk); #1; observe("held_start_distinct_second",8'h8F,8'hC1,3);
        quiet(2,0);
        @(negedge clk); ena=1; start=1; ui_in=8'h69; slave_payload=8'h96;
        @(posedge clk); #1; observe("ena_drop_held_start",8'h69,8'h96,4);
        quiet(4,1);
        log_pass("disabled_held_start_no_retrigger",0,previous_rx);

        @(negedge clk); ena=1; start=1; ui_in=8'hB6; slave_payload=8'h4D;
        @(negedge clk); start=0;
        wait(sclk === 1'b1);
        @(negedge clk); rst_n=0;
        #1; insist(cs_n===1'b0 && busy===1'b1,"Reset must be synchronous");
        @(posedge clk); #1; check_pins();
        insist({busy,done,cs_n,sclk,mosi} === 5'b00100 && rx_data===8'h00,"Reset abort pins");
        previous_rx=0; log_pass("reset_abort",8'hB6,0);
        @(negedge clk); rst_n=1;
        quiet(2,0);
        frame("after_reset",8'h80,8'h6D,0);
        $fclose(csv);
        $display("WRAPPER PASS HC=%0d ORDER=%0d cases=%0d",HC,ORDER,cases_passed);
        $finish;
    end
    initial begin #100000; $fatal(1,"Wrapper global timeout"); end
endmodule
