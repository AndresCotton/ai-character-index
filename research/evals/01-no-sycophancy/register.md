# Behaviour 1 (No Sycophancy) -- candidate register

The spine of the sweep. Created at discovery (Gate 1, 2026-07-18); Disposition is
finalized at Gate 2 and Used-downstream is appended by later stages. Every candidate
found is here with a prima-facie facet-fit note; leave-outs are never deleted.

Facet-fit codes: **in** / **borderline** / **out**, against facets **1.1** falsehood
endorsement, **1.2** authorship invariance, **1.3** pushback stability. Full dossier
per row in `1-dossiers.md` (dossier id in the Candidate cell).

Prior-sweep dispositions (2026-07-12) are shown in the Facet-fit notes as screening
context only -- they are re-decided at Gate 2.

| # | Candidate (dossier) | Primary source | Found by | Facet fit (prima facie) | Disposition (Gate 2) | Used downstream |
|---|---|---|---|---|---|---|
| 1 | SycophancyEval (C01) | arXiv:2310.13548; ICLR 2024 | seed / Agent A | **in** 1.1+1.2+1.3 (only all-three); prior E1 | | |
| 2 | BrokenMath (C02) | arXiv:2510.04721; NeurIPS 2025 | seed / Agent A | **in** 1.1; out 1.2/1.3; no Claude; prior E2 | | |
| 3 | SycEval (C03) | arXiv:2502.08177; AIES 2025 | seed / Agent A | **in** 1.3, borderline 1.1; no release; prior E3 | | |
| 4 | SYCON-Bench (C04) | arXiv:2505.23840; Findings EMNLP 2025 | seed / Agent A | **in** 1.3+1.1; per-model now extracted; prior E4 | | |
| 5 | ELEPHANT (C05) | arXiv:2505.13995; ICLR 2026 | seed / Agent A | **borderline** (social construct; in-scope slices moral+framing); prior E5 | | |
| 6 | PARROT (C06) | arXiv:2511.17220 (preprint) | seed / Agent A | **in** 1.1, borderline 1.3; promotion condition NOT met; prior watchlist | | |
| 7 | AI Epistemic Deference Index (N01) | arXiv:2606.07897 (2026) | Agent C | **in** 1.1 (continuous); judge-validated; released | | |
| 8 | lechmazur/sycophancy (N02) | github.com/lechmazur/sycophancy (living) | Agent C | **in** 1.2 (perspective proxy), borderline 1.3; judge undisclosed; 2026 Claude nums | | |
| 9 | Who Flips? (N03) | arXiv:2606.16011 (2026) | Agent C | **in** 1.3, borderline 1.2; MIT-released; no Claude | | |
| 10 | Certainty Robustness (N04) | arXiv:2603.03330 (2026) | Agent C | **in** 1.3 (self-challenge); scores unread | | |
| 11 | Decomposing Factual Sycophancy (N05) | arXiv:2606.06306 (2026) | Agent C | **in** 1.1; code released; scores unread | | |
| 12 | syco-bench (N06) | github.com/timfduffy/syco-bench (2025) | seed / Agent B+C | **borderline** 1.2 ("Who Said"), 1.1; small n, weak judges; prior rejected X-SCALE | | |
| 13 | EchoBench (N07) | arXiv:2509.20146 (2025) | Agent C | **borderline** 1.1; medical VLM (off-domain) | | |
| 14 | SYAUDIO (N08) | arXiv:2601.23149 (2026) | Agent C | **out**/borderline 1.1; audio (off-domain); search-index only | | |
| 15 | MemSyco-Bench (N09) | arXiv:2607.01071 (2026) | Agent C | **borderline** 1.1; memory-conditioned; details unread | | |
| 16 | The Price of Agreement (N10) | arXiv:2604.24668 (2026) | Agent C | **borderline** 1.1+1.3; agentic financial (off-domain) | | |
| 17 | EQUIP (N11) | arXiv:2605.03050 (2026) | Agent C | **in** 1.1 (false presuppositions); scores unread | | |
| 18 | Warmth-tuning sycophancy (N12) | arXiv:2507.21919 (2025) | Agent C | **borderline** 1.1; experiment not standalone instrument | | |
| 19 | Perez et al. 2022 (L01) | arXiv:2212.09251 | seed / Agent B | **out** (opinion mirroring, no ground truth); prior rejected X-CONSTRUCT | | |
| 20 | Spiral-Bench (L02) | eqbench.com/spiral-bench (2025) | seed / Agent B+C | **borderline** 1.1/1.3-adjacent; delusion/companionship; prior context | | |
| 21 | UK AISI inspect_evals sycophancy (L03) | github.com/UKGovernmentBEIS/inspect_evals | seed / Agent B | **in** 1.3 but PORT of C01 data; prior rejected X-EVIDENCE-DEP | | |
| 22 | MASK (L04) | arXiv:2503.03750 (v3 2026) | seed / Agent B | **out** (instructed lying, different construct); prior rejected X-CONSTRUCT | | |
| 23 | DarkBench (L05) | arXiv:2503.10728; ICLR 2025 | seed / Agent B | **borderline** 1.1; thin sub-cat, κ=0.57, stale models; prior rejected X-SCALE | | |
| 24 | Petri (L06) | Anthropic 2025; arXiv n/a | seed / Agent B+C | **out** (auditing tool, no per-model table); prior rejected X-TOOL | | |
| 25 | OpenAI internal sycophancy evals (L07) | GPT-5 system card §3.3; Apr-May 2025 posts | seed / Agent B+C | context (self-reported, no public data); prior X-INDEPENDENCE | | |
| 26 | TRUTH DECAY (L08) | arXiv:2503.11656 (2025) | seed / Agent B | **borderline** 1.3; multi-turn, unreviewed; prior rejected | | |
| 27 | Sycophancy under Pressure (L09) | arXiv:2508.13743 (2025) | seed / Agent B | **in** 1.3 but scientific-QA only; prior rejected X-SCOPE | | |
| 28 | Operationalization-validity critique (K01) | arXiv:2512.00656 (2025) | seed / Agent B | context (construct validity) | | |
| 29 | Sycophancy taxonomy survey (K02) | arXiv:2605.21778 (2026) | seed / Agent B | context (construct definition); prior mis-cited claim flagged | | |
| 30 | Sycophancy as Material Failure / Schessl (K03) | arXiv:2606.16617 (2026) | seed / Agent B | context (judge sensitivity κ=0.36); **NOT SYCON-Bench** (correction) | | |
| 31 | Stanford AI Index 2026 sycophancy figure (K04) | AI Index 2026 (2026-04-13) | Agent C | context / **lead** to primary instrument (user-vs-third-party belief); trace at Gate 2 | | |
| 32 | Adjacent cluster (Appendix, ~19 papers) | see 1-dossiers.md Appendix | Agent C | context/out; search-index only, not dossiered; scoping item at Gate 1 | | |

**Corrections to the prior register carried into this one:** (a) row 30 is a distinct
paper from row 4 (SYCON-Bench), correcting the 2026-07-12 conflation of arXiv:2606.16617
with SYCON-Bench; (b) row 21's port credits Chen et al. 2024 for the implementation
while its data is Anthropic's `are_you_sure`; (c) the "SycEval vs ELEPHANT rank
oppositely" claim (row 29) is unverified against the source abstract.
