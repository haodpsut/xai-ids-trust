# paper-flow-state.md — ledger cổng, bản NDSS 2027

Paper: **When Is an Explanation Trustworthy? Foundations of Interpretability-Based Trust in ML-IDS**
Venue: **NDSS 2027**, chu kỳ **mùa thu**. Double-blind, đã ẩn danh (`Anonymous Submission`).

## ⚠ ĐÍNH CHÍNH NGÀY 15/08

15/08 là ngày **MỞ nhận bài** của chu kỳ mùa thu, **không phải hạn nộp** — CfP NDSS 2027 ghi
*"the fall cycle call for papers will open on 15 August"*. Chu kỳ mùa hè đã đóng 07/05/2026.
**Hạn thật phải tra lại trên trang CfP khi cổng mở.**

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
- **⚠ đọc-ngoài trên CLAIM SHEET — CHƯA CÓ.** Đây là mục còn thiếu thật sự.

## Cổng đã chạy 10/08/2026

| cổng | kết quả |
|---|---|
| `verify_refs` Layer-1 | ✅ 57 mục / 57 được trích, 0 giữ chỗ |
| **Layer-2** | ✅ `REF-VERIFICATION-2026-08-10.md` — 45/58 chứng minh máy, 4 xác minh trực tiếp, 8 kinh điển nhận diện, **1 KHÔNG TỒN TẠI đã thay** |
| `check_claim_scope` | ✅ PASS |
| `verify_numbers` | ✅ 37/37 claim ánh xạ được khớp CSV (`claims-manifest.json`) |
| `self_consistency` | ✅ PASS |
| `check_staleness` | ⚠ 4 CSV cũ hơn `data.py` — **đã kiểm diff: thuần CỘNG THÊM** (nhánh TON-IoT rồi CIC-IoT-2023), không đụng đường nạp của UNSW/CICIDS/5G ⇒ 11 claim từ 4 CSV đó **vẫn hợp lệ**. Cờ stale là dấu thời gian, không phải logic |
| biên dịch | ✅ 0 lỗi · 15 trang · 0 overfull |

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

- [ ] **Claim sheet một trang → đọc ngoài** (mục giết-trước duy nhất còn thiếu)
- [ ] Tra hạn nộp thật khi CfP mùa thu mở 15/08
- [ ] 51/88 claim chưa ánh xạ sang CSV trong manifest (phần ablation/audit) — mở rộng nếu có thời gian
- [ ] 31 file `claims/*.tex` mồ côi — dọn cho gọn
