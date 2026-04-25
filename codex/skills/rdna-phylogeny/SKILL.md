---
name: rdna-phylogeny
description: Recommend reproducible rDNA phylogenetic tree inference workflows for SSU, ITS, ITS1, 5.8S, ITS2, LSU, D1/D2, and concatenated SSU+ITS+LSU datasets. Use when the user asks how to choose or compare MAFFT L-INS-i, MAFFT E-INS-i, PRANK, ClipKIT, trimAl, and IQ-TREE3 for rDNA alignment, trimming, partitioned concatenation, command examples, sensitivity analyses, Methods text, or Japanese execution reports.
---

# rDNA Phylogeny

## Core Rule

Treat SSU, ITS, and LSU as biologically different regions. Do not recommend aligning concatenated SSU+ITS+LSU in one pass. Align and trim each region separately, then concatenate if needed and infer trees with IQ-TREE3 using partitions.

Before choosing or running a pipeline, confirm the rDNA region with the user. Ask whether the data are SSU, ITS, ITS1, 5.8S, ITS2, LSU, D1/D2, concatenated SSU+ITS+LSU, or unknown. If file contents, filenames, or metadata strongly suggest a region, state it only as a tentative inference and ask for confirmation before executing region-specific commands. Do not treat inferred region identity as confirmed unless the user explicitly agrees.

Before concluding that required tools are unavailable, check both the active PATH and conda/mamba environments. Software such as MAFFT, PRANK, ClipKIT, trimAl, and IQ-TREE3 may be installed inside named environments even when it is not visible in the current shell.

When writing execution reports, do not include a full list of conda/mamba environments that were checked. Report only the software actually used, its version when available, and whether it came from PATH or a specific conda/mamba environment.

Default combined workflow:

```text
SSU: MAFFT L-INS-i -> ClipKIT smart-gap
ITS: PRANK -F -> ClipKIT smart-gap
LSU: MAFFT L-INS-i -> ClipKIT smart-gap
then concatenate -> IQ-TREE3 partition model
```

Use `-m MFP` for single-region analyses. Use `-m MFP+MERGE` with a partition file for concatenated analyses.

## Decision Table

| Input or condition | Recommended pipeline |
| --- | --- |
| SSU, ordinary conserved dataset | MAFFT L-INS-i -> ClipKIT smart-gap -> IQ-TREE3 |
| SSU with distant taxa, long variable regions, partial sequences, or distant outgroup | MAFFT E-INS-i -> ClipKIT smart-gap -> IQ-TREE3 |
| ITS, ordinary indel-rich spacer dataset | PRANK -F -> ClipKIT smart-gap -> IQ-TREE3 |
| ITS when PRANK is avoided, unstable, too slow, or reproducibility/speed is prioritized | MAFFT E-INS-i -> ClipKIT smart-gap -> IQ-TREE3 |
| ITS among very close taxa with small length differences and few indels | Compare MAFFT L-INS-i as a sensitivity analysis |
| LSU, conserved or ordinary LSU dataset | MAFFT L-INS-i -> ClipKIT smart-gap -> IQ-TREE3 |
| LSU containing D1/D2, expansion segments, many variable regions, large length differences, partials, or distant taxa | MAFFT E-INS-i -> ClipKIT smart-gap -> IQ-TREE3 |
| SSU+ITS+LSU | Region-wise alignment and trimming -> concatenate -> IQ-TREE3 partition model |

## Aligner Choice

Prefer MAFFT L-INS-i for conserved regions with similar sequence lengths: SSU, 5.8S, conserved LSU, and close-taxon datasets with few large indels.

Prefer MAFFT E-INS-i for regions with long gaps, large unalignable blocks, partial/full-length mixtures, distant taxa, D1/D2, LSU expansion segments, or ITS when PRANK is not used.

Prefer PRANK `-F` for ITS and other indel-rich spacer regions when preserving insertion/deletion structure matters. Note that PRANK is guide-tree sensitive; treat clades recovered only under PRANK as alignment-sensitive unless corroborated by MAFFT E-INS-i or other evidence.

## Trimming Choice

Use ClipKIT `smart-gap` as the default light trimming method for rDNA. It is usually easier to justify than strict trimming because it reduces obvious gap-dominated noise without automatically discarding most indel-rich signal.

After PRANK, avoid strong trimming. Rank options as:

```text
1. PRANK raw
2. PRANK + ClipKIT smart-gap
3. PRANK + trimAl gappyout
```

Avoid trimAl `strict` and `strictplus` as primary rDNA analyses, especially for ITS. If trimAl is used as a comparison, prefer `gappyout` and treat it as a sensitivity analysis rather than the default.

## Commands

Tool discovery checklist:

