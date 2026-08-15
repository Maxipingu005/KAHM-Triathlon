# KAHM embeddings: retrieval evaluation on Austrian docs.

Generated: 2026-08-15 18:56:26 | script=evaluate_three_embeddings_storylines.py | version=2026-02-23-scientific-pubreport-v1

## Summary

This evaluation compares three retrieval pipelines for mapping natural-language queries to Austrian-law labels via sentence-level retrieval on a fixed corpus:

- **IDF–SVD:** IDF–SVD query embeddings → IDF–SVD corpus embeddings.
- **Mixedbread (true) (reference):** transformer query embeddings → transformer corpus embeddings.
- **KAHM(query→MB corpus):** gradient-free query adapter (IDF–SVD features mapped into the transformer embedding space) → frozen transformer corpus embeddings.

Uncertainty is quantified with a paired nonparametric bootstrap across queries (5000 resamples; seed=0).

## Data and provenance

### Corpus

- Corpus file: `ris_sentences.parquet`
- Aligned sentences (intersection of embedding indices): **529**
- Embedding space dimension (transformer index): **1024**
- Label universe size (docs. present in aligned corpus): **27**

Top-10 corpus law priors (count and prior probability):

| Law | Count | Prior |
| --- | --- | --- |
| WT_Competition_Rules | 172 | 0.325 |
| WT_Anti_Doping_Rules | 103 | 0.195 |
| WT_Para_Classification_Rules | 48 | 0.091 |
| WT_Medical_Guidelines | 47 | 0.089 |
| TRI_Gender_Regulations | 30 | 0.057 |
| ITU_Disciplinary_Rules | 14 | 0.026 |
| WT_Code_of_Ethics | 12 | 0.023 |
| WT_Uniform_Guidelines | 11 | 0.021 |
| WT_Qualification_Criteria_General_Rules | 9 | 0.017 |
| WT_Water_Quality | 9 | 0.017 |

### Queries

- Evaluated query set: `query_set.TEST_QUERY_SET`
- TRAIN query set (diagnostics only): `query_set.TRAIN_QUERY_SET`
- Evaluated queries after filtering: **1000**
- Evaluated cutoffs: **k = 3, 5, 10, 15, 20**

Test query-set composition (after filtering):

- Unique topic IDs: **547**
- Unique query texts: **1000** (duplicates=0)

| Style | Count | Frac |
| --- | --- | --- |
| procedural | 145 | 0.145 |
| authority | 144 | 0.144 |
| keyword | 144 | 0.144 |
| nl_short | 143 | 0.143 |
| fragment | 142 | 0.142 |
| nl_long | 141 | 0.141 |
| scenario | 141 | 0.141 |

### Synthetic query generation (metadata)

- Metadata source: `file:C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\meta.json`
- seed: **19**
- split_mode: **iid**
- train_n: **4000**
- test_n: **1000**
- n_docs.: **27**
- variants_per_style: **3**
- queries_per_topic: **21**
- candidate_oversupply: **2.0**
- law_mention_prob: **0.0**
- keyword_law_mention_prob: **0.0**
- surface_noise_prob: **0.06**
- law_context_prob: **1.0**
- topic_term_prob: **0.0**
- issue_term_prob: **0.0**
- keyword_term_prob: **0.0**
- test_topics_subset_of_train: **True**

Split semantics (from the generator):
- `iid` (default): TRAIN/TEST are stratified; TEST draws only from topics seen in TRAIN (per-law).
- `iid_unrestricted`: TRAIN/TEST are stratified partitions of a shared topic pool (topics may be unseen in TRAIN).
- `topic_disjoint`: no topic appears in both splits (hardest generalization).

### Split hygiene diagnostics

- Exact-text overlap (TRAIN ∩ TEST): **0** queries
- Topic overlap (TRAIN ∩ TEST): **547** topics
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
- **MRR@k (unique docs.):** reciprocal rank of the first occurrence of the gold law when the top-*k* list is collapsed to unique docs..
- **Top-1 accuracy:** 1 if the top-ranked sentence law equals the gold law, else 0.
- **Majority-accuracy:** 1 if the plurality law in top-*k* equals gold **and** its fraction ≥ τ; otherwise 0 (abstentions count as 0).
- **Mean consensus fraction:** fraction of the top-*k* sentences that belong to the gold law.
- **Mean lift (prior):** consensus fraction divided by the corpus prior of the gold law (enrichment over chance).

## Results

### Micro-averaged quality (mean ± 95% CI)

