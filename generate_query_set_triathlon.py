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

#Imports

@dataclass
class LawSpec:
    templates: List[str]
    slots: Dict[str, List[str]]


# Single Placholder Collections
LAWS: List[str] =[
    "CompetitionRules",
    "AntiDopingRules",
    "ParaTriathlonRules",
    "TransgenderRules",
    "ITUDisciplinaryRules",
]

RACES = [
    "World Triathlon Championship Series",
    "World Cup",
    "Continental Cup",
    "Age Group Championship",
    "Sprint Triathlon",
    "Olympic Distance Race",
    "Mixed Relay",
]

LOCATIONS = [
    "Hamburg",
    "Yokohama",
    "Abu Dhabi",
    "Pontevedra",
    "Cagliari",
    "Montreal",
    "Valencia",
    "Samarkand",
    "Qatar",
]

ATHLETES = [
    "elite athlete",
    "age-group athlete",
    "junior athlete",
    "U23 athlete",
    "paratriathlete",
]

OFFICIALS = [
    "technical official",
    "head referee",
    "competition jury",
    "race referee",
]

EVIDENCE = [
    "helmet inspection",
    "bike inspection",
    "race photographs",
    "official report",
    "GPS data",
    "video footage",
    "timing records",
]

TIMES = [
    "before the race",
    "during check-in",
    "during transition",
    "during the bike segment",
    "after finishing",
]
# Extra Regular Expressions
_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9]+", re.UNICODE)
_PLACEHOLDER_RE = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)}")

