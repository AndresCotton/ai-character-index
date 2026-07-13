GOAL: Create a very clear plan on how to convert this conceptual project into a living web-page with the engine that keeps it updated and alive. We need to organize this repo so we can start building. 

## General feel 
- People visiting the site must feel: (1)that is rigorous and trustworthy, (2) that communicates a certain clarity and convergence of opinions, (3) that they can actively contribute to make it better and there are clear channels for that. (4) that our criteria and mechanisms are transparent. 

Considerations:
- We should have a way for people to submit evals that we'll score.
- We should also have a way of allowing people to appeal or "You think we made a mistake?" -> let us know.
- We should publicly promote evals that are well made.
- Changes in notion Databases should automatically produce changes on the webpage - it would be good to have a mechanism to "push into production" to prevent silly errors from transferting, but not having to manually sync duplicated files.
- I want to see a clear system design on how we'll handle new and the different parts of the project. 
- I want to have a folder where we place aesthetics considerations (e.g. font, colour palette, reference examples). No need to define these now, but i want a place where we'll discuss these.
- As part of your plan, I want to see a sketch of how info would be distributed in the page/s. If you have doubts, show me a few options.
- I want a reasonably minmimal CI/CD to make sure we can do sustainable good work. 

## Future
- Backend with include a way of getting new evals
- Evals will be automatically scored according to the rubric we have in notion

