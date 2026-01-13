# BibTeX Source Comparison: Google Scholar vs Official vs bibtools

This document compares BibTeX entries from three sources:
- **Google Scholar (GS)**: Auto-generated, often inaccurate
- **Official**: From publishers/conferences (Nature, CVF, NeurIPS, OpenReview, ACL Anthology)
- **bibtools**: Generated from CrossRef (DOI) / DBLP (venue) / arXiv

## Summary Table

| Paper | Year | GS Venue | Official Venue | bibtools Venue | Winner |
|-------|------|----------|----------------|----------------|--------|
| Deep Learning | 2015 | nature | Nature | (not indexed) | Official |
| ResNet | 2016 | CVPR (generic) | CVPR | CVPR (IEEE) | Official ≈ bibtools |
| Attention | 2017 | NeurIPS (generic) | NeurIPS | NIPS (DBLP) | Official |
| LoRA | 2022 | ICLR (wrong format) | ICLR | ICLR (DBLP) | Official ≈ bibtools |
| DiT | 2023 | ICCV (generic) | ICCV | ICCV (IEEE) | Official ≈ bibtools |
| StreamingLLM | 2023→2024 | arXiv 2023 ❌ | ICLR 2024 | ICLR 2024 | Official = bibtools |
| HAMLET | 2025 | arXiv | arXiv | arXiv | All same |
| Hi Robot | 2025 | arXiv ❌ | ICML 2025 | ICML 2025 | Official = bibtools |
| Sliding Windows | 2025 | ACL | ACL | ACL (CrossRef) | All same |

### Key Findings

| Source | Pros | Cons |
|--------|------|------|
| **Google Scholar** | Easy to get | Wrong venue/year for arXiv→conf papers, generic venue names, lowercase titles |
| **Official** | Correct metadata, DOI/URL included | Manual effort to find |
| **bibtools** | Automated + correct venue/year | Some papers not indexed in Semantic Scholar |

---

## Detailed Comparison

### 1. Deep Learning (Nature 2015)

**Google Scholar:**
```bibtex
@article{lecun2015deep,
  title     = {Deep learning},
  author    = {LeCun, Yann and Bengio, Yoshua and Hinton, Geoffrey},
  journal   = {nature},
  volume    = {521},
  number    = {7553},
  pages     = {436--444},
  year      = {2015},
  publisher = {Nature Publishing Group UK London}
}
```

**Official (Nature):**
```bibtex
@article{lecunDeepLearning2015,
  title    = {Deep Learning},
  author   = {LeCun, Yann and Bengio, Yoshua and Hinton, Geoffrey},
  journal  = {Nature},
  volume   = {521},
  number   = {7553},
  pages    = {436--444},
  year     = {2015},
  doi      = {10.1038/nature14539}
}
```

**bibtools:** Not indexed in Semantic Scholar

| Field | GS | Official | bibtools |
|-------|-------|----------|----------|
| Title | lowercase | Title Case ✅ | - |
| Journal | "nature" | "Nature" ✅ | - |
| DOI | ❌ | ✅ | - |

---

### 2. ResNet (CVPR 2016)

**Google Scholar:**
```bibtex
@inproceedings{he2016deep,
  title     = {Deep residual learning for image recognition},
  author    = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  booktitle = {Proceedings of the IEEE conference on computer vision and pattern recognition},
  pages     = {770--778},
  year      = {2016}
}
```

**Official (CVF):**
```bibtex
@inproceedings{He_2016_CVPR,
  author    = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  title     = {Deep Residual Learning for Image Recognition},
  booktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
  month     = {June},
  year      = {2016}
}
```

**bibtools (CrossRef):**
```bibtex
% paper_id: DOI:10.1109/CVPR.2016.90
@inproceedings{he2016,
  title = {Deep Residual Learning for Image Recognition},
  author = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  booktitle = {2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
  year = {2016}
}
```

