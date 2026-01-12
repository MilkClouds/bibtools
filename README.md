# bibtools

Bibtex verification tool using Semantic Scholar as ground truth.

## Installation

```bash
cd tools/bibtools && uv tool install .
```

## Quick Start

```bash
bibtools verify main.bib              # Verify entries (modifies in-place)
bibtools verify main.bib --dry-run    # Preview only
bibtools fetch ARXIV:2106.15928       # Fetch bibtex by ID
bibtools search "Attention Is All You Need"  # Search and generate bibtex
```

## Commands

### verify

Verifies bibtex entries against Semantic Scholar.

```bash
bibtools verify main.bib                      # Default: --auto-find=id
bibtools verify main.bib --auto-find=none     # Strict: comment only
bibtools verify main.bib --auto-find=none --fix  # Fix mode
```

### fetch

Fetches bibtex by paper ID.

```bash
bibtools fetch ARXIV:2106.15928
bibtools fetch DOI:10.18653/v1/N18-3011
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

### Author Name Enhancement

Semantic Scholar often returns abbreviated names (e.g., `A. Vaswani`). bibtools enhances these via external APIs:

**Priority:**
1. CrossRef (via DOI) - most reliable for published papers
2. arXiv API - for preprints
3. Fallback - format only

**Validation before applying:**
1. Author count must be identical
2. Family names must match in exact order (case-insensitive)

```
Original:  ["A. Vaswani", "N. Shazeer", ...]
Enhanced:  ["Ashish Vaswani", "Noam Shazeer", ...]

Validation:
  Count: 8 == 8 ✓
  Family names: Vaswani==Vaswani ✓, Shazeer==Shazeer ✓, ...
  → Applied
```

If validation fails, enhancement is rejected and the next source is tried.

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


## Comparison with google scholar bibtex

- hirobot2025: better(google scholar: arxiv, bibtools: icml)
- peebles2022dit: worse(William Peebles vs William S. Peebles)
- hamlet2025: worse(google scholar: Younggyo Seo(fix typo on arxiv v2) vs Youngyo Seo)
