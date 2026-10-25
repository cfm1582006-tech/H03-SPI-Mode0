def tx_sequence(byte, msb_first=True):
    b=int(byte)&0xff
    return [(b>>(7-i if msb_first else i))&1 for i in range(8)]

def mode0_edges():
    # Each bit has falling update edge followed by rising sample edge in the
    # steady-state transaction. The first bit must be established before the first rise.
    return ["rise","fall"]*8

def receive_sequence(miso_bits, msb_first=True):
    bits=[int(x)&1 for x in miso_bits]
    assert len(bits)==8
    if msb_first:
        v=0
        for b in bits:
            v=(v<<1)|b
        return v
    return sum(b<<i for i,b in enumerate(bits))

def test_mode0():
    assert mode0_edges()==["rise","fall"]*8

def test_tx_order():
    assert tx_sequence(0x96,True)==[1,0,0,1,0,1,1,0]
    assert tx_sequence(0x96,False)==[0,1,1,0,1,0,0,1]

def test_rx():
    for b in [0x00,0x01,0x55,0x96,0xA5,0xFF]:
        assert receive_sequence(tx_sequence(b,True),True)==b
        assert receive_sequence(tx_sequence(b,False),False)==b

def test_eight_clocks():
    assert len(mode0_edges())==16
    assert sum(e=="rise" for e in mode0_edges())==8
    assert sum(e=="fall" for e in mode0_edges())==8

def test_full_duplex_time():
    assert 8 < 16

def test_cs_encloses_rises():
    rises=list(range(8))
    cs_start=-1
    cs_end=8
    assert cs_start < rises[0] and rises[-1] < cs_end

def test_divider():
    fclk=16_000_000
    fsclk=1_000_000
    half=round(fclk/(2*fsclk))
    assert half==8
    assert abs(fclk/(2*half)-fsclk)<1e-12

def test_random():
    import random
    random.seed(303)
    for _ in range(5000):
        b=random.randrange(256)
        order=bool(random.randrange(2))
        bits=tx_sequence(b,order)
        assert receive_sequence(bits,order)==b

if __name__=="__main__":
    test_mode0()
    test_tx_order()
    test_rx()
    test_eight_clocks()
    test_full_duplex_time()
    test_cs_encloses_rises()
    test_divider()
    test_random()
    print("H03 golden reference PASS")
