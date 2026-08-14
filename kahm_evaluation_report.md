# KAHM embeddings: retrieval evaluation on Austrian laws

Generated: 2026-08-10 00:48:23 | script=evaluate_three_embeddings_storylines.py | version=2026-02-23-scientific-pubreport-v1

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
- Label universe size (laws present in aligned corpus): **27**

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

- Unique topic IDs: **553**
- Unique query texts: **1000** (duplicates=0)

| Style | Count | Frac |
| --- | --- | --- |
| scenario | 145 | 0.145 |
| keyword | 144 | 0.144 |
| nl_short | 144 | 0.144 |
| procedural | 144 | 0.144 |
| nl_long | 143 | 0.143 |
| authority | 140 | 0.140 |
| fragment | 140 | 0.140 |

### Synthetic query generation (metadata)

- Metadata source: `file:C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\meta.json`
- seed: **19**
- split_mode: **iid**
- train_n: **4000**
- test_n: **1000**
- n_laws: **27**
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
- Topic overlap (TRAIN ∩ TEST): **553** topics
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
- **MRR@k (unique documents):** reciprocal rank of the first occurrence of the gold law when the top-*k* list is collapsed to unique documents.
- **Top-1 accuracy:** 1 if the top-ranked sentence law equals the gold law, else 0.
- **Majority-accuracy:** 1 if the plurality law in top-*k* equals gold **and** its fraction ≥ τ; otherwise 0 (abstentions count as 0).
- **Mean consensus fraction:** fraction of the top-*k* sentences that belong to the gold law.
- **Mean lift (prior):** consensus fraction divided by the corpus prior of the gold law (enrichment over chance).

## Results

### Micro-averaged quality (mean ± 95% CI)

**MRR@k (unique documents)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.683 [0.657, 0.709] | 0.622 [0.595, 0.649] | 0.519 [0.491, 0.547] |
| 5 | 0.701 [0.676, 0.725] | 0.644 [0.618, 0.670] | 0.544 [0.517, 0.570] |
| 10 | 0.714 [0.691, 0.737] | 0.665 [0.641, 0.690] | 0.569 [0.543, 0.595] |
| 15 | 0.719 [0.697, 0.742] | 0.673 [0.649, 0.697] | 0.579 [0.554, 0.603] |
| 20 | 0.722 [0.700, 0.744] | 0.678 [0.654, 0.701] | 0.584 [0.559, 0.609] |

**Hit@k**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.788 [0.762, 0.813] | 0.711 [0.683, 0.739] | 0.610 [0.579, 0.639] |
| 5 | 0.844 [0.822, 0.867] | 0.766 [0.739, 0.792] | 0.680 [0.652, 0.710] |
| 10 | 0.899 [0.880, 0.917] | 0.836 [0.812, 0.858] | 0.770 [0.743, 0.795] |
| 15 | 0.930 [0.913, 0.945] | 0.865 [0.842, 0.886] | 0.812 [0.787, 0.836] |
| 20 | 0.944 [0.930, 0.958] | 0.885 [0.865, 0.904] | 0.834 [0.811, 0.857] |

**Top-1 accuracy**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.594 [0.563, 0.625] | 0.542 [0.511, 0.572] | 0.437 [0.406, 0.468] |
| 5 | 0.594 [0.565, 0.625] | 0.542 [0.512, 0.572] | 0.437 [0.406, 0.467] |
| 10 | 0.594 [0.563, 0.625] | 0.542 [0.511, 0.573] | 0.437 [0.406, 0.468] |
| 15 | 0.594 [0.563, 0.624] | 0.542 [0.510, 0.573] | 0.437 [0.406, 0.467] |
| 20 | 0.594 [0.563, 0.624] | 0.542 [0.513, 0.573] | 0.437 [0.406, 0.468] |

**Majority-accuracy** (τ=0.10)

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.572 [0.541, 0.603] | 0.515 [0.483, 0.546] | 0.423 [0.393, 0.455] |
| 5 | 0.525 [0.493, 0.555] | 0.474 [0.444, 0.505] | 0.400 [0.369, 0.431] |
| 10 | 0.459 [0.427, 0.490] | 0.404 [0.373, 0.434] | 0.345 [0.315, 0.375] |
| 15 | 0.402 [0.371, 0.432] | 0.319 [0.290, 0.348] | 0.287 [0.258, 0.315] |
| 20 | 0.334 [0.306, 0.362] | 0.279 [0.250, 0.306] | 0.257 [0.229, 0.284] |

