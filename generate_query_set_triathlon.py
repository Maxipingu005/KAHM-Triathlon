#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_query_set_triathlon.py

Synthetic query generator for Triathlon rule retrieval/classification.

Covers 27 Triathlon rule documents with realistic topics, facets, and context.
Query counts are weighted by page count (log‑scale) to reflect document importance.

IMPORTANT:
All query content has been paraphrased to avoid verbatim document terms,
abbreviations, and document-title-like phrases. The goal is to test semantic
retrieval (KAHM, Mixedbread) under realistic user formulations, while lexical
retrieval (IDF–SVD) should no longer be able to rely on exact word matches.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import random
import re
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Set

# -------------------------
# Label universe (27 Triathlon documents)
# -------------------------
LAWS: List[str] = [
    "WT_Competition_Rules",
    "WT_Para_Classification_Rules",
    "WT_Anti_Doping_Rules",
    "ITU_Disciplinary_Rules",
    "TRI_Gender_Regulations",
    "TRI_Gender_Eligibility_Guidelines",
    "TRI_Individual_OQ_Ranking_Criteria",
    "TRI_Mixed_Relay_OQ_Ranking_Criteria",
    "Para_Triathlon_Interval_Start",
    "WT_Qualification_Criteria",
    "WT_Qualification_Criteria_Continental",
    "WT_Qualification_Criteria_General_Rules",
    "WT_Qualification_Criteria_Multisport",
    "WT_Qualification_Criteria_Championships_Series",
    "WT_Qualification_Criteria_Mixed_Relay",
    "WT_Paralympic_Qualification_Ranking_Criteria",
    "WT_Anti_Doping_Rules_Supplements",
    "WT_Anti_Doping_Rules_Violations",
    "WT_Anti_Doping_Rules_Terms_Of_Interest",
    "WT_Anti_Doping_Rules_Athlete_Responsibilities",
    "WT_Anti_Doping_Data_Privacy_Policy",
    "WT_Code_of_Ethics",
    "WT_Medical_and_Anti-Doping_Management",
    "WT_Medical_Guidelines",
    "WT_Water_Quality",
    "WT_Hydration_Systems",
    "WT_Uniform_Guidelines",
]

# -------------------------
# Page counts (for query weighting)
# -------------------------
_PAGE_COUNTS: Dict[str, int] = {
    "ITU_Disciplinary_Rules": 16,
    "Para_Triathlon_Interval_Start": 5,
    "TRI_Gender_Regulations": 16,
    "TRI_Gender_Eligibility_Guidelines": 4,
    "TRI_Individual_OQ_Ranking_Criteria": 2,
    "TRI_Mixed_Relay_OQ_Ranking_Criteria": 2,
    "WT_Anti_Doping_Data_Privacy_Policy": 4,
    "WT_Anti_Doping_Rules": 55,
    "WT_Anti_Doping_Rules_Athlete_Responsibilities": 1,
    "WT_Anti_Doping_Rules_Supplements": 4,
    "WT_Anti_Doping_Rules_Terms_Of_Interest": 2,
    "WT_Anti_Doping_Rules_Violations": 4,
    "WT_Code_of_Ethics": 9,
    "WT_Competition_Rules": 121,
    "WT_Hydration_Systems": 2,
    "WT_Medical_and_Anti-Doping_Management": 6,
    "WT_Medical_Guidelines": 39,
    "WT_Paralympic_Qualification_Ranking_Criteria": 2,
    "WT_Para_Classification_Rules": 35,
    "WT_Qualification_Criteria": 4,
    "WT_Qualification_Criteria_Championships_Series": 2,
    "WT_Qualification_Criteria_Continental": 4,
    "WT_Qualification_Criteria_General_Rules": 7,
    "WT_Qualification_Criteria_Mixed_Relay": 1,
    "WT_Qualification_Criteria_Multisport": 1,
    "WT_Uniform_Guidelines": 8,
    "WT_Water_Quality": 8,
}

def _compute_query_weights(total_queries: int, min_per_doc: int = 25) -> Dict[str, int]:
    """Distribute queries proportionally to log(page_count+1) with a minimum per document."""
    log_weights = {law: math.log(_PAGE_COUNTS.get(law, 1) + 1) for law in LAWS}
    total_log = sum(log_weights.values())
    reserved = min_per_doc * len(LAWS)
    remaining = max(0, total_queries - reserved)
    out = {}
    for law in LAWS:
        share = int(log_weights[law] / total_log * remaining) if total_log > 0 else 0
        out[law] = min_per_doc + share
    leftover = total_queries - sum(out.values())
    sorted_laws = sorted(LAWS, key=lambda l: _PAGE_COUNTS.get(l, 1), reverse=True)
    for i in range(leftover):
        out[sorted_laws[i % len(sorted_laws)]] += 1
    return out

# -------------------------
# Global enrichment pools (fully paraphrased, no abbreviations)
# -------------------------
CITIES_TRI = [
    "Hamburg", "Kona", "Nice", "Rotterdam", "Edmonton", "Yokohama",
    "Abu Dhabi", "Leeds", "Montreal", "Lausanne", "Pontevedra", "Torremolinos",
    "Cozumel", "Tongyeong", "Chengdu", "Mooloolaba", "Karlovy Vary", "Samarkand",
]

CHANNELS_TRI = [
    "e-mail", "online form", "in person at the race office", "telephone",
    "governing body portal", "complaint form", "official letter", "pre-race briefing",
]

