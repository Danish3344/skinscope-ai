# Dataset strategy

## Current decision - Kaggle candidate

The project is switching away from waiting on Fitzpatrick17k images and will use Kaggle's [Skin Diseases Image Dataset](https://www.kaggle.com/datasets/ismailpromus/skin-diseases-image-dataset) as the first active candidate. The source remains **blocked for training** until the archive is downloaded through authenticated Kaggle access and its license is cleared.

The public Kaggle page reports:

- Dataset name: Skin diseases image dataset
- Owner: Ismail Hossain
- Source: Kaggle
- Size: 27.2k files, version 1, about 5.58 GB
- Top-level folder: `IMG_CLASSES`
- License shown by Kaggle: `Data files © Original Authors`
- Description: no detailed dataset card text is available on the public page

That license label is not a normal open-source or Creative Commons training license. It does not clearly grant redistribution, commercial use, or machine-learning training rights. A later DERMOSAN replication record also points users back to the original Kaggle source and says the underlying data uses the original Kaggle license, `Data files © Original Authors`. Therefore, this project can prepare the Kaggle workflow but must not train on the dataset until the intended research use is accepted as legitimate by the user or a clearer license is obtained.

### Kaggle mapping audit

The documented Kaggle classes are mixed: several folders combine multiple diagnoses into one label. Only exact labels are automatic.

| Target class | Dataset class | Number of images | Mapping type | Supported? | Notes |
| --- | --- | ---: | --- | --- | --- |
| Acne | - | Unknown | UNSUPPORTED | No | No exact Acne folder is documented for this Kaggle candidate |
| Atopic Dermatitis | `Atopic Dermatitis` | Unknown until download | DIRECT | Candidate | Exact folder label, pending archive inspection and license clearance |
| Psoriasis | `Psoriasis pictures Lichen Planus and related diseases` | Unknown until download | POSSIBLE | No | Mixed category, not a direct Psoriasis label |
| Melanoma | `Melanoma` | Unknown until download | DIRECT | Candidate | Exact folder label, pending archive inspection and license clearance |
| Basal Cell Carcinoma | `Basal Cell Carcinoma` | Unknown until download | DIRECT | Candidate | Exact folder label, pending archive inspection and license clearance |
| Seborrheic Keratosis | `Seborrheic Keratoses and other Benign Tumors` | Unknown until download | POSSIBLE | No | Mixed benign-tumor category |
| Rosacea | - | Unknown | UNSUPPORTED | No | No exact Rosacea folder is documented |
| Vitiligo | - | Unknown | UNSUPPORTED | No | No exact Vitiligo folder is documented |
| Warts | `Warts Molluscum and other Viral Infections` | Unknown until download | POSSIBLE | No | Mixed viral-infection category |
| Eczema | `Eczema` | Unknown until download | DIRECT | Candidate | Exact folder label, pending archive inspection and license clearance |

Current scientifically defensible Kaggle model size: **4 candidate direct classes**, not 10. Training remains blocked until actual files and license clearance exist.

## Decision

Fitzpatrick17k remains configured as a future dataset source. It was previously selected provisionally for eight supported application labels, but its image archive has not been received. It is not required for the active Kaggle workflow.