```bash
command -v mafft prank clipkit trimal iqtree3 iqtree2
command -v conda && conda env list
command -v mamba && mamba env list
conda run -n ENV_NAME sh -lc 'command -v mafft'
conda run -n ENV_NAME sh -lc 'command -v prank'
conda run -n ENV_NAME sh -lc 'command -v clipkit'
conda run -n ENV_NAME sh -lc 'command -v trimal'
conda run -n ENV_NAME sh -lc 'command -v iqtree3'
mamba run -n ENV_NAME sh -lc 'command -v mafft'
mamba run -n ENV_NAME sh -lc 'command -v prank'
mamba run -n ENV_NAME sh -lc 'command -v clipkit'
mamba run -n ENV_NAME sh -lc 'command -v trimal'
mamba run -n ENV_NAME sh -lc 'command -v iqtree3'
```

Use the relevant `conda run -n ENV_NAME ...` or `mamba run -n ENV_NAME ...` prefix in executable commands if the required software is only available inside that environment.

SSU or conserved LSU with MAFFT L-INS-i:

```bash
mafft --localpair --maxiterate 1000 SSU.fasta > SSU.linsi.fa
clipkit SSU.linsi.fa -m smart-gap -o SSU.linsi.clipkit.fa
iqtree3 -s SSU.linsi.clipkit.fa -m MFP -B 1000 -alrt 1000 -T AUTO --prefix SSU_linsi_clipkit
```

ITS with PRANK:

```bash
prank -d=ITS.fasta -o=ITS_prank -F
clipkit ITS_prank.best.fas -m smart-gap -o ITS_prank.clipkit.fa
iqtree3 -s ITS_prank.clipkit.fa -m MFP -B 1000 -alrt 1000 -T AUTO --prefix ITS_prank_clipkit
```

ITS, variable SSU, or variable LSU with MAFFT E-INS-i:

```bash
mafft --genafpair --maxiterate 1000 --ep 0 ITS.fasta > ITS.einsi.fa
clipkit ITS.einsi.fa -m smart-gap -o ITS.einsi.clipkit.fa
iqtree3 -s ITS.einsi.clipkit.fa -m MFP -B 1000 -alrt 1000 -T AUTO --prefix ITS_einsi_clipkit
```

Concatenated rDNA:

```bash
iqtree3 -s rDNA_concat.fa -p partitions.nex -m MFP+MERGE -B 1000 -alrt 1000 -T AUTO --prefix rDNA_concat
```

Partition file example:

```text
DNA, SSU = 1-1700
DNA, ITS = 1701-2400
DNA, LSU = 2401-3400
```

## Sensitivity Analysis

For publication-grade or consequential conclusions, recommend a minimal sensitivity analysis instead of a single topology.

ITS:

```text
PRANK raw
PRANK + ClipKIT smart-gap
MAFFT E-INS-i raw
MAFFT E-INS-i + ClipKIT smart-gap
```

SSU or LSU:

```text
MAFFT L-INS-i + ClipKIT smart-gap
MAFFT E-INS-i + ClipKIT smart-gap
```

When the user asks for "only the best" or a rapid preliminary analysis, provide the default recommendation first and mention sensitivity analysis only briefly as a caveat.

## Output Patterns

For a concise answer, give the pipeline only:

```text
SSU: MAFFT L-INS-i -> ClipKIT smart-gap -> IQ-TREE3
ITS: PRANK -F -> ClipKIT smart-gap -> IQ-TREE3
LSU: MAFFT L-INS-i -> ClipKIT smart-gap -> IQ-TREE3
```

For a command request, provide executable command blocks and adapt file names to the user's input when possible.

For a Methods request, write concise English prose based only on the selected optimal/recommended analysis and tree. If sensitivity analyses were run, do not include alternative aligners, trimming methods, or non-recommended trees in the Methods draft unless the user explicitly asks for sensitivity-analysis methods or full supplementary methods. Sensitivity analyses should be described separately in results, caveats, or a sensitivity-analysis section.

For the default optimal workflow, provide prose similar to:

```text
SSU and LSU sequences were aligned using MAFFT L-INS-i, whereas ITS sequences were aligned using PRANK with the -F option to account for indel-rich spacer regions. Alignments were lightly trimmed using ClipKIT in smart-gap mode. Phylogenetic trees were inferred with IQ-TREE3 using ModelFinder, 1,000 ultrafast bootstrap replicates, and 1,000 SH-aLRT replicates. For concatenated analyses, SSU, ITS, and LSU were treated as separate partitions.
```

For an execution report, reproducibility report, analysis log, or result summary request, output a Japanese Markdown report using the template below. Keep unknown fields as blank placeholders rather than inventing values. Keep command lines, model names, file paths, software names, and formal Methods prose in their original language when needed, but write section headings, interpretation, caveats, and conclusions in Japanese.

````markdown
# rDNA 系統推定 実行レポート