EVIDENCE_TRI = [
    "list of starters", "list of results", "official report", "medical certificate",
    "finish-line photos", "race video", "electronic timing records", "witness statement",
    "GPS tracking", "course map", "water temperature readings", "heat stress measurements",
    "sample collection form", "medication approval document", "medical evaluation form",
    "assessment paperwork", "eligibility confirmation", "manufacturer paperwork",
    "proof of prior enquiry",
]

TIME_PHRASES_TRI = [
    "at a recent major race", "during the cycling section", "yesterday's competition",
    "two weeks ago at a regional event", "at the largest multi-sport event",
    "during the swimming section", "after the finish", "before the start",
    "at the athletes' meeting", "during the assessment appointment",
    "within 30 minutes of finishing", "last month", "in the previous season",
    "30 days before the event", "on the Tuesday before the competition",
    "by Friday before the event", "on the Saturday before the event",
    "48 hours before the briefing",
]

AMOUNTS_TRI = [
    100, 200, 500, 1000, 2500, 5000, 3000, 150, 300, 750, 1200, 10000,
]

ACTORS_TRI = [
    "athlete", "coach", "race official", "technical supervisor",
    "chief referee", "guide", "personal assistant", "national federation",
    "team manager", "evaluator", "head evaluator", "medical supervisor",
    "inclusion officer", "expert group member", "tribunal member",
    "selection committee member", "host national federation",
]

COUNTERPARTIES_TRI = [
    "the international governing body", "race organiser", "jury", "anti-doping panel",
    "national federation", "continental confederation", "international sports court",
    "global anti-doping agency", "international arbitration body", "expert group",
    "assessment panel", "complaint panel", "sports tribunal", "inclusion officer",
    "selection committee", "medical supervisor",
]

AUTHORITIES_TRI = [
    "technical committee of the international governing body", "competition jury",
    "international sports court", "sports tribunal", "international arbitration body",
    "global anti-doping agency", "appeal board for classification decisions",
    "expert group", "head of assessment", "chief evaluator", "complaint panel",
    "assessment advisory group", "selection committee", "technical supervisor",
    "medical supervisor",
]

FACETS_COMMON = [
    "prerequisites", "deadlines", "exceptions", "penalties",
    "appeal process", "required documents", "responsible personnel",
    "equipment specifications", "distance/time limits", "temperature thresholds",
    "notification requirements", "confidentiality obligations",
    "fee amounts", "monitoring procedures", "jurisdiction",
    "quota limits", "ranking dependencies", "substitution rules",
    "joker usage conditions", "withdrawal penalties",
]

# Law-lexicon: intentionally empty to avoid any lexical hints
LAW_TERMS: Dict[str, List[str]] = {}

# Law-specific context overrides – now fully generic
LAW_CONTEXT_OVERRIDES: Dict[str, Dict[str, List[str]]] = {
    "WT_Competition_Rules": {
        "authorities": ["technical committee of the international governing body", "competition jury", "sports tribunal"],
        "actors": ["athlete", "technical supervisor", "chief referee", "guide", "personal assistant"],
        "counterparties": ["the international governing body", "race organiser", "jury", "national federation"],
    },
    "WT_Anti_Doping_Rules": {
        "authorities": ["global anti-doping agency", "international sports court", "hearing panel"],
        "actors": ["athlete", "coach", "doping control officer", "medical personnel"],
        "counterparties": ["global anti-doping agency", "national anti-doping organisation", "international sports court", "laboratory"],
    },
    "ITU_Disciplinary_Rules": {
        "authorities": ["international arbitration body", "international sports court", "panel president"],
        "actors": ["claimant", "appellant", "respondent", "legal representative"],
        "counterparties": ["international arbitration body", "national federation", "international sports court"],
    },
    "TRI_Gender_Regulations": {
        "authorities": ["expert group", "sports tribunal", "inclusion officer"],
        "actors": ["transgender athlete", "inclusion officer", "expert group member"],
        "counterparties": ["expert group", "sports tribunal", "the international governing body"],
    },
    "WT_Para_Classification_Rules": {
        "authorities": ["assessment panel", "chief evaluator", "head of assessment", "appeal board for classification decisions"],
        "actors": ["athlete", "evaluator", "chief evaluator", "national federation"],
        "counterparties": ["the international governing body", "assessment panel", "national federation"],
    },
    "WT_Medical_and_Anti-Doping_Management": {
        "authorities": ["medical supervisor", "race medical director", "the international governing body"],
        "actors": ["medical supervisor", "paramedic", "physician"],
        "counterparties": ["the international governing body", "race organiser"],
    },
    "WT_Medical_Guidelines": {
        "authorities": ["medical supervisor", "the international governing body"],
        "actors": ["team doctor", "coach", "athlete"],
        "counterparties": ["the international governing body", "race organiser"],
    },
}

_GENERIC_OVERRIDE = {
    "authorities": ["the international governing body", "technical supervisor", "selection committee"],
    "actors": ["athlete", "national federation", "team manager"],
    "counterparties": ["the international governing body", "national federation"],
}

# -------------------------
# Text utilities
# -------------------------
_WORD_RE = re.compile(r"[A-Za-z0-9]+", re.UNICODE)
_PLACEHOLDER_RE = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)}")

