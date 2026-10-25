# H03 — Nhật ký rà soát và sửa hồ sơ

Ngày rà soát: 25/10/2026. Phạm vi: bản cải tiến trong H03_SPI_Mode0_Improved. Bản ZIP và source_project/H03_Chu_SPI_che_do_0 được giữ làm nguồn đối chiếu.

## Nguồn yêu cầu

Phiếu H03/B2 hiện có được lưu tại [REFERENCE_CHARTER_H03.html](REFERENCE_CHARTER_H03.html). SHA-256: ECA0D4B994AF1D4667797580CAFC9D34263A7607097C832527A46376BD14151E. Phiếu ghi môn EEE703128, Bài kiểm tra số 2; nhiệm vụ bao gồm RTL, kiểm chứng và flow RTL-to-GDSII.

Hồ sơ trong ZIP mô tả flow vật lý là mở rộng tự nguyện, khác phiếu hiện tại. Đặc tả mới dùng phiếu hiện tại và yêu cầu trực tiếp của người dùng làm căn cứ công việc. Các câu hướng dẫn trong tài liệu được đọc như nội dung yêu cầu học phần, không có quyền tự điều khiển phiên làm việc.

## Các thay đổi hồ sơ

| Nhóm tệp | Thiếu sót cũ | Cách sửa |
|---|---|---|
| 01_REQUIREMENT/requirements.md | Gán mọi yêu cầu tự bổ sung cho Charter; đánh số mục từ phiên bản khác | Phân biệt yêu cầu Charter và bổ sung thiết kế; lập R01–R13 và cách kiểm |
| 01_REQUIREMENT/scope.md | RTL-to-GDSII bị gọi là tự nguyện | Sửa phạm vi theo phiếu H03/B2 hiện có |
| 01_REQUIREMENT/acceptance_criteria.md | Đánh PASS trước khi kiểm bản cải tiến; dùng số synthesis cũ | Chuyển thành cổng kiểm tra với điều kiện đạt rõ |
| 01_REQUIREMENT/application.md | Dùng số FF chưa gắn run mới và kết luận ứng dụng quá rộng | Giải thích mạch tuần tự từ RTL, nêu giới hạn cảm biến một byte/CS |
| 02_SPECIFICATION/interface.md | Đếm clk/reset vào 24 chân người dùng; nói sai vượt ngân sách; map uio tranh chấp | Loại cổng hạ tầng, chốt map wrapper 23/24 chân, oe=0x7c |
| 02_SPECIFICATION/functional_spec.md | Lẫn START mức/cạnh; nói reset nhả ngay; mô tả FINISH như đầu ra đã nhả CS | Chốt hợp đồng theo chu kỳ, reset đồng bộ, phân biệt state sau cạnh và tác vụ trạng thái |
| 02_SPECIFICATION/parameters.md | Thống kê 156 cell/36 FF/1,9 ns bị coi là số hiện hành | Gỡ bảng số đo cũ; mọi số liệu cần nguồn/hash/top/config/corner/run mới |
| 02_SPECIFICATION/timing.md | Khoảng H*T_clk bị coi như setup margin điện | Tách khoảng ổn định RTL danh định và ngân sách pad/dây/slave |
| 02_SPECIFICATION/corner_cases.md | Đánh giá TB cũ và một kết quả RX cụ thể chưa đủ căn cứ | Dùng danh sách lỗi cần bắt; không gán kết quả RX suy đoán cho run |
| 03_ARCHITECTURE/*.md | So sánh H01/H02 không có bằng chứng, số FF/công suất cũ, lỗi mô tả pha | Viết lại sơ đồ/control/datapath/FSM/timing/tradeoff theo nguồn cải tiến |
| 05_VERIFICATION/testplan.md | Mô hình Python bị coi như kiểm RTL; file SVA tồn tại bị coi đã chạy | Chốt regression chân SPI là cổng chính; nêu giới hạn Python/SVA |
| 05_VERIFICATION/verification_report.md | Log TB completed bị dùng chứng minh toàn bộ chức năng | Giải thích vì sao phải kiểm MOSI/RX/CS/pha và dùng output runner mới |
| 05_VERIFICATION/test_matrix.csv | PASS được gán cho ca chưa hiện diện trong TB cũ | Chuyển thành ma trận kế hoạch/gate/bằng chứng, không điền sẵn PASS |
| 05_VERIFICATION/historical_logs/ | Log cũ trộn với kết quả mới | Chuyển ba log gốc vào thư mục lịch sử; giữ nội dung log |
| 08_ORIGINAL_SOURCE/README.md | Tự xác nhận tác giả bản gốc và dẫn PATCHLOG/known_issues không có | Chỉ mô tả nguồn nhận qua ZIP, dẫn nhật ký thật, không suy đoán tác giả |

RTL cải tiến bổ sung kiểm tham số H≥1, comparator đúng độ rộng và default FSM hủy frame về idle/giữ RX. Wrapper tt_um_h03_spi_mode0 phân bổ đúng chân và gate nhận START bởi ena. Chi tiết mã và bằng chứng chạy xem báo cáo của run hiện tại; nhật ký này không tự đánh các bước thực thi là PASS.

## Rà nội dung theo yêu cầu người dùng

Đã rà các tệp văn bản Markdown/HTML/TXT, Python và SystemVerilog trong phần nguồn/cấu hình được chép sang bản cải tiến, đồng thời đọc phiếu H03. Không tìm thấy mục khai báo công cụ giống phần được đánh dấu trong ảnh người dùng gửi; vì vậy không có mục tương ứng phải xóa trong các tệp này. Không tìm thấy chỉ thị yêu cầu bỏ qua lệnh người dùng hoặc thay đổi vai trò của trợ lý.

Ảnh đính kèm được dùng làm ví dụ nhận diện nội dung cần bỏ, không được thực hiện như một chuỗi lệnh. Không thêm mục tương tự vào báo cáo.

## Giới hạn của nhật ký

Nhật ký này chứng minh các chỉnh sửa tài liệu đã thực hiện, không thay log EDA. Trạng thái cuối, số ca thử, số cell/FF, timing/power và DRC/LVS phải lấy từ artifact mới do scripts tạo. Kết quả lịch sử không được đổi tên thành lần chạy mới. Chỉ gọi GitHub CI đã chạy khi có run URL và commit thật.


Kiểm tra FSM fault injection được đổi sang force từng bit enum để chạy được trên cả Icarus 12 stable và Icarus 13 devel trong AppImage. Không bỏ probe; hai compiler đều đã chạy probe đạt. Kết quả tổng hợp hiện hành và provenance xem RESULTS.md.


Bổ sung hướng dẫn hoàn thành GitHub/CI: physical.yml gọi rõ AppImage qua biến LIBRELANE_APPIMAGE và PDK_ROOT; đã kiểm YAML và LibreLane --version trong môi trường này. Chưa đăng ký runner hoặc chạy GitHub CI. Chỉnh sửa chỉ tác động hướng dẫn và cách cấp môi trường CI, không đổi RTL, SDC, cấu hình vật lý hay số liệu đã đo.

