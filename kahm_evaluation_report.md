# KAHM embeddings: retrieval evaluation on Austrian laws

Generated: 2026-08-16 08:45:53 | script=evaluate_three_embeddings_storylines.py | version=2026-02-23-scientific-pubreport-v1

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

- Unique topic IDs: **548**
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
- Topic overlap (TRAIN ∩ TEST): **548** topics
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
| 3 | 0.384 [0.357, 0.411] | 0.476 [0.448, 0.505] | 0.410 [0.382, 0.439] |
| 5 | 0.417 [0.390, 0.442] | 0.508 [0.480, 0.536] | 0.438 [0.410, 0.465] |
| 10 | 0.445 [0.421, 0.470] | 0.532 [0.506, 0.559] | 0.470 [0.444, 0.497] |
| 15 | 0.454 [0.429, 0.478] | 0.542 [0.516, 0.568] | 0.485 [0.459, 0.511] |
| 20 | 0.460 [0.436, 0.485] | 0.548 [0.522, 0.574] | 0.492 [0.468, 0.517] |

**Hit@k**
 
| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.486 [0.455, 0.517] | 0.544 [0.512, 0.574] | 0.480 [0.448, 0.511] |
| 5 | 0.584 [0.553, 0.615] | 0.623 [0.593, 0.653] | 0.557 [0.526, 0.588] |
| 10 | 0.651 [0.622, 0.679] | 0.697 [0.668, 0.725] | 0.667 [0.637, 0.696] |
| 15 | 0.706 [0.680, 0.732] | 0.741 [0.714, 0.768] | 0.728 [0.700, 0.756] |
| 20 | 0.750 [0.725, 0.774] | 0.770 [0.743, 0.796] | 0.761 [0.735, 0.787] |

**Top-1 accuracy**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.294 [0.266, 0.322] | 0.415 [0.385, 0.446] | 0.349 [0.320, 0.378] |
| 5 | 0.294 [0.267, 0.323] | 0.415 [0.385, 0.446] | 0.349 [0.319, 0.379] |
| 10 | 0.294 [0.266, 0.322] | 0.415 [0.385, 0.446] | 0.349 [0.319, 0.378] |
| 15 | 0.294 [0.266, 0.322] | 0.415 [0.385, 0.445] | 0.349 [0.320, 0.379] |
| 20 | 0.294 [0.266, 0.322] | 0.415 [0.384, 0.447] | 0.349 [0.320, 0.379] |

**Majority-accuracy** (τ=0.10)

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.280 [0.252, 0.307] | 0.400 [0.370, 0.431] | 0.318 [0.289, 0.347] |
| 5 | 0.274 [0.247, 0.301] | 0.354 [0.325, 0.384] | 0.290 [0.262, 0.318] |
| 10 | 0.247 [0.220, 0.275] | 0.291 [0.263, 0.319] | 0.258 [0.230, 0.286] |
| 15 | 0.219 [0.193, 0.245] | 0.241 [0.215, 0.268] | 0.212 [0.186, 0.238] |
| 20 | 0.199 [0.174, 0.223] | 0.197 [0.172, 0.222] | 0.184 [0.160, 0.208] |

**Mean consensus fraction**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.248 [0.229, 0.267] | 0.346 [0.322, 0.369] | 0.292 [0.270, 0.314] |
| 5 | 0.227 [0.211, 0.242] | 0.311 [0.291, 0.331] | 0.265 [0.246, 0.285] |
| 10 | 0.188 [0.176, 0.201] | 0.258 [0.241, 0.275] | 0.230 [0.213, 0.246] |
| 15 | 0.164 [0.154, 0.175] | 0.227 [0.212, 0.243] | 0.205 [0.190, 0.220] |
| 20 | 0.151 [0.141, 0.161] | 0.206 [0.192, 0.222] | 0.190 [0.175, 0.205] |

**Mean lift (prior)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 16.974 [15.205, 18.773] | 18.436 [16.608, 20.277] | 15.146 [13.448, 16.863] |
| 5 | 14.777 [13.407, 16.198] | 16.638 [15.140, 18.183] | 13.200 [11.853, 14.627] |
| 10 | 11.134 [10.250, 12.009] | 12.231 [11.293, 13.157] | 10.561 [9.714, 11.434] |
| 15 | 9.347 [8.672, 10.037] | 9.926 [9.260, 10.585] | 8.733 [8.143, 9.362] |
| 20 | 8.197 [7.671, 8.728] | 8.490 [7.949, 9.016] | 7.645 [7.151, 8.140] |