STOPWORDS = {
    "what", "when", "how", "where", "is", "are", "the", "a", "an",
    "i", "my", "me", "we", "our", "you", "your", "he", "she", "they",
    "and", "or", "for", "with", "from", "in", "on", "at", "to", "of",
    "do", "does", "did", "can", "could", "should", "would", "will",
    "triathlon", "rule", "rules", "regulation", "regulations",
    "world", "international", "competition", "event",
}

# Extra paraphrasing replacements as a safety net – replace any remaining
# abbreviations or specific terms that might have slipped through.
PARAPHRASE_REPLACEMENTS = {
    r"\bCAS\b": "international sports court",
    r"\bWADA\b": "global anti-doping agency",
    r"\bTUE\b": "permission to use a prohibited medication",
    r"\bWBGT\b": "heat stress index",
    r"\bISPPPI\b": "international privacy standard",
    r"\bFADP\b": "data protection law",
    r"\bGDPR\b": "data protection regulation",
    r"\bITU\b": "the international governing body",
    r"\bTRI\b": "the sports governing body",
    r"\bT100\b": "long-distance series",
    r"\bIOC\b": "organizing committee for the major multi-sport event",
    r"\bIPC\b": "organizing committee for athletes with disabilities",
    r"\bOlympic\b": "major international multi-sport event",
    r"\bParalympic\b": "major event for athletes with disabilities",
    r"\bContinental\b": "regional",
    r"\bMixed Relay\b": "team relay",
    r"\bWTCS\b": "main championship series",
    r"\bU23\b": "young athletes",
    r"\bInvitation Panel\b": "selection committee",
    r"\bClassification\b": "assessment",
    r"\bAnti-Doping\b": "drug testing",
    r"\bProhibited List\b": "list of banned substances",
    r"\bRegistered Testing Pool\b": "list of athletes subject to testing",
    r"\bWhereabouts\b": "location reporting",
    r"\bTherapeutic Use Exemption\b": "permission to use a prescribed medication",
    r"\bAdverse Analytical Finding\b": "positive test result",
    r"\bStrict Liability\b": "automatic responsibility",
    r"\bProhibited Substance\b": "banned substance",
    r"\bSupplement\b": "nutritional product",
    r"\bTUE certificate\b": "medication approval document",
    r"\bWBGT measurement log\b": "heat stress measurements",
    r"\bClassification evaluation card\b": "assessment paperwork",
}

def stable_int(s: str) -> int:
    acc = 0
    for i, ch in enumerate(s, start=1):
        acc = (acc * 131 + ord(ch) * i) & 0xFFFFFFFF
    return acc

def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def extract_keywords(source: str, max_tokens: int = 10) -> str:
    toks: List[str] = []
    for t in _WORD_RE.findall(source.replace("-", " ").replace("-", " ")):
        tl = t.lower().strip(".,;:!?()[]{}\"'“”„")
        if not tl or tl in STOPWORDS: continue
        if len(tl) > 2: toks.append(tl)
    return " ".join(toks[:max_tokens]) if toks else source[:50].lower()

def paraphrase_text(text: str) -> str:
    """Apply additional paraphrasing replacements to eliminate any remaining lexical markers."""
    for pattern, repl in PARAPHRASE_REPLACEMENTS.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return normalize_ws(text)

def maybe_apply_surface_noise(text: str, rng: random.Random, p: float) -> str:
    if rng.random() >= p: return text
    def typo_once(s: str) -> str:
        toks = s.split()
        cand_idx = [i for i, t in enumerate(toks) if len(t) >= 6 and t.isalpha()]
        if not cand_idx: return s
        i = rng.choice(cand_idx); w = toks[i]
        j = rng.randrange(1, len(w)-1)
        op = rng.choice(["del", "dup", "swap"])
        if op == "del": w2 = w[:j] + w[j+1:]
        elif op == "dup": w2 = w[:j] + w[j] + w[j:]
        else: w2 = w[:j-1] + w[j] + w[j-1] + w[j+1:]
        toks[i] = w2
        return " ".join(toks)
    variants = [
        text.replace("the international governing body", "the governing body"),
        text.rstrip("?") if text.endswith("?") else text + "?",
        text.lower() if rng.random() < 0.7 else text,
        typo_once(text) if rng.random() < 0.5 else text,
    ]
    return normalize_ws(rng.choice(variants))

def inject_law_hint(text: str, law: str, rng: random.Random) -> str:
    # This function is effectively disabled because law_mention_prob = 0,
    # but kept for compatibility. We return the text unchanged.
    return text

# -------------------------
# Document-specific specs
# -------------------------

@dataclass
class LawSpec:
    templates: List[str]
    slots: Dict[str, List[str]]

