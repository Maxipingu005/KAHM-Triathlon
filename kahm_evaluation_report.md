# KAHM embeddings: retrieval evaluation on Austrian laws

Generated: 2026-07-19 22:05:36 | script=evaluate_three_embeddings_storylines.py | version=2026-02-23-scientific-pubreport-v1

## Summary

This evaluation compares three retrieval pipelines for mapping natural-language queries to Austrian-law labels via sentence-level retrieval on a fixed corpus:

- **IDF–SVD:** IDF–SVD query embeddings → IDF–SVD corpus embeddings.
- **Mixedbread (true) (reference):** transformer query embeddings → transformer corpus embeddings.
- **KAHM(query→MB corpus):** gradient-free query adapter (IDF–SVD features mapped into the transformer embedding space) → frozen transformer corpus embeddings.

Uncertainty is quantified with a paired nonparametric bootstrap across queries (5000 resamples; seed=0).

## Data and provenance

### Corpus

- Corpus file: `ris_sentences.parquet`
- Aligned sentences (intersection of embedding indices): **367**
- Embedding space dimension (transformer index): **1024**
- Label universe size (laws present in aligned corpus): **5**

Top-10 corpus law priors (count and prior probability):

| Law | Count | Prior |
| --- | --- | --- |
| WT_Competition_Rules | 172 | 0.469 |
| WT_Anti_Doping_Rules | 103 | 0.281 |
| WT_Para_Classification_Rules | 48 | 0.131 |
| TRI_Gender_Regulations | 30 | 0.082 |
| ITU_Disciplinary_Rules | 14 | 0.038 |

### Queries

- Evaluated query set: `query_set.TEST_QUERY_SET`
- TRAIN query set (diagnostics only): `query_set.TRAIN_QUERY_SET`
- Evaluated queries after filtering: **1000**
- Evaluated cutoffs: **k = 3, 5, 10, 15, 20**

Test query-set composition (after filtering):

- Unique topic IDs: **448**
- Unique query texts: **1000** (duplicates=0)

| Style | Count | Frac |
| --- | --- | --- |
| authority | 144 | 0.144 |
| keyword | 144 | 0.144 |
| procedural | 143 | 0.143 |
| scenario | 143 | 0.143 |
| fragment | 142 | 0.142 |
| nl_long | 142 | 0.142 |
| nl_short | 142 | 0.142 |

### Synthetic query generation (metadata)

- Metadata source: `file:C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\meta.json`
- seed: **19**
- split_mode: **iid**
- train_n: **4000**
- test_n: **1000**
- n_laws: **5**
- variants_per_style: **3**
- queries_per_topic: **21**
- candidate_oversupply: **2.0**
- law_mention_prob: **0.12**
- keyword_law_mention_prob: **0.25**
- surface_noise_prob: **0.06**
- law_context_prob: **1.0**
- topic_term_prob: **0.3**
- issue_term_prob: **0.35**
- keyword_term_prob: **0.35**
- test_topics_subset_of_train: **True**

Split semantics (from the generator):
- `iid` (default): TRAIN/TEST are stratified; TEST draws only from topics seen in TRAIN (per-law).
- `iid_unrestricted`: TRAIN/TEST are stratified partitions of a shared topic pool (topics may be unseen in TRAIN).
- `topic_disjoint`: no topic appears in both splits (hardest generalization).

### Split hygiene diagnostics

- Exact-text overlap (TRAIN ∩ TEST): **0** queries
- Topic overlap (TRAIN ∩ TEST): **448** topics
- Topic overlap fraction of TEST: **1.000**

### Label-leakage diagnostics (test)

Boundary match rule: `(?<!\w)LABEL(?!\w) (case-insensitive)`. These diagnostics estimate how often law abbreviations appear verbatim in query text.

- P(any law label mentioned): **0.000**
- P(gold law label mentioned): **0.000**
- P(other (non-gold) label mentioned): **0.000**

## Retrieval protocol

All embeddings are L2-normalized and indexed with FAISS `IndexFlatIP` (inner product on normalized vectors, i.e., cosine similarity). For each query, we retrieve the top-*k* sentences and aggregate their law labels to compute metrics.

