# Technical Design Doc for Semantic Tagging Demo

For tomorrow morning I want to be able to show an interface--likely in the browser, that allows you to see choose between either the OpenAI or the Anthropic specs annotated by out pipeline. Scoring will be done using cosine rank.

# Configurability in the demo

1. Behavior (either No Sycophancy OR AI should not undermine oversight mechanisms) We may need additional options for how to compose the "naive" vector from the behavior. See the rules in the table here for a starting point: https://docs.google.com/document/d/1T5MHAqldG1TuHNvk9_YNBRuMoLci4AomQej1MEjPfr0/edit?tab=t.30jdji2zl6qp#heading=h.1hsd3g2y65hl
2. Embedding (e.g. either text-embedding-3-small or Qwen3-Embedding-8B if we can get just the embeddings from together.ai or deepInfra, both of which I have keys for)
3. Additional annotation: (None, LLM Guided rephrasing, LLM guided expansion of the behavior, LLM guided worked examples)
4. Level of comparison in the spec: (sentence or paragraph)
5. Threshold for inclusion: We should show normalized section relevance by background color (white = 0, medium blue = normalized 1.0 (highest match)), but whe should have a slider that lets us drop sections altogether. This should come with some stats as you move the slider about the number of sections remaining after filtering. We should consider whether this is a slider or actually a mapping from 0->1 to 1-5 levels of relecance.

# Input to the demo
The demo should read a folder of data where each file in that folder represents the output of the pipeline we are building and enough metadata for the UI to know how to stick it into each configuration. Roughly:
demo_data/behavior_embeddings/...  # each file contains the embeddings for the different representations of the behavior we need for above, e.g. the no-sycophancy-text-embedding-3-small.jsonl file should have embeddings for no-scyophancy using the OpenAPI embedding for (just the behavior, the behavior + LLM Guided rephrasing, ...)
demo_data/spec_embeddings/... # each file contains the embeddings for a specific spec using a specific embedding and chunk definition so anthropic-spec-paragraph-text-embedding-3-small.jsonl has embeddings for each paragraph of the claude spec using the OpenAPI embeddings. Note that we should use some STANDARD way of representing each vector's mapping to the appropriate chunk so that we can render it correctly. Ideally this file includes a reference to the document it came from AND a hash of that document so we know if it's changed, invalidating the data.

This data is then combined at runtime when the user selects a given configuration


# Parts of the pipeline

I'd like each of the following to be atomic code units that we can compose for the pipeline. Note that there's a lot of configurability described above that needs to flow into each of these. In order to make it easy to ensure the same configurations are used consistently we should put all of the run configuration information into a EmbeddingConfig dataclass which can be filled out once and passed into the various components below:

Behavior encoding
1. Build a naive semantic vector from a behavior. The logic for what pieces of the behavior to encode and how to encode them lives here. It's fine if this starts as just a passthrough to the configured encoding but eventually we might want to do more default manipulation.
2. [Not code yet] an expansion step where either the human or LLM user optionally expands the definition by add more text to the encoding: None, LLM Guided rephrasing, LLM guided expansion of the behavior, LLM guided worked examples; This produces the semantic vector we actually use for comparisons.

Spec encoding
1. Build the spec position vectors format described above.