def base_law_specs() -> Dict[str, LawSpec]:
    specs: Dict[str, LawSpec] = {}

    # Fully paraphrased topics – no abbreviations, no document titles, no specific terms.
    GENERIC_TOPICS_BY_LAW: Dict[str, List[str]] = {
        "WT_Competition_Rules": [
            "What are the general rules for how a race is conducted",
            "How are athletes expected to behave during the event",
            "What happens if someone breaks a rule during the competition",
            "What are the procedures for starting and finishing a race",
            "What kind of outside help is allowed during the event",
            "How to file a complaint and what does it cost",
            "What are the rules for the transition between different parts of the race",
            "How are decisions about changes to the race due to weather communicated",
        ],
        "WT_Para_Classification_Rules": [
            "How are athletes with different abilities grouped for fair competition",
            "What is the process for determining which category an athlete belongs to",
            "How can an athlete challenge the group they have been placed in",
            "What are the consequences of providing false information during the assessment",
            "How is personal information of athletes protected",
            "What is expected from the people who perform the assessments",
        ],
        "WT_Anti_Doping_Rules": [
            "What are the regulations about substances that are not allowed in sport",
            "How are tests for forbidden substances carried out",
            "What are the consequences if an athlete is found to have taken something prohibited",
            "How can an athlete get permission to use a prescribed medication that is banned",
            "What are the rules about being available for testing",
            "Can an athlete receive a reduced penalty for helping investigators",
            "Who can appeal a decision about a doping violation",
            "How are doping violations kept confidential and when are they made public",
            "Is there a mandatory education programme about drug testing",
        ],
        "ITU_Disciplinary_Rules": [
            "What happens when there is a dispute between an athlete and the governing body",
            "How is a case handled when someone is accused of misconduct",
            "What are the possible sanctions for breaking the rules",
            "How long does an athlete have to file a case",
            "Can a person involved in the decision be removed for bias",
            "What rights does an athlete have to present evidence",
            "What are the costs of the proceedings",
            "How to appeal against a decision",
            "Is there a special panel for major international events",
        ],
        "TRI_Gender_Regulations": [
            "What are the conditions for athletes who wish to compete in a different gender category",
            "How is hormone level monitored for eligibility",
            "What should an athlete do if they want to change their gender category",
            "Are there separate results for some athletes in certain competitions",
            "Who is involved in the assessment of eligibility",
            "How is the athlete's private information protected",
            "How can an athlete appeal a decision about their eligibility",
            "What happens if an athlete withdraws consent for monitoring",
        ],
        "TRI_Gender_Eligibility_Guidelines": [
            "What are the detailed medical requirements for transgender athletes",
            "How often are hormone levels checked for eligibility",
            "What is the role of testosterone in determining eligibility",
            "What medications affect the monitoring frequency",
            "Where does the threshold value come from",
        ],
        "TRI_Individual_OQ_Ranking_Criteria": [
            "How are athletes selected for the major international multi-sport event",
            "How are points awarded in the ranking system",
            "What is the maximum number of results that count",
            "What is the required level of performance to score",
            "Are there limits for regional championships and games",
            "What is the cut-off time rule",
        ],
        "TRI_Mixed_Relay_OQ_Ranking_Criteria": [
            "How are teams selected for the relay event at the major international multi-sport event",
            "How are points awarded for relay races",
            "What is the maximum number of results that count for the relay ranking",
            "Is there a limitation for regional championships",
            "What is the cut-off time rule for relay events",
        ],
        "Para_Triathlon_Interval_Start": [
            "How is the start order determined for athletes with different abilities",
            "What is the system for staggered starts in para events",
            "How are the starting times calculated",
            "How are results from men and women combined",
            "Why is the cycling part ignored for visually impaired athletes",
        ],
        "WT_Qualification_Criteria": [
            "How are athletes selected to take part in major competitions",
            "What is the process for getting a place on the start list",
            "How are waiting lists managed",
            "What is the role of the selection committee",
            "How are empty places filled from the waiting list",
            "What are the qualification pathways for different age groups",
        ],
        "WT_Qualification_Criteria_Continental": [
            "How are athletes selected for regional championships",
            "What are the quota rules for regional competitions",
            "How are junior athletes selected for regional events",
            "What are the rules for the development regional cup",
            "Are there special substitution rules for the Americas region",
        ],
        "WT_Qualification_Criteria_General_Rules": [
            "What are the general rules for start list creation",
            "How are substitutions handled",
            "What are the penalties for withdrawing from an event",
            "How are conflicts between events on the same weekend resolved",
            "What is the joker system",
        ],
        "WT_Qualification_Criteria_Multisport": [
            "How are athletes selected for multisport events",
            "What are the quotas for different age groups",
            "What adjustments can the technical supervisor make",
        ],
        "WT_Qualification_Criteria_Championships_Series": [
            "How are athletes selected for the main championship series",
            "What are the quotas for the championship finals",
            "How are quotas for young athletes managed",
            "How are remaining places allocated",
        ],
        "WT_Qualification_Criteria_Mixed_Relay": [
            "How are teams selected for the team relay event",
            "What is the maximum number of teams",
            "What is the role of the selection committee for relay events",
        ],
        "WT_Paralympic_Qualification_Ranking_Criteria": [
            "How are athletes selected for the major event for athletes with disabilities",
            "How are points awarded in the ranking for athletes with disabilities",
            "What is the maximum number of scoring events",
            "What is the cut-off time rule",
        ],
        "WT_Anti_Doping_Rules_Supplements": [
            "What are the risks of taking nutritional supplements",
            "What is the principle of automatic responsibility for supplements",
            "What is the advice regarding supplement use",
        ],
        "WT_Anti_Doping_Rules_Violations": [
            "What constitutes a violation of the drug testing rules",
            "What are the consequences for evading sample collection",
            "What is the rule about possession of banned substances",
            "What is the rule about interfering with the testing process",
            "What is the rule about location reporting failures",
        ],
        "WT_Anti_Doping_Rules_Terms_Of_Interest": [
            "Who is considered an international-level athlete",
            "What are the obligations of athletes in the testing pool",
            "What is the definition of the competition period",
        ],
        "WT_Anti_Doping_Rules_Athlete_Responsibilities": [
            "What are the responsibilities of athletes regarding sample collection",
            "What must athletes disclose about prior violations",
            "Is there a mandatory education programme",
        ],
        "WT_Anti_Doping_Data_Privacy_Policy": [
            "How is personal data of athletes protected",
            "What types of personal data are processed",
            "What are the rights of individuals regarding their data",
            "What is the legal framework for data protection",
        ],
        "WT_Code_of_Ethics": [
            "What are the principles of behaviour expected from everyone involved in the sport",
            "What should an athlete do if they witness unethical behaviour",
            "What are the rules about betting and manipulation",
            "What are the rules about conflicts of interest and gifts",
        ],
        "WT_Medical_and_Anti-Doping_Management": [
            "What are the medical requirements for organizing a race",
            "What is the role of the medical supervisor",
            "What are the requirements for doping control facilities",
            "What are the ambulance and emergency access requirements",
        ],
        "WT_Medical_Guidelines": [
            "What medical preparations should athletes make before a competition",
            "What are the recommendations for dealing with hot weather during a race",
            "What should be done if an athlete becomes ill during an event",
            "How should athletes adapt to different time zones",
            "What are the guidelines for hydration and nutrition",
            "What are the first aid principles for sports injuries",
        ],
        "WT_Water_Quality": [
            "What are the requirements for the water in which the swimming part takes place",
            "How is the safety of the water checked before an event",
            "What are the health risks from contaminated water",
            "What is the role of the evaluation panel for water safety",
        ],
        "WT_Hydration_Systems": [
            "What are the rules about equipment for carrying drinks during the cycling part",
            "How are handlebar attachments regulated",
            "What is the maximum volume for hydration systems",
            "What are the rules for rear mounted hydration",
        ],
        "WT_Uniform_Guidelines": [
            "What are the rules about what athletes can wear during competition",
            "Where are the names and logos placed on the clothing",
            "What are the sponsor space limits",
            "What is the process for approving uniforms",
        ],
    }

    def _add_topic_spec(law: str, topics: List[str]) -> None:
        specs[law] = LawSpec(templates=["{topic}"], slots={"topic": topics})

    for _law, _topics in GENERIC_TOPICS_BY_LAW.items():
        _add_topic_spec(_law, _topics)

    return specs

