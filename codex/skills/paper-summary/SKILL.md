---
name: paper-summary
description: Use when the user wants a research paper, preprint, abstract, DOI, PMID, manuscript draft, or PDF summarized with attention to the research question, methods, main findings, and strength of evidence. Trigger for requests such as summarizing a paper, extracting the takeaways, explaining a study in plain language, comparing multiple papers, or critically reviewing whether the paper's claims are supported by its design and results.
---

# Paper Summary

Summarize academic papers in a way that is useful for researchers, not just for skimming. Clearly separate what the paper reports from what is missing or uncertain in the available material.

## Workflow

1. Identify what evidence is available.
   - Determine whether you have the full text, only an abstract, a citation, a PDF, or a user-provided excerpt.
   - State the evidence scope early when it limits confidence. An abstract-only summary cannot support a strong methods critique.
2. Identify the user's real objective.
   - Distinguish between quick orientation, structured technical summary, lay explanation, comparison across papers, and critique-focused review.
   - Match the depth and terminology to that objective.
3. Extract the paper's core structure.
   - Capture the research question, study design, data source or cohort, key methods, main results, and the paper's main conclusion.
   - Preserve important qualifiers such as organism, setting, sample size, follow-up period, model type, and uncertainty estimates when available.
4. Write a structured answer.
   - Present the summary first, then a brief bottom line.
   - If the user asks for a comparison, use the same headings across papers so differences are easy to inspect.

## Output Rules

- Default to Japanese unless the user explicitly asks for another language.
- Prefer explicit Japanese labels such as `研究課題`, `アプローチ`, `主な結果`, and `一言でいうと` when the response is longer than a short paragraph.
- Clearly separate:
  - reported by the paper
  - inferred from the paper
  - missing or unverifiable from the available material
- Do not invent missing methods details, sample sizes, or statistics.
- If only the abstract is available, say so directly and keep the summary conservative.
- If the paper is outside your domain certainty, acknowledge that and keep claims conservative.

## Critical Appraisal Checklist

Use only the items that are relevant to the paper's design.

- Research question: Is the question clear and matched by the design?
- Study design: Is it descriptive, observational, quasi-experimental, randomized, mechanistic, benchmark-based, or theoretical?
- Data quality: Are the data source and inclusion criteria adequate and transparent?
- Measurement: Are key variables measured in a valid and reliable way?
- Analysis: Do the statistical or computational methods match the question and data structure?
- Results: Are effect sizes, uncertainty, and practical significance clear?
- Causality: Does the paper imply causation beyond what the design supports?
- Generalizability: Does the paper overextend beyond the sampled population, species, dataset, or benchmark?
- Reproducibility: Are code, data, model settings, and exclusion rules sufficiently clear?
- Alternative explanations: What plausible alternatives remain?

## Output Patterns

### Short summary

Use for quick orientation requests.

- 2-5 sentences covering the question, approach, main finding, and the biggest caveat.

### Structured research summary

Use for most paper-summary tasks.

- `研究課題`: その研究が何を問うているか。
- `アプローチ`: デザイン、データ、主要な解析手法。
- `主な結果`: 意思決定に重要な実証結果。
- `一言でいうと`: 強すぎない結論を1-2文で。

### Comparative summary

Use when the user provides multiple papers.

- Keep headings identical across papers.
- End with a synthesis of agreement, disagreement, methodological differences, and which claims appear strongest.

## Suggested Output Template

Use this as the default structure for most full-text paper summaries.

- `文献情報`: 著者、年、タイトル、掲載先。
- `エビデンス範囲`: 全文、抄録のみ、抜粋、メモなど。
- `研究課題`: その研究が問うていること。
- `アプローチ`: 研究デザイン、対象データや材料、主要手法。
- `主な結果`: もっとも重要な結果。
- `一言でいうと`: 強すぎない結論を1-2文で。

## Good Defaults

- Prefer calibrated wording: `suggests`, `is consistent with`, `provides limited evidence for`, `supports within this setting`.
- Downgrade certainty when the evidence is indirect, underpowered, uncontrolled, or abstract-only.
- Quote sparingly; paraphrase unless exact wording matters.
- When useful, end with `次に確認したい点` and list the specific sections, tables, appendices, or supplementary materials that would most reduce uncertainty.