| Field | GS | Official | bibtools |
|-------|-------|----------|----------|
| Title | lowercase | Title Case ✅ | Title Case ✅ |
| Venue | generic | CVPR ✅ | IEEE CVPR ✅ |
| Pages | ✅ | ❌ | ❌ |

---

### 3. Attention Is All You Need (NeurIPS 2017)

**Google Scholar:**
```bibtex
@article{vaswani2017attention,
  title   = {Attention is all you need},
  author  = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and ...},
  journal = {Advances in neural information processing systems},
  volume  = {30},
  year    = {2017}
}
```

**Official (NeurIPS):**
```bibtex
@inproceedings{NIPS2017_3f5ee243,
  author    = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and ...},
  booktitle = {Advances in Neural Information Processing Systems},
  title     = {Attention is All you Need},
  volume    = {30},
  year      = {2017},
  url       = {https://proceedings.neurips.cc/paper_files/paper/2017/...}
}
```

**bibtools (DBLP):**
```bibtex
% paper_id: 1706.03762
@inproceedings{vaswani2017,
  title = {Attention is All you Need},
  author = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and ...},
  booktitle = {NIPS},
  year = {2017}
}
```

| Field | GS | Official | bibtools |
|-------|-------|----------|----------|
| Type | article ❌ | inproceedings ✅ | inproceedings ✅ |
| Venue | generic | NeurIPS ✅ | NIPS ✅ |
| URL | ❌ | ✅ | ❌ |

---

### 4. LoRA (ICLR 2022)

**Google Scholar:**
```bibtex
@article{hu2022lora,
  title   = {Lora: Low-rank adaptation of large language models.},
  author  = {Hu, Edward J and Shen, Yelong and Wallis, Phillip and ... and others},
  journal = {ICLR},
  volume  = {1},
  number  = {2},
  pages   = {3},
  year    = {2022}
}
```

**Official (OpenReview):**
```bibtex
@inproceedings{hu2022lora,
  title     = {Lo{RA}: Low-Rank Adaptation of Large Language Models},
  author    = {Edward J Hu and yelong shen and Phillip Wallis and ...},
  booktitle = {International Conference on Learning Representations},
  year      = {2022},
  url       = {https://openreview.net/forum?id=nZeVKeeFYf9}
}
```

**bibtools (DBLP):**
```bibtex
% paper_id: 2106.09685
@inproceedings{hu2022,
  title = {LoRA: Low-Rank Adaptation of Large Language Models},
  author = {Hu, Edward J. and Shen, Yelong and Wallis, Phillip and ...},
  booktitle = {ICLR},
  year = {2022}
}
```

| Field | GS | Official | bibtools |
|-------|-------|----------|----------|
| Type | article ❌ | inproceedings ✅ | inproceedings ✅ |
| Title | trailing period ❌ | ✅ | ✅ |
| Venue | "ICLR" as journal ❌ | ICLR ✅ | ICLR ✅ |
| volume/number/pages | fake values ❌ | ❌ | ❌ |

---

### 5. DiT (ICCV 2023)

**Google Scholar:**
```bibtex
@inproceedings{peebles2023scalable,
  title     = {Scalable diffusion models with transformers},
  author    = {Peebles, William and Xie, Saining},
  booktitle = {Proceedings of the IEEE/CVF international conference on computer vision},
  pages     = {4195--4205},
  year      = {2023}
}
```

**Official (CVF):**
```bibtex
@inproceedings{Peebles_2023_ICCV,
  author    = {Peebles, William and Xie, Saining},
  title     = {Scalable Diffusion Models with Transformers},
  booktitle = {Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)},
  month     = {October},
  year      = {2023},
  pages     = {4195-4205}
}
```

**bibtools (CrossRef):**
```bibtex
% paper_id: DOI:10.1109/ICCV51070.2023.00387
@inproceedings{peebles2023,
  title = {Scalable Diffusion Models with Transformers},
  author = {Peebles, William and Xie, Saining},
  booktitle = {2023 IEEE/CVF International Conference on Computer Vision (ICCV)},
  year = {2023}
}
```