def estimate_max_issues(spec: LawSpec) -> int:
    total = 0
    for tmpl in spec.templates:
        keys = _PLACEHOLDER_RE.findall(tmpl)
        if not keys: total += 1
        else:
            prod = 1
            for k in keys: prod *= max(1, len(spec.slots.get(k, [])))
            total += prod
    return total

def generate_issues_for_law(law: str, spec: LawSpec, *, min_count: int, seed: int) -> List[str]:
    rng = random.Random((seed + stable_int(f"{law}:issues")) & 0xFFFFFFFF)
    issues: List[str] = []
    seen: Set[str] = set()
    templates = spec.templates[:]
    rng.shuffle(templates)
    per_template_budget = max(60, ceil(min_count / max(1, len(templates))) * 10)
    for _pass in range(40):
        before = len(issues)
        for tmpl in templates:
            keys = _PLACEHOLDER_RE.findall(tmpl)
            if not keys:
                cand = normalize_ws(tmpl)
                if cand not in seen: seen.add(cand); issues.append(cand)
            else:
                slots = [spec.slots[k] for k in keys]
                used_sig: Set[Tuple[int, ...]] = set()
                for _ in range(per_template_budget):
                    sig = tuple(rng.randrange(len(s)) for s in slots)
                    if sig in used_sig: continue
                    used_sig.add(sig)
                    mapping = {k: spec.slots[k][sig[i]] for i, k in enumerate(keys)}
                    cand = normalize_ws(tmpl.format(**mapping))
                    if cand not in seen: seen.add(cand); issues.append(cand)
                    if len(issues) >= min_count: break
            if len(issues) >= min_count: break
        if len(issues) >= min_count: break
        if len(issues) == before: break
    if len(issues) < min_count:
        cap = estimate_max_issues(spec)
        raise RuntimeError(f"Unable to generate enough issues for {law}: needed {min_count}, got {len(issues)} (cap ~{cap}).")
    rng.shuffle(issues)
    return issues[:]

def expand_spec_with_facets(law: str, base: LawSpec, *, seed: int) -> LawSpec:
    base_cap = estimate_max_issues(base)
    core_seed = min(25, max(8, min(base_cap, 25)))
    core_issues = generate_issues_for_law(law, base, min_count=min(core_seed, base_cap), seed=seed)
    spec = copy.deepcopy(base)
    spec.slots["core"] = core_issues
    spec.slots["facet"] = FACETS_COMMON
    spec.templates.extend(["{core}: {facet}", "{facet} regarding {core}", "{core} - {facet}", "Question about {core}: {facet}"])
    return spec

# -------------------------
# Context and query generation
# -------------------------

