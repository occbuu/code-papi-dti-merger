# Paper 3 — bản sửa thực hiện ngày 09/10/2026

Đã thực hiện sửa dữ liệu, phương pháp, mã phân tích và bản thảo trên nguồn hiện có. Bài được định vị lại thành nghiên cứu về đo lường quản trị số và mất thông tin khi tổng hợp theo địa giới. Không dùng bộ số liệu trước cải cách để khẳng định tác động nhân quả của cải cách năm 2025.

## Đối chiếu các vấn đề reviewer

| Vấn đề | Sửa đã thực hiện | Bằng chứng / giới hạn |
|---|---|---|
| Đồng nhất e-governance với trải nghiệm dịch vụ | Tách Internet, tổng portal access + responsiveness, và trung bình chẩn đoán 5 tỷ lệ dịch vụ có nhãn lặp lại | Trích 13 nhãn từ workbook từng năm, lưu vị trí nguồn. Nhãn giống không chứng minh measurement invariance; 5 tỷ lệ không phải chỉ số chính thức mới. |
| Dữ liệu bị thiếu hoặc điểm 0 bị hiểu sai | Giữ 0 hợp lệ của tỷ lệ; loại các dòng bị ẩn toàn bộ dimension khỏi phân tích tỷ lệ; kiểm tra khóa và cardinality | 315 dòng tiềm năng, 307 full-PAPI quan sát; không nội suy điểm bị thiếu. |
| Khó tái lập từ nguồn gốc | Thêm bộ kiểm tra độc lập workbook PAPI, bảng DTI lưu trữ và JSON NSO | 2.835 bản ghi PAPI dimension/total, 2.762 giá trị quan sát khớp; 315 DTI và 315 controls khớp trong sai số làm tròn. Năm DTI theo inventory, không suy từ điểm bằng nhau. |
| Tuyên bố đứt kết nối readiness–experience quá mạnh | Bootstrap cặp tỉnh cho thay đổi Spearman 2020–2024; tách outcome theo thành phần | Khoảng tin cậy của thay đổi không loại 0; bỏ tuyên bố suy giảm đã được chứng minh. |
| Sai hoặc thiếu rõ ràng về fixed effects và R² | Hấp thụ đúng province/year effects; cluster tỉnh; restricted wild cluster bootstrap-t; partial R² đúng trên cùng mẫu | Hệ số full-PAPI 0,234844 khớp OLS dummy độc lập. Điều kiện hóa không chứng minh nhân quả. |
| Lag/current dùng mẫu khác nhau | So sánh current và lag trên cùng 244 quan sát; sai phân chỉ các cặp năm liền kề | Có đủ ba biến kiểm soát sai phân và year effects. |
| DTI đổi framework | Bổ sung thảo luận hai quyết định 2020/2022 và kiểm tra riêng 2022–2024 | Hệ số full/service trong giai đoạn sau có CI chứa 0. Chưa có item bridge để xây common-core DTI hợp lệ. |
| Nhiều phép thử / machine learning thiếu chặt | Holm trên nhóm 14 outcome thăm dò; loại DML, causal forest, SHAP và permutation độc lập từng năm khỏi chứng cứ chính | Không dùng kết quả ML cũ để bảo vệ diễn giải nhân quả. |
| Theil phụ thuộc điểm gốc và mẫu | Dùng phân rã phương sai có trọng số dân số làm chính; Theil và dịch chuyển thang làm sensitivity; cùng 61 tỉnh năm 2024 | Phương sai bất biến theo dịch chuyển và đổi đơn vị; Theil không có đặc tính này với điểm chỉ số. |
| Random merger không khả thi địa lý | Thêm graph queen và 4 chuỗi swap giữ kích thước/địa lý liên thông | 4.000 partitions đều được kiểm tra; đồ thị hình học lịch sử 2008 đơn giản hóa, chưa có chứng minh irreducibility/uniform sampling. Chỉ là sensitivity reference. |
| Nhầm mất thông tin với bất bình đẳng cá nhân | Bảng range thành viên, đồ thị profiles và kịch bản 2 tỉnh thiếu | Nghiên cứu khoảng cách giữa trung bình tỉnh, không phân phối cá nhân hay chi phí tích hợp thực tế. |
| Prediction chưa có baseline và leakage | Ridge nested CV theo tỉnh: 5 repetitions × 5 outer folds, 4 inner folds; controls, DTI, combined đều có year effects | Scale/center chỉ trên training folds. Paired MSE uncertainty chưa cho thấy lợi ích tăng thêm rõ ràng; không gọi đây là dự báo tương lai. |
| Contribution và literature chưa đủ | Viết lại title, abstract, introduction, conceptual framework, results, discussion, conclusion; bổ sung literature đo lường/MAUP và 2024–2026 | Tập trung đóng góp có dữ liệu kiểm chứng; cần editor/reviewer đánh giá novelty và journal fit. |
| Packaging và disclosure | Script canonical, notebook dùng chung pipeline, bảng sinh từ CSV, hashes/versions, anonymous manuscript và title page, khai báo AI | Bản gốc lưu archive; cần tác giả xác nhận declarations và công bố repository hợp lệ. |