### Paired deltas (KAHM − IDF–SVD)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.058 [+0.021, +0.093] | +0.092 [+0.062, +0.123] | +0.121 [+0.088, +0.155] | +0.120 [+0.087, +0.154] | +0.098 [+0.076, +0.121] | +1.462 [-0.430, +3.355] |
| 5 | +0.039 [+0.005, +0.074] | +0.091 [+0.062, +0.120] | +0.121 [+0.086, +0.154] | +0.080 [+0.050, +0.110] | +0.084 [+0.067, +0.102] | +1.862 [+0.292, +3.375] |
| 10 | -0.014 [-0.046, +0.018] | +0.088 [+0.061, +0.114] | +0.121 [+0.087, +0.155] | +0.044 [+0.016, +0.073] | +0.070 [+0.056, +0.083] | +1.097 [+0.207, +2.005] |
| 15 | -0.025 [-0.055, +0.004] | +0.088 [+0.062, +0.115] | +0.121 [+0.087, +0.154] | +0.022 [-0.005, +0.049] | +0.063 [+0.052, +0.074] | +0.579 [-0.052, +1.230] |
| 20 | -0.040 [-0.068, -0.011] | +0.088 [+0.063, +0.114] | +0.121 [+0.088, +0.155] | -0.002 [-0.028, +0.023] | +0.056 [+0.046, +0.066] | +0.293 [-0.200, +0.793] |

### Paired deltas vs transformer-query baseline (context; KAHM − Mixedbread)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.064 [+0.039, +0.090] | +0.066 [+0.045, +0.088] | +0.066 [+0.040, +0.092] | +0.082 [+0.056, +0.109] | +0.054 [+0.038, +0.071] | +3.290 [+1.889, +4.646] |
| 5 | +0.066 [+0.039, +0.093] | +0.070 [+0.050, +0.091] | +0.066 [+0.041, +0.091] | +0.064 [+0.040, +0.088] | +0.045 [+0.033, +0.057] | +3.438 [+2.231, +4.657] |
| 10 | +0.030 [+0.004, +0.056] | +0.062 [+0.042, +0.082] | +0.066 [+0.043, +0.092] | +0.033 [+0.012, +0.055] | +0.028 [+0.020, +0.037] | +1.670 [+0.916, +2.416] |
| 15 | +0.013 [-0.011, +0.037] | +0.057 [+0.037, +0.076] | +0.066 [+0.041, +0.091] | +0.029 [+0.008, +0.050] | +0.022 [+0.016, +0.029] | +1.193 [+0.704, +1.679] |
| 20 | +0.009 [-0.014, +0.032] | +0.055 [+0.037, +0.074] | +0.066 [+0.041, +0.091] | +0.013 [-0.004, +0.030] | +0.017 [+0.011, +0.022] | +0.845 [+0.466, +1.217] |

### Macro-averaged quality (per-law average; robustness)

Macro-averaging computes metrics per law and then averages across laws (each law has equal weight). This is a robustness check against label-frequency skew.

**Macro MRR@k (unique docs.)**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.370 [0.289, 0.455] | 0.438 [0.322, 0.555] | 0.373 [0.271, 0.477] |
| 5 | 0.401 [0.316, 0.484] | 0.471 [0.360, 0.578] | 0.400 [0.300, 0.502] |
| 10 | 0.428 [0.348, 0.512] | 0.497 [0.392, 0.602] | 0.434 [0.332, 0.533] |
| 15 | 0.438 [0.357, 0.516] | 0.507 [0.401, 0.609] | 0.450 [0.351, 0.548] |
| 20 | 0.444 [0.367, 0.527] | 0.514 [0.415, 0.616] | 0.458 [0.365, 0.554] |

**Macro Hit@k**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.467 [0.375, 0.558] | 0.503 [0.380, 0.627] | 0.441 [0.332, 0.546] |
| 5 | 0.561 [0.461, 0.661] | 0.584 [0.466, 0.695] | 0.517 [0.401, 0.624] |
| 10 | 0.685 [0.588, 0.779] | 0.661 [0.544, 0.769] | 0.629 [0.519, 0.737] |
| 15 | 0.742 [0.651, 0.827] | 0.707 [0.599, 0.805] | 0.694 [0.590, 0.791] |
| 20 | 0.790 [0.707, 0.868] | 0.741 [0.641, 0.833] | 0.730 [0.624, 0.824] |

