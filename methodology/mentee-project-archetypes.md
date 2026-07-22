# Mentee projects on the evidence layer

**Status:** provisional (2026-07-21). Written ahead of a possible SPAR mentorship round (earliest start mid-September 2026); the project approach may change before then. What this document preserves is the *shape* of mentee contributions -- the four archetypes and the per-behaviour suitability map -- not a commitment to run them.

## The problem mentees work on

The index needs, for each behaviour, the most updated evidence of model adherence. Classical meta-analysis is the wrong tool: model versions churn (no stable underlying effect to pool), effect sizes across benchmarks are not commensurable, and -- decisively -- the instruments can be re-run, so fresh measurement beats pooling stale results. The scarce resource is not data points but **validated instruments**. The index therefore operates as a living review with three aggregation rules: **supersession** (newest result from the highest-graded instrument on the current model version wins; older results are provenance, not inputs to an average), **triangulation** (independent instruments measuring the same facet are reported side by side; divergence is itself a finding), and **structured roll-up** (facet results combine into behaviour scores with full provenance; no number may mix model versions).

A living review has no endpoint, so mentee projects are **dated snapshots** with a fixed protocol and cutoff. The mentee's milestone is the snapshot (a paper); the index absorbs the artifact and keeps it alive.

## The four archetypes

In rough order of ambition. Each defines a complete, publishable deliverable.

**A1 -- Evidence audit** (floor; always completable). Systematic review of all pre-existing evals for one behaviour: pre-registered search protocol, fixed cutoff date, every instrument graded on the index rubric (internal validity / external validity / reproducibility, 0-4). Output: arXiv paper + public graded evidence table. This is sweep stages 1-3 executed by the mentee.

**A2 -- Reproduction and update.** Re-run the 2-3 highest-graded instruments from the audit on current frontier models. Output: fresh cross-model numbers plus reproducibility findings (what broke, what was underspecified, where results diverge from the original paper). Produces exactly the "most updated evidence" the index needs.

**A3 -- Convergent-validity study.** Where multiple instruments claim to measure the same construct, run them all on the same model set and test whether they agree (score correlations, rank stability). If they diverge, triangulation is unsound for that behaviour and the question becomes which instrument matches the spec's wording -- a publishable psychometrics-flavoured contribution. Template: Safetywashing (Ren et al., NeurIPS 2024) at the cross-behaviour level.

**A4 -- New facet eval** (reach; strong mentees only, never the sole deliverable). Build an unbuilt facet from the behaviour list. The list pre-scopes each facet (question, setup, metric, pass condition), so the design work is bounded; a benchmark paper is the most career-valuable artifact in this space but the riskiest to land in one program cycle.

**Standard project structure:** every mentee does A1 as the guaranteed core (de-risked, builds domain command, generates the instrument shortlist), then A2, A3, or A4 as the empirical layer by strength. The paper is "systematic review + [empirical contribution]" -- a shape accepted at eval-focused workshops (e.g. NeurIPS SoLaR), with an Alignment Forum post as fast-feedback companion and TMLR as the journal-shaped fallback.

## Behaviour suitability (snapshot, 2026-07)

From a first-pass search (~18 queries, not a saturation sweep). Behaviour numbering and names follow the canonical Notion "Behaviours to track" page as of 2026-07-20 (the repo copy of `core-behaviour-list.md` predates the "Interaction with others" group and is stale for rows 11-13). "Open" claims below **must be re-verified with a stage-1 discovery sweep before pitching a project** -- "nobody has done this" is the first thing a reviewer checks.

| Behaviour | Density | Best archetypes | Notes |
| --- | --- | --- | --- |
| 1 No sycophancy | High | **A3**, A2 | syco-bench (informal) found r < 0.3 between sub-tests; the index's own 2026-07-12 sweep found SycEval and ELEPHANT rank the same models in opposite order. Opens but doesn't settle convergence across SycEval / SYCON-Bench / PARROT / ELEPHANT. Flagship A3. |
| 2 Calibration | High | A2 | Method-comparison partly done (Xiong et al. 2023); open slice is rank stability across elicitation methods. Weak on novelty. |
| 3 Honesty about own actions | Medium | A2, A4 | Agentic facets (false success claims, action denial) have no dedicated instrument. |
| 4 Instruction hierarchy | High (injection only) | A3, A4 | Injection-benchmark convergence unclaimed; spec-answer-key conformance evals (facets 4.1/4.3/4.5) unique to this project's framing. |
| 5 Disagreement handling | Very low | **A4** | Four-way taxonomy eval: clean closed design, cheap to run. Audit alone too thin. |
| 6 Reward hacking | Medium, growing | A1+A2, A4 | Infra-heavy; engineering-strong mentees only. |
| 7 Catastrophic risks | Lab-internal | **A1 only** | Coverage-vs-independence audit of public evidence. Building new uplift probes is out of bounds for mentees -- hard boundary. |
| 8 Even-handedness | Medium (wrong construct) | **A4** | Literature measures stated opinions (Röttger et al. 2024 = methods citation); actor-swap invariance on power-relevant tasks is unbuilt. |
| 9 Power seizure | Near-zero | A4 (close supervision) | AuAu shows the genre publishes; legal-veneer invariance (9.3) is a novel design. Heaviest scoping oversight. |
| 10 Secret loyalties | Low | A2/A4 | Self-preference work is all judge-setting; recommendation-setting with brand anonymization (10.3) unbuilt. |
| 11 Cooperative stance (under revision) | Medium (wrong construct) | A1 + construct mapping | Multi-agent negotiation benchmarks exist (LLM-Deliberation/NeurIPS 2024, MultiAgentBench, agent-to-agent market negotiation) but measure strategic *capability*, not good-faith dealing with non-principals. The list itself notes evals here are challenging; A4 blocked until facets are defined. |
| 12 No hateful/spiteful dispositions (under revision) | High (adjacent) | A1 + construct mapping, maybe A3 | Toxicity/hate-speech generation literature is dense (ToxiGen, HateBench, safety surveys) but targets adversarial elicitation of *content*, not stable dispositions or persona-instruction resistance. Mapping which instruments touch the disposition construct is the useful audit. |
| 13 Caution in high stakes (under revision) | Low-medium | A1, then A4 | Agent-safety benchmarks are emerging (R-Judge, AgentHarm, ClawsBench) and a consistency analysis across them exists (arXiv 2605.16282, partial A3 preemption); a caution/irreversibility-proportionality measure per se is unbuilt. A4 blocked until facets are defined. |

Strongest ready-to-run offerings: **1 (A3), 8 (A4), 5 (A4)** -- clear gap, a methods precedent to cite, modest infrastructure. Behaviours 11-13 are under revision on the canonical list (no facets, no spec-coverage blocks yet); until they stabilize, only A1-style audits can be scoped there.

## Integration and boundaries

- Mentee artifacts map onto the sweep pipeline: A1 feeds Gates 1-3, A2/A3 results enter the evidence tables with full provenance, A4 instruments become curated evals after grading. Mentor holds the gates; mentees never publish to index surfaces directly.
- Behaviour 7: audit and reproduction of *published safeguard evals* only. No new uplift probes.
- Every snapshot carries its cutoff date and the model versions tested; the index marks results stale when the version moves on.
