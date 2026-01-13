# bibtools

**Automated bibtex verification tool** - validates your bibtex entries against official sources (CrossRef, arXiv).

## What it does

1. **verify** - Compare existing .bib entries against official metadata
2. **fetch** - Generate bibtex from DOI or arXiv ID
3. **search** - Search papers by title and generate bibtex

## How it works

```
bibtools verify main.bib
        ↓
Extract paper_id (DOI/arXiv ID) from each entry
        ↓
Semantic Scholar → Resolve to DOI/arXiv ID/DBLP ID
        ↓
CrossRef (DOI) → DBLP (no DOI) → arXiv (preprint)
        ↓
Compare with existing entry → PASS / WARNING / FAIL
```

**Data sources (Single Source of Truth):**

| Priority | Source | When Used | Provides |
|----------|--------|-----------|----------|
| 1 | **CrossRef** | DOI exists | Official venue, year, authors |
| 2 | **DBLP** | No DOI, DBLP ID exists | Conference venue, year (e.g., ICLR) |
| 3 | **arXiv** | No DOI or DBLP | Preprint metadata |

- **Semantic Scholar** - ID resolution only (paper_id → DOI/arXiv ID/DBLP ID)

## Is it reliable?

bibtools does **NOT generate or guess metadata**.
It uses data from official sources only:
- **CrossRef** - Official DOI registry (publisher-submitted)
- **DBLP** - Computer science bibliography (for venues without DOI like ICLR)
- **arXiv** - Preprint source

Semantic Scholar is used only for identifier resolution, not as a metadata source.

→ [Comparison with Google Scholar](docs/comparison_with_google_scholar.md)

---

## Installation

```bash
uv tool install git+https://github.com/MilkClouds/bibtools
```

## Quick Start

```bash
bibtools fetch 2106.09685             # LoRA - auto-detects arXiv ID, gets ICLR 2022 from DBLP
bibtools fetch DOI:10.1109/CVPR.2016.90  # Fetch by DOI
bibtools verify main.bib              # Verify existing entries
bibtools search "Attention Is All You Need"  # Search (use with caution)
```

## Commands

### verify

Verifies bibtex entries against official metadata from CrossRef/DBLP/arXiv.

```bash
bibtools verify main.bib                      # Default: --auto-find=id
bibtools verify main.bib --auto-find=none     # Strict: comment only
bibtools verify main.bib --auto-find=none --fix  # Fix mode
```

### fetch

Fetches bibtex by paper ID. Metadata from CrossRef (DOI) → DBLP → arXiv.

```bash
bibtools fetch 2106.09685                    # LoRA - DBLP (ICLR 2022)
bibtools fetch DOI:10.18653/v1/N18-3011      # CrossRef (ACL)
bibtools fetch DOI:10.1109/CVPR.2016.90      # CrossRef (CVPR)
bibtools fetch ARXIV:2303.08774              # arXiv (GPT-4 - preprint)
```

### search

Searches papers and generates bibtex. **Use with caution** - results may not match your intended paper.

```bash
bibtools search "Attention Is All You Need" --limit 3
```

## Verification Logic

### Status: PASS / WARNING / FAIL

| Status | Exit | Meaning |
|--------|------|---------|
| **PASS** | 0 | All fields match |
| **WARNING** | 1 | Tolerable mismatch (format/case differs) |
| **FAIL** | 2 | Content mismatch or error |

Overall result = worst individual status.

### Field Comparison

| Field | PASS | WARNING | FAIL |
|-------|------|---------|------|
| **title** | Exact match | Case/braces differ | Content mismatch |
| **author** | Exact match | Format differs | Content mismatch |
| **year** | Exact match | - | Mismatch |
| **venue** | Exact match | Alias match | Mismatch |

Examples:
- `{Deep Learning}` vs `Deep Learning` → WARNING (braces)
- `Smith, John` vs `John Smith` → WARNING (format)
- `M. Posner` vs `Michael Posner` → FAIL (abbreviation = content change)
- `NeurIPS` vs `Neural Information Processing Systems` → WARNING (alias)

## Comment Format

```bibtex
% paper_id: ARXIV:2106.15928, verified via bibtools (2025.01.06)
@inproceedings{example2024,
  title = {Example Paper},
  ...
}
```

States:
- `% paper_id: ARXIV:xxx` - unverified
- `% paper_id: ARXIV:xxx, verified via bibtools (YYYY.MM.DD)` - tool verified
- `% paper_id: DOI:xxx, verified via human(Name) (YYYY.MM.DD)` - human verified

Only PASS results are marked as verified.

## Auto-find Levels

| Level | Sources | Use case |
|-------|---------|----------|
| `none` | `% paper_id:` comment only | Strict, required for `--fix` |
| `id` | comment > `doi` > `eprint` | Default |
| `title` | Above + title search | Risky |

Auto-found paper_id is written only on PASS.

## Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview without modifying |
| `--auto-find=none/id/title` | Paper ID discovery (default: id) |
| `--fix` | Auto-correct (requires --auto-find=none) |
| `--reverify` | Re-verify verified entries |
| `--max-age=N` | Re-verify entries older than N days |
| `-o FILE` | Output to different file |
| `--api-key` | Semantic Scholar API key |

## Supported Paper IDs

- `ARXIV:2106.15928`
- `DOI:10.18653/v1/N18-3011`
- `CorpusId:215416146`
- `ACL:W12-3903`
- `PMID:19872477`

## Rate Limits

| API | Limit | Implementation |
|-----|-------|----------------|
| Semantic Scholar | 1 req/sec (with key), 100 req/5min (no key) | 1s or 3s interval |
| CrossRef | 50 req/sec (official) | 0.02s interval (50 req/sec) |
| arXiv | No official limit | No throttling |

Set `SEMANTIC_SCHOLAR_API_KEY` environment variable or use `--api-key` for faster requests.
