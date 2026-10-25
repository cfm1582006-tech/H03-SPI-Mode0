# H03 — SPI Master mode 0: bản cải tiến và full flow

Thiết kế truyền/nhận đồng thời một byte bằng SPI CPOL=0, CPHA=0. Lõi dùng một clock hệ thống; SCLK là đầu ra có đăng ký. Bản này bổ sung kiểm tham số, phục hồi trạng thái FSM không hợp lệ, wrapper Tiny Tapeout, kiểm thử tự đối chiếu và pipeline RTL→GDSII có lưu bằng chứng.

Đọc [báo cáo cải tiến](docs/BAO_CAO_CAI_TIEN.md), [kết quả thực chạy](docs/RESULTS.md) và [nhật ký sửa tài liệu](docs/CHANGE_AUDIT.md). Các con số hiện hành phải đối chiếu với JSON/log của lần chạy trong báo cáo kết quả. Nguồn ZIP gốc được giữ riêng tại workspace để đối chiếu.

## Mã nguồn và giao diện

- Lõi: `04_IMPLEMENTATION/rtl/h03_spi_master.sv`.
- Top Tiny Tapeout: `04_IMPLEMENTATION/rtl/tt_um_h03_spi_mode0.sv`.
- `HALF_CYCLES` ≥ 1; mặc định 4. `MSB_FIRST` mặc định 1.
- Với H=4, clock hệ thống 100 MHz: SCLK danh định 12,5 MHz, START→DONE 65 chu kỳ.
- START là tín hiệu mức, chỉ nhận khi IDLE. Giữ START cao sẽ phát lại frame; cần hạ START nếu chỉ muốn một frame.
- Reset thấp có hiệu lực tại cạnh lên clk. ENA của wrapper chỉ chặn nhận START mới; frame đang chạy vẫn hoàn tất nếu không reset.

| Chân wrapper | Chức năng |
|---|---|
| `ui_in[7:0]` | TX byte |
| `uio_in[0]`, `uio_in[1]` | START, MISO |
| `uo_out[0]`, `[1]`, `[2]` | SCLK, MOSI, CS_n |
| `uo_out[7:3]`, `uio_out[4:2]` | RX[4:0], RX[7:5] |
| `uio_out[5]`, `[6]` | BUSY, DONE |
| `uio[7]` | Dự phòng, không điều khiển |

`RX_BYTE = {uio_out[4:2], uo_out[7:3]}`; `uio_oe = 8'h7c`. START/MISO luôn là đầu vào. Map giải quyết xung đột uio[0:1] trong phiếu đề.

## Chạy kiểm thử

Cần Python ≥ 3.10, Icarus và vvp trong PATH; các runner không cần thư viện Python ngoài.

```bash
python3 scripts/run_regression.py --out evidence/my_regression --mutations
python3 scripts/run_wrapper_test.py --out evidence/my_wrapper
python3 05_VERIFICATION/golden_model/reference_model.py --self-check
```

Runner yêu cầu thư mục đầu ra mới, dừng khi compiler lỗi, không tái sử dụng binary cũ. Ba mutation phải bị phát hiện; hai tham số H không hợp lệ phải bị từ chối. Chi tiết: [verification/README.md](verification/README.md).

## Chạy toàn bộ RTL→GDSII

Trong shell EDA có LibreLane 3.0.16, Yosys, OpenROAD, Magic, KLayout, Netgen, EQY/SBY/ABC, Icarus và PDK sky130A:

```bash
python3 scripts/run_full_flow.py --pdk-root /path/to/pdk-version \
  --tag my_fresh_run --jobs 4 --tops both --out evidence/my_full_flow
```

`/path/to/pdk-version` là thư mục chứa `sky130A`. PDK của lần chạy này là `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`. Có thể dùng AppImage sẵn cài trên máy này để cấp PATH:

```bash
/home/duongluong/librelane-devshell-x86_64.AppImage python3 scripts/run_full_flow.py \
  --pdk-root /home/duongluong/.ciel/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71 \
  --tag my_fresh_run --tops both --out evidence/my_full_flow
```

Pipeline chạy regression, wrapper, Classic flow cho mỗi top, kiểm tất cả corner, chứng minh equivalence RTL–netlist và mô phỏng netlist chức năng. Nó lưu nguồn đầu vào/hash/lệnh/mã thoát, từ chối kết quả thiếu metric hoặc có vi phạm. EQY dùng script riêng để khắc phục lỗi nhập blackbox dư trong script mặc định; kết quả proof vẫn là điều kiện bắt buộc.

Xem [flow/README.md](flow/README.md) về tải, slew, delay và giới hạn tích hợp phần cứng. Layout wrapper là macro với cổng Tiny Tapeout; việc lắp vào harness/tile của shuttle cần flow tích hợp riêng.

## GitHub và CI

`.github/workflows/simulation.yml` chạy trên GitHub-hosted Ubuntu. `physical.yml` chạy thủ công trên runner Linux có nhãn `eda`, biến repository `PDK_ROOT` trỏ PDK đã cài và `LIBRELANE_APPIMAGE` trỏ AppImage. Workflow gọi AppImage trực tiếp để có PATH EDA đúng. Các workflow đã soạn sẵn; trạng thái chạy trên GitHub được ghi riêng trong báo cáo kết quả. Không xem log chạy tại máy là log GitHub Actions.

Làm theo [hướng dẫn hoàn thành GitHub, CI và hồ sơ nộp](docs/HUONG_DAN_HOAN_THANH_DU_AN.md).

Tài liệu và cấu hình được tổ chức theo [cấu hình LibreLane](https://librelane.readthedocs.io/en/latest/reference/configuration.html) và [Classic flow](https://librelane.readthedocs.io/en/latest/reference/flows.html).