# Sentence Placeholder Collection (does not use the previous single lists)
# For each Rulebook; returns Dict[str, LawSpec]
def base_triathlon_specs():
  
  specs: Dict[str, LawSpec] = {}

  specs["CompetitionRules"] = LawSpec(
        templates=[

            "Drafting rules during {segment}",

            "Helmet requirements in {segment}",

            "Wetsuit rules for water temperature of {temperature}",

            "Transition procedures during {transition_phase}",

            "Bike specifications for {bike_type}",

            "Illegal equipment: {equipment}",

            "Penalty for {violation}",

            "Protest procedure after {incident}",

            "Lapped athletes during {race_type}",

            "Race uniform requirements",

            "Aid station rules",

            "Outside assistance during {segment}",

            "Swim conduct and {swim_issue}",

            "Mount and dismount line violations",

            "Finish line procedures",

            "Mixed relay exchange",

        ],

        slots={

            "segment":[
                "the swim",
                "the bike",
                "the run",
                "transition",
            ],

            "temperature":[
                "15°C",
                "18°C",
                "20°C",
                "22°C",
                "25°C",
            ],

            "transition_phase":[
                "T1",
                "T2",
                "bike check-in",
                "bike check-out",
            ],

            "bike_type":[
                "road bikes",
                "time trial bikes",
                "disc wheels",
                "clip-on aerobars",
            ],

            "equipment":[
                "headphones",
                "glass bottles",
                "communication devices",
                "illegal wetsuits",
                "unapproved helmets",
            ],

            "violation":[
                "drafting",
                "mounting before the line",
                "blocking",
                "littering",
                "outside assistance",
                "helmet strap violation",
            ],

            "incident":[
                "a time penalty",
                "a disqualification",
                "a yellow card",
                "a red card",
            ],

            "race_type":[
                "a sprint race",
                "an Olympic-distance race",
                "a relay",
            ],

            "swim_issue":[
                "false starts",
                "swim caps",
                "course cutting",
                "abandoning the swim",
            ],
        }
    )

  specs["AntiDopingRules"] = LawSpec(

        templates=[

            "Therapeutic Use Exemption for {substance}",

            "Doping control during {competition_stage}",

            "Whereabouts requirements",

            "Sample collection procedure",

            "Consequences of {violation}",

            "Athlete rights during doping control",

            "Responsibilities of athlete support personnel",

            "Prohibited substance: {substance}",

            "Testing pool requirements",

            "Missed test and filing failure",

            "Results management",

            "Athlete Biological Passport",

            "Consequences for athlete support personnel",

            "Provisional suspension",

            "Tampering with doping control",

            "Use of prohibited methods",

            "Return to competition after suspension",

            "Education requirements",

            "Risk of contaminated supplements",

            "Responsibilities during sample collection",

        ],

        slots={

            "competition_stage":[
                "competition",
                "out-of-competition testing",
                "training camp",
            ],

            "violation":[
                "refusing sample collection",
                "tampering",
                "three whereabouts failures",
                "presence of a prohibited substance",
                "evading sample collection",
                "possession of a prohibited substance",
                "trafficking",
                "administration of a prohibited substance",
                "complicity",
            ],

            "substance":[
                "salbutamol",
                "glucocorticoids",
                "beta blockers",
                "stimulants",
                "diuretics",
            ]
        }
    )

  specs["ParaTriathlonRules"] = LawSpec(

        templates=[

            "Classification requirements",

            "Eligibility for {sport_class}",

            "Medical review process",

            "Guide requirements during {segment}",

            "Wheelchair specifications",

            "Handcycle specifications",

            "Prosthetic equipment requirements",

            "Assistance during transition",

            "Penalty for {violation}",

            "Equipment inspection",

            "Competition procedures for {sport_class}",

            "Safety requirements during {segment}",

            "Guide communication rules",

            "Replacement of assistive equipment",

        ],

        slots={

            "sport_class":[
                "PTWC",
                "PTS2",
                "PTS3",
                "PTS4",
                "PTS5",
                "PTVI",
            ],

            "segment":[
                "the swim",
                "transition",
                "the bike",
                "the run",
            ],

            "violation":[
                "receiving unauthorized assistance",
                "incorrect guide usage",
                "equipment non-compliance",
                "classification fraud",
                "outside assistance",
            ],
        }
    )

  specs["TransgenderRules"] = LawSpec(

        templates=[

            "Eligibility criteria for transgender athletes",

            "Participation requirements",

            "Medical documentation requirements",

            "Hormone eligibility requirements",

            "Competition eligibility",

            "Review procedure for eligibility",

            "Confidentiality of athlete information",

            "Appeal procedure for eligibility decisions",

            "Responsibilities of National Federations",

            "Changes in eligibility status",

            "Required documentation",

            "Eligibility review timelines",

        ],

        slots={

            "competition":[
                "elite competition",
                "age-group competition",
                "international competition",
            ],

            "document":[
                "medical certificate",
                "laboratory results",
                "supporting documentation",
                "eligibility declaration",
            ],

            "decision":[
                "eligibility approval",
                "eligibility denial",
                "medical review",
            ],
        }
    )

  specs["ITUDisciplinaryRules"] = LawSpec(

    templates=[

        "Disciplinary procedure",

        "Reporting a disciplinary offence",

        "Appeal procedure",

        "Hearing process",

        "Sanctions for {offence}",

        "Responsibilities of the disciplinary panel",

        "Rights of the accused athlete",

        "Evidence requirements",

        "Filing a complaint",

        "Time limits for appeals",

        "Conflict of interest",

        "Suspension procedures",

        "Interim measures",

        "Notification of disciplinary decisions",

    ],

    slots={

        "offence":[
            "unsporting behaviour",
            "harassment",
            "violence",
            "fraud",
            "bringing the sport into disrepute",
            "breach of federation rules",
        ],

        "sanction":[
            "warning",
            "fine",
            "suspension",
            "disqualification",
            "expulsion",
        ],

        "authority":[
            "Disciplinary Tribunal",
            "Executive Board",
            "Appeal Panel",
            "Competition Jury",
        ],
    }
)

  return specs

