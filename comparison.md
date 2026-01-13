# BibTeX Source Comparison

Comparison of BibTeX from **Google Scholar**, **Official sources**, and **bibtools**.

## Summary

**Google Scholar often has wrong venue/year for arXiv papers that were later published at conferences.** Out of 9 test papers, GS had critical errors in 2 cases (StreamingLLM, Hi Robot) where it showed "arXiv" instead of the actual conference. GS also uses lowercase titles and sometimes fabricates metadata (LoRA's fake volume/number/pages).

**Official sources are always correct** but require manual effort to find the right publisher page.

**bibtools matches official sources** for venue and year in all cases where the paper is indexed in Semantic Scholar. It automates what would otherwise require visiting multiple publisher sites.

| Paper | Venue | GS | Official | bibtools |
|-------|-------|:--:|:--------:|:--------:|
| Deep Learning | Nature 2015 | ✓ | ✓ | - |
| Deep Residual Learning for Image Recognition | CVPR 2016 | ✓ | ✓ | ✓ |
| Attention Is All You Need | NeurIPS 2017 | ✓ | ✓ | ✓ |
| LoRA: Low-Rank Adaptation of Large Language Models | ICLR 2022 | ✓ | ✓ | ✓ |
| Scalable Diffusion Models with Transformers | ICCV 2023 | ✓ | ✓ | ✓ |
| Efficient Streaming Language Models with Attention Sinks | ICLR 2024 | ✗ arXiv 2023 | ✓ | ✓ |
| HAMLET | arXiv 2025 | ✓ | ✓ | ✓ |
| Hi Robot | ICML 2025 | ✗ arXiv | ✓ | ✓ |
| Sliding Windows Are Not the End | ACL 2025 | ✓ | ✓ | ✓ |

---

## Detailed Comparison

### 1. Deep Learning (Nature 2015)

| | Google Scholar | Official | bibtools |
|-|----------------|----------|----------|
| title | Deep learning | Deep Learning | - |
| author | LeCun, Yann and ... | LeCun, Yann and ... | - |
| venue | nature | Nature | - |
| year | 2015 | 2015 | - |

bibtools: Not indexed in Semantic Scholar.

---

### 2. ResNet (CVPR 2016)

| | Google Scholar | Official | bibtools |
|-|----------------|----------|----------|
| title | Deep residual learning... | Deep Residual Learning... | Deep Residual Learning... |
| author | He, Kaiming and ... | He, Kaiming and ... | He, Kaiming and ... |
| venue | Proceedings of the IEEE conference... | CVPR | 2016 IEEE CVPR |
| year | 2016 | 2016 | 2016 |

---

### 3. Attention Is All You Need (NeurIPS 2017)

| | Google Scholar | Official | bibtools |
|-|----------------|----------|----------|
| title | Attention is all you need | Attention is All you Need | Attention is All you Need |
| author | Vaswani, Ashish and ... | Vaswani, Ashish and ... | Vaswani, Ashish and ... |
| venue | Advances in neural information... | Advances in Neural Information... | NIPS |
| year | 2017 | 2017 | 2017 |

---

### 4. LoRA (ICLR 2022)

| | Google Scholar | Official | bibtools |
|-|----------------|----------|----------|
| title | Lora: Low-rank adaptation... | LoRA: Low-Rank Adaptation... | LoRA: Low-Rank Adaptation... |
| author | Hu, Edward J and ... others | Edward J Hu and ... | Hu, Edward J. and ... |
| venue | ICLR (as @article) | International Conference on Learning Representations | ICLR |
| year | 2022 | 2022 | 2022 |

GS uses `@article` with fake volume=1, number=2, pages=3.

---

### 5. DiT (ICCV 2023)

| | Google Scholar | Official | bibtools |
|-|----------------|----------|----------|
| title | Scalable diffusion models... | Scalable Diffusion Models... | Scalable Diffusion Models... |
| author | Peebles, William and ... | Peebles, William and ... | Peebles, William and ... |
| venue | Proceedings of the IEEE/CVF... | ICCV | 2023 IEEE/CVF ICCV |
| year | 2023 | 2023 | 2023 |

---

### 6. StreamingLLM (ICLR 2024) ⚠️

| | Google Scholar | Official | bibtools |
|-|----------------|----------|----------|
| title | Efficient streaming... | Efficient Streaming... | Efficient Streaming... |
| author | Xiao, Guangxuan and ... | Guangxuan Xiao and ... | Xiao, Guangxuan and ... |
| venue | **arXiv preprint** ❌ | ICLR | ICLR |
| year | **2023** ❌ | 2024 | 2024 |

**GS shows arXiv 2023, but the paper was published at ICLR 2024.**

---

### 7. HAMLET (arXiv 2025)

| | Google Scholar | Official | bibtools |
|-|----------------|----------|----------|
| title | HAMLET: Switch your... | HAMLET: Switch your... | HAMLET: Switch your... |
| author | Koo, Myungkyu and ... | Myungkyu Koo and ... | Koo, Myungkyu and ... |
| venue | arXiv preprint | arXiv | arXiv |
| year | 2025 | 2025 | 2025 |

All sources agree (paper is arXiv-only).

---

### 8. Hi Robot (ICML 2025) ⚠️

| | Google Scholar | Official | bibtools |
|-|----------------|----------|----------|
| title | Hi robot: Open-ended... | Hi Robot: Open-Ended... | Hi Robot: Open-Ended... |
| author | Shi, Lucy Xiaoyang and ... others | Lucy Xiaoyang Shi and ... | Shi, Lucy Xiaoyang and ... |
| venue | **arXiv preprint** ❌ | ICML | ICML |
| year | 2025 | 2025 | 2025 |

**GS shows arXiv, but the paper was accepted at ICML 2025.**

---

### 9. Sliding Windows (ACL 2025)

| | Google Scholar | Official | bibtools |
|-|----------------|----------|----------|
| title | Sliding windows are not... | Sliding Windows Are Not... | Sliding Windows Are Not... |
| author | Liu, Wenhan and ... | Liu, Wenhan and ... | Liu, Wenhan and ... |
| venue | Proceedings of the 63rd ACL... | Proceedings of the 63rd ACL... | Proceedings of the 63rd ACL... |
| year | 2025 | 2025 | 2025 |

---

## Common Google Scholar Errors

1. **Wrong venue**: Shows "arXiv preprint" for conference papers (StreamingLLM, Hi Robot)
2. **Wrong year**: Shows arXiv submission year instead of publication year
3. **Wrong type**: Uses `@article` for conference papers
4. **Fake metadata**: Invents volume/number/pages (LoRA)
5. **Lowercase titles**: Does not preserve title case
6. **Author truncation**: Uses "and others" instead of full list

