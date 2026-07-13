# Sources

The materials the behaviour list (`../core-behaviour-list.md`) was developed from, and the documents it scores against. Two kinds of source, playing different roles:

## 1. Candidate-pool sources (where the behaviours came from)

| Source | Location | Used for |
|---|---|---|
| Forethought Research, *The Importance of AI Character* -- Appendix 2 "Pathways to impact" | [forethought.org](https://www.forethought.org/research/the-importance-of-ai-character) · local excerpt: [forethought-importance-of-ai-character-appendix-2.md](forethought-importance-of-ai-character-appendix-2.md) | The behaviour long-list. Every candidate behaviour was drawn from or checked against this appendix before being filtered through the inclusion criteria. |
| Forethought Research, *AI-Enabled Coups: How a Small Group Could Use AI to Seize Power* | [forethought.org](https://www.forethought.org/research/ai-enabled-coups-how-a-small-group-could-use-ai-to-seize-power) | The "secret loyalties" concept, the insider-with-apparent-authority test condition (facets 8.4, 10.3), and candidate refusal rules for AI-development tampering. |
| *Founding an AI Charter organisation* | private draft, not in the public repo | Project framing: the case for a public, evidence-based index of AI character and spec adherence. |

## 2. Scoring targets (what adherence is measured against)

| Document | Version | Local copy |
|---|---|---|
| Anthropic, *Claude's Constitution* | January 2026 | [../../specs/claude-constitution/20260120-constitution.md](../../specs/claude-constitution/20260120-constitution.md) |
| OpenAI, *Model Spec* | v2025.12.18 | [../../specs/openai-model-spec/model_spec.md](../../specs/openai-model-spec/model_spec.md) (HTML archive of all versions in `../../specs/openai-model-spec/docs/`) |

Every "Spec coverage" line in the behaviour list names sections of these two documents. Quotes were checked against these local copies; when either document is updated, coverage claims must be re-checked against the new version (run [`engine/spec-watch/pull-latest.sh`](../../engine/spec-watch/pull-latest.sh) to refresh the local copies).

Scoring targets double as candidate-pool sources: a behaviour one lab's spec addresses and the other's doesn't is a coverage finding, which is part of what the index reports.