**Mean consensus fraction**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.478 [0.457, 0.499] | 0.460 [0.436, 0.483] | 0.381 [0.358, 0.405] |
| 5 | 0.412 [0.394, 0.431] | 0.412 [0.391, 0.432] | 0.348 [0.327, 0.369] |
| 10 | 0.325 [0.309, 0.341] | 0.331 [0.314, 0.349] | 0.285 [0.268, 0.303] |
| 15 | 0.280 [0.265, 0.296] | 0.283 [0.267, 0.300] | 0.251 [0.234, 0.267] |
| 20 | 0.249 [0.235, 0.263] | 0.253 [0.238, 0.269] | 0.226 [0.211, 0.242] |

**Mean lift (prior)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 33.651 [31.222, 36.130] | 28.729 [26.542, 31.005] | 21.407 [19.450, 23.394] |
| 5 | 27.162 [25.445, 28.887] | 24.249 [22.480, 25.952] | 18.811 [17.346, 20.368] |
| 10 | 18.567 [17.561, 19.593] | 17.498 [16.455, 18.528] | 13.941 [12.997, 14.860] |
| 15 | 14.810 [14.086, 15.514] | 13.699 [12.954, 14.423] | 11.435 [10.761, 12.113] |
| 20 | 12.293 [11.761, 12.845] | 11.396 [10.836, 11.950] | 9.741 [9.195, 10.268] |

### Paired deltas (KAHM − IDF–SVD)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | -0.077 [-0.107, -0.047] | -0.062 [-0.091, -0.034] | -0.052 [-0.086, -0.019] | -0.057 [-0.090, -0.025] | -0.018 [-0.038, +0.002] | -4.922 [-7.179, -2.707] |
| 5 | -0.078 [-0.104, -0.053] | -0.057 [-0.082, -0.031] | -0.052 [-0.085, -0.019] | -0.051 [-0.083, -0.019] | -0.000 [-0.017, +0.016] | -2.913 [-4.474, -1.308] |
| 10 | -0.063 [-0.086, -0.041] | -0.049 [-0.073, -0.025] | -0.052 [-0.085, -0.019] | -0.055 [-0.084, -0.026] | +0.006 [-0.005, +0.017] | -1.069 [-1.918, -0.190] |
| 15 | -0.065 [-0.086, -0.045] | -0.046 [-0.070, -0.024] | -0.052 [-0.085, -0.019] | -0.083 [-0.109, -0.056] | +0.003 [-0.007, +0.012] | -1.111 [-1.702, -0.525] |
| 20 | -0.059 [-0.079, -0.040] | -0.044 [-0.067, -0.022] | -0.052 [-0.085, -0.019] | -0.055 [-0.080, -0.032] | +0.004 [-0.004, +0.013] | -0.897 [-1.344, -0.459] |

### Paired deltas vs transformer-query baseline (context; KAHM − Mixedbread)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.101 [+0.074, +0.129] | +0.102 [+0.079, +0.126] | +0.105 [+0.077, +0.133] | +0.092 [+0.065, +0.119] | +0.079 [+0.061, +0.096] | +7.321 [+5.257, +9.258] |
| 5 | +0.086 [+0.060, +0.112] | +0.100 [+0.078, +0.121] | +0.105 [+0.076, +0.132] | +0.074 [+0.048, +0.101] | +0.064 [+0.051, +0.077] | +5.438 [+4.083, +6.842] |
| 10 | +0.066 [+0.044, +0.088] | +0.096 [+0.076, +0.115] | +0.105 [+0.077, +0.133] | +0.059 [+0.036, +0.084] | +0.046 [+0.037, +0.055] | +3.556 [+2.853, +4.282] |
| 15 | +0.053 [+0.033, +0.074] | +0.094 [+0.076, +0.113] | +0.105 [+0.077, +0.133] | +0.032 [+0.012, +0.053] | +0.033 [+0.026, +0.040] | +2.264 [+1.792, +2.731] |
| 20 | +0.051 [+0.031, +0.071] | +0.094 [+0.075, +0.112] | +0.105 [+0.077, +0.133] | +0.022 [+0.004, +0.041] | +0.027 [+0.021, +0.033] | +1.655 [+1.294, +2.031] |

### Macro-averaged quality (per-law average; robustness)

Macro-averaging computes metrics per law and then averages across laws (each law has equal weight). This is a robustness check against label-frequency skew.

**Macro MRR@k (unique documents)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.659 [0.576, 0.739] | 0.588 [0.489, 0.682] | 0.484 [0.394, 0.576] |
| 5 | 0.677 [0.592, 0.752] | 0.612 [0.515, 0.701] | 0.510 [0.421, 0.598] |
| 10 | 0.691 [0.615, 0.763] | 0.635 [0.544, 0.723] | 0.536 [0.451, 0.618] |
| 15 | 0.697 [0.623, 0.766] | 0.644 [0.554, 0.726] | 0.547 [0.463, 0.631] |
| 20 | 0.700 [0.626, 0.771] | 0.649 [0.565, 0.732] | 0.553 [0.474, 0.633] |

