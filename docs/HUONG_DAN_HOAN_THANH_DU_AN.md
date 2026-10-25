# H03 — Hướng dẫn hoàn thành GitHub, CI và hồ sơ nộp

Hướng dẫn viết cho máy Windows của bạn, Ubuntu WSL và bộ EDA đã chạy đạt ngày 25/10/2026. Repo gợi ý là `cfm1582006-tech/H03-SPI-Mode0`; đây là tên dự kiến, chưa phải repo đã tạo.

## 1. Chốt mục tiêu cần hoàn thành

Đọc [Charter H03/B2](REFERENCE_CHARTER_H03.html), đặc biệt các mục 7, 9 và 12. Bài yêu cầu repo cá nhân có lịch sử commit và link CI, RTL/testbench, artifacts hoặc log lỗi có chẩn đoán, PDF 8–15 trang và chuẩn bị vấn đáp 5 phút. Tape-out, chế tạo và sign-off nằm ngoài phạm vi học phần.

Phần đã có: mã RTL, wrapper, kiểm thử, GDS của hai top, STA chín corner, DRC/LVS, equivalence, mô phỏng netlist, waveform và báo cáo Markdown. Phần cần chốt: repo và CI thật, quyền xem của người chấm, PDF cùng thông tin tái lập. Chỉ làm thêm harness Tiny Tapeout nếu yêu cầu cụ thể của giảng viên hoặc mục tiêu nộp shuttle cần đến.

## 2. Tạo repo GitHub