## Kết quả làm thay đổi câu chuyện của bài

Trên cùng 61 tỉnh năm 2024, phần phương sai nằm trong nhóm tỉnh sau sáp nhập là **14,1% đối với full e-governance**, **44,7% đối với tổng portal access + responsiveness**, và **45,5% đối với DTI government**. Internet chiếm khoảng 65,6% phương sai full-PAPI khi phân rã thành phần (phần còn lại gồm service và covariance). Vì vậy sự đồng nhất của composite không thể đại diện trực tiếp cho sự đồng nhất của tương tác dịch vụ.

Hệ số panel đầy đủ có liên hệ dương, nhưng độ bền theo giai đoạn, lag, outcome tỷ lệ và hiệu chỉnh nhiều phép thử hạn chế diễn giải. Benchmark có ràng buộc địa lý làm yếu đi câu chuyện về tính đặc biệt của thiết kế gom tỉnh. Thêm DTI vào baseline kinh tế xã hội chưa cải thiện prediction một cách rõ ràng.

Các kết luận này đã được sửa trong bài; không giữ kết luận cũ rồi chỉ thêm caveat.

## Tệp và cách dùng

- `Paper3_DeTaiThayHien/P3_PAPI_DTI_Merger.tex`: bản chính mới.
- `Paper3_DeTaiThayHien/P3_PAPI_DTI_Merger_anonymous.tex`: bản bỏ định danh tác giả.
- `Paper3_DeTaiThayHien/P3_title_page.tex`: thông tin tác giả và declarations.
- `P3_analysis_final.py` và `.ipynb`: entry point thống nhất; không tự cài packages.
- `results_upgrade/VALIDATION_REPORT.json`: báo cáo kiểm tra.
- `README.md` và `Paper3_DeTaiThayHien/REPLICATION.md`: hướng dẫn chạy và giới hạn.
- `archive/pre_revision_2026-10-09/`: bản lưu trước sửa; PDF cũ cũng được đổi tên PRE_REVISION ở thư mục manuscript.

Các tệp LaTeX là sản phẩm của `build_manuscript_upgrade.py`. Sửa generator nếu muốn giữ thay đổi sau khi chạy lại. `results/`, `figures/`, Word draft và script demo cũ chỉ là lịch sử.

## Việc còn lại trước khi nộp

1. **Biên dịch và kiểm tra PDF:** compiler tích hợp báo `Unable to find standard directories for platform`. Kiểm tra cấu trúc LaTeX đã đạt, nhưng chưa xác nhận layout hoặc PDF mới. Không cài thêm TeX trong phiên này.
2. **Tác giả xác nhận:** tên/ORCID, funding, vai trò CRediT, xung đột lợi ích, funder independence và khai báo AI. Các declarations kế thừa cần được xác nhận thực tế.
3. **Public replication:** kiểm tra quyền phân phối nguồn, tạo repository public và DOI; chưa có DOI và chưa publish ra ngoài.
4. **Journal-specific submission:** chọn tạp chí, kiểm tra yêu cầu độ dài/style/template và chính sách dữ liệu/AI tại thời điểm nộp. Bản hiện tại là article độc lập, chưa chuyển sang template của một journal cụ thể.
5. **Nếu muốn nâng lên bài causal/Q1 tham vọng hơn:** thu thập item-level DTI bridge, PAPI microdata có denominators/survey uncertainty hoặc log hoàn thành dịch vụ; bổ sung dữ liệu hậu cải cách và thiết kế nhận dạng có xử lý selection/spillovers. Không thể tạo những chứng cứ này từ dữ liệu hiện có.

Đánh giá sau sửa: bản hiện tại có phương pháp và câu chuyện nhất quán hơn để tác giả tiếp tục chuẩn bị submission. Không thể bảo đảm Q1/Q2 hoặc gọi bài đã sẵn sàng nộp khi PDF, declarations và public replication còn chưa hoàn tất.