**Macro Hit@k**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.766 [0.678, 0.839] | 0.680 [0.583, 0.769] | 0.574 [0.478, 0.669] |
| 5 | 0.825 [0.744, 0.891] | 0.738 [0.646, 0.819] | 0.646 [0.552, 0.731] |
| 10 | 0.883 [0.814, 0.939] | 0.814 [0.733, 0.886] | 0.742 [0.660, 0.819] |
| 15 | 0.918 [0.862, 0.962] | 0.846 [0.774, 0.910] | 0.789 [0.712, 0.860] |
| 20 | 0.935 [0.891, 0.971] | 0.869 [0.808, 0.923] | 0.813 [0.739, 0.880] |

**Macro Top-1 accuracy**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.568 [0.474, 0.657] | 0.507 [0.398, 0.609] | 0.403 [0.313, 0.496] |
| 5 | 0.568 [0.473, 0.654] | 0.507 [0.398, 0.614] | 0.403 [0.313, 0.494] |
| 10 | 0.568 [0.473, 0.659] | 0.507 [0.399, 0.607] | 0.403 [0.316, 0.495] |
| 15 | 0.568 [0.475, 0.659] | 0.507 [0.402, 0.610] | 0.403 [0.310, 0.495] |
| 20 | 0.568 [0.477, 0.656] | 0.507 [0.396, 0.613] | 0.403 [0.314, 0.492] |

**Macro Majority-accuracy** (τ=0.10)

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.541 [0.444, 0.636] | 0.474 [0.365, 0.583] | 0.382 [0.282, 0.485] |
| 5 | 0.490 [0.385, 0.590] | 0.430 [0.314, 0.548] | 0.357 [0.254, 0.464] |
| 10 | 0.416 [0.304, 0.532] | 0.355 [0.230, 0.480] | 0.298 [0.193, 0.410] |
| 15 | 0.355 [0.240, 0.477] | 0.271 [0.157, 0.393] | 0.240 [0.135, 0.356] |
| 20 | 0.285 [0.173, 0.408] | 0.228 [0.116, 0.357] | 0.210 [0.107, 0.329] |

### Macro paired deltas (KAHM − IDF–SVD)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | -0.086 [-0.141, -0.032] | -0.071 [-0.126, -0.017] | -0.061 [-0.127, +0.003] | -0.067 [-0.130, -0.007] | -0.026 [-0.067, +0.017] | -5.792 [-11.189, -0.981] |
| 5 | -0.087 [-0.142, -0.037] | -0.066 [-0.118, -0.015] | -0.061 [-0.125, +0.002] | -0.060 [-0.128, +0.011] | -0.007 [-0.041, +0.028] | -3.562 [-7.669, +0.099] |
| 10 | -0.069 [-0.108, -0.033] | -0.056 [-0.105, -0.008] | -0.061 [-0.125, -0.000] | -0.061 [-0.121, -0.007] | +0.002 [-0.024, +0.028] | -1.340 [-3.354, +0.700] |
| 15 | -0.072 [-0.105, -0.040] | -0.054 [-0.100, -0.006] | -0.061 [-0.126, +0.002] | -0.084 [-0.145, -0.027] | -0.000 [-0.024, +0.022] | -1.346 [-2.728, -0.005] |
| 20 | -0.066 [-0.098, -0.035] | -0.052 [-0.100, -0.005] | -0.061 [-0.126, +0.002] | -0.057 [-0.105, -0.007] | +0.001 [-0.021, +0.023] | -1.093 [-2.159, -0.045] |

### Macro paired deltas vs transformer-query baseline (context; KAHM − Mixedbread)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.106 [+0.061, +0.152] | +0.104 [+0.067, +0.139] | +0.104 [+0.063, +0.145] | +0.092 [+0.060, +0.126] | +0.078 [+0.051, +0.105] | +8.157 [+4.656, +11.842] |
| 5 | +0.092 [+0.051, +0.131] | +0.102 [+0.070, +0.135] | +0.104 [+0.063, +0.146] | +0.073 [+0.035, +0.114] | +0.064 [+0.041, +0.087] | +5.942 [+3.157, +8.751] |
| 10 | +0.072 [+0.049, +0.098] | +0.098 [+0.070, +0.126] | +0.104 [+0.062, +0.146] | +0.056 [+0.019, +0.098] | +0.045 [+0.032, +0.058] | +3.881 [+2.565, +5.308] |
| 15 | +0.058 [+0.033, +0.085] | +0.096 [+0.070, +0.123] | +0.104 [+0.063, +0.145] | +0.031 [+0.007, +0.059] | +0.031 [+0.022, +0.040] | +2.452 [+1.731, +3.199] |
| 20 | +0.055 [+0.030, +0.082] | +0.096 [+0.069, +0.122] | +0.104 [+0.064, +0.146] | +0.019 [-0.003, +0.044] | +0.025 [+0.017, +0.034] | +1.776 [+1.303, +2.228] |