## 1. 解析概要

- プロジェクト:
- 実行日:
- 目的:
- データセット種別: SSU / ITS / LSU / rDNA 連結
- 領域確認: ユーザー確認済み / 確認待ち / 未確認で実行不可
- 領域推定根拠:
- 解析レベル: 予備解析 / 論文用
- 主な問い:

## 2. 入力データ

| 領域 | 入力ファイル | 配列数 | 長さ範囲 | partial 配列 | 備考 |
|---|---:|---:|---:|---:|---|
| SSU |  |  |  | yes/no |  |
| ITS |  |  |  | yes/no |  |
| LSU |  |  |  | yes/no |  |

## 3. パイプライン選択

| 領域 | アライメント法 | トリミング | 選択理由 |
|---|---|---|---|
| SSU | MAFFT L-INS-i / E-INS-i | ClipKIT smart-gap |  |
| ITS | PRANK -F / MAFFT E-INS-i | ClipKIT smart-gap |  |
| LSU | MAFFT L-INS-i / E-INS-i | ClipKIT smart-gap |  |

判断メモ:

- SSU、ITS、LSU は保存性、indel 頻度、長さ変異が異なるため、領域別にアライメントした。
- 連結解析を行った場合は、SSU、ITS、LSU を別 partition として扱った。

## 4. 実行コマンド

```bash
# アライメント

# トリミング

# 系統樹推定
```

## 5. アライメントとトリミングの要約

| 領域 | raw alignment 長 | trimming 後の長さ | 保持 sites | 主な懸念 |
|---|---:|---:|---:|---|
| SSU |  |  |  |  |
| ITS |  |  |  |  |
| LSU |  |  |  |  |

## 6. IQ-TREE3 設定

- 解析タイプ: 単一領域 / partition 付き連結解析
- モデル設定: MFP / MFP+MERGE
- support 指標: UFBoot 1000, SH-aLRT 1000
- partition file:
- prefix:
- ソフトウェアバージョン:
- ソフトウェア探索: PATH / conda / mamba（使用したソフトウェアと検出場所のみ。確認した環境一覧は不要）

## 7. 結果要約

- 主な tree file:
- 最適モデル:
- 強く支持された主要 clade:
- support が弱い、または不安定な node:
- outgroup の挙動:

## 8. 感度分析

| 比較 | topology は変化したか | support は変化したか | 解釈 |
|---|---|---|---|
| PRANK raw vs PRANK + ClipKIT |  |  |  |
| PRANK vs MAFFT E-INS-i |  |  |  |
| L-INS-i vs E-INS-i |  |  |  |

## 9. 批判的評価

- alignment strategy への感受性:
- trimming への感受性:
- taxon sampling の限界:
- partial sequence の影響:
- outgroup に関する懸念:
- 高い support が頑健な signal を反映しているのか、alignment/trimming 由来の artifact である可能性:

## 10. 再現性に必要なファイル

| ファイル種別 | パス |
|---|---|
| Input FASTA |  |
| Aligned FASTA |  |
| Trimmed FASTA |  |
| Partition file |  |
| IQ-TREE log |  |
| Tree file |  |

## 11. Methods 草稿（最適解析のみ）

推奨 tree / 最適解析に使った alignment、trimming、IQ-TREE 設定のみを記述する。感度分析で実行した代替 aligner、代替 trimming、非推奨 tree はここには含めない。

SSU and LSU sequences were aligned using MAFFT L-INS-i, whereas ITS sequences were aligned using PRANK with the -F option to account for indel-rich spacer regions. Alignments were lightly trimmed using ClipKIT in smart-gap mode. Phylogenetic trees were inferred with IQ-TREE3 using ModelFinder, 1,000 ultrafast bootstrap replicates, and 1,000 SH-aLRT replicates. For concatenated analyses, SSU, ITS, and LSU were treated as separate partitions.

## 12. 結論

- 推奨 tree:
- 信頼度: 高 / 中 / 低
- 信頼度判断の主な理由:
- 残る caveat:
````

For a critical review or interpretation request, explicitly discuss:

- Whether the alignment method is appropriate for the region and taxon depth.
- Whether trimming may remove true indel signal or retain non-homologous noise.
- Whether high support values may be an artifact of over-trimming, model choice, or alignment-sensitive sites.
- Whether topology changes across aligners or trimming strategies make the conclusion alignment-sensitive.

## Critical Caveats

Always surface relevant caveats without overstating them:

- PRANK often suits ITS, but it is guide-tree dependent.
- Strong trimming after PRANK may remove the indel structure PRANK was chosen to preserve.
- Increased bootstrap or SH-aLRT support does not automatically imply better biological signal.
- A clade supported only by one alignment strategy should be treated as provisional.
- Region-wise alignment is usually more defensible than one-pass rDNA concatenated alignment.
