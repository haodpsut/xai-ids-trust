# Datasets: what the code expects, and how to verify you have the same bytes

`code/data.py` reads five datasets from `../data`, that is `data/` at the repository root.
`data/` is **not tracked in git** (`.gitignore` line 1) for two reasons that are not
negotiable: two of the files exceed GitHub's hard 100 MB per-file limit, and the datasets are
third-party releases that should be obtained from their own publishers.

This file is the manifest that replaces shipping the bytes. If your five SHA-256 digests match
the table below, you are running on exactly the data that produced every number in the paper.

## Expected layout

```
data/
  unsw/UNSW_NB15_training-set.parquet
  cicids/cicids2017_cleaned.csv
  g5nidd/Combined.csv
  toniot/train_test_network.csv
  ciciot2023/cic_iot_2023.parquet
```

## Manifest (measured 2026-11-10)

| file | bytes | rows | cols | sha256 |
|---|---|---|---|---|
| `unsw/UNSW_NB15_training-set.parquet` | 9,618,034 | 175,341 | 36 | `f6989e65032e7577...b490c1918` |
| `cicids/cicids2017_cleaned.csv` | 717,247,573 | 2,520,751 | 53 | `0ce5a39edffcde3f...f224c292` |
| `g5nidd/Combined.csv` | 275,265,610 | 1,215,890 | 52 | `fa36f80859585f47...ab46ee59` |
| `toniot/train_test_network.csv` | 29,902,775 | 211,043 | 44 | `26ddc513552de36d...a64e1974` |
| `ciciot2023/cic_iot_2023.parquet` | 5,220,239 | 200,000 | 40 | `3b49fa630b754203...ead605b0` |

Full digests are in `data-manifest.sha256`. Verify with:

```bash
cd data && sha256sum -c ../data-manifest.sha256     # Linux
cd data && shasum -a 256 -c ../data-manifest.sha256 # macOS
```

`code/cong_du_lieu.py` runs the same check and also reports which files are absent, so a
missing dataset fails loudly instead of surfacing later as a confusing traceback.

## Provenance

| dataset | original publication | DOI |
|---|---|---|
| UNSW-NB15 | Moustafa and Slay, MilCIS 2015 | `10.1109/MilCIS.2015.7348942` |
| CICIDS2017 | Sharafaldin et al., ICISSP 2018 | `10.5220/0006639801080116` |
| CICIDS2017, corrected labels | Engelen et al., IEEE SPW 2021 | `10.1109/SPW53761.2021.00009` |
| 5G-NIDD | Samarakoon et al., 2022 | arXiv:2212.01298 |
| TON-IoT | Alsaedi et al., IEEE Access 2020 | `10.1109/ACCESS.2020.3022862` |
| CICIoT2023 | Neto et al., Sensors 2023 | `10.3390/s23135941` |

## Known gap: three of the five files are derived, and the derivation is not scripted here

Stated plainly, because the digests above would otherwise imply more than they prove:

- `cicids2017_cleaned.csv` is the **corrected** release that repairs the labeling and
  feature-extraction errors of the original CICIDS2017, following Engelen et al. (2021). It is
  not the file served by the original dataset page.
- `UNSW_NB15_training-set.parquet` and `cic_iot_2023.parquet` are **Parquet conversions** of
  releases that the publishers distribute as CSV.

The conversion and cleaning steps were performed before this repository was created and are
**not reproducible from this repository**. The digests let a reader confirm bit-identical
inputs; they do not let a reader rebuild those inputs from the publishers' downloads. Closing
that gap requires adding the conversion scripts, which is open work.

## Runtime requirement that is easy to miss

Reading the two `.parquet` files needs **`pyarrow`**, which `pandas` imports lazily inside
`read_parquet`. No source file contains `import pyarrow`, so dependency scanners that walk the
import graph do not see it. It is pinned in `requirements.txt`; without it, `data.load("UNSW")`
and `data.load("CIC-IoT-2023")` raise `ImportError` and two of the five datasets are
unavailable.