# Style Templates 
# Just sentences where you can change the placeholders
# by adding your issues that can occur in the races.
# Extend the previous word Lists for more synonym matching.
STYLES = ["nl_short", "nl_long", "scenario", "procedural", "authority", "keyword", "fragment"]
STYLE_TEMPLATES: Dict[str, List[str]] ={

"nl_short":[

    "What are the rules for {issue}?",

    "Is {issue} allowed?",

    "What penalty applies for {issue}?",

    "What requirements apply to {issue}?",

    "Are there exceptions for {issue}?",

],

"nl_long":[

    "{scenario} Which World Triathlon rules apply and what should I do?",

    "{scenario} What are the applicable rules and possible penalties?",

    "{scenario} What evidence or documentation is required?",

    "{scenario} What is the correct procedure according to the Competition Rules?",

],

"scenario":[

    "Scenario: {scenario} What is the correct ruling?",

    "Case: {scenario} Which rule applies?",

    "{scenario} Please explain the relevant competition rule.",

],

"procedural":[

    "What is the official procedure for {issue}?",

    "How is {issue} handled during competition?",

    "Which steps must an athlete follow for {issue}?",

    "How can an athlete appeal a decision regarding {issue}?",

],

"authority":[

    "Who decides on {issue}: the Head Referee or the Competition Jury?",

    "Which official is responsible for {issue}?",

    "Who has authority to rule on {issue}?",

],

"keyword":[

    "{issue}",

    "{issue} penalty",

    "{issue} rule",

    "{issue} World Triathlon",

],

"fragment":[

    "{issue}",

    "{issue} during race",

    "{issue} procedure",

    "{issue} appeal",

]

}

# Helper Functions
def stable_int(s: str) -> int:
    acc = 0
    for i, ch in enumerate(s, start=1):
        acc = (acc * 131 + ord(ch) * i) & 0xFFFFFFFF
    return acc
def target_counts(total: int, labels: Sequence[str]) -> Dict[str, int]:
    n_labels = len(labels)
    base = total // n_labels
    rem = total - base * n_labels
    labs = sorted(labels)
    out = {lab: base for lab in labs}
    for i in range(rem):
        out[labs[i]] += 1
    return out
def target_counts_law_style(total_by_law: Dict[str, int], styles: Sequence[str], seed: int) -> Dict[Tuple[str, str], int]:
    """Expand per-law target counts into (law, style) counts.

    For each law, counts are distributed near-uniformly over styles.
    The remainder is assigned using a deterministic per-law shuffle (seeded) to avoid systematic bias toward early styles.
    """
    styles_list = list(styles)
    n_styles = len(styles_list)
    out: Dict[Tuple[str, str], int] = {}

    for law in sorted(total_by_law):
        total = total_by_law[law]
        base = total // n_styles
        rem = total - base * n_styles

        # Deterministic per-law shuffle to spread remainder across styles.
        rng = random.Random((seed + stable_int(f"{law}:style_rem")) & 0xFFFFFFFF)
        order = styles_list[:]
        rng.shuffle(order)

        for style in styles_list:
            out[(law, style)] = base

        for i in range(rem):
            out[(law, order[i])] += 1

    return out
def estimate_max_issues(spec: LawSpec) -> int:
    """Upper bound estimate used for choosing a reasonable core-seed count."""
    total = 0
    for tmpl in spec.templates:
        keys = _PLACEHOLDER_RE.findall(tmpl)
        if not keys:
            total += 1
        else:
            prod = 1
            for k in keys:
                prod *= max(1, len(spec.slots.get(k, [])))
            total += prod
    return total
def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

# Function for building a szenario.
def build_scenario(issue, ctx, rng):

    skeletons = [

        (
        f"I am an {ctx['athlete']} competing in a {ctx['race']} in {ctx['location']}. "
        f"{ctx['time']} a situation involving {ctx['issue']} occurred. "
        f"{ctx['evidence']}"
        ),

        (
        f"During a {ctx['race']} in {ctx['location']}, "
        f"I was informed by a technical official about {issue}. "
        f"{ctx['evidence']}"
        ),

        (
        f"While competing as an {ctx['athlete']}, "
        f"I may have violated the rules regarding {issue}. "
        f"{ctx['evidence']}"
        ),

        (
        f"After the race in {ctx['location']}, "
        f"I received a penalty related to {issue}. "
        f"{ctx['evidence']}"
        ),
    ]

    template = rng.choice(skeletons)
    template = re.sub(r"\s+", " ", template).strip()

    return template