## Majority-vote routing (coverage/precision)

We report a coverage–precision sweep over routing thresholds τ′ (distinct from the predominance threshold used in the majority metric). Coverage is the fraction of queries that meet τ′; precision is accuracy conditioned on being covered.

Recommended τ′ maximizes precision subject to coverage ≥ **0.50**.

| Method | τ′ | Coverage | Majority-acc | Precision (acc|covered) |
| --- | --- | --- | --- | --- |
| IDF–SVD | 0.31 | 0.696 | 0.358 | 0.514 |
| Mixedbread (true) | 0.41 | 0.701 | 0.247 | 0.352 |
| KAHM(query→MB corpus) | 0.51 | 0.516 | 0.217 | 0.421 |

## Computational profile

This section reports query-time computational profiles for the three retrieval paths. The primary comparison target is **online per-query time** (query embedding + FAISS search). If a query embedding source was loaded from a precomputed NPZ in this run, the corresponding online embedding time is reported as `n/a` and the load time is reported separately.

### Per-query online path comparison

| Path | Query source | Query embed / q | FAISS search / q | Total online / q | Observed step sum / q | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| IDF–SVD | model | 7.908 ms | 0.013 ms | 7.921 ms | 7.921 ms | IDF–SVD model load shown in component table (cold-start). |
| KAHM(query→MB corpus) | model | 56.112 ms | 0.004 ms | 56.116 ms | 56.116 ms | Online total only available when KAHM queries were embedded in this run (not precomputed NPZ). |
| Mixedbread (true) | online | 842.486 ms | 0.004 ms | 842.490 ms | 842.490 ms | Online total only available when Mixedbread queries were encoded on the fly (not precomputed NPZ). |

### Measured components (wall-clock)

| Component | Wall time | Per query | Notes |
| --- | --- | --- | --- |
| IDF–SVD query pipeline init (cold-start) | 3.817 s | 3.817 ms | One-time pipeline/materialization cost. |
| IDF–SVD query embedding (batch) | 7.908 s | 7.908 ms |  |
| KAHM query load (precomputed NPZ) | n/a | n/a | Only present when --kahm_query_embeddings_npz is used. |
| KAHM query model init (cold-start) | 3.706 s | 3.706 ms | Only present for online KAHM embedding. |
| KAHM query warm-up (excluded from online total) | 2.985 s | n/a |  |
| KAHM query embedding (batch) | 56.112 s | 56.112 ms |  |
| Mixedbread query load (precomputed NPZ) | n/a | n/a | Only present when precomputed Mixedbread query embeddings are used. |
| Mixedbread model init (cold-start) | 4.426 s | 4.426 ms | Only present for online transformer query encoding. |
| Mixedbread query warm-up (excluded from online total) | 0.698 s | n/a |  |
| Mixedbread query embedding (batch) | 842.486 s | 842.486 ms |  |
| FAISS build (IDF corpus index) | 0.348 s | n/a |  |
| FAISS search (IDF path) | 0.013 s | 0.013 ms |  |
| FAISS build (MB corpus index) | 0.001 s | n/a | Shared by Mixedbread and KAHM(query→MB) paths. |
| FAISS search (Mixedbread path) | 0.004 s | 0.004 ms |  |
| FAISS search (KAHM→MB path) | 0.004 s | 0.004 ms |  |
| Corpus embedding memory (IDF matrix) | 1,083,392 bytes | n/a | NumPy array nbytes (aligned corpus embeddings used in this run). |
| Corpus embedding memory (MB matrix) | 2,166,784 bytes | n/a | NumPy array nbytes (aligned corpus embeddings used in this run). |

### Derived online speedups (per-query)

| Comparison | Speedup | Definition |
| --- | --- | --- |
| IDF–SVD vs KAHM(query→MB corpus) | 0.14× | IDF online / KAHM online |
| Mixedbread (true) vs KAHM(query→MB corpus) | 15.01× | MB online / KAHM online |
| Mixedbread (true) vs IDF–SVD | 106.37× | MB online / IDF online |

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
| mb_query_npz_test | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\queries_embedding_index_test.npz | yes | 1987130 |
| mb_query_npz_train | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\queries_embedding_index_train.npz | yes | 7920014 |

## Notes and limitations

- Query sets appear to follow the synthetic schema (`query_text`, `consensus_law`, `topic_id`, `style`) when such fields are present; interpretation of results should consider the split mode (topic overlap vs disjoint topics).
- This report focuses on retrieval quality, with added wall-clock query-time profiling; it does not benchmark end-to-end serving latency under concurrency or energy use.
- The transformer-query baseline is reported as a reference; KAHM may outperform it if the adapter is supervised/tuned for this label set.
