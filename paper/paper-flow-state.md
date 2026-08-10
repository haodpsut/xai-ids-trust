# paper-flow-state.md — ledger cổng, bản NDSS 2027

Paper: **When Is an Explanation Trustworthy? Foundations of Interpretability-Based Trust in ML-IDS**
Venue: **NDSS 2027**, chu kỳ **mùa thu**. Double-blind, đã ẩn danh (`Anonymous Submission`).

## ⚠ NGÀY THẬT — TRA LẠI 10/08/2026 TRÊN TRANG CfP ĐÃ MỞ

Trang CfP NDSS 2027 nay đã có đủ mốc chu kỳ mùa thu, chép nguyên văn **kèm nhãn** (§8e):

| nhãn nguyên văn | ngày |
|---|---|
| *"Paper submission deadline"* | **Wed, 19 August 2026** |
| *"Early reject/Round 2 notification and Round 1 reviews"* | Fri, 25 September 2026 |
| *"Author notification"* | Wed, 4 November 2026 |
| *"Camera Ready deadline"* | Wed, 6 January 2027 |

**Hạn nộp là 19/08/2026, không phải 15/08.** 15/08 chỉ là ngày CfP mở. Cả hai bên đã tin nhầm
15/08 là hạn — hoá ra còn **thêm 4 ngày**, chứ không phải ít đi.

## ★ §8b — DANH SÁCH OUT-OF-SCOPE, CHÉP NGUYÊN VĂN (tra 10/08/2026)

NDSS liệt kê thẳng những dạng bài **bị loại không qua phản biện**:

> *"Papers with focus on theoretical cryptography but without implementation or evaluation on real systems"*
> *"Papers with focus on mathematical proof without implementation/evaluation"*
> *"Papers with contributions primarily in another field: AI, ML, etc."*
> *"Papers without any security or privacy contribution; e.g. optimizing network performance"*
> *"Major overlap between a rejected paper from the summer cycle and a submission to the fall cycle"*

**Đối chiếu bài này — hai mục có rủi ro thật:**

- ⚠ *"contributions primarily in another field: AI, ML"* — **đây là rủi ro lớn nhất của bài.**
  Ba tính chất (fidelity/determinacy/groundedness) đọc thoáng qua là một quan sát về XAI. Cái kéo
  bài về phía an ninh là mục **harm**: trên luồng **đã phát hiện đúng và ổn định**, giải thích của
  hai mô hình tốt ngang nhau đẩy nhà phân tích tới **hành động ngược nhau** (tới 0,87 trên
  CICIDS2017). Vế đó **phải đứng sớm và rõ** trong abstract + intro, nếu không desk-reject theo
  đúng dòng này. Đã kiểm: abstract có nêu, nhưng ở câu thứ 6.
- ✅ *"without any security or privacy contribution"* — không vướng, nhờ đúng mục harm ở trên.
- ✅ *"major overlap with a rejected summer-cycle paper"* — bài **chưa từng nộp** chu kỳ mùa hè.
- ✅ hai mục crypto/mathematical-proof — không liên quan.

## Ràng buộc venue (§8b/§8c/§8d), tra 10/08/2026

| | |
|---|---|
| Giới hạn | **13 trang**, KHÔNG kể Ethics Considerations, tài liệu tham khảo, phụ lục |
| Bài hiện tại | **15 trang tổng**: thân bài hết ở tr.13 (Appendix A bắt đầu ngay tr.13), phụ lục tr.13–14, refs tr.15 ⇒ **ĐẠT** |
| Định dạng | US Letter, 2 cột, Times ≥10pt, template NDSS |
| Chi phí | NDSS **không thu phí xuất bản**; kỷ yếu mở truy cập ⇒ không vướng ràng buộc gold OA |
| Ẩn danh | ✅ không tên/affiliation/link repo trong bài; repo `haodpsut/xai-ids-trust` KHÔNG được nhắc |

## Nhóm giết-trước

- **occupied-check** — Related Work đối chiếu ~12 công trình gần nhất; thêm **field audit 12–15 bài
  XAI-IDS chấm theo 6 tiêu chí** (Bảng audit). Khoảng trống: chưa ai đo **đồng thời** cả ba tính chất.
- **hard gate per claim** — ba tính chất đo độc lập, mỗi tính chất có ngưỡng và CI đa-seed riêng;
  thêm **trần khả thi** (`ceiling.csv`) chứng minh thước ĐO ĐƯỢC (đạt ≈1,0 trên dữ liệu tổng hợp
  thưa) chứ không phải rigged-to-fail.
- **Luật 8a — biên vs ngân sách sai số:** biên mệnh đề là khoảng cách tới 1,0 của ba tính chất;
  ngân sách là **độ lệch chuẩn đa-seed** trong `multiseed.csv`. P2 ≈0,45±0,017 và P3 ≈0,53±0,005 —
  biên tới 1,0 lớn hơn std **hai bậc**, nên kết luận "cả ba hỏng" không bị sai số nuốt.