def topic_context(topic_id: str, law: str, seed: int) -> Dict[str, str]:
    rng = random.Random((seed + stable_int(f"{topic_id}:{law}:ctx")) & 0xFFFFFFFF)

    return {
        "athlete": rng.choice(ATHLETES),
        "race": rng.choice(RACES),
        "location": rng.choice(LOCATIONS),
        "official": rng.choice(OFFICIALS),
        "evidence": rng.choice(EVIDENCE),
        "time": rng.choice(TIMES),
        }

def generate_queries_for_topic(
    *,
    topic_id: str,
    issue: str,
    law: str,
    seed: int,
    variants_per_style: int,
    law_mention_prob: float,
    keyword_law_mention_prob: float,
    surface_noise_prob: float,
    law_context_prob: float,
    topic_term_prob: float,
    issue_term_prob: float,
    keyword_term_prob: float,
) -> List[Dict[str, str]]:
    # Context is partly law-conditioned to reduce unrealistic boilerplate.
    ctx = topic_context(topic_id, law, seed, law_context_prob)

    base_rng = random.Random((seed + stable_int(f"{topic_id}:{law}:base")) & 0xFFFFFFFF)

    # Optional per-topic lexicon token (no law abbreviation).
    term_pool = LAW_TERMS.get(law, [])
    topic_term = None
    if term_pool and base_rng.random() < topic_term_prob:
        topic_term = base_rng.choice(term_pool)

    scenario = build_scenario(issue, ctx, base_rng, term=topic_term)
    question = base_rng.choice(QUESTION_FORMS)

    # Keyword source intentionally excludes the law token. Term inclusion is optional.
    k_source = f"{issue} {ctx['city']} {ctx['amount_kw']} {ctx['channel']} {ctx['evidence']} {ctx['time']} {ctx['authority']}"
    if topic_term and base_rng.random() < keyword_term_prob:
        k_source = f"{k_source} {topic_term}"
    keywords = extract_keywords(k_source, max_tokens=11)

    def enrich_issue(rng: random.Random) -> str:
        if not term_pool or rng.random() >= issue_term_prob:
            return issue
        t = topic_term if (topic_term and rng.random() < 0.65) else rng.choice(term_pool)
        return rng.choice([f"{issue} ({t})", f"{issue} - {t}", f"{t}: {issue}"])

    out: List[Dict[str, str]] = []
    for style in STYLES:
        for v in range(1, variants_per_style + 1):
            sseed = (seed + stable_int(f"{topic_id}:{law}:{style}:v{v}")) & 0xFFFFFFFF
            rng = random.Random(sseed)

            template = rng.choice(STYLE_TEMPLATES[style])
            text = template.format(
                issue=enrich_issue(rng),
                scenario=scenario,
                question=question,
                keywords=keywords,
                authority=ctx["authority"],
                city=ctx["city"],
                time=ctx["time"],
                amount_kw=ctx["amount_kw"],
                channel=ctx["channel"],
                evidence=ctx["evidence"],
            )
            text = normalize_ws(text)

            # Optional law hint (kept low)
            p = keyword_law_mention_prob if style == "keyword" else law_mention_prob
            if rng.random() < p:
                text = inject_law_hint(text, law, rng)

            text = maybe_apply_surface_noise(text, rng, surface_noise_prob)

            out.append(
                {
                    "query_id": f"{topic_id}_{style}_v{v:02d}",
                    "topic_id": topic_id,
                    "query_text": text,
                    "consensus_law": law,
                    "style": style,
                    "issue": issue,
                }
            )
    return out

