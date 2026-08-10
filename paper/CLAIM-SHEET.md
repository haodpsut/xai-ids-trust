# CLAIM SHEET — một trang, để ĐỌC NGOÀI

**Bài:** *When Is an Explanation Trustworthy? Foundations of Interpretability-Based Trust in ML-IDS*
**Đích:** NDSS 2027, chu kỳ mùa thu · **Ngày lập:** 10/08/2026

> **Cách dùng.** Đây là mục giết-trước cuối cùng. Người đọc **không cần đọc bài**, chỉ đọc trang
> này rồi trả lời **ba câu** ở cuối. Mục đích không phải khen bài, mà là tìm chỗ một người ngoài
> đọc xong vẫn thấy *"chưa thuyết phục"* hoặc *"cái này ai cũng biết rồi"* — vì đó là hai lý do
> reject phổ biến nhất, và cả hai đều **không cổng nội bộ nào bắt được**.

---

## 1. Bài khẳng định điều gì

**Mệnh đề trung tâm.** Khả năng giải thích (interpretability), tự nó, **không** là căn cứ để tin
một ML-IDS. Muốn tin có căn cứ thì bản đồ giải thích phải thoả **ba tính chất cần**, và trên dữ
liệu thật **cả ba đều hỏng**.

| | tính chất | nghĩa là gì | đo bằng |
|---|---|---|---|
| P1 | **fidelity** | vật thay thế diễn giải được quyết định *giống* mô hình đang chạy | mất tới $0{,}35$ $F_1$ |
| P2 | **determinacy** | lời giải thích do *quyết định* quy định, không do *chọn phương pháp* | các họ explainer chỉ trùng $0{,}15$ số đặc trưng |
| P3 | **groundedness** | phản ánh *bài toán*, không phải *bản mô hình tình cờ* | mô hình chính xác ngang nhau lệch gần một nửa top-feature |

**Hai kết quả âm khai thật** (không giấu): tấn công thao túng giải thích **không chuyển được** giữa
các mô hình; và cổng "điểm tin cậy mỗi cảnh báo" thì **vòng tròn, không chuyển được, bị chơi được**.

**Hệ quả an ninh** (chỗ bài vượt khỏi "một quan sát về XAI"): trên các luồng **đã bị phát hiện đúng
và ổn định**, giải thích của hai mô hình tốt ngang nhau đẩy nhà phân tích tới **hành động ngược
nhau**, tới $0{,}87$ số luồng trên CICIDS2017 (cận trên, nhà phân tích mô phỏng).

## 2. Bằng chứng đứng trên cái gì

- **5 bộ dữ liệu** 2015–2023: UNSW-NB15 · CICIDS2017 · 5G-NIDD · TON-IoT · CIC-IoT-2023.
- **Trần khả thi** (`ceiling.csv`): trên dữ liệu tổng hợp thưa, ba thước đo đạt $\approx 1{,}0$
  ⇒ thước **đo được**, không phải dựng ra để chắc chắn hỏng.
- **Biên vs sai số:** P2 $\approx 0{,}45\pm0{,}017$, P3 $\approx 0{,}53\pm0{,}005$ (đa seed).
  Khoảng cách tới $1{,}0$ lớn hơn độ lệch chuẩn **hai bậc**.
- **53 con số** trong bài được máy đối chiếu về CSV; **62 tài liệu** tham khảo, 42 khớp Crossref
  trên sáu trường (414 phép so), 20 mục không có DOI thì khai kèm nguồn tra cứu được.
- **Khảo sát hiện trạng 12 bài** XAI-IDS chấm theo 6 tiêu chí: **không tiêu chí nào** được quá
  nửa số bài báo cáo; bất biến theo thực thể: **0/12**.

## 3. Chỗ bài TỰ NHẬN là yếu

1. **Nhà phân tích là mô phỏng**, không phải người thật. Con số $0{,}87$ là **cận trên**.
2. Khảo sát 12 bài là **mẫu tiện lợi**, chấm từ tóm tắt/phần phương pháp ⇒ là **cận dưới** về độ
   nghiêm túc của người ta; bài đo **thực hành báo cáo**, không đo chất lượng ẩn.
3. Chỉ xét **attribution hậu nghiệm** trên dữ liệu bảng. Không nói gì về mô hình tự-giải-thích.
4. **Không đưa ra cách sửa.** Bài kết ở "đây là bài toán mở".

---

## ★ BA CÂU HỎI CHO NGƯỜI ĐỌC NGOÀI

1. **Có mới không?** Đọc §1 ở trên, bạn có nghĩ *"cái này biết rồi"* không? Nếu có — **biết từ
   bài nào**? (Câu này quan trọng nhất: occupied-check nội bộ chỉ thấy được cái nó nghĩ ra để tìm.)

2. **Có tin không?** Chỗ nào bạn thấy bước từ **bằng chứng** sang **kết luận** là hụt? Cụ thể:
   ba tính chất kia có thật là **cần** cho "tin có căn cứ", hay chỉ là ba thứ *đo được* rồi được
   gọi là cần?

3. **Có đáng NDSS không?** Một bài không đưa ra cách sửa, kết ở "bài toán mở", cộng hai kết quả
   âm — bạn nghĩ nó bị đánh giá là **đóng góp nền tảng** hay là **kết quả tiêu cực không đủ tầm**?
   Nếu là vế sau, thiếu cái gì thì thành vế trước?

*Trả lời ngắn cũng được. Ghi thẳng vào file này bên dưới, hoặc nhắn lại.*

---

## Ghi nhận đọc-ngoài

| ngày | người đọc | trả lời Q1 | Q2 | Q3 |
|---|---|---|---|---|
| | | | | |