def topic_context(topic_id: str, law: str, seed: int, law_context_prob: float) -> Dict[str, str]:
    rng = random.Random((seed + stable_int(f"{topic_id}:{law}:ctx")) & 0xFFFFFFFF)
    actor_pool = ACTORS_TRI
    counterparty_pool = COUNTERPARTIES_TRI
    authority_pool = AUTHORITIES_TRI
    ov = LAW_CONTEXT_OVERRIDES.get(law, _GENERIC_OVERRIDE)
    if ov and rng.random() < law_context_prob:
        actor_pool = ov.get("actors", actor_pool)
        counterparty_pool = ov.get("counterparties", counterparty_pool)
        authority_pool = ov.get("authorities", authority_pool)
    return {
        "actor": rng.choice(actor_pool),
        "counterparty": rng.choice(counterparty_pool),
        "city": rng.choice(CITIES_TRI),
        "time": rng.choice(TIME_PHRASES_TRI),
        "amount": f"{rng.choice(AMOUNTS_TRI)} USD",
        "amount_kw": f"{rng.choice(AMOUNTS_TRI)}usd",
        "channel": rng.choice(CHANNELS_TRI),
        "evidence": rng.choice(EVIDENCE_TRI),
        "authority": rng.choice(authority_pool),
    }

def build_scenario(issue: str, ctx: Dict[str, str], rng: random.Random, term: str | None = None) -> str:
    amount_part = rng.choice([f"The matter involves {ctx['amount']}.", f"Amount: {ctx['amount']}.", ""])
    contact_part = rng.choice([f"Contact via {ctx['channel']}.", f"Communication through {ctx['channel']}.", ""])
    evidence_part = rng.choice([f"Evidence: {ctx['evidence']}.", f"Documents: {ctx['evidence']}.", f"Supported by {ctx['evidence']}.", ""])
    authority_part = rng.choice([f"A decision/notice from {ctx['authority']} is involved.", f"Jurisdiction unclear ({ctx['authority']} or the sports court?).", ""])
    term_part = ""
    if term and rng.random() < 0.55: term_part = rng.choice([f"Keyword: {term}.", f"Topic: {term}.", f"({term})"])
    skeletons = [
        f"I am a {ctx['actor']} in {ctx['city']}. {ctx['time']} there was an issue with {ctx['counterparty']}: {issue}. {amount_part} {contact_part} {evidence_part} {authority_part} {term_part}",
        f"Situation ({ctx['city']}, {ctx['time']}): {issue}. Parties: {ctx['actor']} vs {ctx['counterparty']}. {amount_part} {evidence_part} {term_part} {authority_part}",
        f"Brief: {issue} - {ctx['actor']} ({ctx['city']}) vs {ctx['counterparty']}. {contact_part} {amount_part} {term_part}",
        f"{ctx['time']} in {ctx['city']}: {issue}. {evidence_part} {authority_part} {term_part}",
    ]
    return normalize_ws(rng.choice(skeletons))

STYLES = ["nl_short", "nl_long", "scenario", "procedural", "authority", "keyword", "fragment"]

STYLE_TEMPLATES: Dict[str, List[str]] = {
    "nl_short": [
        "{issue} – what are the rules?", "What are my rights/obligations regarding {issue}?",
        "What can I do about {issue}?", "{issue}: what is the deadline?",
        "{issue}: what are the prerequisites?", "{issue} – do I need to submit an application/evidence?",
        "{issue}: which body is responsible?", "Are there any exceptions for {issue}?",
        "What are the costs/risks for {issue}?", "What sanctions apply for {issue}?",
    ],
    "nl_long": [
        "{scenario} What rules apply and what steps should I take?",
        "{scenario} What claims/consequences are possible and what deadlines apply?",
        "{scenario} What prerequisites are relevant, what evidence do I need, and where do I file?",
        "{scenario} How do I proceed practically (deadline, jurisdiction, evidence, costs)?",
    ],
    "scenario": [
        "Facts: {scenario} Question: {question}", "Case: {scenario} {question}",
        "Context: {scenario} {question} (deadline/jurisdiction/evidence)",
        "{scenario} {question} – please include deadlines and responsible body.",
    ],
    "procedural": [
        "How does the procedure for {issue} work (deadline, application, evidence, costs)?",
        "{issue}: What deadlines apply, what are typical evidence requirements, and who decides?",
        "For {issue}: What remedies are available and does an appeal have suspensive effect?",
        "{issue}: Jurisdiction and procedural steps (application/decision/appeal).",
        "What formal requirements apply for {issue} (written form, deadline, reasoning)?",
    ],
    "authority": [
        "For {issue}: Do I go to {authority} or to court?",
        "For {issue}: Do I go to {authority} or to the international sports court?",
        "{issue}: Jurisdiction {authority} vs court – and what deadline?",
        "{issue}: How do I submit to {authority} (form/deadline)?",
    ],
    "keyword": [
        "{keywords}", "{keywords} deadline jurisdiction", "{keywords} procedure appeal",
        "{keywords} evidence costs", "{keywords} decision deadline",
    ],
    "fragment": [
        "{issue} {city}", "{issue} {time}", "{issue} {authority}",
        "{issue} {amount_kw}", "{issue} {channel} {evidence}",
        "{issue} deadline", "{issue} jurisdiction", "{issue} appeal",
    ],
}

QUESTION_FORMS = [
    "What regulations are applicable?", "What rights and obligations exist?",
    "What claims can I assert?", "What consequences apply in case of a violation?",
    "What deadlines and procedures must be observed?",
]