**MRR@k (unique docs.)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.537 [0.510, 0.564] | 0.535 [0.507, 0.563] | 0.444 [0.416, 0.471] |
| 5 | 0.559 [0.533, 0.585] | 0.561 [0.535, 0.588] | 0.470 [0.443, 0.497] |
| 10 | 0.577 [0.552, 0.602] | 0.584 [0.559, 0.609] | 0.496 [0.470, 0.521] |
| 15 | 0.585 [0.560, 0.609] | 0.594 [0.570, 0.619] | 0.509 [0.484, 0.534] |
| 20 | 0.590 [0.566, 0.614] | 0.600 [0.576, 0.624] | 0.516 [0.491, 0.541] |

**Hit@k**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.659 [0.629, 0.688] | 0.628 [0.598, 0.658] | 0.529 [0.498, 0.559] |
| 5 | 0.729 [0.700, 0.756] | 0.693 [0.664, 0.722] | 0.596 [0.565, 0.627] |
| 10 | 0.808 [0.783, 0.832] | 0.770 [0.744, 0.796] | 0.686 [0.656, 0.715] |
| 15 | 0.856 [0.834, 0.878] | 0.812 [0.788, 0.835] | 0.744 [0.718, 0.771] |
| 20 | 0.894 [0.874, 0.913] | 0.836 [0.814, 0.859] | 0.776 [0.749, 0.801] |

**Top-1 accuracy**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.432 [0.401, 0.462] | 0.449 [0.418, 0.480] | 0.367 [0.338, 0.398] |
| 5 | 0.432 [0.402, 0.463] | 0.449 [0.418, 0.481] | 0.367 [0.337, 0.398] |
| 10 | 0.432 [0.402, 0.462] | 0.449 [0.418, 0.478] | 0.367 [0.337, 0.397] |
| 15 | 0.432 [0.402, 0.463] | 0.449 [0.418, 0.480] | 0.367 [0.337, 0.397] |
| 20 | 0.432 [0.402, 0.464] | 0.449 [0.418, 0.480] | 0.367 [0.337, 0.397] |

**Majority-accuracy** (τ=0.10)

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.421 [0.390, 0.451] | 0.427 [0.396, 0.457] | 0.338 [0.309, 0.367] |
| 5 | 0.379 [0.349, 0.409] | 0.374 [0.345, 0.404] | 0.314 [0.286, 0.343] |
| 10 | 0.322 [0.294, 0.351] | 0.309 [0.280, 0.338] | 0.266 [0.239, 0.293] |
| 15 | 0.290 [0.262, 0.319] | 0.249 [0.223, 0.277] | 0.230 [0.203, 0.257] |
| 20 | 0.260 [0.233, 0.287] | 0.222 [0.197, 0.247] | 0.201 [0.177, 0.225] |

**Mean consensus fraction**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.346 [0.326, 0.366] | 0.366 [0.343, 0.388] | 0.297 [0.276, 0.318] |
| 5 | 0.292 [0.276, 0.308] | 0.333 [0.313, 0.352] | 0.275 [0.256, 0.295] |
| 10 | 0.238 [0.225, 0.251] | 0.273 [0.257, 0.289] | 0.234 [0.218, 0.250] |
| 15 | 0.209 [0.197, 0.222] | 0.238 [0.224, 0.253] | 0.208 [0.193, 0.222] |
| 20 | 0.190 [0.178, 0.202] | 0.216 [0.201, 0.230] | 0.189 [0.176, 0.203] |

**Mean lift (prior)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 24.716 [22.496, 27.039] | 20.196 [18.444, 21.959] | 15.420 [13.771, 17.176] |
| 5 | 19.299 [17.734, 20.886] | 17.268 [15.898, 18.732] | 13.311 [12.003, 14.667] |
| 10 | 13.620 [12.679, 14.554] | 12.948 [12.051, 13.837] | 10.293 [9.471, 11.121] |
| 15 | 11.262 [10.561, 11.948] | 10.391 [9.752, 11.040] | 8.780 [8.169, 9.424] |
| 20 | 9.600 [9.062, 10.130] | 8.815 [8.303, 9.322] | 7.612 [7.126, 8.111] |