def generate_issues_for_law(law: str, spec: LawSpec, *, min_count: int, seed: int) -> List[str]:
    """Deterministically generate >= min_count distinct issue strings, or raise if impossible."""
    rng = random.Random((seed + stable_int(f"{law}:issues")) & 0xFFFFFFFF)

    issues: List[str] = []
    seen: Set[str] = set()

    templates = spec.templates[:]
    rng.shuffle(templates)

    # Bounded sampling per template (keeps runtime predictable)
    per_template_budget = max(60, ceil(min_count / max(1, len(templates))) * 10)

    # Pass-based loop to detect stagnation (prevents infinite loops)
    max_passes = 40
    for _pass in range(max_passes):
        before_pass = len(issues)
        for tmpl in templates:
            keys = _PLACEHOLDER_RE.findall(tmpl)
            if not keys:
                cand = normalize_ws(tmpl)
                if cand not in seen:
                    seen.add(cand)
                    issues.append(cand)
            else:
                slots = [spec.slots[k] for k in keys]
                used_sig: Set[Tuple[int, ...]] = set()
                for _ in range(per_template_budget):
                    sig = tuple(rng.randrange(len(s)) for s in slots)
                    if sig in used_sig:
                        continue
                    used_sig.add(sig)
                    mapping = {k: spec.slots[k][sig[i]] for i, k in enumerate(keys)}
                    cand = normalize_ws(tmpl.format(**mapping))
                    if cand not in seen:
                        seen.add(cand)
                        issues.append(cand)
                    if len(issues) >= min_count:
                        break
            if len(issues) >= min_count:
                break
        if len(issues) >= min_count:
            break
        if len(issues) == before_pass:
            break  # stagnation

    if len(issues) < min_count:
        cap = estimate_max_issues(spec)
        raise RuntimeError(
            f"Unable to generate enough issues for {law}: needed {min_count}, got {len(issues)} (estimated cap ~{cap})."
        )

    rng.shuffle(issues)
    return issues[:]