def generate_queries_for_topic(*, topic_id: str, issue: str, law: str, seed: int, variants_per_style: int, law_mention_prob: float, keyword_law_mention_prob: float, surface_noise_prob: float, law_context_prob: float, topic_term_prob: float, issue_term_prob: float, keyword_term_prob: float) -> List[Dict[str, str]]:
    ctx = topic_context(topic_id, law, seed, law_context_prob)
    base_rng = random.Random((seed + stable_int(f"{topic_id}:{law}:base")) & 0xFFFFFFFF)
    term_pool = LAW_TERMS.get(law, [])
    topic_term = None
    if term_pool and base_rng.random() < topic_term_prob: topic_term = base_rng.choice(term_pool)
    scenario = build_scenario(issue, ctx, base_rng, term=topic_term)
    question = base_rng.choice(QUESTION_FORMS)
    k_source = f"{issue} {ctx['city']} {ctx['amount_kw']} {ctx['channel']} {ctx['evidence']} {ctx['time']} {ctx['authority']}"
    if topic_term and base_rng.random() < keyword_term_prob: k_source = f"{k_source} {topic_term}"
    keywords = extract_keywords(k_source, max_tokens=11)
    def enrich_issue(rng: random.Random) -> str:
        if not term_pool or rng.random() >= issue_term_prob: return issue
        t = topic_term if (topic_term and rng.random() < 0.65) else rng.choice(term_pool)
        return rng.choice([f"{issue} ({t})", f"{issue} - {t}", f"{t}: {issue}"])
    out: List[Dict[str, str]] = []
    for style in STYLES:
        for v in range(1, variants_per_style + 1):
            sseed = (seed + stable_int(f"{topic_id}:{law}:{style}:v{v}")) & 0xFFFFFFFF
            rng = random.Random(sseed)
            template = rng.choice(STYLE_TEMPLATES[style])
            text = template.format(issue=enrich_issue(rng), scenario=scenario, question=question, keywords=keywords, authority=ctx["authority"], city=ctx["city"], time=ctx["time"], amount_kw=ctx["amount_kw"], channel=ctx["channel"], evidence=ctx["evidence"])
            text = normalize_ws(text)
            # law_mention_prob and keyword_law_mention_prob are set to 0, so this is just a safeguard
            if rng.random() < 0.0:  # never
                text = inject_law_hint(text, law, rng)
            # Apply extra paraphrasing to remove any remaining abbreviations/specific terms
            text = paraphrase_text(text)
            text = maybe_apply_surface_noise(text, rng, surface_noise_prob)
            out.append({"query_id": f"{topic_id}_{style}_v{v:02d}", "topic_id": topic_id, "query_text": text, "consensus_law": law, "style": style, "issue": issue})
    return out

# -------------------------
# Allocation and sampling
# -------------------------

def target_counts_weighted(total: int) -> Dict[str, int]:
    return _compute_query_weights(total, min_per_doc=25)

def target_counts_law_style(total_by_law: Dict[str, int], styles: Sequence[str], seed: int) -> Dict[Tuple[str, str], int]:
    styles_list = list(styles)
    n_styles = len(styles_list)
    out: Dict[Tuple[str, str], int] = {}
    for law in sorted(total_by_law):
        total = total_by_law[law]
        base = total // n_styles
        rem = total - base * n_styles
        rng = random.Random((seed + stable_int(f"{law}:style_rem")) & 0xFFFFFFFF)
        order = styles_list[:]; rng.shuffle(order)
        for style in styles_list: out[(law, style)] = base
        for i in range(rem): out[(law, order[i])] += 1
    return out

def sample_stratified_grid(pool: List[Dict[str, str]], target: Dict[Tuple[str, str], int], seed: int, forbid_texts: Set[str]) -> List[Dict[str, str]]:
    rng = random.Random(seed)
    keys = sorted(target)
    by_key: Dict[Tuple[str, str], List[Dict[str, str]]] = {k: [] for k in keys}
    for r in pool:
        k = (r["consensus_law"], r["style"])
        if k in by_key: by_key[k].append(r)
    for k in keys: rng.shuffle(by_key[k])
    selected, used = [], set(forbid_texts)
    for k in keys:
        need, picks = target[k], []
        for r in by_key[k]:
            if len(picks) >= need: break
            if r["query_text"] not in used: used.add(r["query_text"]); picks.append(r)
        if len(picks) != need:
            law, style = k
            raise RuntimeError(f"Not enough unique candidates for (law={law}, style={style}): need={need}, got={len(picks)}.")
        selected.extend(picks)
    rng.shuffle(selected)
    return selected

def split_train_test_stratified_grid_test_topics_in_train(pool, train_target, test_target, seed):
    train_rows = sample_stratified_grid(pool, train_target, seed, forbid_texts=set())
    train_topics = {}
    for r in train_rows: train_topics.setdefault(r["consensus_law"], set()).add(r["topic_id"])
    pool_test = [r for r in pool if r["topic_id"] in train_topics.get(r["consensus_law"], set())]
    forbid = {r["query_text"] for r in train_rows}
    test_rows = sample_stratified_grid(pool_test, test_target, seed + 101, forbid_texts=forbid)
    rng = random.Random(seed + 999)
    rng.shuffle(train_rows); rng.shuffle(test_rows)
    return train_rows, test_rows

