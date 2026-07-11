#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_query_set_triathlon.py

Synthetic query generator for triathlon retrieval/classification.

Design goals
------------
- Exact train/test sizes.
- I.I.D. train/test by default: TRAIN and TEST share the same latent topic mixture (recommended).
- High semantic diversity and realistic surface forms.
- Minimal label leakage


Outputs (default filenames)
---------------------------
- train.jsonl
- test.jsonl
- meta.json

Each JSONL row includes:
  query_id, topic_id, query_text, style, issue
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import re
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Set