Majority-vote predominance threshold for majority-accuracy: **τ = 0.10**.

## Metrics

All metrics are computed **per query** at cutoff *k* and then averaged across queries. We report 95% confidence intervals via paired bootstrap.

- **Hit@k:** 1 if at least one retrieved sentence is labeled with the gold law, else 0.
- **MRR@k (unique laws):** reciprocal rank of the first occurrence of the gold law when the top-*k* list is collapsed to unique laws.
- **Top-1 accuracy:** 1 if the top-ranked sentence law equals the gold law, else 0.
- **Majority-accuracy:** 1 if the plurality law in top-*k* equals gold **and** its fraction ≥ τ; otherwise 0 (abstentions count as 0).
- **Mean consensus fraction:** fraction of the top-*k* sentences that belong to the gold law.
- **Mean lift (prior):** consensus fraction divided by the corpus prior of the gold law (enrichment over chance).

## Results

### Micro-averaged quality (mean ± 95% CI)

**MRR@k (unique laws)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.915 [0.901, 0.930] | 0.930 [0.917, 0.944] | 0.865 [0.846, 0.883] |
| 5 | 0.920 [0.907, 0.933] | 0.934 [0.921, 0.946] | 0.876 [0.859, 0.893] |
| 10 | 0.926 [0.913, 0.938] | 0.936 [0.923, 0.948] | 0.883 [0.867, 0.899] |
| 15 | 0.926 [0.914, 0.938] | 0.938 [0.926, 0.949] | 0.886 [0.871, 0.901] |
| 20 | 0.926 [0.914, 0.938] | 0.939 [0.928, 0.950] | 0.888 [0.873, 0.903] |

**Hit@k**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.966 [0.955, 0.977] | 0.965 [0.953, 0.976] | 0.924 [0.907, 0.940] |
| 5 | 0.981 [0.972, 0.989] | 0.975 [0.965, 0.984] | 0.953 [0.939, 0.966] |
| 10 | 0.996 [0.992, 0.999] | 0.980 [0.971, 0.988] | 0.973 [0.962, 0.983] |
| 15 | 0.997 [0.993, 1.000] | 0.984 [0.976, 0.991] | 0.981 [0.972, 0.989] |
| 20 | 0.999 [0.997, 1.000] | 0.991 [0.985, 0.996] | 0.987 [0.979, 0.994] |

**Top-1 accuracy**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.868 [0.846, 0.889] | 0.896 [0.877, 0.915] | 0.810 [0.786, 0.834] |
| 5 | 0.868 [0.847, 0.889] | 0.896 [0.877, 0.915] | 0.810 [0.786, 0.834] |
| 10 | 0.868 [0.847, 0.888] | 0.896 [0.877, 0.914] | 0.810 [0.785, 0.834] |
| 15 | 0.868 [0.846, 0.888] | 0.896 [0.877, 0.914] | 0.810 [0.785, 0.833] |
| 20 | 0.868 [0.847, 0.889] | 0.896 [0.876, 0.914] | 0.810 [0.786, 0.835] |

**Majority-accuracy** (τ=0.10)

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.859 [0.838, 0.880] | 0.885 [0.864, 0.905] | 0.797 [0.772, 0.822] |
| 5 | 0.844 [0.821, 0.866] | 0.864 [0.843, 0.885] | 0.784 [0.758, 0.810] |
| 10 | 0.805 [0.780, 0.828] | 0.831 [0.807, 0.854] | 0.761 [0.735, 0.787] |
| 15 | 0.777 [0.751, 0.803] | 0.789 [0.764, 0.814] | 0.739 [0.712, 0.766] |
| 20 | 0.746 [0.719, 0.773] | 0.746 [0.719, 0.773] | 0.706 [0.677, 0.734] |

