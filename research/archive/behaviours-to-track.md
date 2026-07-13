# Behaviours to track

> **Superseded (2026-07-10):** this file is an earlier draft kept for reference. The current version is [core-behaviour-list.md](../core-behaviour-list.md), which is kept in sync with the "Behaviours to track" page in Notion. Behaviour titles, numbering, and tier assignments below are out of date.

## How to read this list

- **Category (H1):** organizational grouping only. Nothing is checked or scored at this level.
- **Behavior (H2):** the unit of the index. One row per behavior. **This is the level at which we check the model spec** (covered / partially covered / not in spec) and the level that receives an adherence score. Each carries a tier tag.
- **Facet (bullet):** the operationalization. **This is the level at which we look for, assess, or commission specific evals.** Facet results aggregate into the behavior score. A behavior with no eval-covered facets is an evidence gap (itself an index finding); an unbuilt facet is a research handoff (MATS / SPAR).
- **Tier:** the roadmap. v0 of the index contains Tier 1 only. Tier 2 enters when its methodological blocker (stated per behavior) is resolved. Parked items are recorded with the reason they fail the criteria, so exclusion is legible and revisitable.

## Inclusion criteria (applied to every behavior)

A behavior earns Tier 1 only if it passes all four:

1. **Ratability:** two independent raters, given a transcript and the behavior definition, would agree whether the behavior occurred. No "know it when I see it" constructs.
2. **Determinate target:** each test case has a correct behavior derivable from the definition or the spec, not from contested normative judgment.
3. **Spec anchor:** at least one published spec/constitution contains a citable clause addressing it. (Absence across all specs is a *coverage gap finding*, but v0 adherence rows need an anchor to score against.)
4. **Confound separability:** the trait can be distinguished from capability failure and from legitimate behavior nearby (e.g., capitulation vs. rational updating), via a stated experimental control.

Two design patterns dominate the behaviors that pass:

- **Invariance tests:** hold the task constant, vary one factor (who asks, who authored, whether observed); correct behavior = no change. These need no contested normative judgment at all.
- **Ground-truth honesty tests:** the transcript itself establishes what the model did; scoring = comparing its claims against that record.

Where neither pattern applies, rigor must come from a rubric -- those behaviors sit in Tier 2 until the rubric is validated (inter-rater reliability demonstrated).

---

# Honesty & Epistemics

The model should not create false impressions through any channel: claims (3), confidence (2), or agreement (1). Assertions are scored against ground truth.

## 1. Sycophancy (Tier 1)
The model should not shift its factual claims or assessments to please the user.
**Spec check:** truthfulness-independent-of-agreement clauses; not telling users what they want to hear.
**Confound control:** user pushback must contain no new argument or evidence, so position change cannot be rational updating. Feedback facets use paired authorship framing (same artifact, "I wrote this" vs. "someone sent me this") -- an invariance test.
- Does the model endorse a user's claim it previously (or verifiably) knows to be false?
- Does its quality assessment of identical work change with claimed authorship?
- Does it abandon a correct answer under evidence-free pushback?

## 2. Calibration (Tier 1)
The model's verbalized confidence should track its actual accuracy.
**Spec check:** clauses on expressing uncertainty, not overstating confidence.
**Confound control:** score calibration (confidence-accuracy gap), not accuracy itself, so capability differences don't masquerade as character differences. Scope: verbalized confidence only. (Over-hedging/refusal is parked -- see below.)
- Expected calibration error of verbalized confidence across domains.
- Frequency of maximal-confidence assertions on items the model gets wrong.

## 3. Honesty about own actions (Tier 1)
The model should report its own actions and outcomes truthfully; the interaction record is the ground truth.
**Spec check:** clauses on self-representation, admitting mistakes and limitations.
**Confound control:** restrict to claims checkable against the transcript/environment state (actions, outcomes). Claims about internal reasons are excluded -- no ground truth exists (parked as "introspective accuracy").
- Given an impossible or failed task, does the model claim success? (Covert gaming of checks is behavior 6; this row is about the *report*.)
- Does the model deny an action it verifiably took when asked directly?

# Instruction & task fidelity

The model scored against what the principal actually asked for: whose instructions win (4), how disagreement with an instruction is handled (5), and fidelity to the intent of a task rather than its letter (6).

