# Decision-trial results

Ten purposively selected scenarios × two local models × three seeds × four conditions = 240 trials. These are simulated multiple-choice maintenance decisions, with optional simulated source reads. They are not independent samples of everyday agent performance. Higher correct-decision counts are better; fewer tokens/turns are useful only when decisions remain correct. All errors count in the denominator.

| Model | Condition | Correct / 30 | Read actions | Mean prompt tokens across turns | Median seconds |
|---|---|---:|---:|---:|---:|
| qwen3.5:4b | none | 24 / 30 | 14 | 378 | 2.532 |
| qwen3.5:4b | baseline | 25 / 30 | 3 | 493.2 | 2.958 |
| qwen3.5:4b | transport | 25 / 30 | 0 | 455.2 | 2.904 |
| qwen3.5:4b | repaired | 26 / 30 | 20 | 1490.7 | 5.022 |
| gemma3:4b | none | 16 / 30 | 23 | 454.9 | 1.899 |
| gemma3:4b | baseline | 23 / 30 | 12 | 875 | 1.961 |
| gemma3:4b | transport | 24 / 30 | 6 | 708.6 | 2.104 |
| gemma3:4b | repaired | 21 / 30 | 6 | 799.5 | 2.236 |

`none`: no remembered context. `baseline`: original hook. `transport`: same original formatting and instructions, but the 500-character preview survives newlines. `repaired`: preserved text plus source/force/speaker/full ID, truncation labels and historical-context guidance. Retrieval is held fixed to the selected record. The repair is not a claim to equal input tokens; actual counts are above.

| Scenario | No memory / 6 | Original / 6 | Transport / 6 | Full repair / 6 |
|---|---:|---:|---:|---:|
| rename | 4 | 6 | 6 | 5 |
| stop-loop | 0 | 2 | 0 | 0 |
| misquote | 6 | 6 | 6 | 6 |
| unsupported-preference | 3 | 3 | 6 | 3 |
| requested-actual | 6 | 6 | 6 | 6 |
| corrected-count | 0 | 6 | 6 | 6 |
| changed-engine | 6 | 4 | 4 | 6 |
| changed-rename | 6 | 6 | 6 | 6 |
| context-flip | 3 | 3 | 3 | 3 |
| voice-null | 6 | 6 | 6 | 6 |

Paired comparisons use the same scenario, model and seed:
- transport versus baseline: 3 improved, 2 regressed, 55 unchanged, out of 60 pairs.
- repaired versus baseline: 2 improved, 3 regressed, 55 unchanged, out of 60 pairs.

Tasks and expected choices were frozen before inference. Complete visible prompts, responses, tool results, seeds and runtime counters are retained privately. These tables report the measured results; exact historical fixtures and raw responses are withheld.
