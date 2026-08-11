# CLAIM SHEET — một trang, để ĐỌC NGOÀI

**Bài:** *When Is an Explanation Trustworthy? Foundations of Interpretability-Based Trust in ML-IDS*
**Đích:** NDSS 2027, chu kỳ mùa thu · **Lập** 10/08/2026 · **sửa lớn 11/08/2026 sau phản biện ngoài**

> **Cách dùng.** Đây là mục giết-trước cuối cùng. Người đọc **không cần đọc bài**, chỉ đọc trang
> này rồi trả lời **ba câu** ở cuối. Mục đích không phải khen bài, mà là tìm chỗ một người ngoài
> đọc xong vẫn thấy *"chưa thuyết phục"* hoặc *"cái này ai cũng biết rồi"* — vì đó là hai lý do
> reject phổ biến nhất, và cả hai đều **không cổng nội bộ nào bắt được**.

---

## 1. Bài khẳng định điều gì

**Mệnh đề trung tâm.** Khả năng giải thích (interpretability), tự nó, **không** là căn cứ để tin
một ML-IDS. Muốn tin có căn cứ thì bản đồ giải thích phải thoả **ba tính chất cần**, và trên dữ
liệu thật **hai trong ba hỏng hẳn, cái thứ ba mua được nhưng có giá**.

| | tính chất | nghĩa là gì | đo được gì |
|---|---|---|---|
| P1 | **fidelity** | vật thay thế diễn giải được quyết định *giống* mô hình đang chạy | **KHÔNG hỏng**: cây sâu 4 khớp quyết định $0{,}96$–$1{,}00$. Nhưng mua nó tốn tới $0{,}35$ $F_1$ |
| P2 | **determinacy** | lời giải thích do *quyết định* quy định, không do *chọn phương pháp* | **hỏng**: các họ explainer chỉ đồng ý $0{,}26$ số đặc trưng hiện ra, so với sàn ngẫu nhiên $0{,}06$–$0{,}09$ |
| P3 | **groundedness** | phản ánh *bài toán*, không phải *bản mô hình tình cờ* | **hỏng**: mô hình chính xác ngang nhau lệch gần một nửa top-feature |

**Ba kết quả âm khai thật** (không giấu): tấn công thao túng giải thích **không chuyển được**;
cổng "điểm tin cậy mỗi cảnh báo" thì **vòng tròn, không chuyển được, bị chơi được**; và **mô hình
thưa theo thiết kế** cứu được determinacy gần như miễn phí nhưng **chỉ đóng được khoảng cách hại ở
những bộ dễ nhất**.

**Hệ quả an ninh** — đây là số headline, và nó **có sàn nội tại**: một nhà phân tích mô phỏng đã
được hiệu chỉnh trên mô hình đang chạy bỏ qua **$0{,}018$** số tấn công thật đã phát hiện đúng trên
CICIDS2017; thay bằng **mô hình anh em chính xác ngang nhau** thì thành **$0{,}433$**; đọc
attribution **vô nghĩa** thì $0{,}505$. Tức niềm tin đã hiệu chỉnh **sống sót qua việc đổi seed
chẳng hơn bao nhiêu so với không đọc gì**.

⚠ **Đã RÚT so với bản 10/08:** con số cũ *"$0{,}87$ luồng bị đẩy tới hành động ngược nhau"*. Phép
thử null hoán vị cho thấy **0/10 dòng vượt ngẫu nhiên** — phân kỳ hành động được giải thích trọn vẹn
bởi tỉ lệ bỏ sót biên, nên nó không phải bằng chứng độc lập. Bỏ khỏi abstract.

## 2. Bằng chứng đứng trên cái gì

- **5 bộ dữ liệu** 2015–2023: UNSW-NB15 · CICIDS2017 · 5G-NIDD · TON-IoT · CIC-IoT-2023.
- **Trần khả thi** (`ceiling.csv`): trên dữ liệu tổng hợp thưa, ba thước đo đạt $\approx 1{,}0$
  ⇒ thước **đo được**, không phải dựng ra để chắc chắn hỏng.
- **Biên vs sai số:** P2 $\approx 0{,}45\pm0{,}017$, P3 $\approx 0{,}53\pm0{,}005$ (đa seed).
  Khoảng cách tới $1{,}0$ lớn hơn độ lệch chuẩn **hai bậc**.
- **95 con số** trong bài được máy đối chiếu về CSV; **62 tài liệu** tham khảo, 42 khớp Crossref
  trên sáu trường (414 phép so), 20 mục không có DOI thì khai kèm nguồn tra cứu được.
- **Khảo sát hiện trạng 12 bài** XAI-IDS chấm theo 6 tiêu chí: **không tiêu chí nào** được quá
  nửa số bài báo cáo; bất biến theo thực thể: **0/12**.

## 3. Chỗ bài TỰ NHẬN là yếu

1. **Nhà phân tích là mô phỏng**, không phải người thật. Mọi tỉ lệ là **cận trên**.
0. **Ba trong năm detector bão hoà** ($F_1$ = 1,00 · 0,99 · 0,99) ⇒ kết quả hại thật ra dựa trên
   **hai bộ dữ liệu, không phải năm**. Bài khai thẳng chỗ này.
2. Khảo sát 12 bài là **mẫu tiện lợi**, chấm từ tóm tắt/phần phương pháp ⇒ là **cận dưới** về độ
   nghiêm túc của người ta; bài đo **thực hành báo cáo**, không đo chất lượng ẩn.
3. Chỉ xét **attribution hậu nghiệm** trên dữ liệu bảng. Không nói gì về mô hình tự-giải-thích.
4. **Không đưa ra cách sửa.** Bài kết ở "đây là bài toán mở". Cách sửa hiển nhiên nhất — dùng mô
   hình thưa — đã được **thử và không đủ**.
5. **Ba tính chất không dự báo được tác hại.** Tương quan giữa groundedness và hại là **ngược dấu**
   ($\rho = +0{,}70$, $n=5$, không có ý nghĩa). Bài khai điều này thay vì giấu.

---

## ★ BA CÂU HỎI CHO NGƯỜI ĐỌC NGOÀI

1. **Có mới không?** Đọc §1 ở trên, bạn có nghĩ *"cái này biết rồi"* không? Nếu có — **biết từ
   bài nào**? (Câu này quan trọng nhất: occupied-check nội bộ chỉ thấy được cái nó nghĩ ra để tìm.)

2. **Có tin không?** Chỗ nào bạn thấy bước từ **bằng chứng** sang **kết luận** là hụt? Cụ thể:
   ba tính chất kia có thật là **cần** cho "tin có căn cứ", hay chỉ là ba thứ *đo được* rồi được
   gọi là cần?

3. **Có đáng NDSS không?** Một bài không đưa ra cách sửa, kết ở "bài toán mở", cộng **ba** kết quả
   âm, và **tự rút** một trong các số headline của chính mình — bạn nghĩ nó bị đánh giá là **đóng
   góp nền tảng** hay là **kết quả tiêu cực không đủ tầm**? Nếu là vế sau, thiếu cái gì thì thành
   vế trước?

4. **(mới)** Bài tự rút con số $0{,}87$ vì nó không vượt sàn ngẫu nhiên. Việc **tự khai** như vậy
   làm bạn tin bài hơn, hay làm bạn nghi phần còn lại?

*Trả lời ngắn cũng được. Ghi thẳng vào file này bên dưới, hoặc nhắn lại.*

---

## Ghi nhận đọc-ngoài

| ngày | người đọc | trả lời Q1 | Q2 | Q3 |
|---|---|---|---|---|
| | | | | |
