---
name: migrate-qmd-references
description: Quarto / QMD 文書でベタ打ちされた著者年引用、DOI、手書き参考文献節を、共有 `references.bib` と Pandoc/Quarto citation syntax (`[@citekey]`, `@citekey`, `[-@citekey]`) に移行する。Use when Codex needs to clean up `.qmd` chapters that already have or should have a project bibliography, append BibTeX entries, search bibliographic metadata, and replace manual `References` / `参考文献` lists with Quarto-managed references.
---

# Migrate QMD References

## Quick Start

- 読む: `references/project-conventions.md`
- 監査する: `python3 scripts/audit_qmd_references.py /path/to/project`
- `book.chapters` だけでなく全 `qmd` を見たいときは `python3 scripts/audit_qmd_references.py /path/to/project --all-qmd`
- JSON が必要なときは `python3 scripts/audit_qmd_references.py /path/to/project --json`

## Default Workflow

1. `_quarto.yml` を読み、`bibliography:` と `book.chapters:` を確認する。
2. 既存 `references.bib` を先に再利用する。既存キーで足りる引用には新規 BibTeX を作らない。
3. `scripts/audit_qmd_references.py` を実行し、対象ファイル、手書き引用、参考文献節、DOI、有力な既存キー候補を把握する。
4. 章ごとに処理する。大きな章を一気に変えず、引用置換と参考文献追加を小さく区切る。
5. 置換後に未解決 `@citekey`、重複 BibTeX、残存する手書き参考文献節を確認する。

## Migration Rules

### 既存 BibTeX を優先する

- 既存 `references.bib` に著者・年・タイトルが整合する項目があるなら、そのキーを使う。
- 既存キーが複数候補になるときは、タイトルか掲載誌まで確認する。年と筆頭著者だけで決め打ちしない。
- 既存エントリが不完全でも DOI が正しいなら、重複追加より既存修正を優先する。

### DOI があるとき

- DOI を本文、脚注、図注、手書き参考文献節から抽出する。
- DOI から文献情報を取得し、`references.bib` に BibTeX を追加または更新する。
- DOI 取得結果と本文の主張が食い違うときは、誤 DOI・誤引用の可能性を疑う。
- 本文は Quarto citation syntax へ置換する。

例:

- `(Leake 2005)` -> `[@leake2005]`
- `Leake (2005)` -> `@leake2005`
- `(Taylor and Bruns 1997; McKendrick et al. 2002)` -> `[@taylor1997; @mckendrick2002]`
- `Zimmer et al. (2007)` -> `@zimmer2007`

### DOI がないとき

- 手書き参考文献節か本文から、著者・年・タイトル・誌名・巻号・ページを拾う。
- Crossref などで書誌情報を検索する。
- 著者、年、タイトルの主要語、掲載誌の少なくとも 3 要素が整合する場合のみ採用する。
- 曖昧な候補しかないときは、無理に追加せず、候補を短く列挙してユーザー確認を求める。
- 書誌情報が十分に確定できたら `references.bib` に追加し、本文を `[@citekey]` 系へ置換する。

### 手書き参考文献節を消す

- 手書きの `## References` / `## 参考文献` / `### 参考文献（References）` の本文は削除する。
- 文末の参考文献位置を固定したいときだけ、見出しと空の refs div を残す。

```markdown
## References
::: {#refs}
:::
```

- 位置にこだわらないなら、見出し自体も削除し、Quarto に末尾生成させる。
- Quarto 管理の参考文献と手書きリストを二重に残さない。

## Validation

- すべての新規 `@citekey` が `references.bib` に存在することを確認する。
- 手書きの著者年表記が残っていないか再検索する。
- `scripts/audit_qmd_references.py` を再実行し、未解決候補と手書き参考文献節が減っていることを確認する。
- 可能なら Quarto をレンダリングし、未解決引用や重複参考文献がないか確認する。

## Repo-Specific Notes

- この repo では `_quarto.yml` に `bibliography: references.bib` が既にある。設定を足すより、本文と参考文献節を正規化することが主作業になる。
- この repo では `comps/` 配下にも `qmd` があるが、既定では `book.chapters` 外なので触らない。比較用成果物まで直す必要があるときだけ `--all-qmd` を使う。
- 既存本文には Quarto citation syntax とベタ打ち引用が混在している。章ごとに置換ルールが揺れていないか確認する。
- 和訳された参考文献節には原題が崩れている行や途中で省略された行がある。DOI がない案件ほど誤同定の危険が高い。