# Conceptual Project Idea
"""
# **AI character index / Model specs org**

**By Andrés Cotton**

**TL;DR:** We should have an independent org that does for **AI character** what AI Lab Watch did for lab safety practices: **a public, evidence-based index anchored in model specs**. It centralizes and **assesses evidence of spec coverage and adherence**, then makes the gaps publicly legible. That legibility is what routes technical effort toward neglected areas and holds labs accountable to their own declared targets.

<aside>
<img src="i" alt="i" width="40px" />

**Provide input →** Behaviours to track

</aside>

## Theory of Change

During and after the intelligence explosion, AI systems will be involved in almost every consequential decision: advising leaders, drafting legislation, running organisations, generating culture, researching new technologies. Small differences in AI character, aggregated across hundreds of millions of interactions or surfacing in rare but high-stakes scenarios, could have enormous effects on concentration of power, epistemics, ethical reflection, catastrophic risk, and much else that shapes society's long-term flourishing. (The Importance of AI Character, n.d.)

The main instrument we have for explicitly defining that character are **Model specs / Constitutions**, which function as a behavioral target developers can aim for. These behaviors that are set for present LLMs will have a large influence on the behavior of future, more powerful AIs. There are many reasons why this might be the case:

- **Institutional inertia**: Once a spec is written, costly consensus-building, optimized training pipelines, de-risking, and organizational pride make substantial rewrites unlikely — pushing changes toward small, iterative adjustments
- **Direct inertia**: Current LLM behaviors transfer to future models via synthetic training data and natural pretraining data, even without deliberate human choice.
- **User-and-developer inertia**: Users habituate to current behaviors and resist change; developers build systems that assume them, creating implicit standards that are very sticky.
- **Norm-setting inertia**: Widespread public knowledge of current LLM behaviors effectively works as a precedent and visible social contract

If you are interested in these arguments, their more developed version can be found here.

This inertia has an upside: effort spent now, while specs are still being written and norms are still forming, has outsized and durable leverage. This is the case for dedicated work in this direction that: (1) centralizes information about model spec coverage and spec-adherence evals, (2) makes gaps in coverage and adherence public, raising the cost of unattended areas or missing declared targets.

## Desired Outcomes

Assuming (1) and (2) go well, we'd aim for this work to:

1. Direct technical work on model specs and character evaluations to important, neglected areas (e.g., hand-off gaps/research ideas to MATS, CG, Longview)
2. Generate publicly available, easily understandable artifacts for outsiders to understand the current state of model specs and spec adherence, helping to keep labs accountable.
3. Improve the labs' model specs to cover important, neglected areas (e.g., improving model behavior in high stakes scenarios). This outcome is more long-term and requires actively engaging with these stakeholders.

## Hypotheses that need to be tested

- **Conceptual:**
    - You can come up with at least 5 important behaviors people agree on and map them clearly to the model spec.
    - You can map behaviour to evals clearly.
- **User based - Who will use this and how:**
    - Grant makers will use this to create RFPs
    - Conceptual AIS researchers like Forethought will use this to clarify scenarios and behaviours that are unattended.
    - Technical AIS researchers at SPAR, MATS [make a list of mentors and reach out directly to them] , etc. will use this to decide which evals to create
        - Can we send a survey to SPAR / MATS?
    - Labs will use it to:
        1. Improve the coverage of their specs.
        2. Direct training efforts towards the behavioural targets they are not meeting.

**Key question for stakeholders:**

- Under which conditions would you advise me in making this project succeed?
- What version of this would actually influence your work?

### Scope and Deliverables

**What do you plan to output / accomplish over the next two months?**

**Initial derisking sprint (1-2 weeks):**

- **Rubric** of how we assess the evals.
    - Potential useful sources for Eval standardization:
        - Conceptual validity.
            - RAND: Preliminary suggestions for rigorous GPAI model evaluations
            - NIST/AISI: International consensus and open questions in AI evaluations
- Doing one full sweep from one high-stake scenario -> model spec -> eval scoring
- Start thinking about how to scale it and which parts can be automated.

**Month 2 goal: a public AI-character index.** A public webpage, built in the open, in the spirit of resources like AI Lab Watch but with a neutral, METR-like framing: an index of *coverage and adherence*. v0 scope:

- Mapping of:
    - Important behaviours (our priority list, independent of whether the spec addresses them). These should be more visually salient if there's more agreement.
    - Model spec coverage: addressed, or not in spec
    - Available evidence (pre-existing evals), for behaviours the spec does address
    - Quality score of available evidence
- Compare when possible: what each major lab declares it's aiming for, sourced from published specs/constitutions and model cards -- side by side, so differences are legible.
- Adherence/transparency index: for each declared goal, how legible the target is and what evidence exists on whether models meet it -- aggregating existing third-party and lab evals rather than running our own at this stage.
- v0 uses public information only (fully independent, no lab buy-in needed); inviting labs to contribute evidence is a later potential step.

Building in public doubles as outreach -- a concrete artifact to put in front of labs, stakeholders, and potential collaborators that the mapping work identifies.

MVP will be shared within the model character community for iterative improvement and de-risking.

## Why would I be a good fit?

- It needs someone fluent across industry, academia, and non-profits and comfortable translating between technical and non-technical audiences. It matches exactly my background spanning ML engineering in industry, research management, science communication.
- I'm very good at stakeholder mapping / stakeholder engagement, I'm quick to understand the different incentives different orgs and people might have.
- Co-published a paper measuring propensity toward utilitarianism in LLMs (EMNLP 2024); relevant to operationalizing fuzzy traits into evals.

## How to measure success the next 2 months?

How many people are engaged and invested on seeing this succeed?

Are they making intros to other people or using the product directly?

## Advisor

- Main Advisor: Henry Sleight

## Open questions

- On top of coverage and adherence, a big problem in specs are contradictions.
    - Some automated tooling to address find these contradictions has been build in https://arxiv.org/abs/2510.07686.
    - How should this project address contradictions in model specs? Are these a pre-requisite to measure spec adherence?

- Prioritization. this is an ambitious project with many action directions, more work is needed to prioritize and push the sub-initiatives forward. Public legibility and stakeholder engagement and  are my clearest edge; adherence evals are more obviously useful but require more rigorous and time consuming scientific work.
- Sustainability. Solo transparency projects are launch-able but hard to maintain (AI Lab Watch's maintainer stepped back after ~a year). What keeps this updated and credible past my own involvement?
- Stakeholders. Who are all the current stakeholders involved in model spec? What's their hierarchy of influence?
    - model specs reflect consensus that likely incorporates input from many different stakeholders, including internal teams – alignment, legal, technical training, and so on; plus leadership, board, customers, external stakeholders (Inside Our Approach to the Model Spec, 2026; Stickiness in AI Behavioral Design, n.d.)
- Spec Update processes. What are the processes labs currently have for updating their model specs? What properties does that process have? There's a very vague explanation here about how OpenAI does this, I'm looking for more information.
- Claim: The important people already have enough info on the landscape -> to which extent this is true? Would they benefit from more centralized and systematic info?
- I was primarily thinking of providing signal to technical researchers to orient their efforts. However, how should this interact with policy makers? -> probably this should be done at a later stage.

*I have many more open questions, but I prefer to keep this concise…*

**Thank you for looking at my proposal!**

Behaviours to track

I really appreciate your time and input.

## References

- Hammond, L., Chan, A., Clifton, J., Hoelscher-Obermaier, J., Khan, A., McLean, E., Smith, C., Barfuss, W., Foerster, J., Gavenčiak, T., Han, T. A., Hughes, E., Kovařík, V., Kulveit, J., Leibo, J. Z., Oesterheld, C., Witt, C. S. de, Shah, N., Wellman, M., … Rahwan, I. (2025). Multi-Agent Risks from Advanced AI (arXiv:2502.14143). arXiv. https://doi.org/10.48550/arXiv.2502.14143
- Inside our approach to the Model Spec. (2026, June 17). OpenAI. https://openai.com/index/our-approach-to-the-model-spec/
- Stickiness in AI Behavioral Design. (n.d.). Forethought. Retrieved June 23, 2026, from https://www.forethought.org/research/stickiness-in-ai-behavioral-design
- The importance of AI character. (n.d.). Forethought. Retrieved June 21, 2026, from https://www.forethought.org/research/the-importance-of-ai-character

---"""