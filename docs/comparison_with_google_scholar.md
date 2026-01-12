# Comparison: bibtools vs Google Scholar

This document compares bibtex output from bibtools and Google Scholar for the same papers.

## Test Papers

| # | Paper | GS Key | Official Source |
|---|-------|--------|-----------------|
| 1 | Hi Robot (2025) | shi2025hi | ICML OpenReview |
| 2 | DiT (2023) | peebles2023scalable | ICCV |
| 3 | HAMLET (2025) | koo2025hamlet | arXiv only |
| 4 | ResNet (2016) | he2016deep | CVPR |
| 5 | Attention (2017) | vaswani2017attention | NeurIPS |
| 6 | StreamingLLM (2023) | xiao2023efficient | ICLR OpenReview |
| 7 | Sliding Windows (2025) | liu2025sliding | ACL Anthology |

---

## 1. Hi Robot (ICML 2025)

### Google Scholar
```bibtex
@article{shi2025hi,
  title   = {Hi robot: Open-ended instruction following with hierarchical vision-language-action models},
  author  = {Shi, Lucy Xiaoyang and Ichter, Brian and Equi, Michael and ... and others},
  journal = {arXiv preprint arXiv:2502.19417},
  year    = {2025}
}
```

### bibtools
```bibtex
@inproceedings{shi2025,
  title = {Hi Robot: Open-Ended Instruction Following with Hierarchical Vision-Language-Action Models},
  author = {Shi, Lucy Xiaoyang and Ichter, Brian and Equi, Michael and Ke, Liyiming and Pertsch, Karl and Vuong, Quan and Tanner, James and Walling, Anna and Wang, Haohuan and Fusai, Niccolo and Li-Bell, Adrian and Driess, Danny and Groom, Lachy and Levine, Sergey and Finn, Chelsea},
  booktitle = {International Conference on Machine Learning},
  year = {2025}
}
```

### Comparison
| Field | Google Scholar | bibtools | Winner |
|-------|----------------|----------|--------|
| type | article (preprint) | inproceedings | ✅ bibtools |
| venue | arXiv | ICML | ✅ bibtools |
| authors | truncated ("others") | full 15 authors | ✅ bibtools |
| title case | lowercase | Title Case | ✅ bibtools |

**Result: ✅ bibtools is better** - Correctly identifies ICML publication with full author list.

---

## 2. DiT - Scalable Diffusion Models with Transformers (ICCV 2023)

### Google Scholar
```bibtex
@inproceedings{peebles2023scalable,
  title     = {Scalable diffusion models with transformers},
  author    = {Peebles, William and Xie, Saining},
  booktitle = {Proceedings of the IEEE/CVF international conference on computer vision},
  pages     = {4195--4205},
  year      = {2023}
}
```

### bibtools
```bibtex
@inproceedings{peebles2023,
  title = {Scalable Diffusion Models with Transformers},
  author = {Peebles, William and Xie, Saining},
  booktitle = {2023 IEEE/CVF International Conference on Computer Vision (ICCV)},
  year = {2023}
}
```

### Comparison
| Field | Google Scholar | bibtools | Winner |
|-------|----------------|----------|--------|
| author | William Peebles | William Peebles | Draw |
| venue | generic proceedings | official venue name | ✅ bibtools |
| pages | included | missing | ⚠️ GS |

**Result: Draw** - bibtools has better venue, GS has pages.

---

## 3. HAMLET (arXiv 2025, unpublished)

### Google Scholar
```bibtex
@article{koo2025hamlet,
  author  = {Koo, Myungkyu and ... and Seo, Younggyo and Shin, Jinwoo},
  journal = {arXiv preprint arXiv:2510.00695},
  year    = {2025}
}
```

### bibtools
```bibtex
@inproceedings{koo2025,
  author = {Koo, Myungkyu and ... and Seo, Younggyo and Shin, Jinwoo},
  booktitle = {arXiv.org},
  year = {2025}
}
```

### Comparison
| Field | Google Scholar | bibtools | Note |
|-------|----------------|----------|------|
| author spelling | Younggyo (correct) | Younggyo | Same (arXiv v1 typo) |

**Result: Draw** - Both use arXiv metadata. Note: arXiv v2 fixed "Youngyo" → "Younggyo".

---

## 4. ResNet (CVPR 2016)

### Google Scholar
```bibtex
@inproceedings{he2016deep,
  title     = {Deep residual learning for image recognition},
  author    = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  booktitle = {Proceedings of the IEEE conference on computer vision and pattern recognition},
  pages     = {770--778},
  year      = {2016}
}
```

