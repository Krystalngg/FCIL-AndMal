# FCIL-AndMal Experiment Validation

## Executive verdict

The checkout was **not paper-ready before these changes**, and the historical result tables cannot be independently validated from this repository because the raw dataset, prepared splits, client partitions, prediction files, logs, and checkpoints are absent or ignored. The supplied report's exact collapse numbers may be accurate for an external run, but they are **not reproducible evidence from this checkout**.

The implementation now improves experimental validity, but it does **not** establish publishable performance. A real-data, multi-seed benchmark must still be run and archived before making scientific claims.

## Confirmed strengths

- The default protocol is a clearly defined 5-task, 3-new-class-per-task single-head CIL setup.
- Client partitions are generated from the training split rather than directly from the held-out test split.
- Evaluation computes cumulative seen-class metrics and labeled confusion matrices.
- Classifier expansion preserves prior classifier rows.
- A deterministic seed utility and structured experiment logging/checkpointing exist.

## Critical findings from the pre-change checkout

1. **Historical results were not independently verifiable.** The reports reference external paths and ignored artifacts; no primary evidence was tracked here.
2. **Synthetic data could silently replace missing real data.** `main.py` and Stage 1 preparation could generate simulated files without a strict scientific/development boundary.
3. **Missing classes were warnings, not a hard failure.** A nominal 15-class run could proceed without Benign or another configured class.
4. **No train-fitted input scaler existed.** Documentation claimed normalization, but loaders consumed raw numeric values.
5. **Row-level splitting did not preserve application identity.** Before/after or repeated observations could cross train/validation/test splits.
6. **Fused fallback paired unrelated rows by class and position.** This is not valid sample-level multimodal fusion.
7. **Centralized training repeatedly evaluated the test split and selected a best checkpoint using test Macro-F1.** This compromises test-set purity.
8. **EWC had duplicate penalty/Fisher accumulation paths.** The active implementation could count historical terms multiple times and its empirical Fisher accumulation used squared summed gradients.
9. **The runner's 20 processes are not 20 independent replications.** They are method/client-scenario combinations with a single seed (`42`).
10. **The review's fixed Macro-F1 thresholds (70%/75%) are not scientific validity criteria.** Performance must be judged against prespecified baselines, uncertainty, and leakage-controlled protocols.

## Changes implemented in this local worktree

### Priority 0: provenance and benchmark integrity

- Removed implicit synthetic generation from `main.py` and `data/prepare_dataset.py`.
- Synthetic generation now requires explicit `--generate_synthetic`, prints a development-only warning, and writes `SYNTHETIC_DATASET.json`.
- Added persisted `data_provenance.json` and strict class-coverage support.
- Added `--allow_incomplete_benchmark` for explicitly labeled development runs; scientific mode fails on missing configured classes.
- Propagated real raw-data paths and strict/provenance arguments through `run_all.py`.

### Priority 1: preprocessing and split validity

- Added `data/scaling.py`.
- Stage 1 fits `StandardScaler` and train-only imputation on the training split, persists `scaler.joblib` and `scaler_metadata.json`, and applies the same transform to validation/test.
- Added canonical feature-order checks when loading prepared splits.
- Preserved hash-derived `Split_Group_ID` as a non-feature identity column and use it for group-disjoint splitting when present.
- Added per-source schema validation so incompatible modality CSVs fail instead of being unioned silently.
- Disabled class-wise fused pairing by default; it is now an explicit development-only option.

### Priority 2: test-set and method correctness

- Centralized interim monitoring now uses a validation evaluator.
- Test evaluation remains task-final and is no longer used for best-checkpoint selection.
- Repaired EWC to apply one overlap penalty per historical tensor element, merge Fisher tensors once during expansion, and accumulate per-example squared gradients.
- Added regression coverage for the exact EWC penalty and scaler persistence.
- Reconciled stale tests with the documented current checkpoint and distinct `MALFSIL`/`MalFSCIL` semantics.
- Added `entrypoint.sh` for reproducible test, development smoke, preparation, and benchmark commands.

## Items deliberately not implemented

The broad implementation plan proposed several changes that would confound validity or require a new study, so they were intentionally deferred:

- No synthetic or fabricated Benign telemetry was accepted as benchmark evidence.
- No arbitrary Macro-F1 target was used as an acceptance criterion.
- No global cosine head, Weight Alignment, BiC, or replay-ratio change was silently enabled across all baselines.
- No claim was made that centralized MalFSCIL is a federated method.
- No automatic conversion of legacy MALFSIL into MalFSCIL was made.
- No full 20-run benchmark was launched because the real CIC-AndMal-2020 data are not present in this checkout.
- No statistical conclusions, confidence intervals, or paper-level performance claims were fabricated.

## Validation commands and outcomes

Environment dependencies were installed into the workspace package directory because the base interpreter did not expose pip.

- `python3 -m compileall .` — passed.
- `PYTHONPATH=... python3 -m pytest tests -vv` — **45 passed**, with two expected warnings from a development-only incomplete fused fixture.
- `./entrypoint.sh test` — **45 passed**.
- `./entrypoint.sh smoke` — passed Stage 1/2 synthetic development preparation with explicit provenance, train-fitted scaling, 15 observed classes, and `--prepare_only`; no benchmark claim was made.
- `python3 run_all.py --list --clients 20` — passed; confirms the runner exposes 10 cases per client scenario. This is a listing check, not training.

No full real-data experiment was run because no real raw dataset is available in the checkout.

## Current paper-readiness assessment

**Status: improved infrastructure, not yet paper-ready.** Before submission, run at least:

1. Real, same-instrumentation Benign and malware data with documented provenance and source hashes.
2. A schema audit confirming exact feature columns and application/hash group disjointness.
3. Centralized MLP sanity baselines: joint-training upper bound, fine-tuning lower bound, and replay.
4. At least three independent seeds, reporting mean, standard deviation or confidence intervals, per-class F1, Benign false-positive rate, and confusion matrices.
5. One fixed federated baseline (FedAvg) before adding FedNova or specialized methods.
6. Validation-only hyperparameter selection and one predefined final test evaluation per task.
7. Archived configs, commit hash, environment/package lock, dataset manifest/hash, predictions, metrics, and checkpoints.
8. Isolated ablations for backbone, scaling, replay ratio, classifier calibration, and any proposed method contribution.

Do not report the historical exact accuracies or macro-F1 values as reproduced by this checkout. They remain external, unverified artifacts until the real benchmark is rerun.