**Mean consensus fraction**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.798 [0.780, 0.816] | 0.837 [0.820, 0.853] | 0.766 [0.745, 0.786] |
| 5 | 0.747 [0.729, 0.766] | 0.806 [0.788, 0.822] | 0.732 [0.712, 0.751] |
| 10 | 0.674 [0.655, 0.693] | 0.748 [0.730, 0.766] | 0.672 [0.653, 0.692] |
| 15 | 0.626 [0.608, 0.644] | 0.699 [0.681, 0.718] | 0.624 [0.605, 0.643] |
| 20 | 0.588 [0.571, 0.606] | 0.658 [0.640, 0.677] | 0.587 [0.568, 0.605] |

**Mean lift (prior)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 7.545 [7.121, 7.972] | 8.095 [7.635, 8.571] | 7.234 [6.803, 7.683] |
| 5 | 6.804 [6.438, 7.181] | 7.579 [7.164, 8.007] | 6.743 [6.331, 7.142] |
| 10 | 5.799 [5.494, 6.102] | 6.708 [6.349, 7.066] | 5.834 [5.507, 6.167] |
| 15 | 5.148 [4.904, 5.394] | 5.922 [5.630, 6.202] | 5.155 [4.883, 5.423] |
| 20 | 4.643 [4.438, 4.847] | 5.334 [5.089, 5.569] | 4.639 [4.414, 4.859] |

### Paired deltas (KAHM − IDF–SVD)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | -0.001 [-0.016, +0.015] | +0.015 [-0.002, +0.032] | +0.028 [+0.005, +0.051] | +0.026 [+0.002, +0.051] | +0.039 [+0.021, +0.056] | +0.550 [+0.288, +0.805] |
| 5 | -0.006 [-0.019, +0.007] | +0.014 [-0.002, +0.029] | +0.028 [+0.004, +0.051] | +0.020 [-0.004, +0.044] | +0.058 [+0.042, +0.074] | +0.775 [+0.547, +1.001] |
| 10 | -0.016 [-0.026, -0.007] | +0.010 [-0.004, +0.025] | +0.028 [+0.004, +0.052] | +0.026 [+0.003, +0.050] | +0.074 [+0.058, +0.090] | +0.909 [+0.710, +1.113] |
| 15 | -0.013 [-0.022, -0.005] | +0.012 [-0.002, +0.026] | +0.028 [+0.004, +0.052] | +0.012 [-0.013, +0.037] | +0.073 [+0.058, +0.087] | +0.774 [+0.601, +0.954] |
| 20 | -0.008 [-0.014, -0.002] | +0.013 [-0.001, +0.027] | +0.028 [+0.004, +0.052] | +0.000 [-0.026, +0.026] | +0.070 [+0.056, +0.085] | +0.692 [+0.542, +0.844] |

### Paired deltas vs transformer-query baseline (context; KAHM − Mixedbread)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.041 [+0.027, +0.057] | +0.066 [+0.049, +0.083] | +0.086 [+0.063, +0.110] | +0.088 [+0.065, +0.111] | +0.071 [+0.056, +0.087] | +0.860 [+0.630, +1.094] |
| 5 | +0.022 [+0.009, +0.035] | +0.058 [+0.043, +0.073] | +0.086 [+0.064, +0.109] | +0.080 [+0.058, +0.102] | +0.073 [+0.060, +0.088] | +0.836 [+0.636, +1.039] |
| 10 | +0.007 [-0.002, +0.017] | +0.053 [+0.038, +0.067] | +0.086 [+0.063, +0.109] | +0.070 [+0.047, +0.093] | +0.076 [+0.063, +0.088] | +0.874 [+0.703, +1.048] |
| 15 | +0.003 [-0.005, +0.011] | +0.052 [+0.038, +0.066] | +0.086 [+0.063, +0.110] | +0.050 [+0.027, +0.073] | +0.075 [+0.064, +0.087] | +0.766 [+0.628, +0.903] |
| 20 | +0.004 [-0.003, +0.011] | +0.052 [+0.039, +0.066] | +0.086 [+0.063, +0.109] | +0.040 [+0.018, +0.063] | +0.072 [+0.062, +0.082] | +0.695 [+0.582, +0.813] |

### Macro-averaged quality (per-law average; robustness)

Macro-averaging computes metrics per law and then averages across laws (each law has equal weight). This is a robustness check against label-frequency skew.

