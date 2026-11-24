# Choosing the Second Check: Provenance-Guided Verification for AI Agents

Empirical follow-up study and paper draft expanding on the foundational concept of **Shared Blindness in Agentic AI**.

## Working Title
**“Choosing the Second Check: Provenance-Guided Verification for AI Agents”**

## Authors
- **Parag Paul** (RigAi / Agentic Memory Foundation)
- **Saurabh Sarkar** (Chicory AI / Agentic Memory Foundation)

---

## 1. Executive Summary & Contributions

This paper investigates whether an autonomous agent system can dynamically select a verification path to catch failures that are highly likely to survive its first execution pass. Instead of standardizing on a single, static reviewer panel or randomly allocating human reviewers, the proposed **Provenance-Guided Verification (PGV)** framework leverages the primary agent’s execution trace—such as policy version citations, source coverage, and mathematical operational logs—to predict and route cases to specialized complementary verifiers.

### Core Contributions
1. **Dynamic Routing Paradigm:** Shifting the focus from static, general-purpose multi-agent panels to per-case dynamic selection among complementary specialized checkers, guided by execution history.
2. **Mathematical Formalization:** Modeling PGV as a bounded decision problem with an action set containing `Retain`, `Invoke B`, `Invoke C`, and `Defer`.
3. **Auditable Experimental Design:** Specifying the **Policy-to-Record Reconciliation** domain, representing a high-stakes compliance environment containing clean/stale policies, arithmetic discrepancies, and unresolvable omissions.
4. **Escalation-Routing Separation:** Separating the binary decision to escalate from the choice of verifier to ensure a clean, paired-case comparison of routing strategies.
5. **Causal Ablation:** Outlining a controlled comparison to isolate the performance impact of specialized reasoning procedures from simple source-access/information asymmetry.

---

## 2. Repository Structure

```
.
├── paper.tex                  # Standard double-column ACM SIGCONF LaTeX draft
├── references.bib             # LaTeX Bibliography file containing 18 verified entries
├── acmart.cls                 # ACM Reference Document Class (copied from shared-blindness)
├── ACM-Reference-Format.bst   # ACM Bibliography Style File (copied from shared-blindness)
├── Makefile                   # Automation script for simulation and compilation
├── README.md                  # Project overview, submission plan, and guide (this file)
├── experiments/
│   └── simulation.py          # Python simulation script implementing the study pilot
└── generated/
    └── stats.tex              # Dynamically generated LaTeX statistical macros
```

---

## 3. Concrete, Runnable Study Design

To prove the feasibility of the study design, we have implemented a **statistical pilot simulation** in `experiments/simulation.py`.

### The Simulation Mechanics
The script simulates a corpus of 10,000 reconciliation cases split across five categories:
- **Clean Cases (50%):** Standard cases where calculations and policies align.
- **Stale Policy Versions (15%):** Induces temporal mismatches. Primary Agent A has a 65% failure rate here, but Verifier B (policy-first temporal specialist) recovers 90% of those failures.
- **Record Discrepancy (15%):** Induces mathematical errors. Primary Agent A has a 55% failure rate, but Verifier C (computational ledger specialist) recovers 95% of those failures.
- **Conflicting Evidence (10%):** Standard evidentiary conflicts.
- **Shared Omissions (10%):** Complete omissions where the receipt is corrupted/blank. Both specialists fail (0% recovery), forcing the selector to choose `Defer` (route to human).

### Statistical Sizing & Pilot
Using a pilot split ($N_{\text{pilot}} = 100$ cases where Agent A failed), the script identifies **discordant cases** (where exactly one verifier succeeds) to calculate the required sample size for the full evaluation study.
- **Pilot Discordant Rate ($r_{\text{disc}}$):** measured at **48%** of failed cases.
- **Power Sizing:** Under McNemar's test for paired binary outcomes with power $1-\beta=0.80$ and $\alpha=0.05$, the system calculates that exactly **46 escalated cases** are needed to statistically prove that our provenance-guided selector outperforms the best fixed verifier.

### How to Run the Simulation
```bash
# Execute the pilot simulation and generate stats.tex
python3 experiments/simulation.py
```
This script dynamically outputs the statistical macros used in `paper.tex` into `generated/stats.tex`.

---

## 4. Submission Plan

### Thesis Statement
*Multi-agent verification panels fail when checkers share their creator's blind spots; by routing cases dynamically based on the primary agent's execution provenance, an agent system can select a specialized second check that is uniquely suited to catch the active failure mode, thereby bypassing the shared-model floor at matched verification cost.*

### Closest-Prior-Work Comparison
The closest prior method in literature is **Static Class-Based Routing** (allocating specialised verifiers based on metadata category) or **Confidence-Based Cascades** (e.g., FrugalGPT). 
Our proposed decision rule is fundamentally distinct: it selects the verifier based on the **execution provenance** $\tau_A$ of the first attempt, exploiting runtime-specific signals (such as citation date ranges and mathematical execution logs) rather than static categories or generic confidence scores.

### Page Budgets (6-Page vs. 8-Page)
- **6-Page Version:** Focuses purely on the same-model comparison between the fixed verifier and adaptive choice, using identical escalation decisions.
  - *Intro & Background:* 1.5 pages
  - *Formal Model:* 1.0 page
  - *Experimental Setup:* 1.5 pages
  - *Evaluation & Results:* 1.5 pages
  - *Conclusion:* 0.5 pages
- **8-Page Version (Recommended):** Adds the controlled **source-access ablation** (procedural specialization vs. source lineage) to prove whether the benefit comes from specialized procedures or simple information access, and tests a second base-model family (cross-model transfer).
  - *Intro & Background:* 1.5 pages
  - *Formal Model:* 1.0 page
  - *Source Ablation Formulation:* 1.0 page
  - *Experimental Setup:* 1.5 pages
  - *Evaluation & Results:* 2.0 pages
  - *Conclusion & Future Work:* 1.0 page

---

## 5. Longer-Term Research Agenda

The paper concludes with three follow-up studies extending the PGV paradigm:

1. **Active Evidence Acquisition:** 
   - *Hypothesis:* When every available check depends on the same inadequate source, the system can identify and acquire a specific missing observation or request a human query, rather than failing closed.
   - *Success Criterion:* $>30\%$ reduction in human deferrals with $0\%$ false approvals.
2. **Transfer Across Harness & Model Upgrades:**
   - *Hypothesis:* A verifier's declared capabilities and measured co-failure profile on a legacy model predict which failures it will recover after changing the task distribution or model.
   - *Success Criterion:* Retaining $>80\%$ of the selection value on upgraded models without retraining the decision tree.
3. **Verification Over Long Workflows:**
   - *Hypothesis:* Keeping evidence lineage across multi-agent handoffs allows the system to identify the earliest unsupported decision and recheck only downstream work that depends on it.
   - *Success Criterion:* $2\times$ reduction in token cost and latency with identical final accuracy compared to full-workflow reruns.