### Paired deltas (KAHM − IDF–SVD)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | -0.031 [-0.064, +0.002] | -0.002 [-0.031, +0.028] | +0.017 [-0.017, +0.050] | +0.006 [-0.029, +0.040] | +0.020 [-0.001, +0.040] | -4.520 [-6.343, -2.762] |
| 5 | -0.036 [-0.067, -0.006] | +0.003 [-0.024, +0.030] | +0.017 [-0.017, +0.050] | -0.005 [-0.038, +0.028] | +0.041 [+0.025, +0.057] | -2.031 [-3.433, -0.659] |
| 10 | -0.038 [-0.066, -0.010] | +0.007 [-0.018, +0.032] | +0.017 [-0.016, +0.050] | -0.013 [-0.043, +0.018] | +0.035 [+0.023, +0.047] | -0.672 [-1.489, +0.147] |
| 15 | -0.044 [-0.070, -0.018] | +0.010 [-0.014, +0.035] | +0.017 [-0.016, +0.050] | -0.041 [-0.067, -0.015] | +0.029 [+0.019, +0.038] | -0.871 [-1.499, -0.282] |
| 20 | -0.058 [-0.082, -0.033] | +0.010 [-0.015, +0.035] | +0.017 [-0.017, +0.051] | -0.038 [-0.063, -0.013] | +0.026 [+0.017, +0.034] | -0.786 [-1.241, -0.326] |

### Paired deltas vs transformer-query baseline (context; KAHM − Mixedbread)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.099 [+0.073, +0.124] | +0.092 [+0.070, +0.114] | +0.082 [+0.055, +0.109] | +0.089 [+0.063, +0.116] | +0.068 [+0.054, +0.083] | +4.776 [+3.218, +6.346] |
| 5 | +0.097 [+0.074, +0.122] | +0.091 [+0.072, +0.112] | +0.082 [+0.057, +0.108] | +0.060 [+0.033, +0.086] | +0.058 [+0.046, +0.070] | +3.957 [+2.872, +5.040] |
| 10 | +0.084 [+0.061, +0.107] | +0.089 [+0.070, +0.107] | +0.082 [+0.056, +0.108] | +0.043 [+0.021, +0.066] | +0.039 [+0.031, +0.046] | +2.655 [+2.018, +3.308] |
| 15 | +0.068 [+0.045, +0.091] | +0.085 [+0.066, +0.103] | +0.082 [+0.056, +0.107] | +0.019 [+0.001, +0.037] | +0.031 [+0.025, +0.036] | +1.611 [+1.163, +2.034] |
| 20 | +0.060 [+0.037, +0.083] | +0.084 [+0.066, +0.103] | +0.082 [+0.056, +0.108] | +0.021 [+0.004, +0.038] | +0.027 [+0.022, +0.031] | +1.203 [+0.860, +1.550] |

### Macro-averaged quality (per-law average; robustness)

Macro-averaging computes metrics per law and then averages across docs. (each law has equal weight). This is a robustness check against label-frequency skew.

**Macro MRR@k (unique docs.)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.512 [0.430, 0.591] | 0.489 [0.390, 0.586] | 0.395 [0.306, 0.488] |
| 5 | 0.533 [0.450, 0.612] | 0.515 [0.420, 0.607] | 0.421 [0.334, 0.511] |
| 10 | 0.552 [0.469, 0.626] | 0.540 [0.449, 0.631] | 0.448 [0.362, 0.532] |
| 15 | 0.560 [0.483, 0.631] | 0.551 [0.458, 0.640] | 0.463 [0.380, 0.549] |
| 20 | 0.566 [0.490, 0.641] | 0.558 [0.471, 0.646] | 0.471 [0.392, 0.552] |

**Macro Hit@k**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.634 [0.547, 0.713] | 0.581 [0.478, 0.676] | 0.476 [0.379, 0.578] |
| 5 | 0.704 [0.612, 0.784] | 0.647 [0.544, 0.741] | 0.543 [0.440, 0.640] |
| 10 | 0.783 [0.705, 0.850] | 0.733 [0.639, 0.817] | 0.640 [0.551, 0.726] |
| 15 | 0.836 [0.771, 0.892] | 0.778 [0.690, 0.855] | 0.704 [0.618, 0.787] |
| 20 | 0.877 [0.817, 0.927] | 0.805 [0.721, 0.880] | 0.740 [0.659, 0.815] |

**Macro Top-1 accuracy**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.406 [0.320, 0.490] | 0.403 [0.301, 0.501] | 0.321 [0.235, 0.410] |
| 5 | 0.406 [0.324, 0.490] | 0.403 [0.301, 0.503] | 0.321 [0.237, 0.413] |
| 10 | 0.406 [0.323, 0.490] | 0.403 [0.301, 0.500] | 0.321 [0.236, 0.412] |
| 15 | 0.406 [0.319, 0.488] | 0.403 [0.303, 0.501] | 0.321 [0.235, 0.410] |
| 20 | 0.406 [0.324, 0.490] | 0.403 [0.301, 0.503] | 0.321 [0.237, 0.409] |