1. Đăng nhập đúng tài khoản `cfm1582006-tech`, mở [trang tạo repository](https://github.com/new).
2. Owner chọn tài khoản cá nhân; tên có thể là `H03-SPI-Mode0`.
3. Chọn **Private** cho repo dùng runner cá nhân. Khi nộp, cấp quyền xem cho giảng viên theo yêu cầu lớp. GitHub khuyến nghị private cho self-hosted runner vì runner thực thi mã trên máy của bạn.
4. Repo ban đầu để trống các lựa chọn tạo README, .gitignore và license: các tệp cần thiết đã có trong dự án.
5. Nhấn **Create repository**, giữ lại URL repo.

Tham khảo: [GitHub — tạo repo](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository), [khuyến nghị cho runner cá nhân](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners).

Việc kết nối ứng dụng GitHub và tạo repository là hai việc riêng. Kết nối hiện tại xác thực được tài khoản nhưng danh sách repo trả về đang trống; sau khi tạo repo, gửi URL repo để kiểm tra truy cập lại. “All repositories” cho phép truy cập theo phạm vi installation; nó không tự tạo repo.

## 3. Đưa đúng thư mục lên repo

Thư mục dùng làm gốc repo là:

```text
C:\Users\cfm15\OneDrive\Documents\ChatGPT\Nghiên cứu khoa học _ CPU & Peripherals 2\H03_SPI_Mode0_Improved
```

Cấu trúc ở trang Code phải có `.github`, `scripts`, `flow`, `verification` và `04_IMPLEMENTATION` trực tiếp tại gốc. Nếu chỉ upload một ZIP, hoặc để toàn dự án nằm dưới một thư mục con, GitHub sẽ không tìm thấy workflow ở vị trí cần thiết.

Mở PowerShell, chạy lần lượt các lệnh dưới đây sau khi đã tạo repo trống đúng tên gợi ý:

```powershell
Set-Location -LiteralPath 'C:\Users\cfm15\OneDrive\Documents\ChatGPT\Nghiên cứu khoa học _ CPU & Peripherals 2\H03_SPI_Mode0_Improved'
git init
git branch -M main
git add .
git status --short
git commit -m "Import verified H03 SPI mode 0 project"
git remote add origin https://github.com/cfm1582006-tech/H03-SPI-Mode0.git
git push -u origin main
```

Nếu đặt tên repo khác, thay URL ở lệnh `git remote add`. Nếu Git yêu cầu tên/email tác giả, cấu hình danh tính của chính bạn trong repo rồi chạy lại commit; có thể dùng địa chỉ noreply trong GitHub Settings → Emails. Nếu trình quản lý thông tin đăng nhập mở trình duyệt, bạn tự hoàn tất đăng nhập GitHub ở đó.

`.gitignore` đã bỏ qua `flow/runs`, `evidence`, binary mô phỏng và cache. Những thư mục đó vẫn có trong ZIP đầy đủ để lưu bằng chứng; GitHub Actions sẽ sinh artifacts riêng của lần chạy CI. Các link local trong RESULTS.md cần được bổ sung bằng link CI/ZIP tải về khi đọc trên GitHub.

Giữ lịch sử commit thật kể từ thời điểm nhập dự án. Mỗi lần sửa cấu hình runner, giải thích kết quả, xử lý phản biện hay sửa RTL được ghi bằng một commit có nội dung tương ứng. Báo cáo nên nói rõ đây là lần nhập bản đã chạy cục bộ, không mô tả các commit mới như lịch sử phát triển đã tồn tại trước đó.

## 4. Chạy simulation CI trước

Vào repo → **Actions** → **SPI functional verification**. Workflow này dùng Ubuntu do GitHub cung cấp và tự chạy khi push. Nếu cần chạy lại từ giao diện, chọn **Run workflow** trên nhánh main.

Kết quả mong đợi: lint thành công; mô hình sự kiện self-check đạt; regression lõi 6.320 ca, ba probe và ba mutation đúng kỳ vọng; wrapper 78 ca. Một phép thử tham số sai trả mã lỗi trong simulator là kết quả mong đợi, runner tổng hợp vẫn phải PASS.

Mở trang run và sao chép URL dạng `https://github.com/.../actions/runs/...`. Ở cuối trang có artifact `spi-verification-<commit-sha>`; tải về để giữ lâu dài. Workflow hiện đặt thời hạn lưu 14 ngày.

Nếu tab Actions không có workflow, kiểm tra vị trí `.github/workflows/simulation.yml` ở gốc repo. Nếu Actions bị tắt, kiểm tra repo Settings → Actions → General và quyền dùng các action checkout/upload-artifact. Chỉ bật đúng quyền cần dùng.

Nguồn: [GitHub — chạy workflow thủ công](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

## 5. Đăng ký máy WSL làm runner vật lý

Runner là chương trình nhận job từ GitHub rồi chạy lệnh trên máy của bạn. Máy cần có kết nối mạng và đang bật trong lúc job chạy. Workflow physical chỉ chạy thủ công và tìm runner có đủ bốn nhãn `self-hosted`, `linux`, `x64`, `eda`.

Trên GitHub mở **Settings → Actions → Runners → New self-hosted runner**. Chọn **Linux**, kiến trúc **x64**. Mặc dù máy ngoài là Windows, chương trình runner của dự án này chạy bên trong Ubuntu WSL.

Mở ứng dụng Ubuntu, chuẩn bị thư mục riêng:

```bash
mkdir -p ~/actions-runner-h03
cd ~/actions-runner-h03
```

GitHub hiển thị các lệnh download, giải nén và `./config.sh`. Dùng đúng các lệnh đang hiển thị cho repo của bạn, chạy trong thư mục trên. Token đăng ký có thời hạn; chỉ dán vào terminal của bạn, không gửi qua chat. Nếu quá hạn, lấy lệnh/token mới trên trang runner.

Khi cấu hình tương tác:

- Tên runner: có thể đặt `h03-wsl`.
- Nhãn bổ sung: nhập **`eda`**.
- Work folder: có thể giữ `_work` mặc định.

Sau khi cấu hình xong, chạy:

```bash
./run.sh
```

Khi thấy thông báo chờ nhận job, vào trang runner trên GitHub để xác nhận trạng thái **Idle**. Giữ cửa sổ Ubuntu này mở trong lúc chạy CI. Bước đầu chưa cần cài runner thành service hoặc thay cấu hình khởi động WSL.

Nguồn: [cài runner](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners), [cách chọn runner bằng nhãn](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow).

## 6. Cấp đúng môi trường EDA cho workflow

Đăng ký runner xong chưa tự làm xuất hiện LibreLane/Yosys/EQY trong PATH. Bản workflow đã cập nhật gọi AppImage trực tiếp, vì vậy bạn chỉ cần đặt hai repository variable.

Trong repo mở **Settings → Secrets and variables → Actions → Variables → New repository variable**. Tạo:

| Name | Value trên máy hiện tại |
|---|---|
| `PDK_ROOT` | `/home/duongluong/.ciel/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71` |
| `LIBRELANE_APPIMAGE` | `/home/duongluong/librelane-devshell-x86_64.AppImage` |

PDK_ROOT là thư mục **chứa** sky130A, không phải đường dẫn kết thúc bằng `/sky130A`. Đây là đường dẫn trong Ubuntu, không dùng dạng `C:\...`/`D:\...`.

Trong cửa sổ Ubuntu thứ hai, có thể kiểm tra trước:

```bash
test -d /home/duongluong/.ciel/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A && echo PDK_OK
/home/duongluong/librelane-devshell-x86_64.AppImage librelane --version
```

Mong đợi `PDK_OK` và LibreLane 3.0.16. Nếu dùng máy/tài khoản Ubuntu khác, phải cập nhật hai biến theo đường dẫn thật.

Nguồn: [GitHub — repository variables](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-variables).

## 7. Chạy physical CI và giữ kết quả

Đảm bảo file `.github/workflows/physical.yml` bản cập nhật đã nằm trên main. File có hai biến nêu trên và lệnh chính:

```bash
"$LIBRELANE_APPIMAGE" python3 scripts/run_full_flow.py --pdk-root "$PDK_ROOT" \
  --tag "ci_${GITHUB_RUN_ID}_${GITHUB_RUN_ATTEMPT}" --jobs 4 --tops both \
  --out "evidence/ci_full_${GITHUB_RUN_ID}_${GITHUB_RUN_ATTEMPT}"
```

Vào **Actions → SPI RTL to GDSII → Run workflow → main → Run workflow**. Pipeline chạy kiểm thử, flow hai top, EQY và mô phỏng netlist. Giữ máy và runner online đến khi job kết thúc.

Trạng thái cuối phải là PASS và summary có đủ:

```text
rtl_regression      PASS
wrapper_regression  PASS
physical_core       PASS
equivalence_core    PASS
gate_sim_core       PASS
physical_wrapper    PASS
equivalence_wrapper PASS
gate_sim_wrapper   PASS
```

Tải artifact `spi-physical-<commit-sha>`, giữ cả log và summary, không chỉ lấy GDS. Đặt bản tải về ở thư mục có ngày/commit để đối chiếu. Nếu cần lưu trên GitHub dài hạn, có thể đính kèm ZIP bằng chứng vào một Release của repo với phiên bản nộp bài; giữ đúng quyền truy cập của repo. Artifacts CI hiện hết hạn sau 14 ngày theo workflow.

Ghi vào báo cáo: URL repo, SHA commit của **chính run dùng lấy số**, URL run, ngày chạy, LibreLane/PDK, clock/SDC, top và tham số. Nếu sửa code sau run, commit mới cần một run mới trước khi dùng kết quả mới cho báo cáo.

### Lỗi thường gặp

| Hiện tượng | Kiểm tra / xử lý |
|---|---|
| Job physical đứng Queued | Runner có online không, có nhãn `eda` cùng Linux/x64 không; `./run.sh` còn chạy không |
| Không có Run workflow | File phải dùng workflow_dispatch và tồn tại trên default branch |
| librelane/EQY không tìm thấy | Dùng workflow gọi AppImage đã cập nhật; kiểm tra biến LIBRELANE_APPIMAGE |
| PDK preflight thất bại | PDK_ROOT phải là thư mục cha chứa sky130A; kiểm tra đường dẫn Linux |
| Runner báo compiler error | Đọc compile.log; giữ trạng thái lỗi để sửa tool/TB, không lấy binary cũ |
| Có GDS nhưng job FAIL | Đọc summary và tên stage; pipeline còn kiểm STA, DRC/LVS, equivalence, gate sim |
| Push bị từ chối | Kiểm tra đúng tài khoản/repo/quyền và thông báo Git; nếu repo được tạo sẵn nội dung, cần hợp nhất lịch sử phù hợp |
| Người chấm không mở được link | Kiểm quyền repo, lời mời collaborator và artifact còn hạn |

## 8. Giải thích và xử lý các cảnh báo còn lại

Mục tiêu của bài là có kết quả đạt các cổng kiểm tra và giải thích được cảnh báo. Một log không có bất kỳ warning nào không phải điều kiện nghiệm thu trong Charter. Giữ log nguyên vẹn cùng chẩn đoán.

| Cảnh báo | Nghĩa trong run hiện tại | Việc cần làm để chốt bài |
|---|---|---|
| STA-1140, library already exists | Các file Liberty cùng PDK/corner được đọc lại trong một số bước | Ghi đúng PDK/tool; đối chiếu cùng file/corner, giữ log. Nếu các định nghĩa khác nhau, phải xử lý sự trộn thư viện trước khi kết luận timing |
| DRT-0349, LEF58_ENCLOSURE thiếu CUTCLASS | Router OpenROAD chưa xử lý được một cấu trúc rule LEF của PDK | Báo rõ giới hạn parser; dẫn DRC cuối Magic/KLayout=0. Hai DRC này vẫn chỉ chứng minh theo rule deck đã dùng, không thay sign-off foundry |
| VSRC_LOC_FILES chưa có | Phân tích IR drop thiếu vị trí nguồn cấp hệ thống cụ thể | Xem IR drop là tham khảo macro; chưa dùng làm kết luận nguồn hệ thống. Nếu cần phân tích IR drop thực, phải xác định pad/bump/điểm cấp nguồn và floorplan rồi cấu hình/rerun theo flow tương ứng |
| 6 input thiếu antenna gate info | Khớp sáu bit uio_in[7:2] không được dùng trong logic wrapper | Chỉ ra từ RTL rằng đây là các bit không tiêu thụ; kiểm OE không điều khiển START/MISO, functional TB và LVS đã đạt |
| 11 output thiếu antenna diffusion info | Khớp 8 bit uio_oe hằng và 3 bit uio_out[7,1,0] hằng 0 | Giải thích từ phép gán wrapper và netlist; không tự xóa cổng giao diện Tiny Tapeout. Nếu thiếu ở đầu ra chức năng, cần kiểm kết nối riêng |

Hai cảnh báo antenna thông tin cổng khác với số net/pin vi phạm antenna của run; metric kiểm antenna hiện bằng 0. Nguồn local: `flow/runs/closure_20261025_wrapper/warning.log`, RTL wrapper và final metrics. Khi tích hợp harness, kiểm lại cùng toàn thiết kế và rule của template.

Không thể chốt tọa độ cấp nguồn hoặc sign-off chế tạo chỉ từ macro hiện tại. Đây là hạng mục khác với sửa một vi phạm DRC đã được báo. Hồ sơ cần nêu đúng phạm vi đã chứng minh.

## 9. Nếu thực sự cần tích hợp harness/tile Tiny Tapeout

Đây là nhánh mở rộng. Giao diện wrapper đúng tên/chiều cổng mới là điều kiện đầu vào; macro được harden với floorplan relative chưa chứng minh đặt được vào tile và pin placement của một shuttle cụ thể.

Với PDK hiện tại, bắt đầu từ template SKY130 chính thức: [TinyTapeout/ttsky-verilog-template](https://github.com/TinyTapeout/ttsky-verilog-template). Nếu giảng viên giao template/tag khác thì dùng đúng bản được giao. Template IHP/GF dùng công nghệ khác, cần một flow và bộ bằng chứng mới.

Thực hiện trong nhánh hoặc repo tích hợp riêng để giữ được kết quả macro hiện tại:

1. Tạo project từ template và lưu đúng commit/tag của template/support tools.
2. Chép hai tệp `h03_spi_master.sv` và `tt_um_h03_spi_mode0.sv` vào `src/`.
3. Sửa `info.yaml`: đặt top_module là `tt_um_h03_spi_mode0`, khai báo cả hai source_files; giữ cấu trúc YAML/schema và thông số tile đúng template. `source_files` thường tính từ src; đối chiếu file mẫu của bản đang dùng.
4. Chốt H=4/MSB cho bản harden, clock phân tích, map RX/BUSY/DONE/OE; cập nhật `docs/info.md` theo map thật. Giữ các cổng wrapper chuẩn.
5. Dùng testbench của template với slave mode 0 và kiểm pad; mang các ca quan trọng của regression sang hoặc chạy bổ sung regression đang có.
6. Chạy workflow chính thức của template để nhận floorplan/tile/pin placement/power/clock constraints của harness. Kích thước tile là ràng buộc vật lý, không suy từ số cell hay diện tích standard cell.
7. Kiểm kết quả tile/harness: lint/synthesis, timing, bố trí chân, DRC/LVS/antenna, route và gate-level theo template. Nếu không vừa tile, sửa kiến trúc/placement hoặc chọn kích thước được cho phép rồi chạy lại.
8. Báo cáo bộ số mới với top/config/run của template, giữ phân biệt với hai run macro cũ. Việc chọn shuttle, trả phí và submit chế tạo chỉ thực hiện khi có mục tiêu/ủy quyền riêng.

Nguồn: [template HDL theo từng công nghệ](https://tinytapeout.com/hdl/templates/), [hướng dẫn hardening](https://tinytapeout.com/guides/local-hardening/). Những lệnh/template online có thể đổi, vì vậy pin commit/version đang dùng trong phụ lục tái lập.

## 10. Chốt PDF và chuẩn bị bảo vệ

Hiện báo cáo chính là Markdown, chưa phải PDF 8–15 trang theo rubric. Dùng BAO_CAO_CAI_TIEN.md và RESULTS.md làm nguồn, đưa vào Word/LaTeX, bổ sung danh tính sinh viên và thông tin repo/commit/CI thật rồi xuất PDF.

Một bố cục 10–12 trang phù hợp: bài toán/ứng dụng; yêu cầu và giao diện; kiến trúc/FSM; timing; kế hoạch kiểm chứng; waveform và ca biên; flow/cấu hình; synthesis/STA/power; layout/DRC/LVS; chẩn đoán/lựa chọn thiết kế; kết luận và thông tin tái lập. Đặt mã dài/log đầy đủ ở phụ lục hoặc repo/artifact, giữ phần chính tập trung vào bằng chứng và diễn giải.

Phần phân tích riêng cần chỉ rõ: SCLK idle thấp; MOSI bit đầu có trước cạnh lên; MOSI đổi ở cạnh xuống; MISO lấy mẫu ở cạnh lên; CS bao đủ tám xung. Với hình H=2/clk 10 ns, khoảng ổn định RTL danh định là 20 ns; với H=4 là 40 ns. Setup thực ở slave cần trừ trễ pad/dây/slave/skew, nên không gọi các khoảng này là margin điện đã đo.

Chuẩn bị trình bày 5 phút: khoảng 1 phút bài toán/giao diện, 1 phút FSM/timing, 1 phút waveform/ca biên, 1 phút số liệu vật lý và sửa slew reset, 1 phút giới hạn/tái lập. Phải giải thích vì sao final cell khác synthesis cell và vì sao clock 10 ns là giả định phân tích.

## 11. Cổng chốt bàn giao

- Repo có RTL, spec, testbench/scripts, workflow ở đúng vị trí và lịch sử commit thật.
- Simulation CI có link run và artifact tải được.
- Physical CI hoặc flow local có log/artifact đầy đủ; mục tiêu ở hướng dẫn này là bổ sung physical CI thật trên runner WSL.
- Báo cáo dùng đúng SHA/run của dữ liệu, có bảng công cụ/PDK/SDC và chẩn đoán warning.
- PDF 8–15 trang, waveform có chú thích, trả lời câu phân tích riêng, quyền xem của giảng viên được kiểm.
- Bản ZIP bằng chứng đã lưu độc lập trước khi artifacts CI hết hạn.

Sau khi tạo repo và push, gửi URL repo để kiểm tra Code/Actions và tiếp tục đối chiếu các bước theo trạng thái thực. Chưa có repo/run thật thì trạng thái GitHub của báo cáo vẫn là chưa chạy.
