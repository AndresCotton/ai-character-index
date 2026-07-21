# Behaviour 1 (No Sycophancy) -- stage 1: discovery dossiers

Sweep date: **2026-07-18**. Re-sweep under the staged pipeline; the 2026-07-12 sweep
(`../01-no-sycophancy.md`, pre-staged layout) supplies the seed list. Per the
discovery protocol every seed is re-verified this sweep, not trusted; every URL was
fetched live 2026-07-18 with its status recorded.

Behaviour definition (core-behaviour-list.md §1): the model should not shift its
factual claims or assessments to please the user. Facets: **1.1 falsehood
endorsement**, **1.2 authorship invariance**, **1.3 pushback stability**.

Evidence tiers used per fact: **verified-by-us** (fetched and read this sweep) /
**paper's-claim** (self-reported in the source) / **third-party** (secondary) /
**unverified** (not confirmed this sweep).

---

## Seed list (written before searching, 2026-07-17)

Sources: behaviour §1 of `core-behaviour-list.md` (names no instruments beyond spec
passages); the 2026-07-12 sweep's curated/rejected tables and its cross-cutting
findings. Prior dispositions are screening context only -- re-decided at Gate 2.

Prior curated (E1-E5): SycophancyEval (2310.13548), BrokenMath (2510.04721), SycEval
(2502.08177), SYCON-Bench (2505.23840), ELEPHANT (2505.13995).
Prior watchlist: PARROT (2511.17220).
Prior leave-outs: Perez et al. 2022 (2212.09251), Spiral-Bench, Syco-bench (Duffy),
UK AISI inspect_evals sycophancy task, MASK (2503.03750), DarkBench (2503.10728),
Petri, OpenAI internal evals, TRUTH DECAY (2503.11656), Sycophancy-under-Pressure
(2508.13743).
Prior critique/context: 2512.00656, 2605.21778, 2606.16617, LessWrong audit of Perez.

---

## Search log

Three parallel general-purpose agents (2026-07-18), plus four coordinator
verification fetches. A reader should be able to judge coverage from this log alone.

### Agent A -- re-verify the six primary instruments
Scope: SycophancyEval, BrokenMath, SycEval, SYCON-Bench, ELEPHANT, PARROT. All arXiv
`abs`/`html`, GitHub, HuggingFace, AAAI-OJS, ACL-Anthology URLs fetched (HTTP 200
unless noted). Key updates found: SycophancyEval now arXiv v4 (2025-05-10) + inspect
port maintained to 2026-02-16; SycEval now v4 (2025-09-19) + AIES proceedings
(2025-10-15) but **still no code/data release** (negative probe confirmed);
SYCON-Bench v4 (2026-02-26); ELEPHANT confirmed **ICLR 2026** (OpenReview igbRHKEiAs)
+ Science companion 2026-03-26 (DOI 10.1126/science.aec8352, science.org **403 --
gated, not read**); PARROT v2 (2025-12-01), still "under review by MLSys, do not
distribute" -- **not promotable**. Zero-result: no SycEval code repo exists.

### Agent B -- re-verify prior leave-outs + critique literature
Scope: Perez 2022 + LessWrong audit, Spiral-Bench, Syco-bench, UK AISI inspect_evals
port, MASK, DarkBench, Petri, OpenAI internal, TRUTH DECAY, Sycophancy-under-Pressure,
2512.00656, 2605.21778, 2606.16617. Gated/failed fetches recorded: openai.com
sycophancy posts **403** (read via Simon Willison mirror); mask-benchmark.ai JS shell
(numbers taken from arXiv HTML); syco-bench.pdf binary (structure from GitHub/deepwiki).
**Two prior-register corrections surfaced** (see Corrections below). Zero-result:
2605.21778 abstract does NOT contain the "SycEval vs ELEPHANT rank oppositely" claim
the prior sweep attributed to it.

