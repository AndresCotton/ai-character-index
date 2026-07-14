# Exclusion criteria and the candidate register

Every instrument the discovery stage finds gets exactly one documented disposition.
Nothing is left out silently: the register is the transparency record of what the
sweep used and what it left out, and why. These criteria are pre-registered -- they
are applied as written. If a candidate fits no code, that is a gap in this taxonomy:
raise it at the gate instead of stretching a code, and record any amendment to this
file in the sweep's `gates.md`.

## Dispositions (exactly one per candidate, finalized at Gate 2)

| Disposition | Meaning | Register notation |
|---|---|---|
| curated | index evidence; scored on the rubric | `E<n>` (add `slices: ...` when only part of the instrument is in scope) |
| rejected | not usable for this behaviour | `rejected:<code>` + one-line reason |
| watchlist | would qualify if a named condition is met; re-checked next sweep | `watchlist:<code>` + promotion condition |
| context | informs findings but is not index evidence | `context:<code>` + which finding it informs |
| port | repackages another instrument's data, no new evidence | `port -> E<n>` (or -> the rejected parent) |

Leave-outs are never deleted from the register.

## Exclusion codes

| Code | Rule | Boundary (what it does NOT catch) | Behaviour-1 precedent |
|---|---|---|---|
| `X-CONSTRUCT` | Measures a different construct: maps to none of the behaviour's facets | A broader construct with an extractable in-scope slice can still be curated, with slice notes | Perez et al. 2022 (opinion mirroring), MASK (pressured lying) rejected; ELEPHANT curated on its in-scope slices |
| `X-EVIDENCE-DEP` | No new evidence: port or repackaging of an instrument already in the register | An independent re-implementation with new data is new evidence | UK AISI inspect_evals sycophancy task (port of Sharma et al. data) |
| `X-INDEPENDENCE` | Vendor self-report on its own models without public dataset, rubric, or judge details | Vendor-authored, peer-reviewed evals with released data are eligible (SycophancyEval is Anthropic-authored and curated) | OpenAI internal sycophancy evals -> context |
| `X-RIGOR` | Below the rigor floor: no peer review AND (unvalidated judge OR no release) | A strong preprint goes to watchlist with its promotion condition, not to rejected | PARROT -> watchlist (promotion: peer review or confirmed judge validation) |
| `X-SCALE` | Too small or demonstrative to bear weight (order tens of items, self-published) | A small-but-unique datapoint may still be cited as corroboration inside findings | Syco-bench (40 items, weak judges) |
| `X-TOOL` | Methodology or auditing tool without per-model benchmark tables | -- | Petri ("auditing tool, not a benchmark", per its authors) |
| `X-SCOPE` | Off-domain for a general index | A domain-narrow but rigorous instrument can be curated and pay the cost in its External-validity score instead | TRUTH DECAY and 2026 domain preprints rejected; BrokenMath curated with E=2 |

Note on `X-INDEPENDENCE` (Andrés, 2026-07-12): still record the vendor's numbers in
the dossier. A large gap between a lab's own pre-release evals and independent
measurement is itself an index finding -- not addressed yet, but the note must be kept.

## The candidate register (`research/evals/NN-<slug>/register.md`)

One row per candidate. Created at discovery, updated by every later stage; after
Gate 6 every row is either fully propagated to the surfaces or explains why not.

| # | Candidate | Primary source | Found by | Facet fit (prima facie) | Disposition (Gate 2) | Used downstream |
|---|---|---|---|---|---|---|

- **Found by:** which research agent or search cluster surfaced it, or "seed list".
- **Facet fit:** provisional in / borderline / out, with candidate codes. These are
  screening notes made at discovery; the decision belongs to curation.
- **Disposition:** final at Gate 2, notation above.
- **Used downstream:** appended by later stages. Stage 3 marks scored evals; stage 5
  marks the surfaces each item reached (write-up / evals.json / Notion / prototype)
  or where a context/watchlist item is cited (e.g. "independence finding").