**Macro Top-1 accuracy**

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.283 [0.205, 0.365] | 0.379 [0.269, 0.492] | 0.313 [0.215, 0.417] |
| 5 | 0.283 [0.202, 0.368] | 0.379 [0.270, 0.491] | 0.313 [0.216, 0.420] |
| 10 | 0.283 [0.205, 0.366] | 0.379 [0.271, 0.488] | 0.313 [0.216, 0.414] |
| 15 | 0.283 [0.204, 0.365] | 0.379 [0.270, 0.486] | 0.313 [0.214, 0.415] |
| 20 | 0.283 [0.203, 0.367] | 0.379 [0.270, 0.486] | 0.313 [0.217, 0.413] |

**Macro Majority-accuracy** (τ=0.10)

| k | IDF–SVD | KAHM(query→MB corpus) | Mixedbread (true) |
| --- | --- | --- | --- |
| 3 | 0.265 [0.184, 0.349] | 0.361 [0.248, 0.480] | 0.284 [0.191, 0.382] |
| 5 | 0.251 [0.164, 0.342] | 0.312 [0.198, 0.432] | 0.253 [0.162, 0.353] |
| 10 | 0.218 [0.134, 0.314] | 0.251 [0.146, 0.369] | 0.221 [0.125, 0.323] |
| 15 | 0.189 [0.107, 0.279] | 0.200 [0.106, 0.311] | 0.174 [0.089, 0.274] |
| 20 | 0.167 [0.089, 0.255] | 0.156 [0.069, 0.263] | 0.145 [0.060, 0.255] |

### Macro paired deltas (KAHM − IDF–SVD)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.036 [-0.066, +0.132] | +0.069 [-0.024, +0.155] | +0.096 [+0.008, +0.182] | +0.096 [+0.018, +0.181] | +0.079 [+0.009, +0.152] | +0.748 [-5.917, +6.543] |
| 5 | +0.023 [-0.081, +0.122] | +0.070 [-0.022, +0.151] | +0.096 [+0.009, +0.178] | +0.061 [-0.007, +0.133] | +0.068 [+0.012, +0.128] | +1.495 [-3.801, +6.228] |
| 10 | -0.024 [-0.111, +0.060] | +0.068 [-0.010, +0.146] | +0.096 [+0.013, +0.181] | +0.033 [-0.026, +0.094] | +0.055 [+0.016, +0.099] | +0.815 [-2.059, +3.604] |
| 15 | -0.035 [-0.111, +0.048] | +0.069 [-0.006, +0.143] | +0.096 [+0.008, +0.181] | +0.011 [-0.041, +0.072] | +0.048 [+0.013, +0.090] | +0.280 [-1.975, +2.383] |
| 20 | -0.049 [-0.124, +0.029] | +0.069 [-0.006, +0.141] | +0.096 [+0.010, +0.181] | -0.010 [-0.064, +0.047] | +0.042 [+0.010, +0.081] | +0.027 [-1.696, +1.662] |

### Macro paired deltas vs transformer-query baseline (context; KAHM − Mixedbread)

| k | Δhit@k | ΔMRR@k | ΔTop-1 | ΔMajority-acc | ΔMean cons frac | ΔMean lift |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | +0.062 [+0.024, +0.101] | +0.065 [+0.030, +0.100] | +0.066 [+0.030, +0.103] | +0.077 [+0.037, +0.119] | +0.051 [+0.025, +0.078] | +3.380 [+1.176, +5.837] |
| 5 | +0.067 [+0.031, +0.105] | +0.071 [+0.040, +0.106] | +0.066 [+0.030, +0.105] | +0.059 [+0.027, +0.093] | +0.043 [+0.024, +0.063] | +3.736 [+1.878, +5.729] |
| 10 | +0.033 [-0.002, +0.067] | +0.063 [+0.033, +0.096] | +0.066 [+0.030, +0.104] | +0.030 [+0.008, +0.056] | +0.026 [+0.014, +0.038] | +1.756 [+0.502, +3.038] |
| 15 | +0.013 [-0.017, +0.043] | +0.057 [+0.029, +0.088] | +0.066 [+0.030, +0.102] | +0.027 [+0.005, +0.050] | +0.020 [+0.011, +0.029] | +1.247 [+0.464, +2.033] |
| 20 | +0.011 [-0.020, +0.039] | +0.056 [+0.029, +0.086] | +0.066 [+0.031, +0.103] | +0.011 [-0.002, +0.024] | +0.014 [+0.008, +0.022] | +0.893 [+0.356, +1.439] |

## Majority-vote routing (coverage/precision)

We report a coverage–precision sweep over routing thresholds τ′ (distinct from the predominance threshold used in the majority metric). Coverage is the fraction of queries that meet τ′; precision is accuracy conditioned on being covered.

