`timescale 1ns/1ps
// Independent, pin-level regression against the supplied RTL.
// Slave preloads MISO at CS assertion, then changes it on SCLK falling edges.
module h03_spi_regression_tb;
    parameter integer HC = 2;
    parameter bit ORDER = 1'b1;
    parameter integer RANDOM_CASES = 128;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0, start = 0;
    reg [7:0] tx_data = 0;
    reg miso = 0;
    wire mosi, sclk, cs_n, busy, done;
    wire [7:0] rx_data;
`ifdef GATE_LEVEL
    // The technology-mapped netlist has its parameters fixed at synthesis.
    h03_spi_master dut (
`else
    h03_spi_master #(.HALF_CYCLES(HC), .MSB_FIRST(ORDER)) dut (
`endif
        .clk(clk), .rst_n(rst_n), .start(start), .tx_data(tx_data),
        .miso(miso), .mosi(mosi), .sclk(sclk), .cs_n(cs_n),
        .rx_data(rx_data), .busy(busy), .done(done));

    reg [7:0] slave_payload = 0;
    integer slave_index = 0;
    integer selected_frames = 0;
    integer cases_passed = 0;
    integer csv;
    reg [7:0] previous_rx = 0;
    reg [31:0] random_state = 32'h1a2b3c4d;
    reg [7:0] random_tx, random_rx;
    integer vector_index, reset_offset;

    // Fixed xorshift32 seed, independent of simulator random-number algorithms.
    function automatic reg [31:0] next_random(input reg [31:0] value);
        reg [31:0] x;
        begin
            x = value ^ (value << 13);
            x = x ^ (x >> 17);
            next_random = x ^ (x << 5);
        end
    endfunction

    function automatic bit serial_bit(input reg [7:0] value, input integer index);
        serial_bit = ORDER ? value[7-index] : value[index];
    endfunction

    always @(negedge cs_n) begin
        if (rst_n === 1'b1) begin
            slave_index = 0;
            miso = serial_bit(slave_payload, 0);
            selected_frames = selected_frames + 1;
        end
    end
    always @(negedge sclk) begin
        if (cs_n === 1'b0 && rst_n === 1'b1 && slave_index < 7) begin
            slave_index = slave_index + 1;
            miso = serial_bit(slave_payload, slave_index);
        end
    end

    task automatic insist(input bit condition, input string message);
        if (!condition) begin
            $display("FAIL HC=%0d ORDER=%0d t=%0t: %s", HC, ORDER, $time, message);
            $fatal(1, "%s", message);
        end
    endtask

    task automatic log_pass(input string name, input reg [7:0] tx,
                            input reg [7:0] rx, input integer latency);
        cases_passed = cases_passed + 1;
        $fdisplay(csv, "%0d,%0d,%s,%02h,%02h,%0d,PASS", HC, ORDER, name, tx, rx, latency);
        $display("CASE PASS HC=%0d ORDER=%0d %s TX=%02h RX=%02h latency=%0d",
            HC, ORDER, name, tx, rx, latency);
    endtask

    // Called just after an accepting clock edge. mode: 0 normal;
    // 1 pulse START while busy; 2 hold START and TX through the next frame;
    // 3 drop START on the next falling system-clock edge.
    task automatic observe_frame(input string name, input reg [7:0] tx,
        input reg [7:0] rx, input integer mode);
        integer cycle, rises, falls;
        reg previous_sclk, previous_mosi;
        reg completed;
        begin
            insist(busy === 1'b1 && cs_n === 1'b0 && sclk === 1'b0,
                {name, ": accepting edge must assert BUSY/CS with SCLK low"});
            insist(mosi === serial_bit(tx, 0), {name, ": first MOSI bit"});
            insist(done === 1'b0, {name, ": no DONE at acceptance"});
            rises = 0; falls = 0; completed = 0;
            previous_sclk = sclk; previous_mosi = mosi;
            for (cycle = 1; cycle <= 16*HC+3 && !completed; cycle = cycle + 1) begin
                @(negedge clk);
                if (mode == 2) begin
                    start = 1; tx_data = tx;
                end else begin
                    start = (mode == 1 && cycle == 4) ||
                            (mode == 4 && cycle <= 16*HC) ||
                            (mode == 5 && cycle == 16*HC+1);
                    tx_data = ~tx; // Verify that the accepted byte is latched.
                end
                @(posedge clk); #1;
                insist((^{busy, done, cs_n, sclk, mosi, rx_data}) !== 1'bx,
                    {name, ": unexpected X/Z"});
                if (!previous_sclk && sclk) begin
                    rises = rises + 1;
                    insist(rises <= 8, {name, ": extra rising edge"});
                    insist(cycle == (2*rises-1)*HC, {name, ": rising-edge divider/phase"});
                    insist(cs_n === 1'b0 && busy === 1'b1, {name, ": CS/BUSY at sample edge"});
                    insist(mosi === serial_bit(tx, rises-1), {name, ": transmitted bit mismatch"});
                end
                if (previous_sclk && !sclk) begin
                    falls = falls + 1;
                    insist(falls <= 8, {name, ": extra falling edge"});
                    insist(cycle == 2*falls*HC, {name, ": falling-edge divider/phase"});
                    insist(cs_n === 1'b0, {name, ": CS must enclose final falling edge"});
                    if (falls == 8)
                        insist(mosi === previous_mosi, {name, ": MOSI changed on final falling edge"});
                end
                if (mosi !== previous_mosi)
                    insist(previous_sclk && !sclk && falls < 8,
                        {name, ": MOSI changed away from data-update edge"});
                if (done === 1'b1) begin
                    insist(cycle == 16*HC+1, {name, ": DONE latency"});
                    insist(rises == 8 && falls == 8, {name, ": exactly eight full SCLK pulses"});
                    insist(cs_n === 1'b1 && sclk === 1'b0 && busy === 1'b0,
                        {name, ": completion bus state"});
                    insist(rx_data === rx, {name, ": received byte mismatch"});
                    previous_rx = rx;
                    completed = 1;
                    log_pass(name, tx, rx, cycle);

                end else begin
                    insist(cycle <= 16*HC, {name, ": missing DONE"});
                    insist(cs_n === 1'b0 && busy === 1'b1, {name, ": premature CS/BUSY release"});
                    insist(rx_data === previous_rx, {name, ": RX_DATA changed before DONE"});
                end
                previous_sclk = sclk; previous_mosi = mosi;
            end
            insist(completed, {name, ": transaction timeout"});
        end
    endtask

    task automatic check_idle(input integer clocks);
        integer i, frames_before;
        begin
            frames_before = selected_frames;
            for (i = 0; i < clocks; i = i + 1) begin
                @(negedge clk); start = 0; tx_data = tx_data ^ 8'h5A;
                @(posedge clk); #1;
                insist(cs_n === 1'b1 && sclk === 1'b0 && busy === 1'b0 && done === 1'b0,
                    "Idle bus or DONE pulse width");
                insist(rx_data === previous_rx, "RX_DATA must hold in idle");
            end
            insist(selected_frames == frames_before, "Unexpected extra frame in idle");
        end
    endtask

    task automatic run_frame(input string name, input reg [7:0] tx,
        input reg [7:0] rx, input integer mode);
        integer frames_before;
        begin
            frames_before = selected_frames;
            @(negedge clk); slave_payload = rx; tx_data = tx; start = 1;
            @(posedge clk); #1;
            observe_frame(name, tx, rx, mode);
            check_idle(3);
            insist(selected_frames == frames_before + 1, {name, ": START while busy queued an extra frame"});
        end
    endtask

    task automatic abort_frame(input integer elapsed);
        integer i, frames_before;
        reg [2:0] bus_before_reset;
        begin
            frames_before = selected_frames;
            @(negedge clk); slave_payload = 8'hC3; tx_data = 8'h5A; start = 1;
            @(posedge clk); #1;
            for (i = 0; i < elapsed; i = i + 1) begin
                @(negedge clk); start = 0;
                @(posedge clk); #1;
            end
            @(negedge clk);
            start = 0;
            bus_before_reset = {busy, cs_n, sclk};
            rst_n = 0;
            #1;
            insist({busy, cs_n, sclk} === bus_before_reset,
                "Synchronous reset must not change outputs before a clock edge");
            @(posedge clk); #1;
            insist(cs_n === 1'b1 && sclk === 1'b0 && busy === 1'b0 && done === 1'b0,
                "Synchronous mid-frame reset must abort and release bus");
            insist(rx_data === 8'h00 && mosi === 1'b0, "Reset RX_DATA/MOSI");
            previous_rx = 0;
            @(negedge clk); rst_n = 1;
            check_idle(2);
            insist(selected_frames == frames_before + 1, "Reset should not trigger a replacement frame");
            log_pass($sformatf("reset_abort_at_%0d", elapsed), 8'h5A, 0, elapsed+1);
        end
    endtask

    task automatic reset_start_priority;
        begin
            @(negedge clk); rst_n = 0; start = 1; tx_data = 8'h73;
            slave_payload = 8'hB2;
            repeat (3) begin
                @(posedge clk); #1;
                insist(cs_n === 1'b1 && busy === 1'b0 && sclk === 1'b0 &&
                       done === 1'b0 && rx_data === 8'h00 && mosi === 1'b0,
                       "Reset must override held START");
                @(negedge clk);
            end
            previous_rx = 0;
            rst_n = 1;
            @(posedge clk); #1;
            observe_frame("held_start_after_reset", 8'h73, 8'hB2, 3);
            check_idle(2);
        end
    endtask

    initial begin
        csv = $fopen("cases.csv", "w");
        insist(csv != 0, "Cannot create cases.csv");
        $fdisplay(csv, "half_cycles,msb_first,test,tx_hex,rx_hex,latency_cycles,status");
`ifdef DUMP_VCD
        $dumpfile("sample_mode0.vcd");
        $dumpvars(0, h03_spi_regression_tb);
`endif
        repeat (3) @(posedge clk);
        #1;
        insist(cs_n === 1'b1 && sclk === 1'b0 && busy === 1'b0 && done === 1'b0,
            "Reset outputs");
        @(negedge clk); rst_n = 1;
        check_idle(2);

        run_frame("mandatory_00", 8'h00, 8'hFF, 0);
        run_frame("mandatory_FF", 8'hFF, 8'h00, 0);
        run_frame("mandatory_A5", 8'hA5, 8'h3C, 0);
        run_frame("pattern_96", 8'h96, 8'hC3, 0);
        run_frame("asymmetric_01", 8'h01, 8'h80, 0);
        run_frame("asymmetric_80", 8'h80, 8'h01, 0);
        run_frame("alternating_55", 8'h55, 8'hAA, 0);
        run_frame("alternating_AA", 8'hAA, 8'h55, 0);
        run_frame("start_while_busy", 8'h69, 8'hE1, 1);

        // Held START retriggers. The low-CS start interval is 16*HC+2 clocks.
        @(negedge clk); slave_payload = 8'h27; tx_data = 8'hD2; start = 1;
        @(posedge clk); #1;
        observe_frame("held_start_first", 8'hD2, 8'h27, 2);
        @(posedge clk); #1;
        insist(done === 1'b0 && cs_n === 1'b0 && busy === 1'b1,
            "Held START must retrigger at first IDLE accepting edge");
        observe_frame("held_start_second", 8'hD2, 8'h27, 3);
        check_idle(3);

        abort_frame(HC);       // Reset while SCLK high.
        run_frame("after_reset_high", 8'h01, 8'hB6, 0);
        abort_frame(2*HC);     // Reset while SCLK low.
        run_frame("after_reset_low", 8'h80, 8'h6D, 0);

        run_frame("busy_start_every_cycle", 8'h38, 8'hA7, 4);
        run_frame("start_in_finish_not_queued", 8'hF0, 8'h0F, 5);
        reset_start_priority();

`ifdef DUMP_VCD
        // Keep the example waveform compact; all later checks still execute.
        $dumpoff;
`endif
        // The odd multiplier is a permutation modulo 256. Each possible byte
        // therefore appears once on TX and once independently on RX.
        for (vector_index = 0; vector_index < 256; vector_index = vector_index+1)
            run_frame($sformatf("exhaustive_byte_%03d", vector_index),
                      vector_index[7:0], (vector_index*73+41) & 255, 0);

        for (vector_index = 0; vector_index < RANDOM_CASES; vector_index = vector_index+1) begin
            random_state = next_random(random_state); random_tx = random_state[7:0];
            random_state = next_random(random_state); random_rx = random_state[7:0];
            run_frame($sformatf("seeded_random_%03d", vector_index), random_tx, random_rx,
                      (vector_index % 7 == 0) ? 1 : 0);
        end

        // Include every divider phase, all eight bit positions, and the FINISH
        // state reached just after the last falling edge. Reset cancels DONE.
        for (reset_offset = 0; reset_offset <= 16*HC; reset_offset = reset_offset+1) begin
            abort_frame(reset_offset);
            run_frame($sformatf("recover_offset_%03d", reset_offset),
                      reset_offset[7:0] ^ 8'h96, reset_offset[7:0] ^ 8'hE1, 0);
        end

        $fclose(csv);
        $display("REGRESSION PASS HC=%0d ORDER=%0d cases=%0d", HC, ORDER, cases_passed);
        $finish;
    end
    initial begin
        #10000000;
        $fatal(1, "Global timeout");
    end
endmodule