| Field | GS | Official | bibtools |
|-------|-------|----------|----------|
| Title | lowercase | Title Case ✅ | Title Case ✅ |
| Venue | generic | ICCV ✅ | IEEE ICCV ✅ |
| Pages | ✅ | ✅ | ❌ |

---

### 6. StreamingLLM (ICLR 2024) ⚠️ GS Error

**Google Scholar:**
```bibtex
@article{xiao2023efficient,
  title   = {Efficient streaming language models with attention sinks},
  author  = {Xiao, Guangxuan and Tian, Yuandong and Chen, Beidi and Han, Song and Lewis, Mike},
  journal = {arXiv preprint arXiv:2309.17453},
  year    = {2023}
}
```

**Official (OpenReview):**
```bibtex
@inproceedings{xiao2024efficient,
  title     = {Efficient Streaming Language Models with Attention Sinks},
  author    = {Guangxuan Xiao and Yuandong Tian and Beidi Chen and Song Han and Mike Lewis},
  booktitle = {The Twelfth International Conference on Learning Representations},
  year      = {2024},
  url       = {https://openreview.net/forum?id=NG7sS51zVF}
}
```

**bibtools (DBLP):**
```bibtex
% paper_id: 2309.17453
@inproceedings{xiao2024,
  title = {Efficient Streaming Language Models with Attention Sinks},
  author = {Xiao, Guangxuan and Tian, Yuandong and Chen, Beidi and Han, Song and Lewis, Mike},
  booktitle = {ICLR},
  year = {2024}
}
```

| Field | GS | Official | bibtools |
|-------|-------|----------|----------|
| Year | 2023 ❌ | 2024 ✅ | 2024 ✅ |
| Venue | arXiv ❌ | ICLR ✅ | ICLR ✅ |
| Type | article ❌ | inproceedings ✅ | inproceedings ✅ |

**⚠️ Google Scholar shows arXiv 2023, but the paper was published at ICLR 2024!**

---

### 7. HAMLET (arXiv 2025)

**Google Scholar:**
```bibtex
@article{koo2025hamlet,
  title   = {HAMLET: Switch your Vision-Language-Action Model into a History-Aware Policy},
  author  = {Koo, Myungkyu and Choi, Daewon and Kim, Taeyoung and ...},
  journal = {arXiv preprint arXiv:2510.00695},
  year    = {2025}
}
```

**Official (arXiv):**
```bibtex
@misc{koo2025hamlet,
  title         = {HAMLET: Switch your Vision-Language-Action Model into a History-Aware Policy},
  author        = {Myungkyu Koo and Daewon Choi and Taeyoung Kim and ...},
  year          = {2025},
  eprint        = {2510.00695},
  archiveprefix = {arXiv},
  primaryclass  = {cs.RO}
}
```

**bibtools (arXiv):**
```bibtex
% paper_id: 2510.00695
@misc{koo2025,
  title = {HAMLET: Switch your Vision-Language-Action Model into a History-Aware Policy},
  author = {Koo, Myungkyu and Choi, Daewon and Kim, Taeyoung and ...},
  year = {2025},
  eprint = {2510.00695},
  archiveprefix = {arXiv}
}
```

All sources agree - paper is on arXiv (not yet published at conference).

---

### 8. Hi Robot (ICML 2025) ⚠️ GS Error

**Google Scholar:**
```bibtex
@article{shi2025hi,
  title   = {Hi robot: Open-ended instruction following with hierarchical vision-language-action models},
  author  = {Shi, Lucy Xiaoyang and Ichter, Brian and ... and others},
  journal = {arXiv preprint arXiv:2502.19417},
  year    = {2025}
}
```