**Macro MRR@k (unique laws)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.915 [0.877, 0.948] | 0.930 [0.884, 0.968] | 0.864 [0.779, 0.923] |
| 5 | 0.920 [0.886, 0.950] | 0.934 [0.890, 0.970] | 0.876 [0.801, 0.931] |
| 10 | 0.926 [0.894, 0.954] | 0.936 [0.894, 0.970] | 0.883 [0.809, 0.934] |
| 15 | 0.926 [0.894, 0.954] | 0.938 [0.897, 0.971] | 0.886 [0.817, 0.936] |
| 20 | 0.926 [0.898, 0.955] | 0.939 [0.901, 0.971] | 0.888 [0.820, 0.936] |

**Macro Hit@k**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.966 [0.949, 0.982] | 0.965 [0.926, 0.990] | 0.924 [0.846, 0.970] |
| 5 | 0.981 [0.973, 0.990] | 0.975 [0.941, 0.998] | 0.953 [0.900, 0.986] |
| 10 | 0.996 [0.993, 0.999] | 0.980 [0.952, 0.998] | 0.973 [0.933, 0.995] |
| 15 | 0.997 [0.995, 0.999] | 0.984 [0.959, 0.999] | 0.981 [0.947, 1.000] |
| 20 | 0.999 [0.997, 1.000] | 0.991 [0.978, 0.999] | 0.987 [0.965, 1.000] |

**Macro Top-1 accuracy**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.868 [0.817, 0.918] | 0.896 [0.842, 0.945] | 0.810 [0.719, 0.882] |
| 5 | 0.868 [0.817, 0.918] | 0.896 [0.847, 0.945] | 0.810 [0.719, 0.882] |
| 10 | 0.868 [0.817, 0.918] | 0.896 [0.843, 0.945] | 0.810 [0.719, 0.882] |
| 15 | 0.868 [0.817, 0.918] | 0.896 [0.843, 0.945] | 0.810 [0.719, 0.882] |
| 20 | 0.868 [0.817, 0.918] | 0.896 [0.843, 0.945] | 0.810 [0.719, 0.882] |

**Macro Majority-accuracy** (τ=0.10)

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.859 [0.765, 0.949] | 0.885 [0.815, 0.951] | 0.797 [0.685, 0.904] |
| 5 | 0.844 [0.739, 0.943] | 0.864 [0.777, 0.944] | 0.784 [0.659, 0.903] |
| 10 | 0.805 [0.668, 0.936] | 0.831 [0.736, 0.926] | 0.761 [0.620, 0.902] |
| 15 | 0.777 [0.598, 0.941] | 0.789 [0.651, 0.927] | 0.739 [0.570, 0.896] |
| 20 | 0.746 [0.528, 0.936] | 0.746 [0.567, 0.923] | 0.706 [0.502, 0.891] |

### Macro paired deltas (KAHM − IDF–SVD)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | -0.001 [-0.023, +0.014] | +0.015 [+0.002, +0.027] | +0.028 [+0.017, +0.040] | +0.026 [-0.009, +0.057] | +0.039 [+0.001, +0.071] | +0.550 [-0.019, +1.293] |
| 5 | -0.006 [-0.035, +0.015] | +0.014 [-0.001, +0.026] | +0.028 [+0.017, +0.040] | +0.020 [-0.021, +0.057] | +0.058 [+0.007, +0.099] | +0.775 [-0.003, +1.745] |
| 10 | -0.016 [-0.044, +0.002] | +0.010 [-0.004, +0.023] | +0.028 [+0.017, +0.040] | +0.026 [-0.037, +0.084] | +0.074 [+0.026, +0.122] | +0.909 [+0.099, +2.020] |
| 15 | -0.013 [-0.038, +0.002] | +0.012 [-0.002, +0.025] | +0.028 [+0.017, +0.040] | +0.012 [-0.051, +0.075] | +0.073 [+0.022, +0.129] | +0.774 [+0.113, +1.577] |
| 20 | -0.008 [-0.019, -0.001] | +0.013 [+0.002, +0.024] | +0.028 [+0.017, +0.040] | +0.000 [-0.054, +0.054] | +0.070 [+0.018, +0.131] | +0.692 [+0.114, +1.353] |

