# Thực hiện góp ý về bản đồ, trực quan và nền tảng lý thuyết

Đã đọc và sửa trực tiếp bản `Paper3_DeTaiThayHien/P3_PAPI_DTI_Merger.tex` đang mở. Lưu bản trước lượt sửa này tại `archive/pre_visual_revision_2026-10-09/`. Không tạo tài liệu thay thế hay mở tab khác.

## Các sửa đã thực hiện

| Góp ý | Thực hiện trong bản chính |
|---|---|
| Thiếu study-area / reform map | Figure 1: hai panel 63 tỉnh trước cải cách và 34 nhóm tỉnh theo crosswalk; phân biệt merged / unchanged, thêm nhãn địa danh định hướng. |
| Thiếu spatial distributions | Figure 3: ba choropleths năm 2024: DTI government, full e-governance, portal access + response; thang riêng và thiếu dữ liệu được ghi rõ. |
| Thiếu methodological workflow | Figure 2: nguồn và kiểm tra dữ liệu → bóc tách measurement → territorial sensitivity → association / prediction. Nêu đúng burn-in, thinning, retained draws và grouped CV. |
| Rank tables khó đọc | Figure 4: bốn scatter panels (2020/2024 × full/service), cùng 61 tỉnh; đường fit mô tả, Spearman và trục cố định theo outcome. Bảng endpoint uncertainty chuyển sang appendix. |
| Regression tables dày | Figure 6: coefficient plots với 95% cluster CI, bốn outcomes và bốn specification sensitivities; không gọi đây là equality test. Numeric estimates, wild p và lag/service details vẫn ở appendix. |
| Bar chart quá ít thông tin | Figure 5: actual share so với mean của unrestricted grouping và mean/5–95% reference range của connected chains, bốn measures. Không gọi simulation ranges là CI. |
| Quá nhiều bảng ở main text | Bản chính còn 2 bảng (coverage, prediction); 5 bảng chuyển sang appendix, cùng bảng sensitivity vốn có. |
| Nền tảng lý thuyết mỏng | Tăng từ 27 lên 51 references; thêm subsection TAM/UTAUT, IS success và benchmark validity; mở rộng MAUP/uncertain geographic context, quốc tế hoá amalgamation bằng Đan Mạch, Phần Lan, Nhật Bản và comparative Europe. |
| Tài liệu mới | Có Haug et al. 2024, OECD/UN 2024, Lee et al. 2025, Skargren et al. 2026 và Klausen 2026 (online 2024); không gán các kết quả quốc tế thành hiệu ứng ở Việt Nam. |

Hình và các dẫn chiếu trong bài được nối với câu hỏi nghiên cứu; không chỉ bổ sung hình minh hoạ cuối bài. Các hình scientific được xuất PNG/SVG trong `figures_upgrade/`; đường polygon, điểm, hệ số và CI được nhúng trực tiếp bằng TikZ trong .tex để giữ nguồn độc lập cho editor. Không dùng image generation để dựng bản đồ hoặc dữ liệu.

## Những điểm cần điều chỉnh trong nhận xét reviewer

- Số references không phải ngưỡng đảm bảo Q1. 24 nguồn bổ sung có vai trò cụ thể trong lý thuyết, nguồn bản đồ hoặc phương pháp; không dùng danh mục dài thay cho contribution.
- MAUP đã có Lee et al. (2025) từ lượt sửa trước. Lượt này mở rộng thêm vấn đề uncertainty/exposure và phân biệt scale với zoning.
- 50.000 proposals là burn-in **mỗi chuỗi**, không phải toàn bộ connected simulation. Mỗi chuỗi còn 500.000 proposals để giữ 1.000 partitions theo thinning 500; tổng bốn chuỗi có 4.000 retained partitions.
- Gom tỉnh làm mất độ phân giải báo cáo trung bình tỉnh; dữ liệu hiện có chưa chứng minh bất bình đẳng giữa người dân. Không suy ra sáp nhập làm thành tích thực tế tốt hơn.
- Bản đồ đang dùng hình học geoBoundaries lịch sử 2008 trong bộ dữ liệu. Bản đồ 34 nhóm được dựng bằng crosswalk và bỏ internal edges; đây chưa phải bản đồ địa giới chính thức năm 2025. Caption và limitations công khai vintage, cách chuẩn hoá Hue/Con Dao và các địa vật không có trong nguồn. Cần thay bằng nguồn địa giới hiện hành đã xác minh nếu journal yêu cầu cartography chính thức.
- Choropleths có thang điểm khác nhau; không lấy màu hoặc hiệu hai điểm chưa chuẩn hoá làm readiness–experience gap. Global Moran không đủ để gắn nhãn local significant clusters.

## Kiểm tra và tái lập

`build_visual_upgrade.py`: dựng sáu họ hình từ output CSV và geometry gốc, lưu `visual_inline_tikz.json` và `VISUAL_VALIDATION.json`.

`enhance_manuscript_visual.py`: đọc/sửa bản chính tại chỗ; idempotent, cập nhật lại hình khi chạy tiếp. `build_manuscript_upgrade.py` đã gọi bước dựng hình và enhancement để các sửa không bị mất khi chạy pipeline sau này.

`check_visual_upgrade.py` đã đạt: 63 spatial keys, 34 mapped groups, 52 merged constituents, đầy đủ missing-score coverage; Spearman/fit của 4 scatter panels; hệ số và CI của 8 points; 4 actual variance shares; 6 main figures, 2 main tables, 51 references; labels/refs và grouping braces hợp lệ. Bộ kiểm tra khoa học cũ cũng đạt. PNG được đọc lại bằng mắt; kiểm tra này không thay thế PDF layout QA.

Compiler tích hợp sau sửa trả về trạng thái không xác định. Lỗi môi trường ở lượt trước là `Unable to find standard directories for platform`. **Chưa có PDF mới được xác nhận**; không chạy compiler khác hoặc cài TeX. Giữ editor hiện tại mở.

Các bản anonymous/title-page từ lượt trước chưa được viết lại trong lượt sửa tại editor này. Bước build đầy đủ về sau sẽ đồng bộ chúng; cần kiểm tra lại bản anonymous trước khi dùng để submission. Chưa publish ra ngoài.

Metadata/link của 24 nguồn bổ sung lưu trong `literature_visual_revision.json`. Một số nguồn được đọc qua publisher abstract hoặc author manuscript; không khẳng định đã đọc toàn văn tất cả tài liệu. Trước nộp cần hoàn thiện reference style theo journal và kiểm tra PDF, declarations, public replication như revision log trước.