def expand_spec_with_facets(law: str, base: LawSpec, *, seed: int) -> LawSpec:
    """Automatic expansion: combine representative core issues with common legal facets."""
    base_cap = estimate_max_issues(base)
    core_seed = min(25, max(8, min(base_cap, 25)))  # robust even for small base caps

    # Generate representative cores from the base spec (low count)
    core_issues = generate_issues_for_law(law, base, min_count=min(core_seed, base_cap), seed=seed)

    spec = copy.deepcopy(base)
    spec.slots["core"] = core_issues
    spec.slots["facet"] = FACETS_COMMON

    # Facet expansion templates; yields hundreds of distinct, meaningful issues
    spec.templates.extend(
        [
            "{core}: {facet}",
            "{facet} zu {core}",
            "{core} - {facet}",
            "Frage zu {core}: {facet}",
        ]
    )
    return spec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=19)
    ap.add_argument("--train_n", type=int, default=40000)
    ap.add_argument("--test_n", type=int, default=5000)
    ap.add_argument("--output_dir", type=str, default=".")
    ap.add_argument("--variants_per_style", type=int, default=5)

    # Split policy
    ap.add_argument(
        "--split_mode",
        choices=["iid", "iid_unrestricted", "topic_disjoint"],
        default="iid",
        help=(
            "iid (default): stratified TRAIN/TEST; TEST draws only from topics seen in TRAIN (max transfer). "
            "iid_unrestricted: stratified TRAIN/TEST as a partition of one pool (topics may be unseen in TRAIN). "
            "topic_disjoint: no topic appears in both splits (hardest)."
        ),
    )

    # Leakage control
    ap.add_argument("--law_mention_prob", type=float, default=0.12)
    ap.add_argument("--keyword_law_mention_prob", type=float, default=0.25)

    # Noise control
    ap.add_argument("--surface_noise_prob", type=float, default=0.06)

    # Richness controls (improve topical realism and discriminative signal)
    ap.add_argument(
        "--law_context_prob",
        type=float,
        default=0.65,
        help="Probability of using law-specific context overrides (authority/counterparty) when available.",
    )
    ap.add_argument(
        "--topic_term_prob",
        type=float,
        default=0.30,
        help="Probability of selecting a per-topic law-lexicon term (no law abbreviations).",
    )
    ap.add_argument(
        "--issue_term_prob",
        type=float,
        default=0.35,
        help="Per-query probability of enriching the issue with a law-lexicon term.",
    )
    ap.add_argument(
        "--keyword_term_prob",
        type=float,
        default=0.35,
        help="Probability of including the per-topic term into keyword-style queries.",
    )

    # Candidate oversupply safety factor (per law, per split or combined depending on split_mode)
    ap.add_argument("--candidate_oversupply", type=float, default=2.0)

    args = ap.parse_args()
    seed = args.seed
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Sanity: ensure no duplicate labels
    if len(set(LAWS)) != len(LAWS):
        raise RuntimeError("LAWS contains duplicates; fix the label universe.")
    if len(LAWS) < 2:
        raise RuntimeError("LAWS is unexpectedly small.")

    train_target_law = target_counts(args.train_n, LAWS)
    test_target_law = target_counts(args.test_n, LAWS)

    # Also match style marginals (near-uniform within each law).
    train_target = target_counts_law_style(train_target_law, STYLES, seed + 777)
    test_target = target_counts_law_style(test_target_law, STYLES, seed + 777)

    queries_per_topic = len(STYLES) * args.variants_per_style

    base_specs = base_triathlon_specs()
    topics_by_law: Dict[str, List[Tuple[str, str]]] = {}

    # --- Topic allocation ---
    extra_topics_per_law = 4  # slack for allocation randomness

    if args.split_mode == "topic_disjoint":
        # Old behavior: allocate disjoint topic sets for TRAIN and TEST.
        train_topics_per_law: Dict[str, int] = {}
        test_topics_per_law: Dict[str, int] = {}
        for law in sorted(LAWS):
            train_topics_per_law[law] = max(
                6, ceil((train_target_law[law] * args.candidate_oversupply) / max(1, queries_per_topic))
            )
            test_topics_per_law[law] = max(
                3, ceil((test_target_law[law] * args.candidate_oversupply) / max(1, queries_per_topic))
            )

        for law in sorted(LAWS):
            if law not in base_specs:
                raise RuntimeError(f"Missing base spec for {law}")

            spec = expand_spec_with_facets(law, base_specs[law], seed=seed)
            need_topics = train_topics_per_law[law] + test_topics_per_law[law] + extra_topics_per_law
            issues = generate_issues_for_law(law, spec, min_count=need_topics, seed=seed)
            topics_by_law[law] = [(f"{law}_T{i:03d}", issues[i - 1]) for i in range(1, need_topics + 1)]

        rng = random.Random(seed)
        train_topics: List[Tuple[str, str, str]] = []  # topic_id, issue, law
        test_topics: List[Tuple[str, str, str]] = []
        for law in sorted(LAWS):
            topics = topics_by_law[law][:]
            rng.shuffle(topics)
            tr = topics[: train_topics_per_law[law]]
            te = topics[
                train_topics_per_law[law] : train_topics_per_law[law] + test_topics_per_law[law]
            ]
            train_topics.extend([(tid, issue, law) for tid, issue in tr])
            test_topics.extend([(tid, issue, law) for tid, issue in te])

        def build_pool(topics: List[Tuple[str, str, str]], split_seed: int) -> List[Dict[str, str]]:
            pool: List[Dict[str, str]] = []
            for tid, issue, law in topics:
                pool.extend(
                    generate_queries_for_topic(
                        topic_id=tid,
                        issue=issue,
                        law=law,
                        seed=split_seed,
                        variants_per_style=args.variants_per_style,
                        law_mention_prob=args.law_mention_prob,
                        keyword_law_mention_prob=args.keyword_law_mention_prob,
                        surface_noise_prob=args.surface_noise_prob,
                        law_context_prob=args.law_context_prob,
                        topic_term_prob=args.topic_term_prob,
                        issue_term_prob=args.issue_term_prob,
                        keyword_term_prob=args.keyword_term_prob,
                    )
                )
            return pool

        train_pool = build_pool(train_topics, seed + 101)
        test_pool = build_pool(test_topics, seed + 202)

        train_rows = sample_stratified_grid(train_pool, train_target, seed + 303, forbid_texts=set())
        forbid = {r["query_text"] for r in train_rows}
        test_rows = sample_stratified_grid(test_pool, test_target, seed + 404, forbid_texts=forbid)

        split_meta = {
            "train_topics_per_law": train_topics_per_law,
            "test_topics_per_law": test_topics_per_law,
            "extra_topics_per_law": extra_topics_per_law,
        }

    else:
        # New default: single shared topic pool; TRAIN/TEST are stratified partitions of that pool.
        topics_per_law: Dict[str, int] = {}
        for law in sorted(LAWS):
            total_need = train_target_law[law] + test_target_law[law]
            topics_per_law[law] = max(
                8, ceil((total_need * args.candidate_oversupply) / max(1, queries_per_topic))
            )

        for law in sorted(LAWS):
            if law not in base_specs:
                raise RuntimeError(f"Missing base spec for {law}")

            spec = expand_spec_with_facets(law, base_specs[law], seed=seed)
            need_topics = topics_per_law[law] + extra_topics_per_law
            issues = generate_issues_for_law(law, spec, min_count=need_topics, seed=seed)
            topics_by_law[law] = [(f"{law}_T{i:03d}", issues[i - 1]) for i in range(1, need_topics + 1)]

        all_topics: List[Tuple[str, str, str]] = []
        for law in sorted(LAWS):
            for tid, issue in topics_by_law[law]:
                all_topics.append((tid, issue, law))

        def build_pool(topics: List[Tuple[str, str, str]], split_seed: int) -> List[Dict[str, str]]:
            pool: List[Dict[str, str]] = []
            for tid, issue, law in topics:
                pool.extend(
                    generate_queries_for_topic(
                        topic_id=tid,
                        issue=issue,
                        law=law,
                        seed=split_seed,
                        variants_per_style=args.variants_per_style,
                        law_mention_prob=args.law_mention_prob,
                        keyword_law_mention_prob=args.keyword_law_mention_prob,
                        surface_noise_prob=args.surface_noise_prob,
                        law_context_prob=args.law_context_prob,
                        topic_term_prob=args.topic_term_prob,
                        issue_term_prob=args.issue_term_prob,
                        keyword_term_prob=args.keyword_term_prob,
                    )
                )
            return pool

        # One pool only -> no query_id collisions even when topics appear in both splits.
        pool = build_pool(all_topics, seed + 111)

        if args.split_mode == "iid_unrestricted":
            train_rows, test_rows = split_train_test_stratified_grid(pool, train_target, test_target, seed + 303)
            split_meta = {
                "topics_per_law": topics_per_law,
                "extra_topics_per_law": extra_topics_per_law,
                "test_topics_subset_of_train": False,
            }
        else:
            # Default: maximize train→test performance by restricting TEST to topics observed in TRAIN.
            train_rows, test_rows = split_train_test_stratified_grid_test_topics_in_train(
                pool, train_target, test_target, seed + 303
            )
            split_meta = {
                "topics_per_law": topics_per_law,
                "extra_topics_per_law": extra_topics_per_law,
                "test_topics_subset_of_train": True,
            }

    # --- Write outputs ---
    train_path = outdir / "train.jsonl"
    test_path = outdir / "test.jsonl"
    meta_path = outdir / "meta.json"

    write_jsonl(train_path, train_rows)
    write_jsonl(test_path, test_rows)

    def _count(rows: List[Dict[str, str]], fields: Tuple[str, ...]) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for r in rows:
            k = "||".join(r[f] for f in fields)
            out[k] = out.get(k, 0) + 1
        return out

    meta = {
        "seed": seed,
        "split_mode": args.split_mode,
        "train_n": args.train_n,
        "test_n": args.test_n,
        "laws": sorted(LAWS),
        "n_laws": len(LAWS),
        "styles": STYLES,
        "variants_per_style": args.variants_per_style,
        "queries_per_topic": queries_per_topic,
        "law_mention_prob": args.law_mention_prob,
        "keyword_law_mention_prob": args.keyword_law_mention_prob,
        "surface_noise_prob": args.surface_noise_prob,
        "law_context_prob": args.law_context_prob,
        "topic_term_prob": args.topic_term_prob,
        "issue_term_prob": args.issue_term_prob,
        "keyword_term_prob": args.keyword_term_prob,
        "candidate_oversupply": args.candidate_oversupply,
        "train_target_counts_by_law": train_target_law,
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