- **DC-5 (bản phi vật lý)** — mục *Threats to Validity* liệt kê giả định bỏ ngoài (phạm vi
  attribution, chọn mô hình, quy mô khảo sát) kèm hướng ảnh hưởng. Kết quả tấn công **khai thật là
  inconclusive**, gate khai thật là **kết quả âm**.
- **claim scope** — `claim-scope.json`, 2 mệnh đề độc quyền đều có `hedged_by` đã verify.
- **⚠ đọc-ngoài trên CLAIM SHEET — tờ đã viết (`CLAIM-SHEET.md`), NGƯỜI ĐỌC THÌ CHƯA CÓ.**
  Đây là mục DANGEROUS duy nhất còn lại, và nó chặn đúng. Khi có người đọc, ghi **một dòng**
  vào file này: `CLAIM-SHEET-READ: <ngày> <người> -- <họ nói gì>`. Cổng chỉ nhận đúng dạng đó.

## Cổng đã chạy 10/08/2026 (vòng hai)

| cổng | kết quả |
|---|---|
| `verify_refs` Layer-1 | ✅ **62 mục / 62 được trích**, 0 giữ chỗ |
| **Layer-2 (chạy thật, không phải file .md)** | ✅ **42 mục khớp Crossref trên cả sáu trường, 414 phép so trường**; 5 ca nhà XB nộp tiêu đề cắt/nối được dung thứ và **in ra**; 20 mục không có DOI Crossref khai trong `refs-manual.txt`, mỗi mục kèm nguồn tra cứu được (DBLP rec / arXiv id) |
| `check_claim_scope` | ✅ PASS |
| `verify_numbers` | ✅ **54/54** claim khớp CSV ở đúng độ chính xác in ra |
| `trace_prose_numbers` | ✅ 0 số không truy được · **0 bảng không claim nào chạm tới** (trước là 4) · miễn trừ cắt từ 9 xuống **3** |
| `ssot_prose_numbers` | ✅ **0 số gõ tay** ngoài `\input{}` (trước là 2) |
| `self_consistency` | ✅ PASS |
| `check_freshness` | ✅ 4 CSV cũ hơn `data.py` — đã kiểm diff: thuần **CỘNG THÊM**, không đụng đường nạp cũ |
| biên dịch | ✅ 0 lỗi · 15 trang (thân bài hết tr.12) · 0 overfull |
| `g0_kill_first` | ❌ 1 mục: **đọc-ngoài claim sheet** — đúng, chưa ai đọc |

## ★ Bốn lỗi thật bắt được trong vòng HAI (10/08, sau khi nạp DOI)

1. **`arreche2024exai` thiếu một tác giả** — bib ghi 3, bản ghi nhà XB có 4: thiếu **Jack W.
   Roberts** ở vị trí thứ ba. Đúng lớp lỗi L2 đã cảnh báo: sai nằm ở tác giả **giữa**.
2. **`cicids2017` sai họ** — họ là **Habibi Lashkari**, bib tách thành `Lashkari, Arash Habibi`.
3. **Hai ref còn nằm ở dạng preprint dù đã xuất bản** — `xgnid2024` → *Expert Systems with
   Applications* 287:128089 (2025); `feat5g2025` → *J. Inf. Secur. Appl.* 99:104448 (2026).
   Cùng lớp với `krishna2022` → TMLR 2024.
4. **`action2026` mất tiền tố tiêu đề** — tên thật bắt đầu bằng **“TRACE:”**. Lỗi ở ĐẦU tiêu đề,
   chỗ mắt người đọc lướt qua nhanh nhất.

## ★ Bảng field-audit: từ “không kiểm chứng được” sang “kiểm chứng được”

