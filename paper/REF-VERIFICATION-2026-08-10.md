# Xác minh tài liệu tham khảo — 10/08/2026 (vòng hai)

**62 mục** trong `refs.bib`, **62/62 được trích** trong bài, 0 mục giữ chỗ.

## Trạng thái theo nguồn chứng minh

| | số mục | chứng minh bằng gì |
|---|---|---|
| **Khớp Crossref trên sáu trường** | **42** | tra theo **DOI**, so tiêu đề · từng tác giả theo thứ tự · tạp chí/kỷ yếu · volume · number · trang · năm. Tổng **414 phép so trường**. |
| Nhà XB nộp tiêu đề cắt/nối | 5 | vẫn nằm trong 42 ở trên; xem mục dưới |
| Không có bản ghi Crossref | 20 | khai trong `refs-manual.txt`, **mỗi mục kèm nguồn tra cứu được** |

Chạy lại bất cứ lúc nào:

```
M=$(grep -vE '^\s*(#|$)' refs-manual.txt | awk '{print $1}' | paste -sd, -)
python3 <pipeline>/scripts/verify_refs_layer2.py refs.bib --manual "$M"
```

## Vì sao 20 mục không có DOI — và vì sao đó KHÔNG phải miễn trừ im lặng

NeurIPS, ICML, ICLR, USENIX Security, JMLR và arXiv **không đăng ký DOI Crossref**. Với một bài
ML/an ninh thì đó là một phần ba thư mục. Cổng Layer-2 đòi DOI cho mọi mục sẽ **FAIL vĩnh viễn**
trên một thư mục hoàn toàn đúng — và cách "sửa" duy nhất còn lại là hạ ngưỡng, tức vứt bỏ đúng cái
khả năng phát hiện mà L2 sinh ra để có.

Nên: 20 mục đó khai trong `refs-manual.txt`, **mỗi dòng bắt buộc kèm bằng chứng máy tra được**
(bản ghi DBLP hoặc arXiv id đã đối chiếu tiêu đề + họ tác giả đầu + năm). Cổng đọc file này, đếm
riêng, **in ra từng khoá**, và **CHẶN nếu có khoá khai trần không kèm bằng chứng**. Bỏ qua vẫn
không phải đã xác minh — nhưng nó không còn vô hình.

## Bốn lỗi THẬT bắt được ở vòng này

1. **`arreche2024exai`** thiếu tác giả thứ ba **Jack W. Roberts** (bib 3 người, bản ghi 4).
2. **`cicids2017`** họ tác giả thứ hai là **Habibi Lashkari**, không phải Lashkari.
3. **`action2026`** thiếu tiền tố tiêu đề **“TRACE:”**.
4. **Ba mục còn ở dạng preprint dù đã xuất bản**: `xgnid2024` → ESWA 287:128089 (2025);
   `feat5g2025` → JISA 99:104448 (2026); `krishna2022` → TMLR (2024).

Cộng với lỗi đã sửa ở vòng một: **`salo2022soc` KHÔNG TỒN TẠI**, đã thay bằng Nyre-Yu và cs.,
USEC 2022, DOI `10.14722/usec.2022.23014`.

## Năm ca nhà xuất bản nộp tiêu đề khác bản trích (L2-6g) — dung thứ nhưng IN RA

Nhà xuất bản không phải lúc nào cũng nộp đúng tiêu đề mà tác giả sẽ trích:

| khoá | bài trích | nhà XB nộp |
|---|---|---|
| `ribeiro2016lime` | *"Why Should I Trust You?": Explaining the Predictions of Any Classifier* | `"Why Should I Trust You?"` (ACM cắt ở dấu hai chấm) |
| `slack2020` | *Fooling LIME and SHAP: Adversarial Attacks on Post Hoc Explanation Methods* | `Fooling LIME and SHAP` |
| `jacovi2021formalizing` | *Formalizing Trust in AI: Prerequisites, Causes and Goals…* | `Formalizing Trust in Artificial Intelligence` |
| `breiman2001two` | *Statistical Modeling: The Two Cultures* | `… (with comments and a rejoinder by the author)` |
| `unsw2015` | *UNSW-NB15: A Comprehensive Data Set…* | `… (UNSW-NB15 network data set)` |

Chỉ **quan hệ tiền tố trọn vẹn** (hai chiều, phần ngắn ≥ 3 từ) được dung thứ, và vẫn phải khớp mọi
trường còn lại. Một cái **đuôi sai** không bao giờ là tiền tố trọn vẹn, nên khả năng bắt lỗi gốc của
L2 giữ nguyên — control có ca chứng minh điều đó.

## Cảnh báo còn lưu: tra theo TIÊU ĐỀ mà không chứng minh danh tính là bẫy

Khi thử tra tiêu đề để tìm DOI cho các mục thiếu, Crossref trả về:
- `jacovi2021formalizing` → một bài về **môi trường xây dựng** của tác giả khác, 2024;
- `arp2022` → một bài **chỉnh hình tiếng Đức** về khớp gối nhiễm trùng.

Cả hai đều là "kết quả gần nhất". Bộ so khớp chặt (tiêu đề **và** họ tác giả đầu **và** năm) loại
đúng cả hai. Đây chính là L2-6a: **một phép tra không định danh được thì phải nói là không, chứ
không được đoán.**

Và thêm một chiều nữa học được ở vòng này: **phải so cả VENUE**. Tra tiêu đề LIME cho ra DOI của
bản **demo NAACL 2016** — cùng tiêu đề, cùng tác giả, cùng năm với bản **KDD 2016** mà bài trích.
Tiêu đề + tác giả + năm **không đủ** để phân biệt hai bản của cùng một công trình.
