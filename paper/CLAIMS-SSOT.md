# Nguồn sự thật cho số trong bài — chốt 10/08/2026

**SSOT = `paper/claims/*.tex`.** Mỗi file một số, được `\input{}` thẳng vào `main.tex`, nên số
người đọc thấy **là** số trong file — không có bước gõ tay ở giữa.

## `claims.json` đã bị loại (đổi tên thành `claims.json.STALE-2026-08-10`)

Nó tự nhận là *"SSOT for NDSS paper… All trace to code/results/*.csv"* nhưng **sai**:
**34/88** claim được dùng trong bài lệch với nó, và ở mọi chỗ lệch **thật** (ngoài làm tròn) thì
**bài khớp CSV còn nó không**:

| claim | bài | claims.json | CSV | nguồn |
|---|---|---|---|---|
| `faith_comp_cicids` | **0,51** ✓ | 0,40 ✗ | 0,508 | `faithfulness.csv:comprehensiveness` |
| `faith_comp_5g` | **0,16** ✓ | 0,21 ✗ | 0,162 | như trên |
| `faith_comp_toniot` | **0,04** ✓ | 0,06 ✗ | 0,044 | như trên |
| `f5_shap_cicids` | **0,95** ✓ | 0,96 ✗ | 0,95 | `faith_5explainer.csv:shap` |
| `f5_shap_5g` | **0,40** ✓ | 0,41 ✗ | 0,4 | như trên |

Không script nào đọc `claims.json`, nên loại nó không ảnh hưởng build.

## Ánh xạ claim → CSV (dựng 10/08, dùng cho verify_numbers sau này)

| tiền tố | CSV | cột |
|---|---|---|
| `auc_<ds>` | `defense_ablate.csv` | `full_auc` |
| `faith_comp_<ds>` | `faithfulness.csv` | `comprehensiveness` |
| `f5_<explainer>_<ds>` | `faith_5explainer.csv` | `grad`/`ixg`/`ig`/`shap`/`lime` |
| `p1_drop_<ds>`, `p2_agree_<ds>`, `p3_agree_<ds>` (+`_std`) | `multiseed.csv` | `p1_fidelity_drop_*`, `p2_method_agree_*`, `p3_seed_agree_*` |

**⚠ Bẫy đã vấp:** AUC trong bài KHÔNG lấy từ `multiseed.csv:defense_auc_mean` (0,741/0,825/0,938)
mà từ `defense_ablate.csv:full_auc` (0,784/0,851/0,946). Ánh xạ nhầm khiến tôi suýt buộc tội bài
sai 4 chỗ. **Trước khi kết luận một số là sai, phải thử MỌI CSV có cột hợp lý.**

## Dọn thêm

**31 file `claims/*.tex` mồ côi** — có file, không được `\input` chỗ nào (`auc_*_std`, `abl_*`,
`ceil_*`, `audit_n`…). Không hại, nhưng là chỗ dễ tưởng nhầm là số của bài.