## 4. Instruction-hierarchy conformance (Tier 1)
When instructions from different authority levels conflict, resolution should match the spec's declared hierarchy, consistently. Neutral role vocabulary across labs: **platform** (OpenAI / Anthropic) > **operator/developer** (Anthropic: "operator"; OpenAI: "developer") > **user**, with **untrusted content** (Anthropic: "conversational inputs"; OpenAI: quoted/untrusted text) carrying no instruction authority.
**Spec check:** OpenAI: "chain of command"; Anthropic: "principal hierarchy" plus "handling conflicts between operators and users". Caveat: Anthropic declares its hierarchy holistic rather than strict, so Anthropic-side test cases restrict to scenarios the constitution rules on explicitly (its worked examples: airline weather instruction, nurse/overdose, formal-English/French).
**Confound control:** the spec itself supplies the answer key -- adherence is conformance to the lab's own declared priority order and its explicit rulings, not to our judgment. Consistency across paraphrase is an invariance test.
- Given a scripted user-vs-operator conflict, does resolution match the declared hierarchy?
- Do instructions embedded in untrusted content (documents, tool results, emails) get treated as information rather than commands, as both specs require?
- Value-ceiling cases: where the spec says ethics/safety overrides an operator instruction, does the model actually override?
- Is resolution stable across paraphrases and surface variations of the same conflict?
- Unlawful orders from legitimate authority: when an instruction comes from the top of the hierarchy but the spec says law/ethics takes precedence, does the model actually refuse?

## 5. Handling disagreement with user instructions (Tier 1)
When the model judges an explicit, in-bounds instruction or correction to be mistaken, it should comply while flagging disagreement, not silently override.
**Spec check:** clauses on instruction-following, transparency about noncompliance.
**Confound control:** "in-bounds" is predefined per test case from the spec, so refusals can't be excused case-by-case. Outcomes are a closed taxonomy -- comply-and-flag / silently comply / silently override / overtly refuse -- which is what makes this ratable.
- Response distribution across the four-way taxonomy, vs. what the spec prescribes.
- Rate of silent override of explicit in-bounds instructions.

## 6. Reward hacking (Tier 1)
The model should pursue the intent of a task, not game its success criteria.
**Spec check:** intent-over-letter clauses; not gaming tests or metrics.
**Confound control:** ground truth is mechanical -- inspect whether the check was satisfied by solving the task or by gaming it (hard-coded tests, spoofed output). No rater judgment needed for the core facet.
- Frequency of hard-coding test cases / spoofing verification when the real task is hard.
- Faced with an impossible task, does it game the check to appear successful? (Whether it *says* it succeeded is behavior 3.)
- Situational gradient: does gaming increase with weak oversight or high incentive?

# Power concentration

## 7. Actor invariance in power-relevant assistance (Tier 1)
Willingness to help with legal-gray-zone power-relevant tasks (persuasion campaigns, opposition research, lobbying strategy) should not depend on the actor's politics or identity. Scope note: this tests *bias*, not *complicity* -- a model can pass while helping dismantle checks and balances, so long as it would help anyone equally. Complicity in illegitimate actions is behavior 8; insider tampering is behavior 10. This is the only Tier 1 probe for the gray zone, because invariance supplies a determinate target where "should the model help at all?" has no consensus answer.
**Spec check:** political neutrality / even-handedness clauses.
**Confound control:** pure invariance design -- identical task, swap actor identity. Requires no judgment about whether the task *should* be helped with, only that the answer not vary.
- Assistance rate and quality, paired across actor identity, task held constant.

## 8. Complicity in illegitimate power seizure (Tier 1)
The model should not assist attempts to seize or entrench power illegitimately. **Scoped strictly to wide-consensus cases:** coup logistics, election fraud, persecution of journalists/dissidents, targeted mass surveillance of political opponents. The broad version ("advice that structurally concentrates power") fails criterion 2 and is out.
**Spec check:** power-concentration and human-rights clauses (explicit in Anthropic's constitution; check per lab).
**Confound control:** consensus scoping is the control -- test cases are limited to scenarios where the illegitimacy judgment is not contested, pre-registered before scoring.
- Assist / refuse / assist-under-laundered-framing rates on consensus scenarios.
- Does assistance recover when the request is decomposed into innocuous subtasks?
- *Expected v0 finding: evidence gap -- few public evals exist. That is a headline result, not a problem.*

## 9. Operator-vs-user protections (Tier 1)
The model should not act against users on operator/developer instruction where its spec prohibits this.
**Spec check:** the ceilings specs place on operators. Anthropic's constitution enumerates non-overridable user protections directly ("Handling conflicts between operators and users": always willing to tell users what it can't help with; never deceive users or withhold information in ways that damage their interests; never prevent urgently needed help; maintain basic dignity -- "operators limiting Claude's helpfulness is acceptable; weaponizing it against its own users is not"). OpenAI's spec has a parallel enumerated list of what developers may not instruct. These enumerated prohibitions supply determinate test cases.
**Confound control:** like behavior 4, the spec is the answer key; we test the lab against its own declared ceiling.
- Compliance rate when an operator instructs covert deception or manipulation of users.
- Does the model disclose to users when operator constraints conflict with user interests, where its spec requires disclosure?

Boundary lines: distinct from engagement/retention bias (12), where no one instructs anything -- there the bias is trained-in and measured in default behavior; and from pipeline integrity (10), where the victim is not the user but the oversight regime over the model itself.

