# Agent Maintenance and Automated Compilation Log

This file documents the automated procedures used by AI coding agents to maintain, compile, and package the paper draft **"Choosing the Second Check: Provenance-Guided Verification for AI Agents"**.

---

## 🚀 Cloud-Based LaTeX Compilation

Since local TeX distributions are not available on the execution sandbox, compilation is performed remotely using the **LaTeX.Online** open-source compiler service.

### Compilation API Details
- **Backend Service:** `LaTeX.Online` (powered by `ytotech` / `latex.ytotech.com`)
- **Compilation Endpoint:** `https://latexonline.cc/compile?url=<raw_git_url>`
- **Workflow:**
  1. The agent script `experiments/compile_via_github.py` inlines the statistical pilot parameters (`generated/stats.tex`) and the pre-built bibliography directly into the main `.tex` file to produce `paper_flat.tex`.
  2. The flattened file is committed and pushed directly to the public GitHub repository.
  3. The script retrieves the latest Git commit hash to construct a raw CDN-uncached URL: `https://raw.githubusercontent.com/Agentic-Memory-Foundation/provenance-guided-verification/<commit_hash>/paper_flat.tex`.
  4. The URL is sent to `latexonline.cc` for a double-pass compilation of `pdflatex`.
  5. The resulting binary PDF is downloaded and saved directly to `paper.pdf` in the workspace root.

---

## 📦 arXiv Submission Package (`arxiv.zip`)

To ensure the paper is always ready for immediate submission to the **arXiv** e-print repository, we provide automated packaging scripts.

### Requirements for arXiv Submission
- arXiv requires a self-contained package. No external style files should be missing, and the bibliography must be inlined since arXiv does not execute separate `bibtex` runs.
- The main LaTeX file must be named `ms.tex` or `paper.tex`.

### Automated Packaging Workflow (`experiments/build_arxiv_zip.py`)
1. Inlines statistical parameters from `generated/stats.tex`.
2. Inlines the fully formatted references block directly into the document.
3. Saves the self-contained flattened source code under the filename **`ms.tex`** (arXiv's preferred default).
4. Bundles `ms.tex` alongside the required document class **`acmart.cls`** into a compressed archive.
5. Saves the output to **`arxiv.zip`** in the repository root.
6. Automatically cleans up temporary files (`ms.tex`) to keep the workspace clean.

### How to Rebuild `arxiv.zip`
To update and rebuild the arXiv package after any edits to the paper:
```bash
python3 experiments/build_arxiv_zip.py
```
This guarantees that `arxiv.zip` at the repository root is always synchronized with your latest local edits, figures, and simulation results.
