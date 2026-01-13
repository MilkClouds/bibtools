# Comparison: bibtools vs Google Scholar

## Summary

| Paper | Source | Winner | Key Difference |
|-------|--------|--------|----------------|
| ResNet (CVPR 2016) | CrossRef | Draw | bibtools: official venue, GS: pages |
| Attention (NeurIPS 2017) | DBLP | ✅ bibtools | DBLP title search finds NIPS 2017 |
| LoRA (ICLR 2022) | DBLP | ✅ bibtools | Correct year (2022) and venue (ICLR) |
| StreamingLLM (ICLR 2024) | DBLP | ✅ bibtools | DBLP title search finds ICLR 2024 |
| Self-Instruct (ACL 2023) | DBLP | ✅ bibtools | DBLP title search finds ACL 2023 |
| ACL Paper (ACL 2023) | CrossRef | ✅ bibtools | Full official metadata from CrossRef |

### Key Findings

**bibtools advantages:**
- **CrossRef (DOI)**: Official venue names and correct publication years
- **DBLP (venue-based)**: Uses SS venue to search DBLP by title - works even when DBLP ID is arXiv version
- **arXiv**: Full author lists without truncation

**bibtools limitations:**
- No page numbers (not in metadata)

**New in this version:**
- Uses SS venue field to decide source (not DBLP ID format)
- DBLP title search with canonical venue names (e.g., "Neural Information Processing Systems" → "NIPS")

---

## Data Sources

bibtools uses **official sources only** with single source of truth principle:

| Condition | Source |
|-----------|--------|
| DOI exists | **CrossRef** |
| No DOI, venue != arXiv | **DBLP** |
| No DOI, venue == arXiv | **arXiv** |

- **Semantic Scholar** - ID resolution + venue detection (determines which source to use)

---

## Test Results (Actual `bibtools fetch` Output)

### 1. ResNet (CVPR 2016) - via DOI

```bash
$ bibtools fetch DOI:10.1109/CVPR.2016.90
```

```bibtex
% paper_id: DOI:10.1109/CVPR.2016.90
@inproceedings{he2016,
  title = {Deep Residual Learning for Image Recognition},
  author = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  booktitle = {2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
  year = {2016}
}
```

**Source: CrossRef** ✅ Official venue with year

---

### 2. Attention Is All You Need (NeurIPS 2017) - via DBLP

```bash
$ bibtools fetch 1706.03762
```

```bibtex
% paper_id: 1706.03762
@inproceedings{vaswani2017,
  title = {Attention is All you Need},
  author = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N. and Kaiser, Lukasz and Polosukhin, Illia},
  booktitle = {NIPS},
  year = {2017}
}
```

**Source: DBLP** ✅ SS venue="Neural Information Processing Systems" → DBLP title search with "NIPS"

---

### 3. LoRA (ICLR 2022) - via DBLP

```bash
$ bibtools fetch 2106.09685
```

```bibtex
% paper_id: 2106.09685
@inproceedings{hu2022,
  title = {LoRA: Low-Rank Adaptation of Large Language Models},
  author = {Hu, Edward J. and Shen, Yelong and Wallis, Phillip and Allen-Zhu, Zeyuan and Li, Yuanzhi and Wang, Shean and Wang, Lu and Chen, Weizhu},
  booktitle = {ICLR},
  year = {2022}
}
```

**Source: DBLP** ✅ Correct year (2022) and venue (ICLR) - ICLR has no DOI

---

### 4. StreamingLLM (ICLR 2024) - via DBLP

```bash
$ bibtools fetch 2309.17453
```

```bibtex
% paper_id: 2309.17453
@inproceedings{xiao2024,
  title = {Efficient Streaming Language Models with Attention Sinks},
  author = {Xiao, Guangxuan and Tian, Yuandong and Chen, Beidi and Han, Song and Lewis, Mike},
  booktitle = {ICLR},
  year = {2024}
}
```

**Source: DBLP** ✅ SS venue="ICLR" → DBLP title search finds ICLR 2024

---

### 5. Self-Instruct (ACL 2023) - via DBLP

```bash
$ bibtools fetch 2212.10560
```

```bibtex
% paper_id: 2212.10560
@inproceedings{wang2023,
  title = {Self-Instruct: Aligning Language Models with Self-Generated Instructions},
  author = {Wang, Yizhong and Kordi, Yeganeh and Mishra, Swaroop and Liu, Alisa and Smith, Noah A. and Khashabi, Daniel and Hajishirzi, Hannaneh},
  booktitle = {ACL},
  year = {2023}
}
```

**Source: DBLP** ✅ SS venue="ACL" → DBLP title search finds ACL 2023

---

### 6. ACL Paper (ACL 2023) - via DOI

```bash
$ bibtools fetch DOI:10.18653/v1/2023.acl-long.10
```

```bibtex
% paper_id: DOI:10.18653/v1/2023.acl-long.10
@inproceedings{deguchi2023,
  title = {Subset Retrieval Nearest Neighbor Machine Translation},
  author = {Deguchi, Hiroyuki and Watanabe, Taro and Matsui, Yusuke and Utiyama, Masao and Tanaka, Hideki and Sumita, Eiichiro},
  booktitle = {Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  year = {2023}
}
```

**Source: CrossRef** ✅ Official venue and correct year

---

### 7. GPT-4 (arXiv-only)

```bash
$ bibtools fetch ARXIV:2303.08774
```

```bibtex
% paper_id: ARXIV:2303.08774
@inproceedings{openai2023,
  title = {GPT-4 Technical Report},
  author = {OpenAI,  and Achiam, Josh and Adler, Steven and ...},  # 281 authors
  booktitle = {arXiv},
  year = {2023}
}
```

**Source: arXiv** ✅ Correctly shows arXiv as venue (not published elsewhere)

---

## Comparison with Google Scholar

| Aspect | bibtools | Google Scholar |
|--------|----------|----------------|
| **Venue (DOI)** | Official from CrossRef | Often generic |
| **Venue (DBLP)** | Correct conference name | Shows "arXiv preprint" |
| **Venue (arXiv)** | "arXiv" | Shows "arXiv preprint" |
| **Year (DOI)** | ✅ Correct (CrossRef) | ✅ Correct |
| **Year (DBLP)** | ✅ Correct conference year | ⚠️ arXiv submission date |
| **Year (arXiv)** | ⚠️ arXiv submission date | ⚠️ arXiv submission date |
| **Authors** | Full list from all sources | Often truncated |
| **Pages** | ❌ Not included | ✅ Included |
| **Title case** | Title Case | lowercase |

### GS Errors That bibtools Fixes

| Paper | Google Scholar | bibtools |
|-------|----------------|----------|
| Hi Robot (2502.19417) | arXiv 2025 ❌ | ICML 2025 ✅ |
| StreamingLLM (2309.17453) | arXiv 2023 ❌ | ICLR 2024 ✅ |

### Source Priority

| Priority | Source | When Used |
|----------|--------|-----------|
| 1 | CrossRef | DOI exists |
| 2 | DBLP | No DOI, venue != arXiv |
| 3 | arXiv | venue == arXiv |

### Known Limitations

- **No page numbers**: Not included in CrossRef/DBLP/arXiv metadata.
- **Semantic Scholar coverage**: Some papers (e.g., LeCun's "Deep Learning" in Nature 2015) are not indexed.