The selected work is published under **CC BY-NC-SA 3.0**, so this plan is limited to attributed, non-commercial research and carries ShareAlike obligations. The repository states that images originated in DermaAmin and Atlas Dermatologico; downstream users must preserve the required attribution and confirm that their planned use fits the terms. See the [official Fitzpatrick17k repository and access instructions](https://github.com/mattgroh/fitzpatrick17k).

## Candidate audit

| Dataset | Official source | License | Size / format | Labels and metadata | Identifiers / imbalance | Fit for this task |
| --- | --- | --- | --- | --- | --- | --- |
| Fitzpatrick17k | [Official repository](https://github.com/mattgroh/fitzpatrick17k) | CC BY-NC-SA 3.0 as stated by the publisher; original atlas provenance must be retained | 16,577 clinical images; source downloads are predominantly encoded web images | 114 condition labels; URL, MD5 hash, skin-tone annotations, QC field | No patient or lesion ID in the published CSV; exact MD5 enables duplicate checks. Published class range is 53–653 before mappings | Selected provisionally. Eight target concepts have explicit labels, but Atopic Dermatitis and Warts do not |
| HAM10000 / ISIC 2018 | [Official ISIC challenge data](https://challenge.isic-archive.com/data/) and [data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC6091241/) | CC BY-NC for ISIC 2018 distribution; descriptor metadata is CC0 | 10,015 JPEG dermoscopic images | Seven pigmented-lesion categories; age, sex, site, diagnosis method | `lesion_id` groups repeat images; severe imbalance (for example, melanocytic nevi dominate) | Useful for melanoma/BCC, but not inflammatory targets. Its `bkl` class combines several benign keratoses, so it is not a clean Seborrheic Keratosis mapping |
| ISIC 2019 | [Official ISIC challenge data](https://challenge.isic-archive.com/data/) | CC BY-NC | 25,331 JPEG training images | Eight dermoscopic diagnosis outputs; age, sex, site | Common lesion identifier is published; constituent datasets and duplicate handling require care | Cancer-focused only; does not solve acne, psoriasis, rosacea, vitiligo, warts, or eczema |
| DermNet website images | [Official image licence](https://dermnetnz.org/image-licence) | Website images are explicitly prohibited for AI training; a separately licensed paid dataset is offered | Not applicable without a negotiated dataset licence | Broad clinical coverage | Terms and metadata depend on the commercial agreement | Rejected. Website images must not be scraped or used for this model |

## Audited class mapping

Counts below were computed from the official 16,577-row `fitzpatrick17k.csv` metadata on 25 August 2026. They are **candidate metadata counts**, not prepared-image counts: broken links, corrupt files, exact duplicates, and quality filtering can reduce them.

| Target class | Dataset class(es) | Dataset | Mapping type | Metadata images | Confidence |
| --- | --- | --- | --- | ---: | --- |
| Acne | `acne`, `acne vulgaris` | Fitzpatrick17k | Direct + synonym | 518 | High |
| Atopic Dermatitis | — | — | Unavailable | 0 | High confidence that no explicit source label exists |
| Psoriasis | `psoriasis`, `pustular psoriasis` | Fitzpatrick17k | Direct + subtype | 706 | High |
| Melanoma | `melanoma`, `malignant melanoma`, `superficial spreading melanoma ssm` | Fitzpatrick17k | Direct + subtype | 490 | High |
| Basal Cell Carcinoma | `basal cell carcinoma`, `basal cell carcinoma morpheiform`, `solid cystic basal cell carcinoma` | Fitzpatrick17k | Direct + subtype | 596 | High |
| Seborrheic Keratosis | `seborrheic keratosis` | Fitzpatrick17k | Direct | 69 | High mapping confidence; low sample count |
| Rosacea | `rosacea` | Fitzpatrick17k | Direct | 102 | High mapping confidence; low sample count |
| Vitiligo | `vitiligo` | Fitzpatrick17k | Direct | 166 | High |
| Warts | — | — | Unavailable | 0 | High confidence that no wart/verruca source label exists |
| Eczema | `eczema`, `dyshidrotic eczema` | Fitzpatrick17k | Direct + subtype | 287 | Moderate–high; broad target remains heterogeneous |

`seborrheic dermatitis` is not mapped to Seborrheic Keratosis. Broad `eczema` is not relabeled as Atopic Dermatitis. These are clinically different or insufficiently specific concepts.

## Consequences and limitations

- Only **8 of 10** application labels are supported by the selected source. Phase 3B must stop unless the user accepts an eight-class model or supplies a compatible, explicitly licensed source for Atopic Dermatitis and Warts.
- Atopic dermatitis is a type of eczema. Keeping both as visually exclusive classes requires precise, independently verified source diagnoses; broad eczema examples cannot safely populate both.
- There are only 69 mapped Seborrheic Keratosis images and 102 Rosacea images before file-quality filtering, creating substantial imbalance.
- Fitzpatrick17k provides no patient or lesion identifiers. The pipeline can prevent exact-file leakage by SHA-256, but cannot guarantee that different photographs of the same patient or lesion remain together.
- Source URLs include broken links according to the publisher. Actual usable counts will be known only after official image access and preparation.
- Clinical atlas imagery may contain acquisition, framing, annotation, or site artifacts. Contact sheets must be reviewed before training.
- Combining clinical photographs with dermoscopic HAM10000 images could teach modality/source shortcuts. This plan therefore does not merge HAM10000 automatically.

## Training gate

Do not train until all of these are true:

1. The official Fitzpatrick17k images and metadata are present locally.
2. The preparation pipeline has produced real statistics and contact sheets.
3. Samples and mappings have been visually reviewed.
4. The eight-class limitation—or a properly licensed extension for the missing classes—has been explicitly approved.

## Acquisition status — 25 August 2026

The official `fitzpatrick17k.csv` and upstream README have been downloaded into `data/raw/fitzpatrick17k/`. The CSV parses successfully and contains 16,577 rows, 16,577 unique MD5 hashes, 114 labels, and 2,934 rows covered by the eight approved mappings.

The image archive is **not present**: `data/raw/fitzpatrick17k/images/` does not exist and zero local images are available. The publisher states that some source links are broken and directs users to complete its access form and contact the team for the complete images. That user-mediated request has not been submitted automatically. Consequently:

- 16,577 metadata references currently have no corresponding local image;
- corruption, image-level duplication, dimensions, and visual quality cannot be evaluated;
- preparation, split statistics, manifest generation, and galleries have not been run;
- metadata counts remain candidate counts, not final usable-image counts.

Environment readiness was checked on 25 August 2026: Python 3.12.13 is available, the C: drive has 344.42 GB free, PowerShell `Invoke-WebRequest`/`Expand-Archive`, `curl.exe`, and `tar.exe` are installed, and the official GitHub repository is reachable. The existing CSV is 4,104,341 bytes with SHA-256 `851DFAABF1791C2A8B1C2957619F3E0673CF0002F4CE924A5C02D185C7D4A1CD`. Disk and tooling are sufficient to receive an archive, but there is no authorized public archive URL to automate.

### Supplemental candidates for unavailable targets

| Target | Candidate | Verified source coverage | Licence / permitted use | Quality and metadata | Decision |
| --- | --- | ---: | --- | --- | --- |
| Warts | [SCIN](https://github.com/google-research-datasets/scin) | `Verruca vulgaris`: 20 cases / 46 images where it is the top weighted dermatologist label; 40 cases / 95 images where it appears anywhere in the differential | SCIN Data Use License permits reproduction and adapted material with attribution; re-identification is prohibited. The official release is intended for research/AI development. The licence does not state a non-commercial-only restriction, but all its conditions still apply | Consented smartphone images; case IDs, up to three images per contribution, symptoms/demographics, weighted dermatologist differential labels. These are diagnostic estimates, not uniformly confirmed diagnoses | Legitimate candidate, but 20 top-label cases are too small to justify production training without expert review and careful case-grouped evaluation |
| Atopic Dermatitis | [SkinDisNet](https://data.mendeley.com/datasets/yj3md44hxg/) | 70 original images; publisher also provides 490 augmented derivatives, which must remain grouped with originals and must not inflate independent sample counts | CC BY-NC 4.0; academic/research ML use is explicitly described. Commercial use is **not permitted** | Smartphone clinical images from hospitals in Bangladesh, dermatologist diagnoses, 416 patients across the complete six-class dataset, clinical/demographic metadata | Legitimate non-commercial candidate, but only 70 originals and source/domain imbalance require validation before mapping |
| Atopic Dermatitis | [National Eczema Association Visual Guide](https://nationaleczema.org/visual-guide-license-application/) | Count not accepted until a licence is granted | Application-based image licence; terms depend on approval | Curated eczema/AD visual guide across skin tones and body sites | Not usable without explicit licence approval; no request was submitted |
| Atopic Dermatitis / Warts | DermNet website | Not considered | Website licence explicitly prohibits AI training unless a separate paid dataset licence is obtained | Broad clinical coverage | Rejected for current use |

SCIN's official metadata was audited without retaining its images. It contains 5,033 cases and 10,407 image references. The release documents 15 duplicate images appearing 42 times, 48 gradable cases without a condition label, and one missing image. Any future SCIN integration must split by `case_id`, remove exact duplicates across cases, and retain only reviewed labels meeting a documented confidence rule.

These candidates show that licensed supplemental data may exist, but a **10-class dataset is not currently justified or locally available**. Combining Fitzpatrick17k, SCIN, and SkinDisNet would also introduce strong source, geography, acquisition, and label-certainty differences that a classifier could exploit as shortcuts.