Năm trong mười hai dòng của `tab:audit` trước đây **không có trích dẫn** (“Robust NID via XAI
('22)”). Trong một bài mà luận điểm chính là *ngành này không tự kiểm chứng*, một bảng khảo sát
không ai tra được là chỗ hở nặng nhất — và câu văn còn hứa *“the full list with DOIs … is released
as field\_audit.csv”* trong khi CSV **không có cột DOI**. Đã: định danh cả năm về bản ghi đã xuất
bản, thêm **cột `doi`** cho cả 12 dòng, trích dẫn đủ 12/12 trong bảng. **Điểm C1–C6 không đổi một ô
nào** (đã đối chiếu máy trước/sau), nên mọi con số coverage giữ nguyên.

| khoá | bài | DOI |
|---|---|---|
| `robustxai2022` | Barnard và cs., IEEE Netw. Lett. 4(3) | `10.1109/LNET.2022.3186589` |
| `ngshap2025` | Dong và cs., Computer Networks 275 | `10.1016/j.comnet.2025.111937` |
| `selfattn2025` | Sharma và cs., Sci. Rep. 15 | `10.1038/s41598-025-23750-0` |
| `fronteval2025` | Mohale & Obagbuwa, Front. Comput. Sci. 7 | `10.3389/fcomp.2025.1520741` |
| `insider2026` | Faqihi và cs., FGCS 183 | `10.1016/j.future.2026.108543` |

## ★ Bảng dữ liệu (tab:data) nay tính lại được

Cột **Features** và **Attack rate** trước đây chỉ tồn tại trong mã LaTeX. Thêm
`code/exp_dataset_profile.py` → `dataset_profile.csv`: nạp đúng đường mà thí nghiệm nạp (bỏ cột
định danh, seed 0, n=40000) rồi tính. **Cả 10 số khớp bài y nguyên** (34/52/48/38/39 và
0,68/0,17/0,61/0,76/0,97) — bảng vốn đúng, nay là **tính lại được** chứ không phải gõ tay.

Một điều chỉnh thật: hàng *detection agreement* của `tab:harm` in ở 2 chữ số làm TON-IoT thành
`1.00` trong khi CSV là `0.995` — đúng ranh giới làm tròn. Đã in cả hàng ở **3 chữ số**
(0.961 · 0.880 · 0.998 · 0.995 · 0.986) để không giấu quyết định làm tròn nào.

## ★ Ba lỗi thật bắt được trong vòng này

1. **`salo2022soc` KHÔNG TỒN TẠI** — *"Towards Explainable AI in the SOC", IEEE Big Data 2022*.
   Hai lượt tìm độc lập không ra. Đã thay bằng **Nyre-Yu và cs., USEC 2022**,
   DOI `10.14722/usec.2022.23014` (xác minh qua Crossref), và **viết lại câu trích** vì Nyre-Yu là
   nghiên cứu triển khai thực địa chứ không phải survey.
2. **`claims.json` mâu thuẫn với chính bài** — 34/88 claim lệch; ở mọi chỗ lệch thật thì **bài khớp
   CSV còn nó không**. Đã loại (`claims.json.STALE-2026-08-10`), ghi `CLAIMS-SSOT.md`.
   **Bài tự mô tả sai cơ chế của mình** ở 3 chỗ ("read through a single claims.json source of
   truth") — đã sửa.
3. **`faith_comp_ciciot` in 0.00 giấu dấu âm** — CSV là **−0,001**. Với comprehensiveness, âm nghĩa
   là bỏ top-5 làm dự đoán TĂNG, khác hẳn bằng không. Đã sửa thành `-0.001`.
   Thiếu trích dẫn: câu *"Rule- and concept-based methods"* chỉ trích Anchors (rule-based);
   đã thêm `ghorbani2019towards` cho vế concept-based.

## Còn lại

- [ ] **⚠ LÀM MỚI MIRROR ẨN DANH — chặn thứ hai, phát hiện 10/08.** Bài trỏ reviewer tới
      `anonymous.4open.science/r/xai-ids-trust-2826`. **Link mở được, nhưng bên trong là bài khác:**

      | | mirror (reviewer mở) | cây làm việc |
      |---|---|---|
      | `paper/main.tex` | 36 KB | **87 KB** |
      | `paper/refs.bib` | 4,1 KB | **20 KB** |
      | `code/*.py` | 10 | **23** |
      | `paper/claims.json` | **CÒN** | đã loại vì mâu thuẫn bài ở 34/88 claim |

      Kho GitHub thật thì đúng HEAD — nên cổng AR-1 vẫn xanh; chỉ AR-6 (mới) thấy. Hảo phải vào
      4open.science **tạo lại mirror từ commit hiện tại** trước khi nộp, rồi thay ID trong bài nếu
      ID đổi. Kiểm lại bằng `check_anon_mirror.py main.tex --code ../code`.
- [x] ~~Khai dùng generative AI~~ — NDSS ghi *"The use of generative AI software tools must be
      disclosed as part of the paper submission."* Đã thêm đoạn khai trong **Ethics Considerations**
      (mục này không tính trang). Kiểm kèm: Ethics ở NDSS là **tuỳ chọn**, nhưng nếu có thì phải
      đặt *"immediately preceding the reference section"* — bài đặt đúng.
- [x] ~~Cover letter~~ — **NDSS là hội nghị, KHÔNG có cover letter.** Gói nộp chỉ gồm PDF + source.
- [ ] **Claim sheet một trang → đọc ngoài** — mục DANGEROUS còn lại. Đưa
      `CLAIM-SHEET.md` cho một người ngoài, xin trả lời **ba câu** ở cuối tờ, rồi ghi vào file này:
      `CLAIM-SHEET-READ: <ngày> <người> -- <họ nói gì>`
- [ ] Nếu người đọc ngoài nói *"cái này nghiêng về ML hơn an ninh"* thì **phải xử trước khi nộp** —
      đó đúng là dòng desk-reject của NDSS (xem §8b ở trên).
- [x] ~~Tra hạn nộp thật~~ — **19/08/2026**, đã chép nguyên nhãn ở đầu file.
- [x] ~~51 claim chưa ánh xạ~~ — manifest nay **54 claim**, `trace_prose_numbers` báo **0 bảng**
      không được claim nào chạm tới. Số claim thấp hơn 88 vì 88 là số **file** `claims/*.tex`,
      không phải số mệnh đề cần đối chiếu; nhiều file là hai mặt của cùng một con số.
- [x] ~~31 file `claims/*.tex` mồ côi~~ — đã xoá **29** file không được `\input`, còn **90/90** dùng thật.