**Macro Majority-accuracy** (τ=0.10)

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.390 [0.312, 0.468] | 0.374 [0.271, 0.476] | 0.292 [0.210, 0.378] |
| 5 | 0.344 [0.261, 0.429] | 0.319 [0.222, 0.425] | 0.265 [0.184, 0.351] |
| 10 | 0.283 [0.197, 0.377] | 0.251 [0.152, 0.354] | 0.211 [0.124, 0.306] |
| 15 | 0.243 [0.154, 0.346] | 0.191 [0.101, 0.294] | 0.175 [0.089, 0.275] |
| 20 | 0.211 [0.121, 0.313] | 0.163 [0.070, 0.272] | 0.148 [0.066, 0.247] |

### Macro paired deltas (KAHM − IDF–SVD)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | -0.054 [-0.117, +0.011] | -0.023 [-0.085, +0.040] | -0.003 [-0.077, +0.073] | -0.016 [-0.081, +0.048] | -0.000 [-0.046, +0.048] | -6.238 [-11.722, -1.400] |
| 5 | -0.057 [-0.122, +0.008] | -0.018 [-0.080, +0.045] | -0.003 [-0.077, +0.068] | -0.025 [-0.086, +0.037] | +0.022 [-0.016, +0.062] | -3.218 [-7.494, +0.563] |
| 10 | -0.050 [-0.107, +0.003] | -0.011 [-0.069, +0.047] | -0.003 [-0.076, +0.065] | -0.032 [-0.095, +0.035] | +0.021 [-0.010, +0.053] | -1.215 [-3.737, +0.991] |
| 15 | -0.058 [-0.121, -0.002] | -0.009 [-0.063, +0.051] | -0.003 [-0.075, +0.068] | -0.052 [-0.108, +0.005] | +0.016 [-0.009, +0.044] | -1.401 [-3.251, +0.236] |
| 20 | -0.071 [-0.137, -0.012] | -0.008 [-0.066, +0.048] | -0.003 [-0.074, +0.067] | -0.048 [-0.100, +0.010] | +0.014 [-0.008, +0.040] | -1.235 [-2.870, +0.089] |

### Macro paired deltas vs transformer-query baseline (context; KAHM − Mixedbread)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.104 [+0.059, +0.156] | +0.094 [+0.054, +0.137] | +0.081 [+0.043, +0.123] | +0.082 [+0.045, +0.122] | +0.065 [+0.039, +0.092] | +5.341 [+1.489, +9.503] |
| 5 | +0.104 [+0.069, +0.143] | +0.094 [+0.062, +0.132] | +0.081 [+0.043, +0.123] | +0.054 [+0.022, +0.089] | +0.054 [+0.037, +0.073] | +4.370 [+2.238, +6.760] |
| 10 | +0.093 [+0.057, +0.136] | +0.092 [+0.060, +0.129] | +0.081 [+0.044, +0.123] | +0.040 [+0.006, +0.076] | +0.036 [+0.023, +0.049] | +2.979 [+1.680, +4.453] |
| 15 | +0.074 [+0.039, +0.113] | +0.088 [+0.055, +0.125] | +0.081 [+0.043, +0.122] | +0.016 [-0.008, +0.045] | +0.027 [+0.017, +0.037] | +1.732 [+0.789, +2.714] |
| 20 | +0.065 [+0.030, +0.100] | +0.087 [+0.055, +0.122] | +0.081 [+0.043, +0.122] | +0.015 [-0.008, +0.040] | +0.023 [+0.015, +0.031] | +1.268 [+0.586, +1.965] |

## Majority-vote routing (coverage/precision)

We report a coverage–precision sweep over routing thresholds τ′ (distinct from the predominance threshold used in the majority metric). Coverage is the fraction of queries that meet τ′; precision is accuracy conditioned on being covered.

Recommended τ′ maximizes precision subject to coverage ≥ **0.50**.

| Method | τ′ | Coverage | Majority-acc | Precision (acc|covered) |
| --- | --- | --- | --- | --- |
| IDF–SVD | 0.31 | 0.666 | 0.229 | 0.344 |
| Mixedbread (true) | 0.51 | 0.502 | 0.141 | 0.281 |
| KAHM(query→MB corpus) | 0.41 | 0.721 | 0.225 | 0.312 |

