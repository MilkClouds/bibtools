# Comparison: bibtools vs Google Scholar

## Summary

| Paper | Source | Winner | Key Difference |
|-------|--------|--------|----------------|
| ResNet (CVPR 2016) | CrossRef | Draw | bibtools: official venue, GS: pages |
| Attention (NeurIPS 2017) | arXiv | ⚠️ Note | SS returns arXiv DBLP key → skip |
| LoRA (ICLR 2022) | DBLP | ✅ bibtools | Correct year (2022) and venue (ICLR) |
| StreamingLLM (ICLR 2024) | arXiv | ⚠️ Note | DBLP search fails → arXiv fallback |
| Self-Instruct (ACL 2023) | arXiv | ⚠️ Note | SS returns arXiv DBLP key → skip |
| ACL Paper (ACL 2023) | CrossRef | ✅ bibtools | Full official metadata from CrossRef |

### Key Findings

**bibtools advantages:**
- **CrossRef (DOI)**: Official venue names and correct publication years
- **DBLP**: Correct venue/year for DOI-less conferences (ICLR, some NeurIPS)
- **arXiv**: Full author lists without truncation

**bibtools limitations:**
- **arXiv fallback**: When DBLP lookup fails, year is arXiv submission date
- No page numbers (not in metadata)
- Some papers have SS returning arXiv DBLP key instead of conference key

**Recommendation:**
- bibtools automatically uses the best source available (DOI > DBLP > arXiv)
- ICLR papers now get correct year/venue via DBLP

---

## Data Sources

bibtools uses **official sources only** with single source of truth principle:

| Priority | Source | Used When | Provides |
|----------|--------|-----------|----------|
| 1 | **CrossRef** | DOI exists | Official venue, year, authors |
| 2 | **DBLP** | No DOI, DBLP ID exists | Conference venue, year, authors |
| 3 | **arXiv** | No DOI or DBLP | Preprint metadata |

- **Semantic Scholar** - Only for ID resolution (DOI/arXiv/DBLP ID extraction)

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

### 2. Attention Is All You Need (NeurIPS 2017) - via arXiv

```bash
$ bibtools fetch 1706.03762
```

```bibtex
% paper_id: 1706.03762
@inproceedings{vaswani2017,
  title = {Attention Is All You Need},
  author = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N. and Kaiser, Lukasz and Polosukhin, Illia},
  booktitle = {arXiv},
  year = {2017}
}
```

**Source: arXiv** ⚠️ No DOI or DBLP ID from SS → arXiv fallback (venue shows "arXiv")

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

### 4. StreamingLLM (ICLR 2024) - via arXiv (DBLP search failed)

```bash
$ bibtools fetch 2309.17453
```

```bibtex
% paper_id: 2309.17453
@inproceedings{xiao2023,
  title = {Efficient Streaming Language Models with Attention Sinks},
  author = {Xiao, Guangxuan and Tian, Yuandong and Chen, Beidi and Han, Song and Lewis, Mike},
  booktitle = {arXiv},
  year = {2023}
}
```

**Source: arXiv** ⚠️ SS returns valid DBLP key but DBLP search fails → arXiv fallback

---

### 5. Self-Instruct (ACL 2023) - via arXiv (arXiv DBLP key)

```bash
$ bibtools fetch 2212.10560
```

```bibtex
% paper_id: 2212.10560
@inproceedings{wang2022,
  title = {Self-Instruct: Aligning Language Models with Self-Generated Instructions},
  author = {Wang, Yizhong and Kordi, Yeganeh and Mishra, Swaroop and Liu, Alisa and Smith, Noah A. and Khashabi, Daniel and Hajishirzi, Hannaneh},
  booktitle = {arXiv},
  year = {2022}
}
```

**Source: arXiv** ⚠️ SS returns `journals/corr/...` DBLP key (arXiv preprint) → skipped

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

### Source Priority

bibtools automatically selects the best available source:

| Priority | Source | When Used | Example |
|----------|--------|-----------|---------|
| 1 | CrossRef | DOI exists | Most ACL, NeurIPS papers |
| 2 | DBLP | No DOI, DBLP ID exists | ICLR papers |
| 3 | arXiv | No DOI or DBLP | Preprints, SS returning arXiv DBLP key |

### Known Limitations

- **arXiv DBLP key**: SS sometimes returns the arXiv version DBLP key (`journals/corr/...`) instead of the conference version. bibtools skips these and falls back to arXiv.
- **DBLP search**: Even with valid DBLP key, the search query may not find the paper. This is being improved.
- **No page numbers**: Page numbers are not included in CrossRef/DBLP/arXiv metadata.