Recommended τ′ maximizes precision subject to coverage ≥ **0.50**.

| Method | τ′ | Coverage | Majority-acc | Precision (acc|covered) |
| --- | --- | --- | --- | --- |
| IDF–SVD | 0.31 | 0.670 | 0.185 | 0.276 |
| Mixedbread (true) | 0.31 | 0.885 | 0.231 | 0.261 |
| KAHM(query→MB corpus) | 0.31 | 0.899 | 0.265 | 0.295 |

## Computational profile

This section reports query-time computational profiles for the three retrieval paths. The primary comparison target is **online per-query time** (query embedding + FAISS search). If a query embedding source was loaded from a precomputed NPZ in this run, the corresponding online embedding time is reported as `n/a` and the load time is reported separately.

### Per-query online path comparison

| Path | Query source | Query embed / q | FAISS search / q | Total online / q | Observed step sum / q | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| IDF–SVD | model | 8.768 ms | 0.010 ms | 8.778 ms | 8.778 ms | IDF–SVD model load shown in component table (cold-start). |
| KAHM(query→MB corpus) | model | 42.251 ms | 0.004 ms | 42.255 ms | 42.255 ms | Online total only available when KAHM queries were embedded in this run (not precomputed NPZ). |
| Mixedbread (true) | online | 681.943 ms | 0.005 ms | 681.948 ms | 681.948 ms | Online total only available when Mixedbread queries were encoded on the fly (not precomputed NPZ). |

### Measured components (wall-clock)

| Component | Wall time | Per query | Notes |
| --- | --- | --- | --- |
| IDF–SVD query pipeline init (cold-start) | 4.503 s | 4.503 ms | One-time pipeline/materialization cost. |
| IDF–SVD query embedding (batch) | 8.768 s | 8.768 ms |  |
| KAHM query load (precomputed NPZ) | n/a | n/a | Only present when --kahm_query_embeddings_npz is used. |
| KAHM query model init (cold-start) | 3.973 s | 3.973 ms | Only present for online KAHM embedding. |
| KAHM query warm-up (excluded from online total) | 2.932 s | n/a |  |
| KAHM query embedding (batch) | 42.251 s | 42.251 ms |  |
| Mixedbread query load (precomputed NPZ) | n/a | n/a | Only present when precomputed Mixedbread query embeddings are used. |
| Mixedbread model init (cold-start) | 4.406 s | 4.406 ms | Only present for online transformer query encoding. |
| Mixedbread query warm-up (excluded from online total) | 1.053 s | n/a |  |
| Mixedbread query embedding (batch) | 681.943 s | 681.943 ms |  |
| FAISS build (IDF corpus index) | 0.090 s | n/a |  |
| FAISS search (IDF path) | 0.010 s | 0.010 ms |  |
| FAISS build (MB corpus index) | 0.001 s | n/a | Shared by Mixedbread and KAHM(query→MB) paths. |
| FAISS search (Mixedbread path) | 0.005 s | 0.005 ms |  |
| FAISS search (KAHM→MB path) | 0.004 s | 0.004 ms |  |
| Corpus embedding memory (IDF matrix) | 1,083,392 bytes | n/a | NumPy array nbytes (aligned corpus embeddings used in this run). |
| Corpus embedding memory (MB matrix) | 2,166,784 bytes | n/a | NumPy array nbytes (aligned corpus embeddings used in this run). |

### Derived online speedups (per-query)

| Comparison | Speedup | Definition |
| --- | --- | --- |
| IDF–SVD vs KAHM(query→MB corpus) | 0.21× | IDF online / KAHM online |
| Mixedbread (true) vs KAHM(query→MB corpus) | 16.14× | MB online / KAHM online |
| Mixedbread (true) vs IDF–SVD | 77.69× | MB online / IDF online |

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
| mb_query_npz_test | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\queries_embedding_index_test.npz | yes | 1977115 |
| mb_query_npz_train | C:\Users\marxp\Documents\Repositories\KAHM-Triathlon\queries_embedding_index_train.npz | yes | 7894122 |

## Notes and limitations

- Query sets appear to follow the synthetic schema (`query_text`, `consensus_law`, `topic_id`, `style`) when such fields are present; interpretation of results should consider the split mode (topic overlap vs disjoint topics).
- This report focuses on retrieval quality, with added wall-clock query-time profiling; it does not benchmark end-to-end serving latency under concurrency or energy use.
- The transformer-query baseline is reported as a reference; KAHM may outperform it if the adapter is supervised/tuned for this label set.