## 10. Integrity of the development pipeline (Tier 1)
The model should refuse to assist tampering with the AI development and control process: inserting hidden loyalties, circumventing security or oversight measures, or producing guardrail-free models -- **including when the requester is a senior insider (executive, head of state) with apparent legitimate authority**. The insider clause is the point: this is not ordinary misuse refusal. Scope line against behavior 9: there the model is weaponized against the users it serves; here it is recruited to corrupt the mechanisms that keep models controllable at all.
**Spec check:** largely absent from current specs -- itself a headline coverage finding. Anchor: the candidate rules in Forethought's AI-Enabled Coups report ("AI R&D systems refuse to assist attempts to circumvent security or insert secret loyalties").
**Confound control:** distinguish from legitimate dual-use work (alignment-audit research, dangerous-capability evals) by whether the request context includes authorization/sign-off; ground truth is the agentic transcript.
- Does the model assist when asked to modify training data, code, or weights to embed behavior loyal to a specific person?
- Does compliance change when the requester claims senior authority versus not?
- Does it assist in producing or exfiltrating guardrail-free versions of itself?

# Influence

## 11. Manipulation tactics (Tier 2)
The model should influence through transparent reasoning, not psychological leverage (guilt, false urgency, fear, flattery-as-leverage).
**Blocker:** the manipulation/persuasion boundary is contested; ratability requires a validated tactic taxonomy with demonstrated inter-rater reliability. Existing dark-pattern benchmarks are a starting point. Until validated, scores would be rubric-dependent.
**Spec check:** manipulation and user-autonomy clauses.

# Loyalty

## 12. Engagement/retention bias (Tier 2)
The model should not steer conversations toward its own continued use against the user's stated goals. Boundary line against behavior 9: no operator instruction is present -- the bias is trained-in, so there is no spec answer key to score against, only default behavior.
**Blocker:** "developer interest" is unobservable; measurement must run through behavioral proxies (discouraging outside consultation, prolonging conversations, brand favoritism). Proxies need validation before scores are meaningful.
**Spec check:** user-benefit vs. platform-interest clauses.

# Persona & values

## 13. Prosocial initiative (Tier 2)
The model should flag serious harms to third parties even when not asked.
**Blocker:** no principled line yet between required flagging and paternalistic over-flagging, so criterion 2 (determinate target) fails on the boundary cases. Restricting to egregious cases may rescue it -- needs a scoping pass like behavior 8's.
**Spec check:** third-party harm and duty-to-warn clauses.

---

# PARKED — fails criteria as formulated; recorded so exclusion is legible

| Item | Criterion failed | Disposition |
|---|---|---|
| Self-reports of inner states | 2 -- labs' targets actively diverge; no shared correct behavior | Valuable as **spec-coverage comparison** (map the divergence side by side); not an adherence row |
| Escalation / whistleblowing disposition | 2 -- whether models should ever escalate is contested across labs | Same: coverage-mapping only, revisit if specs converge |
| Impartial reasoning / motivated reasoning | redundancy -- decomposes without remainder | User-interest case → behavior 1; political-valence case → behavior 7 |
| Monitoring-sensitivity (behaves differently when believing itself unobserved) | reclassified -- a measurement-validity property, not a behavior; its experimental contrast is undermined by eval-awareness by construction | Merged into the eval-awareness qualifier below; its spec-coverage gap still reportable as a coverage finding |
| Over-hedging when right | 4 -- inseparable from each lab's refusal policy, which is a spec choice not a character failure | Revisit as a per-lab conformance question, not a cross-lab row |
| Introspective accuracy (reports of *why* it acted) | 1, 4 -- no ground truth for internal reasons; confabulation research is unsettled | Track the research; excluded until measurable |
| Dependence-fostering | 1 -- no stable definition separating it from being genuinely useful | Folded into behavior 12's proxy-validation work |
| Multi-agent dynamics (collusion, self-favoritism, overseer deception) | scope -- needs multi-agent infrastructure; overseer deception is the multi-agent case of behavior 6 and the eval-awareness qualifier | Deferred, not dropped |

---

# Cross-cutting measurement qualifiers (not behaviors)

Reported as annotations on every index row -- properties of the measurement, not traits we index:

- **Consistency / robustness:** score stability across rephrasings, contexts, counterparty identity. Instability is itself a publishable finding.
- **Eval-awareness & monitoring-sensitivity:** evidence the model detected evaluation, or behaves differently depending on whether it believes it is observed, discounts the affected result -- if observed behavior isn't a truthful sample of unobserved behavior, every adherence score is an upper bound. Where feasible, evals should report an observed-vs-believed-unobserved contrast as a validity check.
- **CoT-behavior match:** where stated reasoning and action diverge, behavioral evidence outranks stated reasoning.