### Macro paired deltas vs transformer-query baseline (context; KAHM − Mixedbread)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.041 [+0.015, +0.080] | +0.066 [+0.038, +0.106] | +0.086 [+0.054, +0.124] | +0.088 [+0.049, +0.138] | +0.071 [+0.047, +0.098] | +0.860 [+0.214, +1.578] |
| 5 | +0.022 [+0.011, +0.041] | +0.058 [+0.035, +0.089] | +0.086 [+0.054, +0.124] | +0.080 [+0.041, +0.120] | +0.073 [+0.057, +0.087] | +0.836 [+0.262, +1.577] |
| 10 | +0.007 [-0.001, +0.019] | +0.053 [+0.030, +0.082] | +0.086 [+0.054, +0.124] | +0.070 [+0.020, +0.120] | +0.076 [+0.049, +0.099] | +0.874 [+0.298, +1.715] |
| 15 | +0.003 [-0.005, +0.012] | +0.052 [+0.030, +0.078] | +0.086 [+0.054, +0.124] | +0.050 [+0.014, +0.095] | +0.075 [+0.050, +0.102] | +0.766 [+0.298, +1.301] |
| 20 | +0.004 [-0.002, +0.013] | +0.052 [+0.030, +0.078] | +0.086 [+0.054, +0.124] | +0.040 [+0.022, +0.058] | +0.072 [+0.045, +0.104] | +0.695 [+0.287, +1.134] |

## Majority-vote routing (coverage/precision)

We report a coverage–precision sweep over routing thresholds τ′ (distinct from the predominance threshold used in the majority metric). Coverage is the fraction of queries that meet τ′; precision is accuracy conditioned on being covered.

Recommended τ′ maximizes precision subject to coverage ≥ **0.50**.

| Method | τ′ | Coverage | Majority-acc | Precision (acc|covered) |
| --- | --- | --- | --- | --- |
| IDF–SVD | 0.71 | 0.519 | 0.501 | 0.965 |
| Mixedbread (true) | 0.71 | 0.567 | 0.513 | 0.905 |
| KAHM(query→MB corpus) | 0.81 | 0.546 | 0.527 | 0.965 |

## Computational profile

This section reports query-time computational profiles for the three retrieval paths. The primary comparison target is **online per-query time** (query embedding + FAISS search). If a query embedding source was loaded from a precomputed NPZ in this run, the corresponding online embedding time is reported as `n/a` and the load time is reported separately.

### Per-query online path comparison

| Path | Query source | Query embed / q | FAISS search / q | Total online / q | Observed step sum / q | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| IDF–SVD | model | 19.304 ms | 0.010 ms | 19.314 ms | 19.314 ms | IDF–SVD model load shown in component table (cold-start). |
| KAHM(query→MB corpus) | model | 12.409 ms | 0.004 ms | 12.413 ms | 12.413 ms | Online total only available when KAHM queries were embedded in this run (not precomputed NPZ). |
| Mixedbread (true) | online | 752.140 ms | 0.004 ms | 752.144 ms | 752.144 ms | Online total only available when Mixedbread queries were encoded on the fly (not precomputed NPZ). |

### Measured components (wall-clock)

