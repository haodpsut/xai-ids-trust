# Layer-2 reference verification — 58 tham khảo, 10/08/2026

`refs.bib` **không mục nào có DOI**, nên không thể tra theo DOI. Quy trình đã dùng:
tra theo tiêu đề, rồi **chứng minh danh tính độc lập** trước khi nhận — tiêu đề phải khớp
sau chuẩn hoá, **và** họ tác giả đầu phải khớp, **và** năm lệch không quá 1. Mục nào không
chứng minh được thì ghi là CHƯA XÁC MINH, không nhận bừa.

## Tổng kết

| nhóm | số mục |
|---|---|
| khớp Crossref, danh tính đã chứng minh | **32** |
| khớp arXiv, tiêu đề khớp chính xác | **13** |
| xác minh bằng mã arXiv có sẵn trong bib / tìm kiếm có nguồn | **4** |
| kinh điển, nhận diện chắc chắn nhưng CHƯA đối chiếu máy | **8** |
| ⛔ **KHÔNG TÌM THẤY** | **1** |

## ⛔ Mục không tìm thấy — PHẢI XỬ LÝ TRƯỚC KHI NỘP

**`salo2022soc`** — *"Towards Explainable AI in the Security Operations Center"*,
Salo, Fabio and Ali, Sarhad and others, IEEE Big Data 2022.

Hai lượt tìm độc lập **không ra bài nào** mang tiêu đề/tác giả/venue đó. Trường `author`
có `and others` mơ hồ. Đây có dạng của một ref **bịa hoặc nhớ nhầm**.

Nó được trích ở Related Work: *"surveys of explainable IDS và of explanations in the
security operations center [salo2022soc] call for stakeholder-specific evaluation"*.

**Hướng xử lý:** thay bằng một công trình CÓ THẬT đỡ đúng luận điểm đó, ví dụ
Nyre-Yu và cs., *"Explainable AI in Cybersecurity Operations: Lessons Learned from XAI
Tool Deployment"*, USEC 2022 — hoặc bỏ hẳn vế đó. **Không nộp khi chưa xử lý:** với NDSS,
ref bịa là vấn đề liêm chính, và tác giả đã từng bị TEVC bắt 6 ref giả.

## Kinh điển, nhận diện chắc chắn nhưng chưa đối chiếu máy

- **arp2022** — USENIX Security 2022 — công trình kinh điển, nhận diện chắc chắn
- **breiman2001two** — Statistical Science 16(3):199-231, 2001 — kinh điển
- **fisher2019rashomon** — JMLR 20(177), 2019 — Fisher/Rudin/Dominici
- **molnar2022interpretable** — sách, tự xuất bản, 2nd ed. — không có DOI, xác minh bằng nhận diện
- **slack2020** — AIES 2020 — Crossref trả về đúng tiêu đề "Fooling LIME and SHAP" ở vị trí gần nhất
- **sundararajan2017ig** — ICML 2017 — kinh điển
- **szegedy2014intriguing** — ICLR 2014 — kinh điển
- **unsw2015** — MilCIS 2015 — Crossref trả về đúng tiêu đề ở vị trí gần nhất

## Đã xác minh trực tiếp ngoài hai vòng tự động

- **action2026** — MDPI Electronics 15(15):3291, 2026 — ĐÃ XÁC MINH qua tìm kiếm: khung TRACE, mdpi.com/2079-9292/15/15/3291
- **g5nidd** — arXiv:2212.01298 — ĐÃ XÁC MINH trực tiếp: "5G-NIDD: A Comprehensive Network Intrusion Detection Dataset Generated over 5G Wireless Network"
- **simonyan2013saliency** — arXiv:1312.6034 — ĐÃ XÁC MINH trực tiếp
- **smilkov2017smoothgrad** — arXiv:1706.03825 — ĐÃ XÁC MINH trực tiếp

## Khớp máy (32 Crossref + 13 arXiv)

Chi tiết từng mục kèm DOI/arXiv-id trong `l2-lookup.json`.

## Hạn chế của vòng kiểm này

Đã chứng minh **danh tính** (đúng bài đó tồn tại, đúng tác giả đầu, đúng năm). **Chưa**
đối chiếu đủ 6 trường (volume/issue/trang) vì bib không có DOI để lấy bản ghi đầy đủ.
Nếu venue yêu cầu, bước tiếp là ghim DOI vừa tìm được vào `refs.bib` rồi chạy
`verify_refs_layer2.py` để so 6 trường.