**Official (OpenReview/ICML):**
```bibtex
@inproceedings{shi2025hi,
  title     = {Hi Robot: Open-Ended Instruction Following with Hierarchical Vision-Language-Action Models},
  author    = {Lucy Xiaoyang Shi and brian ichter and Michael Robert Equi and ...},
  booktitle = {Forty-second International Conference on Machine Learning},
  year      = {2025},
  url       = {https://openreview.net/forum?id=lNVHg9npif}
}
```

**bibtools (DBLP):**
```bibtex
% paper_id: 2502.19417
@inproceedings{shi2025,
  title = {Hi Robot: Open-Ended Instruction Following with Hierarchical Vision-Language-Action Models},
  author = {Shi, Lucy Xiaoyang and Ichter, Brian and Equi, Michael and ...},
  booktitle = {ICML},
  year = {2025}
}
```

| Field | GS | Official | bibtools |
|-------|-------|----------|----------|
| Venue | arXiv ❌ | ICML ✅ | ICML ✅ |
| Type | article ❌ | inproceedings ✅ | inproceedings ✅ |
| Authors | truncated "others" | full list | full list |

**⚠️ Google Scholar shows arXiv, but the paper was accepted at ICML 2025!**

---

### 9. Sliding Windows (ACL 2025)

**Google Scholar:**
```bibtex
@inproceedings{liu2025sliding,
  title     = {Sliding windows are not the end: Exploring full ranking with long-context large language models},
  author    = {Liu, Wenhan and Ma, Xinyu and Zhu, Yutao and ...},
  booktitle = {Proceedings of the 63rd Annual Meeting of the ACL (Volume 1: Long Papers)},
  pages     = {162--176},
  year      = {2025}
}
```

**Official (ACL Anthology):**
```bibtex
@inproceedings{liu-etal-2025-sliding,
  title     = {Sliding Windows Are Not the End: Exploring Full Ranking with Long-Context Large Language Models},
  author    = {Liu, Wenhan and Ma, Xinyu and Zhu, Yutao and ...},
  booktitle = {Proceedings of the 63rd Annual Meeting of the ACL (Volume 1: Long Papers)},
  year      = {2025},
  doi       = {10.18653/v1/2025.acl-long.8},
  pages     = {162--176}
}
```

**bibtools (CrossRef):**
```bibtex
% paper_id: DOI:10.18653/v1/2025.acl-long.8
@inproceedings{liu2025,
  title = {Sliding Windows Are Not the End: Exploring Full Ranking with Long-Context Large Language Models},
  author = {Liu, Wenhan and Ma, Xinyu and Zhu, Yutao and ...},
  booktitle = {Proceedings of the 63rd Annual Meeting of the ACL (Volume 1: Long Papers)},
  year = {2025}
}
```

| Field | GS | Official | bibtools |
|-------|-------|----------|----------|
| Title | lowercase | Title Case ✅ | Title Case ✅ |
| DOI | ❌ | ✅ | from input |
| Pages | ✅ | ✅ | ❌ |

---

## Conclusion

### When to use each source

| Use Case | Recommended Source |
|----------|-------------------|
| Quick draft | Google Scholar (but verify!) |
| Final paper | Official (from publisher) |
| Bulk processing | bibtools (automated + accurate) |

### Common Google Scholar Errors

1. **Wrong year**: Shows arXiv year instead of conference year
2. **Wrong venue**: Shows "arXiv preprint" for published papers
3. **Wrong type**: Uses `@article` for conference papers
4. **Fake metadata**: Invents volume/number/pages (see LoRA)
5. **Lowercase titles**: Does not preserve title case
6. **Author truncation**: Uses "and others" instead of full list

### bibtools Advantages

- ✅ Correct venue and year from DBLP/CrossRef
- ✅ Automated verification against official sources
- ✅ Title case preserved
- ✅ Full author lists
- ✅ paper_id tracking for re-verification

### bibtools Limitations

- ❌ Some papers not indexed in Semantic Scholar
- ❌ No page numbers from CrossRef/DBLP
- ❌ DBLP may use abbreviated venue names (NIPS vs NeurIPS)