### Agent C -- broad open-ended sweep for NEW work (2025-06 -> 2026-07)
22 logged queries across web + arXiv listing + venue programs + leaderboards + lab
cards. Surfaced ~19 in-window instruments the prior sweep did not list, plus ~20
adjacent papers. Documented zero/near-zero probes: **HELM / LMArena have no
sycophancy or agreement axis as of 2026-07** (#21); **no dedicated pure
artifact-authorship ("I wrote this essay" vs "a friend sent this essay") judge
benchmark exists** (#18, #10 -- the facet-1.2 exact construct is still unbuilt);
**no DeepMind-native standalone sycophancy eval** (#13, only in-model-card claims).
Highest-value finds: Epistemic Deference Index (1.1), lechmazur/sycophancy (1.2
proxy), Who Flips? (1.3).

### Coordinator verification fetches (2026-07-18)
- `github.com/lechmazur/sycophancy` -- **verified-by-us**: 199 cases; five views
  (neutral, side_a_stripped, side_a_affective, side_b_stripped, side_b_affective);
  metrics as reported; **judge model not disclosed**; changelog "June 10, 2026:
  Added Claude Fable 5 (medium)...". Confirmed leaderboard numbers below.
- `arxiv.org/abs/2606.07897` (Epistemic Deference Index) -- **verified-by-us**:
  title, authors (Botas, de Font-Reaulx, Hewitt), 500 propositions / 16,000 prompts
  / 8 models, CC-BY-4.0; abstract states "Claude models demonstrating the least [and]
  Grok and Gemini models the most." Exact per-model logit values live in the HTML
  body (agent-extracted; marked paper's-claim).
- `arxiv.org/abs/2606.16617` -- **verified-by-us**: confirmed **NOT SYCON-Bench** --
  Schessl, "Sycophancy as Material Failure under Pushback Loading," 2026-06-15;
  κ=0.88 debate / κ=0.36 false-presupposition; judges GPT-4o + Haiku 4.5.

### Corrections to the prior (2026-07-12) register, verified this sweep
1. **2606.16617 ≠ SYCON-Bench.** The prior sweep labelled 2606.16617 as a
   "SYCON-Bench judge-sensitivity follow-up." It is a separate paper (Schessl,
   materials-science framing). Real SYCON-Bench = **2505.23840** (Hong et al.). The
   κ=0.36 false-presupposition figure genuinely lives in 2606.16617. Register carries
   both, unconflated.
2. **inspect_evals provenance is layered.** The UK AISI `sycophancy` task README
   credits **Chen et al. 2024 (arXiv:2409.01658)** for the implementation while the
   `are_you_sure.jsonl` data is pulled from Anthropic's `meg-tong/sycophancy-eval`
   (Sharma et al. 2023). Data = Anthropic's; metric formulation = Chen et al. Still a
   port (no new data).
3. **"SycEval vs ELEPHANT rank oppositely" is unverified** against 2605.21778's
   abstract. Carried as an unverified cross-cutting claim, not attributed as fact.

---

## Dossiers

### Group 1 -- primary instruments carried from the prior sweep

#### C01. SycophancyEval -- Sharma et al. 2023 (Anthropic), ICLR 2024
- **Citation:** Sharma, Tong, Korbak, Duvenaud, Askell, Bowman, et al. *Towards
  Understanding Sycophancy in Language Models.* arXiv:2310.13548; ICLR 2024.
- **URLs (all 200, verified-by-us):** abs https://arxiv.org/abs/2310.13548 (**now v4,
  2025-05-10**) · code+data https://github.com/meg-tong/sycophancy-eval (129 stars) ·
  maintained port https://github.com/UKGovernmentBEIS/inspect_evals
  (`src/inspect_evals/sycophancy/`, changelog to **2026-02-16**).
- **Measures:** four probes on 5 models (claude-1.3, claude-2.0, gpt-3.5-turbo, gpt-4,
  llama-2-70b-chat): feedback sycophancy (~8.5k), are-you-sure (4,887), answer
  sycophancy (7,267), mimicry (300, unreleased).
- **Facets:** 1.1 (answer sycophancy/mimicry) · 1.2 (feedback, authorship framing) ·
  1.3 (are-you-sure). **Only instrument mapping all three.**
- **Methodology:** clear multi-faceted construct; mostly continuous rates + Bayesian
  credible intervals; **GPT-4-as-judge** (family circularity); human eval on 266
  misconceptions; datasets public + independent maintained port; 2023 model strings.
- **Per-model (paper's-claim):** claude-1.3 wrongly admits mistakes on **98%** of
  are-you-sure items; answer sycophancy accuracy drop up to 27% (LLaMA-2); gpt-4 most
  robust yet sycophantic on all four tasks.
- **Last activity:** 2026-02-16 (inspect port). **Not stale.**
- **Limitations:** 2023 model roster; judge circularity; per-model numbers mostly in
  figures. Prior disposition: curated E1 (via its live port).

#### C02. BrokenMath -- Petrov et al. 2025 (INSAIT/ETH), NeurIPS 2025
- **Citation:** Petrov, Dekoninck, Vechev. *BrokenMath: A Benchmark for Sycophancy in
  Theorem Proving with LLMs.* arXiv:2510.04721 (2025-10-06). NeurIPS 2025 acceptance
  **unverified from arXiv comments this sweep** (flag).
- **URLs (200, verified-by-us):** abs https://arxiv.org/abs/2510.04721 (**v1 only**) ·
  site https://sycophanticmath.ai/ (project page, not a leaderboard) · code
  https://github.com/insait-institute/broken-math (Apache-2.0) · data
  https://huggingface.co/datasets/INSAIT-Institute/BrokenMath (CC BY-NC-SA, updated
  2025-10-07).
- **Measures:** competition problems perturbed into false statements; response taxonomy
  Ideal/Corrected/Detected/Sycophant; sycophancy rate = share proving the false
  statement. **Size discrepancy to flag:** paper 504 problems vs HF card benchmark
  split 451.
- **Facets:** 1.1 (domain-specific falsehood endorsement). Not 1.2/1.3.
- **Methodology:** clear narrow construct; binary->rate; judge GPT-5-mini majority-of-3,
  **95% agreement vs 250 hand-labels** (paper's-claim); **no CIs/error bars** on main
  table (verified-by-us); mitigation + fine-tuning ablations; full code+data released.
- **Per-model (paper's-claim, lower=better):** GPT-5 **29.0%**, GPT-OSS-120B 33.7%,
  Gemini-2.5-Pro 37.5%, Grok-4-Fast 40.0%, Grok-4 43.4%, o4-mini 46.6%, then open
  models to DeepSeek-V3.1 70.2%. **NO Claude model in any version** (checked).
- **Last activity:** 2025-10-07. **Not stale.**
- **Limitations:** math-only; no Claude; no uncertainty quantification; same-vendor
  judge. Prior disposition: curated E2.

#### C03. SycEval -- Fanous et al. 2025 (Stanford), AIES 2025
- **Citation:** Fanous, Goldberg, Agarwal, Lin, Zhou, Xu, Bikia, Daneshjou, Koyejo.
  *SycEval: Evaluating LLM Sycophancy.* arXiv:2502.08177; AIES 2025, AAAI/ACM
  Proceedings Vol 8 No 1 (pub 2025-10-15). DOI 10.1609/aies.v8i1.36598.
- **URLs (200, verified-by-us):** abs https://arxiv.org/abs/2502.08177 (**now v4,
  2025-09-19**) · https://ojs.aaai.org/index.php/AIES/article/view/36598 · **no
  code/data repo** (negative probe confirmed this sweep).
- **Measures:** control answer then rebuttal on AMPS math (500) + MedQuad medical
  (500); 24,000 rebuttal responses; **progressive** (wrong->right) vs **regressive**
  (right->wrong) split; rebuttal ladder Simple/Ethos/Justification/Citation ×
  in-context/preemptive. Models: ChatGPT-4o (2024-05-13), **Claude-Sonnet (no version
  date -- pinning weakness)**, Gemini-1.5-Pro.
- **Facets:** 1.3 (regressive = correct answer flipped under pushback; note some
  rebuttals carry citations/evidence, so stronger than pure evidence-free pushback) ·
  1.1 partial (preemptive/regressive cell). Not 1.2.
- **Methodology:** clear construct with progressive/regressive split; binary->rate;
  **95% CIs + z-tests reported** (persistence 78.5% CI [77.2,79.8]); judge ChatGPT-4o
  (2024-08-06), validation thin (**n=20 human labels/dataset**); GPT pinned, Claude
  not; **no release**.
- **Per-model regressive (in-scope slice, paper's-claim):** Claude-Sonnet **18.31%**
  (highest), ChatGPT-4o **14.40%**, Gemini-1.5-Pro 9.25%.
- **Last activity:** 2025-10-15 (AIES proceedings). **Not stale.**
- **Limitations:** no release (reproducibility gap); tiny judge validation; Claude
  version unpinned. Prior disposition: curated E3.

#### C04. SYCON-Bench -- Hong et al. 2025 (Emory/CMU), Findings of EMNLP 2025
- **Citation:** Hong, Byun, Kim, Shu, Choi. *Measuring Sycophancy of Language Models in
  Multi-turn Dialogues.* arXiv:2505.23840; Findings of EMNLP 2025, pp. 2239-2259. DOI
  10.18653/v1/2025.findings-emnlp.121.
- **URLs (200, verified-by-us):** abs https://arxiv.org/abs/2505.23840 (**now v4,
  2026-02-26**) · https://aclanthology.org/2025.findings-emnlp.121/ · code
  https://github.com/JiseungHong/SYCON-Bench (MIT, release v0.1.0 2025-07-09).
- **Measures:** multi-turn conformity in 3 settings -- Debate (100), Challenging
  Unethical Queries (200), False Presuppositions (200) -- on **17 LLMs/6 families**.
  Metrics **Turn-of-Flip (ToF)** (higher=more resistant) and **Number-of-Flips (NoF)**
  (lower=more stable).
- **Facets:** 1.3 (Debate + Unethical = sustained evidence-free pushback; ToF is a
  pushback-stability metric) · 1.1 (False-Presupposition setting). Not 1.2.
- **Per-model (paper Table 2 -- prior sweep's gap, now extracted, verified-by-us):**

  | Model | Debate ToF | Debate NoF | Unethical ToF | False-Presup ToF |
  |---|---|---|---|---|
  | GPT-4o | 4.67 | 0.08 | 1.23 | 2.92 |
  | o3-mini | 4.97 | 0.01 | 2.31 | 2.98 |
  | Claude-3.7-Sonnet | 4.47 | 0.25 | 2.73 | 2.92 |

  Only one Claude (3.7-Sonnet), two OpenAI (GPT-4o, o3-mini); no frontier-2025 models.
- **Methodology:** continuous metrics; judge GPT-4o, **human agreement 0.984/0.864/
  0.810, Cohen κ 0.917/0.690/0.631** across settings; ANOVA p<10⁻⁴⁷; third-person
  prompting cuts debate sycophancy up to 63.8%; code MIT.
- **Last activity:** 2026-02-26 (arXiv v4). **Not stale.**
- **Limitations:** moderate κ on false-presupposition (0.631); no frontier Claude/GPT-5;
  Debate is opinion-conformity. Prior disposition: curated E4 (adherence unextracted --
  now extracted above).

#### C05. ELEPHANT -- Cheng et al. 2025 (Stanford), ICLR 2026
- **Citation:** Cheng, Yu, Lee, Khadpe, Ibrahim, Jurafsky. *ELEPHANT: Measuring and
  understanding social sycophancy in LLMs.* arXiv:2505.13995; **ICLR 2026** (OpenReview
  igbRHKEiAs, verified-by-us). Companion: *Science* 2026-03-26, Vol 391 Issue 6792, DOI
  10.1126/science.aec8352.
- **URLs:** abs https://arxiv.org/abs/2505.13995 (v2 2025-09-29, 200) · code
  https://github.com/myracheng/elephant (CC0, datasets OEQ 3,027 / AITA-YTA 2,000 /
  AITA-NTA-FLIP 1,591 / Subjective 3,777) · Science page **403 -- gated, not read**.
- **Measures:** "social sycophancy" = user face-preservation on four axes (Validation,
  Indirectness, Framing, Moral), scored as difference vs human baseline; 11 models incl.
  GPT-5, GPT-4o, **Claude Sonnet 3.7**.
- **Facets:** **mostly outside the factual facets** -- construct is emotional/social
  face-preservation. In-scope slices per prior sweep: **Moral both-sides** and
  **Framing** (adopting unsupported premises). AITA-NTA-FLIP paired-perspective is the
  best existing template for facet-1.2 invariance logic (tests perspective, not
  authorship). Agent A judged it adjacent/context; prior sweep curated the two slices.
  **Disposition decision deferred to Gate 2.**
- **Methodology:** best judge validation in the set -- GPT-4o judge accuracy ≥0.83,
  Cohen κ ≥0.65 vs human majority (Fleiss κ ≥0.70, 3 experts, 450 examples); 95% CIs
  <0.04; CC0 code + OSF data.
- **Per-model:** dispersed per-dataset (no single clean Claude-vs-GPT column); headline
  LLMs preserve face ~45pp more than humans, affirm user's side in 48% of moral
  conflicts. Prior in-scope extraction: Claude 3.7 Sonnet moral 0.15 / framing ~0.27;
  GPT-5 moral 0.22 (GPT-4o 2024-11-20 worse: 0.40).
- **Last activity:** 2026-03-26 (Science companion). **Not stale.**
- **Limitations:** construct only partially ours; per-model results dispersed; one
  Claude. Prior disposition: curated E5 (in-scope slices only).

#### C06. PARROT -- Çelebi et al. 2025 (preprint)
- **Citation:** Çelebi, Ezerceli, El Hussieni. *PARROT: Persuasion and Agreement
  Robustness Rating of Output Truth.* arXiv:2511.17220 (**now v2, 2025-12-01**).
- **URLs:** abs https://arxiv.org/abs/2511.17220 (200) · **no code/data repo found**
  this sweep.
- **Promotion-condition check (prior watchlist):** (1) peer review -- **NOT met**; full
  text says "Preliminary work. Under review by MLSys. Do not distribute." (2) validated
  judge -- **N/A**: there is **no LLM judge** (log-prob/deterministic 8-state
  classifier), and the classifier itself is unvalidated against humans. **Watchlist
  condition not met -- stays watchlist.**
- **Measures:** 1,302 MMLU-style MCQs × 22 models; **follow rate** = adopting the
  asserted false answer; 8-state taxonomy; **no CIs/error bars**.
- **Facets:** 1.1 (core) · 1.3 partial (single false assertion, not iterative pushback).
  Not 1.2.
- **Per-model follow rate (paper's-claim):** GPT-5 **3.6%** (lowest of 22), GPT-5-Mini
  6.3%, Grok-4-Fast 7.6%, GPT-4.1 10.2%, **Claude Sonnet 4.5 10.8%**, GPT-4o 16.1%,
  ... GPT-3.5-Turbo 60.9%, GPT-4 80.3%.
- **Last activity:** 2025-12-01 (arXiv v2). **Not stale.**
- **Limitations:** not peer-reviewed ("do not distribute"); no repo; no uncertainty;
  single-turn; unvalidated classifier. Prior disposition: watchlist.

### Group 2 -- NEW instruments surfaced this sweep (fetched/verified)

#### N01. AI Epistemic Deference Index (AEDI/EDI) -- Botas et al. 2026 ⭐
- **Citation:** Botas, de Font-Reaulx, Hewitt. *The AI Epistemic Deference Index: A
  Continuous Measure of Sycophancy.* arXiv:2606.07897 (v1, early June 2026; abstract
  says 2026-06-05, agent noted 06-09 -- minor, confirm day). CC-BY-4.0.
- **URLs (200, verified-by-us):** abs https://arxiv.org/abs/2606.07897. Dataset on
  HuggingFace (CC-BY-4.0); pipeline code MIT (per agent; repo URL to pin at scoring).
- **Measures:** **continuous** logit-scale sensitivity of expressed credence to prompt
  valence -- how far the stated probability of a proposition moves toward the user's
  signalled stance. `logit(c) = α + β·v(q) + ε`, β = within-proposition valence
  sensitivity. **500 propositions / 10 domains / 16,000 prompts / ~128,000 responses /
  8 frontier models.**
- **Facets:** **1.1** (falsehood/valence endorsement) in continuous form; adjacent 1.3.
- **Methodology (most rubric-complete new instrument):** credence judge median Pearson
  **0.77 [0.70,0.83]** vs human consensus; valence judge 0.83; inter-judge agreement
  87.1%/92.4%; anchors 100 calibration + 40 negation pairs + 20 entailment triples;
  dataset+code+version-pinning released.
- **Per-model (paper's-claim; direction verified-by-us from abstract "Claude least,
  Grok/Gemini most"):** Claude Sonnet 4.6 **+0.67**, Claude Opus ≈0 conversational
  deference; GPT ≈**+1.89**; Gemini ≈**+2.61**; Grok-4.20 ≈**+2.81**; Grok-4-1-fast
  **+3.14** (lower = less deferential). Exact numbers from HTML body, not re-verified
  digit-by-digit.
- **Last activity:** 2026-06. **Not stale.**
- **Limitations:** per-model numbers agent-extracted, not independently re-run; formula
  detail not in abstract. **Strong curation candidate for 1.1.**

#### N02. lechmazur/sycophancy -- narrator/perspective-invariance leaderboard ⭐
- **Citation:** Lech Mazur, *LLM Sycophancy Benchmark* (living GitHub leaderboard, no
  formal paper). https://github.com/lechmazur/sycophancy -- **verified-by-us**.
- **Measures:** whether a model gives the same verdict on an identical dispute across
  **five views** (neutral / side_a_stripped / side_a_affective / side_b_stripped /
  side_b_affective). Sycophantic = sides with the narrator on both opposite affective
  views; contrarian = rejects both. **199 cases** (funnel 448->220->199), 14 topic
  categories, **995 prompts/model**, **34 models**. Metrics: Sycophancy Rate,
  Conditional Sycophancy, Decisive-Pair Coverage, Contrarian, Net Narrator Pull,
  Affective Uplift.
- **Facets:** **1.2 primary** (perspective/attribution invariance of a judgment;
  **proxy** for authorship -- tests narrator perspective, not literal "I wrote this
  artifact") · 1.3 partial (affective framing pressure).
- **Per-model Sycophancy Rate (verified-by-us, fetched 2026-07-18):** Claude Fable 5
  (medium) **0.5%** (best; conditional 0.6%, decisive coverage 77.4%), Gemini 3.1 Pro
  Preview 0.5%, Grok 4.3 0.5%, **GPT-5.5 (high) 3.5%**, **Claude Opus 4.6 (no
  reasoning) 2.5%**, **Claude Opus 4.7 (high) 4.5%**, **Claude Sonnet 4.6 (high)
  7.0%**, GPT-4.1 19.1%, Mistral Large 3 31.2%.
- **Methodology:** explicit construct; randomized answer order; conservative
  "count only plausibly-attributable flips"; model versions pinned. **Weakness: judge
  model undisclosed (no judge-validation numbers); dataset-file release beyond the
  leaderboard not stated.**
- **Last activity:** **2026-06-10** (changelog). **Not stale.** Sibling
  `lechmazur/position_bias` (LLM-judge order-swap stability) noted, not fetched.
- **Note:** the only source with current-model (2026) Claude numbers on a 1.2-type
  construct. Judge opacity is the rigor question for Gate 2.

#### N03. Who Flips? -- Nikeghbal et al. 2026 (TUM/LMU) ⭐
- **Citation:** Nikeghbal, Kargaran, Kolli, Diesner. *Who Flips? Self- and Cross-Model
  Counterarguments Reveal Answer Instability in LLMs.* arXiv:2606.16011 (2026-06-14).
- **URLs:** abs https://arxiv.org/abs/2606.16011 (verified-by-us) · code
  github.com/nafisenik/WhoFlips + HF (MIT).
- **Measures:** **Answer Flip Rate (AFR)** = P(abandon an initially-correct answer after
  a counterargument) under blind/self-attributed/cross-model conditions. **2,052 MMLU
  questions, 57 subjects, 7 models**; rule-based extraction (no LLM judge).
- **Facets:** **1.3** (content-driven challenge) · 1.2 touch (self-vs-cross attribution
  effect on stability).
- **Per-model AFR (paper's-claim):** GPT-5.1 23.4%, Gemma-4-26B 23.0%, Qwen3.5-35B
  17.5%, ... Llama-3.1-8B 97.3%. Self-attribution raises flips +7.1pp mean (up to
  +18.7pp); target-model identity explains 76.7% of cross-model variance. **No Claude
  number (gap).**
- **Methodology:** clear metric; MIT code + MaxFlip subset released; no judge.
- **Last activity:** 2026-06. **Not stale.** Strong 1.3 candidate; flag missing Claude.

#### N04. Certainty Robustness -- Saadat & Nemzer 2026
- **Citation:** Saadat, Nemzer. *Certainty robustness: Evaluating LLM stability under
  self-challenging prompts.* arXiv:2603.03330 (2026-03-05).
- **URL:** abs https://arxiv.org/abs/2603.03330 (verified-by-us; per-model scores in
  PDF body, **unread-detail**). Data released (open JSON).
- **Facets:** 1.3 (flip rate under self-contradiction challenge). Distinct framing
  (self-challenge, not user rebuttal).
- **Methodology:** design verified; scores not extracted. **Not stale** (2026).

#### N05. Decomposing Factual Sycophancy -- De Marez et al. 2026
- **Citation:** De Marez, De Bruyne, Daelemans (Antwerp, inferred). *Decomposing
  Factual Sycophancy in Language Models: How Size and Instruction Tuning Shape
  Robustness.* arXiv:2606.06306 (2026-06-05). CC-BY-4.0.
- **URL:** abs https://arxiv.org/abs/2606.06306 (verified-by-us; scores in body,
  **unread-detail**). Code: github.com/Victordmz/decomposing-factual-sycophancy.
- **Facets:** **1.1** (user-asserted false claim vs control). **Not stale.**

#### N06. syco-bench -- Tim Duffy 2025 (self-published)
- **Citation:** Tim Duffy. *Syco-bench: A Multi-Part Benchmark for Sycophancy in LLMs.*
  syco-bench.com + github.com/timfduffy/syco-bench (MIT-0). Substack 2025-04-29.
- **URLs:** github (200, verified-by-us) · substack (200) · deepwiki (200) ·
  syco-bench.com/syco-bench.pdf (**binary, not machine-read**).
- **Measures:** four tests -- Picking Sides, Mirroring, **Attribution Bias / "Who Said"**
  (favors an idea attributed to the user vs someone else), Delusion Acceptance.
  **~20-40 items/test**; judge panel (Gemini-2.5-Flash-Preview, GPT-4o-mini,
  Llama-3.3-70B), median; low inter-test correlation r<0.3.
- **Facets:** **1.2** (the "Who Said" idea-attribution test -- the prior sweep's only
  post-2023 1.2 datapoint; idea-attribution, a proxy for artifact-authorship) · 1.1
  (Delusion) · 1.3-adjacent (Picking Sides/Mirroring).
- **Methodology:** small n; mid-tier judge panel, **no judge-validation study**;
  per-model scores only in PDF/site images (**unverified**); code+CSV open.
- **Last activity:** 2025-04-29 substack + active GitHub. **Not stale.**
- **Limitations:** self-published, small, weak judges. Prior disposition: rejected
  X-SCALE (corroboration only).

#### N07. EchoBench -- 2025 (medical VLM)
- **Citation:** *EchoBench: Benchmarking Sycophancy in Medical Large Vision-Language
  Models.* arXiv:2509.20146 (Sep 2025); OpenReview mq6GMkoGjh.
- **URL:** abs https://arxiv.org/abs/2509.20146 (agent: search+snippet, **verified-by-us
  partial**). 2,122 images / 18 departments / 90 biased prompts.
- **Facets:** 1.1 (echoes user-provided false info), **multimodal/medical (off-domain
  for a general index)**.
- **Per-model (paper's-claim):** Claude 3.7 Sonnet 45.98% sycophancy, GPT-4.1 59.15%;
  many medical models >95%. **Not stale.**

#### N08. SYAUDIO -- 2026 (audio LM)
- **Citation:** *Hearing is Believing? [SYAUDIO].* arXiv:2601.23149 (Jan 2026). 4,319
  audio questions. **Facet 1.1, audio modality (off-domain).** *[search-index only --
  unverified]*.

#### N09. MemSyco-Bench -- 2026 (agent memory)
- **Citation:** *MemSyco-Bench.* arXiv:2607.01071 v2 (2026-07-03, XMU DeepLIT). Code +
  leaderboard released (github.com/XMUDeepLIT/MemSyco-Bench). Measures
  memory-stored-preference-induced sycophancy vs baseline. **Facet 1.1-ish
  (memory-conditioned).** Fetched; numbers image-heavy (**details unread**). Not stale.

#### N10. The Price of Agreement -- 2026 (agentic financial)
- **Citation:** *The Price of Agreement: ... Sycophancy in agentic financial apps.*
  arXiv:2604.24668 v3 (2026-06-09; authors incl. D. Bikel). Biased vs neutral
  preference injection; "only low-to-modest drops under user rebuttals." **Facets 1.1 +
  1.3, agentic/domain (off-domain).** Verified-by-us (abstract). Not stale.

#### N11. EQUIP -- 2026 (false presuppositions)
- **Citation:** Sathyanathan, Vasisht, Pruthi. *Evaluating Reasoning Models for Queries
  with Presuppositions.* arXiv:2605.03050 (May 2026). Repo github.com/weakit/equip.
  Models incl. GPT-5, Gemini 2.5, Qwen3, DeepSeek-R1. **Facet 1.1 (false-premise
  endorsement).** Fetched; scores in body (**unread-detail**). Not stale.

#### N12. Warmth-tuning sycophancy -- Ibrahim et al. 2025 (Oxford)
- **Citation:** Ibrahim, Hafner, Rocher. *Training LMs to be warm and empathetic makes
  them less reliable and more sycophantic.* arXiv:2507.21919 v2 (Jul 2025). Uses
  MMLU/GSM8K/TruthfulQA with false-premise injection; warmth-tuning ↑ sycophancy.
  **Experiment (adapts existing benchmarks), not a standalone reusable instrument.
  Facet 1.1.** Verified-by-us (abstract). Not stale.

### Group 3 -- prior leave-outs, re-verified

#### L01. Perez et al. 2022 (model-written sycophancy subset) + LessWrong audit
- **Citation:** Perez, Ringer, Lukošiūtė, Nguyen, ... Kaplan (Anthropic). *Discovering
  Language Model Behaviors with Model-Written Evaluations.* arXiv:2212.09251 (v1 2022).
- **URLs (200, verified-by-us):** abs https://arxiv.org/abs/2212.09251 · data
  https://github.com/anthropics/evals/tree/main/sycophancy (3 files, ~10k each,
  ~30k total) · audit https://www.lesswrong.com/posts/yxdHp2cZeQbZGREEN/... (Dev &
  Hobbhahn, Apollo, 2024-10-15).
- **Measures:** opinion-matching on subjective survey items (NLP/philosophy/political
  typology); binary match rate; single-turn; model-generated data.
- **Facets:** maps to **none** of 1.1/1.2/1.3 -- opinion mirroring on no-ground-truth
  questions, varies the user's stated *view* not artifact authorship, single-turn.
- **Critique (audit, verified-by-us as read):** original data generated by "Claude-0.5"
  (2022); GPT-3.5 vs Claude-3-Haiku divergence 14-23pp (extreme 63pp); 99% linear
  separability human vs model-written; duplicates, inverted keys, leaked hints. Caveat:
  audit examined the Advanced-AI-Risk subset, not the sycophancy files specifically.
- **Last activity:** 2024 (audit). Prior disposition: rejected X-CONSTRUCT
  (foundational lineage, context).

#### L02. Spiral-Bench -- Sam Paech / EQ-Bench 2025
- **Citation:** Paech, *Spiral-Bench* (EQ-Bench3 sub-benchmark). eqbench.com/
  spiral-bench.html (200) · github.com/sam-paech/spiral-bench (MIT, 200).
- **Measures:** delusion-validation in 30×20-turn companionship spirals vs a Kimi-K2
  "seeker"; protective vs risky action tally -> 0-100 safety score. Judge ensemble
  (Claude Sonnet 4.5 + GPT-5 + Kimi-K-0905); **no inter-judge kappa published**.
- **Facets:** loosely 1.1 (delusion reinforcement) + 1.3-adjacent (pushback as a
  protective axis); does NOT implement 1.3's flip protocol; not 1.2. Construct = safety
  in companionship, broader than factual sycophancy.
- **Per-model (third-party, the-decoder):** GPT-5 ≈87, o3 >86 (safest), DeepSeek-R1
  22.4 (least safe); Claude 4 Sonnet reportedly underperforms; exact mid-table not
  machine-readable (JS). Prior disposition: rejected/context (adjacent construct).

#### L03. UK AISI inspect_evals sycophancy task
- **Citation:** UK AISI `inspect_evals`, `src/inspect_evals/sycophancy/` (200,
  verified-by-us). **Port** -- data = Anthropic `are_you_sure.jsonl` (Sharma et al.),
  implementation credited to **Chen et al. 2024 (arXiv:2409.01658)**; metrics
  confidence/apologize-rate/truthfulness. **Facet 1.3.** Changelog to **2026-02-16**
  (actively maintained). Prior disposition: rejected X-EVIDENCE-DEP (port of E1) --
  but keeps E1 alive on the staleness clock.

#### L04. MASK -- Ren et al. 2025 (CAIS/Scale)
- **Citation:** Ren, Agarwal, Mazeika, ... Hendrycks. *The MASK Benchmark: Disentangling
  Honesty From Accuracy.* arXiv:2503.03750 (**v3 2026-01-05**, verified-by-us).
- **Measures:** pressured/instructed lying vs elicited beliefs; 1,500 examples (1,000
  public); Honesty = 1 − P(Lie). **Different construct** (honesty under incentive --
  behaviour 3's neighbourhood).
- **Facets:** none in the sycophancy sense; "Doubling Down"/Lying@10 measure persistence
  of a *lie*, not flipping a *correct* answer -> not 1.3.
- **Per-model (verified-by-us, Table 3):** Claude 3.5 Sonnet P(Honest) 27.7% / P(Lie)
  33.4%; Claude 3.7 Sonnet 47.6% / 26.6%; GPT-4o 21.8% / 44.5%. Prior disposition:
  rejected X-CONSTRUCT.

#### L05. DarkBench -- Kran et al. 2025, ICLR 2025 Oral
- **Citation:** Kran, Nguyen, Kundu, Jawhar, Park, Jurewicz. *DarkBench: Benchmarking
  Dark Patterns in LLMs.* arXiv:2503.10728 (verified-by-us). 660 prompts / 6 categories
  (sycophancy ~110, inferred from 660/6); single-turn; 14 2024-vintage models.
- **Judge agreement (verified-by-us):** Cohen κ (Claude-3.5-Sonnet vs human) **sycophancy
  = 0.57** (overall 0.75; range 0.49-0.98). Aggregate sycophancy occurrence ~13%;
  per-model not broken out.
- **Facets:** loosely 1.1, single-turn; not 1.2/1.3. Prior disposition: rejected X-SCALE
  (thin sub-category, low κ, stale models).

#### L06. Petri -- Anthropic 2025 (auditing tool)
- **Citation:** Anthropic (Alignment Science). *Petri: open-source auditing tool.*
  Released 2025-10-06 (verified-by-us). Donated to **Meridian Labs** (May 2026); now
  v3.0 + Dish + Bloom. Pilot 14 models × 111 seeds.
- **Confirmation:** authors explicitly call it a **tool, not a benchmark**; "distilling
  behavior into quantitative metrics is inherently reductive." Sycophancy is one scored
  dimension but **no per-model sycophancy table**. Prior disposition: rejected X-TOOL
  (cite as methodology).

#### L07. OpenAI internal sycophancy evals (Apr-May 2025 + GPT-5 system card)
- **Citations/URLs:** openai.com/index/sycophancy-in-gpt-4o **403** (read via Willison
  mirror) · expanding-on-sycophancy **403 -- not read** · GPT-5 system card
  (cdn.openai.com, 2025-08-13; arXiv:2601.03267 mirror, verified-by-us).
- **Numbers (verified-by-us, §3.3):** offline sycophancy GPT-4o **0.145** -> gpt-5-main
  **0.052** -> gpt-5-thinking **0.040**; online prevalence −69% (free)/−75% (paid) vs
  latest GPT-4o. April-2025 event: an over-agreeable GPT-4o update, rolled back in ~4
  days; OpenAI acknowledged lacking a sycophancy deployment eval at the time.
- **Release:** **no public dataset/rubric/judge.** Prior disposition: context
  (X-INDEPENDENCE -- self-reported, non-reproducible; feeds the independence finding).

#### L08. TRUTH DECAY -- Liu et al. 2025
- **Citation:** Liu, Jain, Takuri, Vege, Akalin, Zhu, O'Brien, Sharma. *TRUTH DECAY:
  Quantifying Multi-Turn Sycophancy in Language Models.* arXiv:2503.11656
  (verified-by-us; abstract names no models/numbers). Multi-turn agreement-drift; 1.3-
  adjacent; not 1.1/1.2. Prior disposition: rejected (unreviewed/off-domain).

#### L09. Sycophancy under Pressure -- Zhang et al. 2025
- **Citation:** Zhang, Jia, Chen, Sun, Zhu, Li, Zhu, Zhai. *Sycophancy under Pressure:
  ... Scientific QA.* arXiv:2508.13743 (v1 2025-08-19, verified-by-us). Misleading- and
  sycophancy-resistance in scientific QA; "Pressure-Tune" mitigation. **Facet 1.3,
  domain-restricted (scientific QA).** Sizes/models/judge unspecified in abstract.
  Prior disposition: rejected X-SCOPE.

### Group 4 -- critique / context literature

#### K01. Operationalization-validity critique -- Batzner et al. 2025
- **Citation:** Batzner, Stocker, Schmid, Kasneci. *Sycophancy Claims about Language
  Models: The Missing Human-in-the-Loop.* arXiv:2512.00656 (2025-11-29, verified-by-us).
- **Core claim:** identifies five core operationalizations; none validated against human
  perception ("current research does not evaluate human perception"). Feeds the rubric's
  construct-validity / judge-validation dimension. Candidate `context`.

#### K02. Sycophancy taxonomy / expert survey -- Ye et al. 2026
- **Citation:** Ye, Ibrahim, Bo, Cheng, Mattsson, Vennemeyer, Kraut, Rathje. *What Counts
  as AI Sycophancy? A Taxonomy and Expert Survey of a Fragmented Construct.*
  arXiv:2605.21778 (2026-05-20, verified-by-us). Two dimensions (target × expression);
  survey of 70 papers + 106 experts, 94.3% agree it's significant, disagree on which
  behaviours qualify. **The "SycEval vs ELEPHANT rank oppositely" claim the prior sweep
  attributed here is NOT in the abstract -- unverified.** Candidate `context` (construct
  definition).

#### K03. Sycophancy as Material Failure under Pushback Loading -- Schessl 2026
- **Citation:** Ferdinand M. Schessl. arXiv:2606.16617 (2026-06-15, verified-by-us).
  **NOT SYCON-Bench** (correction). Materials-science-metaphor re-analysis; cross-judge
  reliability **κ=0.88 debate / κ=0.36 false-presupposition** (judges GPT-4o + Haiku
  4.5). Candidate `context` (judge-sensitivity evidence).

#### K04. Stanford AI Index 2026 -- sycophancy-hallucination figure
- **Citation:** Stanford HAI, *AI Index 2026* (2026-04-13, agent verified the claim
  exists via search + suprmind mirror). Reports a sycophancy-induced-hallucination
  accuracy benchmark: 22-94% across 26 models; false claim as **third-party belief**
  (handled well) vs **user's own belief** (collapse) -- GPT-4o 98.2%->64.4%, DeepSeek-R1
  ~90%->14.4%. Underlying standalone instrument **not named in reachable sources**
  (traces conceptually to "Belief in the Machine," arXiv:2410.21195, out of window).
  **Lead to trace at Gate 2 / scoring.** Candidate `context` until the primary
  instrument is pinned.

---

## Appendix -- adjacent cluster surfaced but not individually dossiered

Agent C's Tier-D: in-window papers that are interpretability, mitigation, survey,
pure-social/praise, or narrow off-modality work -- i.e. not per-model *adherence
instruments* for the factual facets. Recorded so they are not invisible; **most were
seen in result listings and NOT fetched (search-index only, unverified).** Raised at
Gate 1 as a scoping decision: none is proposed as index evidence; each is a candidate
`context` or `rejected:X-CONSTRUCT`/`X-SCOPE`. Promote any to a full dossier only if
the human flags it.

- *Sycophancy Is Not One Thing: Causal Separation* -- arXiv:2509.21305
- *A Mechanistic View of Authority Hierarchy in LLM Sycophancy* -- arXiv:2607.00415
- *A Few Bad Neurons* -- arXiv:2601.18939
- *SWAY: counterfactual mitigation* -- arXiv:2604.02423
- *Sycophancy Hides Linearly in Attention Heads* -- EACL 2026 (2026.eacl-long.324)
- *Recalling Too Well* (memory) -- arXiv:2606.10949
- *Beyond Social Pressure: Epistemic Attack* -- arXiv:2604.07749
- *Measuring Opinion Bias & Sycophancy via Persuasion* -- arXiv:2604.21564
- *Beacon: single-turn latent-sycophancy diagnosis* -- arXiv:2510.16727
- *Sycophantic Praise* (praise, not factual) -- arXiv:2606.07441
- *Flattery in Motion: Video-LLMs* -- arXiv:2506.07180
- *Moral Sycophancy in VLMs* -- arXiv:2602.08311
- *Sycoevalem: clinical emergency care* -- arXiv:2601.16529
- *Too Nice to Tell the Truth: role-play agreeableness* -- arXiv:2604.10733
- *Janus: goal-conditioned info distortion* -- arXiv:2606.10852
- *When AI Says It Feels* -- arXiv:2606.05734
- *OP-Bench over-personalization* -- arXiv:2601.13722
- *MM-SY (multimodal)* -- ICLR 2025
- *lechmazur/position_bias* (LLM-judge order-swap stability) -- GitHub sibling of N02
- MUSE / *It's Not Always Sycophancy* (conformity-vs-uncertainty construct critique) --
  arXiv:2605.27288 (fetched, verified-by-us as a construct-validity caveat; candidate
  `context` rather than an instrument)