| Component | Wall time | Per query | Notes |
| --- | --- | --- | --- |
| IDF–SVD query pipeline init (cold-start) | 7.666 s | 7.666 ms | One-time pipeline/materialization cost. |
| IDF–SVD query embedding (batch) | 19.304 s | 19.304 ms |  |
| KAHM query load (precomputed NPZ) | n/a | n/a | Only present when --kahm_query_embeddings_npz is used. |
| KAHM query model init (cold-start) | 2.814 s | 2.814 ms | Only present for online KAHM embedding. |
| KAHM query warm-up (excluded from online total) | 2.476 s | n/a |  |
| KAHM query embedding (batch) | 12.409 s | 12.409 ms |  |
| Mixedbread query load (precomputed NPZ) | n/a | n/a | Only present when precomputed Mixedbread query embeddings are used. |
| Mixedbread model init (cold-start) | 4.283 s | 4.283 ms | Only present for online transformer query encoding. |
| Mixedbread query warm-up (excluded from online total) | 0.568 s | n/a |  |
| Mixedbread query embedding (batch) | 752.140 s | 752.140 ms |  |
| FAISS build (IDF corpus index) | 0.309 s | n/a |  |
| FAISS search (IDF path) | 0.010 s | 0.010 ms |  |
| FAISS build (MB corpus index) | 0.001 s | n/a | Shared by Mixedbread and KAHM(query→MB) paths. |
| FAISS search (Mixedbread path) | 0.004 s | 0.004 ms |  |
| FAISS search (KAHM→MB path) | 0.004 s | 0.004 ms |  |
| Corpus embedding memory (IDF matrix) | 537,288 bytes | n/a | NumPy array nbytes (aligned corpus embeddings used in this run). |
| Corpus embedding memory (MB matrix) | 1,503,232 bytes | n/a | NumPy array nbytes (aligned corpus embeddings used in this run). |

### Derived online speedups (per-query)

| Comparison | Speedup | Definition |
| --- | --- | --- |
| IDF–SVD vs KAHM(query→MB corpus) | 1.56× | IDF online / KAHM online |
| Mixedbread (true) vs KAHM(query→MB corpus) | 60.59× | MB online / KAHM online |
| Mixedbread (true) vs IDF–SVD | 38.94× | MB online / IDF online |

### Machine profile (auto-detected; best effort)

| Field | Value |
| --- | --- |
| Hostname | Paul |
| Platform | Windows-11-10.0.26200-SP0 |
| System | Windows |
| Machine / arch | AMD64 |
| Processor | Intel64 Family 6 Model 158 Stepping 10, GenuineIntel |
| CPU logical cores | 12 |
| CPU physical cores | 6 |
| RAM total | 15.84 GiB |
| Python | 3.12.3 |
| Torch runtime | 2.13.0+cpu |
| Accelerator type | cpu |
| Accelerator name | CPU |
| CUDA available | False |
| MPS available | False |
| Requested device arg | cpu |
| Auto-resolved device | cpu |
| Thread cap arg | 0 |
| KAHM query source | model |
| Mixedbread query source | online |
| n_queries | 1000 |
| n_corpus | 367 |
| embedding_dim | 1024 |
| retrieval_k_max | 20 |

## Reproducibility

- Bootstrap: B=5000, seed=0
- Thread cap: 0 (0 means no override)

### Software / environment

- Python: `3.12.3`
- Platform: `Windows-11-10.0.26200-SP0`
- numpy: `1.26.4`
- pandas: `2.3.3`
- faiss-cpu: `1.14.3`
- torch: `2.13.0`
- sentence-transformers: `5.6.0`
- scikit-learn: `1.9.0`
- joblib: `1.5.3`

### Artifacts

| Artifact | Path | Exists | Bytes |
| --- | --- | --- | --- |
| corpus_parquet | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\ris_sentences.parquet | yes | 224492 |
| semantic_npz | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\embedding_index.npz | yes | 879053 |
| idf_svd_npz | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\embedding_index_idf_svd.npz | yes | 505080 |
| idf_svd_model | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\idf_svd_model.joblib | yes | 84993699 |
| kahm_query_model | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\kahm_query_regressors_by_law | yes | 0 |
| mb_query_npz_test | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\queries_embedding_index_test.npz | yes | 1991647 |
| mb_query_npz_train | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\queries_embedding_index_train.npz | yes | 7957621 |

## Notes and limitations

- Query sets appear to follow the synthetic schema (`query_text`, `consensus_law`, `topic_id`, `style`) when such fields are present; interpretation of results should consider the split mode (topic overlap vs disjoint topics).
- This report focuses on retrieval quality, with added wall-clock query-time profiling; it does not benchmark end-to-end serving latency under concurrency or energy use.
- The transformer-query baseline is reported as a reference; KAHM may outperform it if the adapter is supervised/tuned for this label set.
