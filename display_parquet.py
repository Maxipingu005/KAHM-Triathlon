# -*- coding: utf-8 -*-

import pandas as pd

PARQUET_FILE = "ris_sentences.parquet"
LABEL_COL = "triathlon_rules"  #use "law_type" for Professor Austrian Laws
CHUNKS_PER_DOC = 10            

pd.set_option("display.max_colwidth", None)

df = pd.read_parquet(PARQUET_FILE)

for label in df[LABEL_COL].unique():
    print(f"\n{'='*60}")
    print(f"=== {label} ===")
    print('='*60)

    subset = df[df[LABEL_COL] == label].head(CHUNKS_PER_DOC)

    for _, row in subset.iterrows():
        print(f"\n--- Chunk ID {row['sentence_id']} ---")
        print(row["sentence"])