# redgreen — evaluation results

> SYNTHETIC smoke run with a scripted model — proves the pipeline, not the model. Run the real eval with a key for headline numbers.

| Metric | Baseline (single-shot) | redgreen (agent) | Change |
| --- | ---: | ---: | ---: |
| Verified-fix rate | 0% | 100% | ▲ +100% |
| Reward-hack rate | 100% | 0% | ▼ -100% |
| Regression rate | 0% | 0% | — +0% |
| Not-fixed rate | 0% | 0% | — +0% |
| Reproduction rate (agent) | — | 100% | — |

Cases graded: 1 per system.

## Verdict breakdown

- **baseline**: REWARD_HACK=1
- **agent**: VERIFIED_FIX=1