### bibtools
```bibtex
@inproceedings{he2016,
  title = {Deep Residual Learning for Image Recognition},
  author = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  booktitle = {2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
  year = {2016}
}
```

### Comparison
| Field | Google Scholar | bibtools | Winner |
|-------|----------------|----------|--------|
| venue | generic | official with year | ✅ bibtools |
| pages | included | missing | ⚠️ GS |
| title | lowercase | Title Case | ✅ bibtools |

**Result: Draw** - bibtools has better venue/title, GS has pages.

---

## 5. Attention Is All You Need (NeurIPS 2017)

### Google Scholar
```bibtex
@article{vaswani2017attention,
  title   = {Attention is all you need},
  author  = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N and Kaiser, Lukasz and Polosukhin, Illia},
  journal = {Advances in neural information processing systems},
  volume  = {30},
  year    = {2017}
}
```

### bibtools
```bibtex
@inproceedings{vaswani2017,
  title = {Attention Is All You Need},
  author = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N. and Kaiser, Lukasz and Polosukhin, Illia},
  booktitle = {Neural Information Processing Systems},
  year = {2017}
}
```

### Comparison
| Field | Google Scholar | bibtools | Winner |
|-------|----------------|----------|--------|
| authors | full | full | Draw |
| type | article | inproceedings | ✅ bibtools |
| venue | journal style | conference style | Draw |
| volume | included | missing | ⚠️ GS |

**Result: Draw** - Both good, different styles.

---

## 6. StreamingLLM (ICLR 2024)

### Google Scholar
```bibtex
@article{xiao2023efficient,
  title   = {Efficient streaming language models with attention sinks},
  author  = {Xiao, Guangxuan and Tian, Yuandong and Chen, Beidi and Han, Song and Lewis, Mike},
  journal = {arXiv preprint arXiv:2309.17453},
  year    = {2023}
}
```

### bibtools
```bibtex
@inproceedings{xiao2023,
  title = {Efficient Streaming Language Models with Attention Sinks},
  author = {Xiao, Guangxuan and Tian, Yuandong and Chen, Beidi and Han, Song and Lewis, Mike},
  booktitle = {International Conference on Learning Representations},
  year = {2023}
}
```

### Comparison
| Field | Google Scholar | bibtools | Winner |
|-------|----------------|----------|--------|
| type | article (preprint) | inproceedings | ✅ bibtools |
| venue | arXiv | ICLR | ✅ bibtools |
| year | 2023 | 2023 | ⚠️ Both wrong (ICLR 2024) |

**Result: ✅ bibtools is better** - Correctly identifies ICLR publication. Note: year should be 2024.

---

## 7. Sliding Windows (ACL 2025)

### Google Scholar
```bibtex
@inproceedings{liu2025sliding,
  title     = {Sliding windows are not the end: Exploring full ranking with long-context large language models},
  author    = {Liu, Wenhan and Ma, Xinyu and Zhu, Yutao and Zhao, Ziliang and Wang, Shuaiqiang and Yin, Dawei and Dou, Zhicheng},
  booktitle = {Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  pages     = {162--176},
  year      = {2025}
}
```

### bibtools
```bibtex
@inproceedings{liu2025,
  title = {Sliding Windows Are Not the End: Exploring Full Ranking with Long-Context Large Language Models},
  author = {Liu, Wenhan and Ma, Xinyu and Zhu, Yutao and Zhao, Ziliang and Wang, Shuaiqiang and Yin, Dawei and Dou, Zhicheng},
  booktitle = {Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  year = {2025}
}
```

### Comparison
| Field | Google Scholar | bibtools | Winner |
|-------|----------------|----------|--------|
| venue | ACL | ACL | Draw |
| pages | included | missing | ⚠️ GS |
| title | lowercase | Title Case | ✅ bibtools |

**Result: Draw** - Both correct, GS has pages.

---

## Summary

| Paper | Winner | Reason |
|-------|--------|--------|
| Hi Robot | ✅ bibtools | ICML instead of arXiv |
| DiT | Draw | bibtools: venue, GS: pages |
| HAMLET | Draw | Both use arXiv |
| ResNet | Draw | bibtools: venue, GS: pages |
| Attention | Draw | Both good |
| StreamingLLM | ✅ bibtools | ICLR instead of arXiv |
| Sliding Windows | Draw | Both correct |

### Key Findings

**bibtools advantages:**
- Detects conference publications from arXiv papers (via Semantic Scholar venue)
- Uses official venue names from CrossRef
- Provides full author lists without truncation

**Google Scholar advantages:**
- Includes page numbers
- Sometimes has more up-to-date arXiv versions (typo fixes)

**Common issues with both:**
- Year may reflect arXiv submission, not conference year
