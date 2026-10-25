`ifdef H03_SVA

// SCLK must return to idle-low after a completed transaction.
assert sclk_idle:
    assert property (@(posedge clk) !busy |-> !sclk);

// DONE is a pulse.
assert done_pulse:
    assert property (@(posedge clk) done |=> !done);

`endif