## Computational profile

This section reports query-time computational profiles for the three retrieval paths. The primary comparison target is **online per-query time** (query embedding + FAISS search). If a query embedding source was loaded from a precomputed NPZ in this run, the corresponding online embedding time is reported as `n/a` and the load time is reported separately.

### Per-query online path comparison

| Path | Query source | Query embed / q | FAISS search / q | Total online / q | Observed step sum / q | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| IDF–SVD | model | 9.249 ms | 0.012 ms | 9.261 ms | 9.261 ms | IDF–SVD model load shown in component table (cold-start). |
| KAHM(query→MB corpus) | model | 40.468 ms | 0.006 ms | 40.474 ms | 40.474 ms | Online total only available when KAHM queries were embedded in this run (not precomputed NPZ). |
| Mixedbread (true) | online | 623.526 ms | 0.004 ms | 623.530 ms | 623.530 ms | Online total only available when Mixedbread queries were encoded on the fly (not precomputed NPZ). |

### Measured components (wall-clock)

| Component | Wall time | Per query | Notes |
| --- | --- | --- | --- |
| IDF–SVD query pipeline init (cold-start) | 4.731 s | 4.731 ms | One-time pipeline/materialization cost. |
| IDF–SVD query embedding (batch) | 9.249 s | 9.249 ms |  |
| KAHM query load (precomputed NPZ) | n/a | n/a | Only present when --kahm_query_embeddings_npz is used. |
| KAHM query model init (cold-start) | 4.551 s | 4.551 ms | Only present for online KAHM embedding. |
| KAHM query warm-up (excluded from online total) | 3.104 s | n/a |  |
| KAHM query embedding (batch) | 40.468 s | 40.468 ms |  |
| Mixedbread query load (precomputed NPZ) | n/a | n/a | Only present when precomputed Mixedbread query embeddings are used. |
| Mixedbread model init (cold-start) | 4.236 s | 4.236 ms | Only present for online transformer query encoding. |
| Mixedbread query warm-up (excluded from online total) | 0.592 s | n/a |  |
| Mixedbread query embedding (batch) | 623.526 s | 623.526 ms |  |
| FAISS build (IDF corpus index) | 0.115 s | n/a |  |
| FAISS search (IDF path) | 0.012 s | 0.012 ms |  |
| FAISS build (MB corpus index) | 0.001 s | n/a | Shared by Mixedbread and KAHM(query→MB) paths. |
| FAISS search (Mixedbread path) | 0.004 s | 0.004 ms |  |
| FAISS search (KAHM→MB path) | 0.006 s | 0.006 ms |  |
| Corpus embedding memory (IDF matrix) | 1,083,392 bytes | n/a | NumPy array nbytes (aligned corpus embeddings used in this run). |
| Corpus embedding memory (MB matrix) | 2,166,784 bytes | n/a | NumPy array nbytes (aligned corpus embeddings used in this run). |

### Derived online speedups (per-query)

| Comparison | Speedup | Definition |
| --- | --- | --- |
| IDF–SVD vs KAHM(query→MB corpus) | 0.23× | IDF online / KAHM online |
| Mixedbread (true) vs KAHM(query→MB corpus) | 15.41× | MB online / KAHM online |
| Mixedbread (true) vs IDF–SVD | 67.33× | MB online / IDF online |

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
| n_corpus | 529 |
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
| corpus_parquet | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\ris_sentences.parquet | yes | 335629 |
| semantic_npz | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\embedding_index.npz | yes | 1265607 |
| idf_svd_npz | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\embedding_index_idf_svd.npz | yes | 1015735 |
| idf_svd_model | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\idf_svd_model.joblib | yes | 158043209 |
| kahm_query_model | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\kahm_query_regressors_by_law | yes | 0 |
| mb_query_npz_test | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\queries_embedding_index_test.npz | yes | 1973812 |
| mb_query_npz_train | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\queries_embedding_index_train.npz | yes | 7895910 |

## Notes and limitations

- Query sets appear to follow the synthetic schema (`query_text`, `consensus_law`, `topic_id`, `style`) when such fields are present; interpretation of results should consider the split mode (topic overlap vs disjoint topics).
- This report focuses on retrieval quality, with added wall-clock query-time profiling; it does not benchmark end-to-end serving latency under concurrency or energy use.
- The transformer-query baseline is reported as a reference; KAHM may outperform it if the adapter is supervised/tuned for this label set.