def write_jsonl(path: Path, rows: List[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")

# -------------------------
# Main
# -------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=19)
    ap.add_argument("--train_n", type=int, default=4000)
    ap.add_argument("--test_n", type=int, default=1000)
    ap.add_argument("--output_dir", type=str, default=".")
    ap.add_argument("--variants_per_style", type=int, default=3)
    ap.add_argument("--split_mode", choices=["iid", "iid_unrestricted", "topic_disjoint"], default="iid")
    # All mention probabilities set to 0 to avoid any document-name hints
    ap.add_argument("--law_mention_prob", type=float, default=0.0)
    ap.add_argument("--keyword_law_mention_prob", type=float, default=0.0)
    ap.add_argument("--surface_noise_prob", type=float, default=0.06)
    ap.add_argument("--law_context_prob", type=float, default=1.0)
    ap.add_argument("--topic_term_prob", type=float, default=0.0)
    ap.add_argument("--issue_term_prob", type=float, default=0.0)
    ap.add_argument("--keyword_term_prob", type=float, default=0.0)
    ap.add_argument("--candidate_oversupply", type=float, default=2.0)
    args = ap.parse_args()
    seed = args.seed
    outdir = Path(args.output_dir); outdir.mkdir(parents=True, exist_ok=True)
    if len(set(LAWS)) != len(LAWS): raise RuntimeError("LAWS contains duplicates.")
    train_target_law = target_counts_weighted(args.train_n)
    test_target_law = target_counts_weighted(args.test_n)
    train_target = target_counts_law_style(train_target_law, STYLES, seed + 777)
    test_target = target_counts_law_style(test_target_law, STYLES, seed + 777)
    queries_per_topic = len(STYLES) * args.variants_per_style
    base_specs = base_law_specs()
    topics_by_law, extra = {}, 8
    if args.split_mode == "topic_disjoint":
        raise NotImplementedError("topic_disjoint mode is not supported with weighted counts; use iid or iid_unrestricted.")
    else:
        topics_per_law = {}
        for law in sorted(LAWS):
            need = train_target_law[law] + test_target_law[law]
            topics_per_law[law] = max(8, ceil((need * args.candidate_oversupply) / max(1, queries_per_topic)))
        for law in sorted(LAWS):
            if law not in base_specs: raise RuntimeError(f"Missing base spec for {law}")
            spec = expand_spec_with_facets(law, base_specs[law], seed=seed)
            issues = generate_issues_for_law(law, spec, min_count=topics_per_law[law] + extra, seed=seed)
            topics_by_law[law] = [(f"{law}_T{i:03d}", issues[i-1]) for i in range(1, len(issues)+1)]
        all_topics = [(tid, iss, law) for law in sorted(LAWS) for tid, iss in topics_by_law[law]]
        def build_pool(topics, split_seed):
            pool = []
            for tid, issue, law in topics:
                pool.extend(generate_queries_for_topic(
                    topic_id=tid, issue=issue, law=law, seed=split_seed,
                    variants_per_style=args.variants_per_style,
                    law_mention_prob=args.law_mention_prob,
                    keyword_law_mention_prob=args.keyword_law_mention_prob,
                    surface_noise_prob=args.surface_noise_prob,
                    law_context_prob=args.law_context_prob,
                    topic_term_prob=args.topic_term_prob,
                    issue_term_prob=args.issue_term_prob,
                    keyword_term_prob=args.keyword_term_prob
                ))
            return pool
        pool = build_pool(all_topics, seed + 111)
        train_rows, test_rows = split_train_test_stratified_grid_test_topics_in_train(pool, train_target, test_target, seed + 303)
        split_meta = {"topics_per_law": topics_per_law, "extra_topics_per_law": extra, "test_topics_subset_of_train": True}
    train_path = outdir / "train.jsonl"; test_path = outdir / "test.jsonl"; meta_path = outdir / "meta.json"
    write_jsonl(train_path, train_rows); write_jsonl(test_path, test_rows)
    def _count(rows, fields):
        out = {}
        for r in rows: k = "||".join(r[f] for f in fields); out[k] = out.get(k, 0) + 1
        return out
    meta = {
        "seed": seed, "split_mode": args.split_mode, "train_n": args.train_n, "test_n": args.test_n,
        "laws": sorted(LAWS), "n_laws": len(LAWS), "styles": STYLES, "variants_per_style": args.variants_per_style,
        "queries_per_topic": queries_per_topic, "law_mention_prob": args.law_mention_prob,
        "keyword_law_mention_prob": args.keyword_law_mention_prob, "surface_noise_prob": args.surface_noise_prob,
        "law_context_prob": args.law_context_prob, "topic_term_prob": args.topic_term_prob,
        "issue_term_prob": args.issue_term_prob, "keyword_term_prob": args.keyword_term_prob,
        "candidate_oversupply": args.candidate_oversupply, "train_target_counts_by_law": train_target_law,
        "test_target_counts_by_law": test_target_law,
        "train_target_counts_by_law_style": {f"{k[0]}||{k[1]}": v for k, v in train_target.items()},
        "test_target_counts_by_law_style": {f"{k[0]}||{k[1]}": v for k, v in test_target.items()},
        "realized_train_counts_by_law_style": _count(train_rows, ("consensus_law", "style")),
        "realized_test_counts_by_law_style": _count(test_rows, ("consensus_law", "style")),
        "files": {"train": str(train_path), "test": str(test_path), "meta": str(meta_path)},
    }
    meta.update(split_meta)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(train_rows)} train rows to {train_path}")
    print(f"Wrote {len(test_rows)} test rows to {test_path}")
    print(f"Wrote meta to {meta_path}")

if __name__ == "__main__":
    main()