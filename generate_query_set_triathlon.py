#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_query_set_triathlon.py

Synthetic query generator for Triathlon rule retrieval/classification.

Design goals
------------
- Exact train/test sizes.
- I.I.D. train/test by default: TRAIN and TEST share the same latent topic mixture (recommended).
- Near-uniform stratification across the five Triathlon rule documents.
- High semantic diversity and realistic surface forms.
- Minimal label leakage: document abbreviations are *not* included by default; optional low-probability hints.
- Always uses document-specific context overrides to avoid unrealistic role/authority combinations.

Outputs (default filenames)
---------------------------
- train.jsonl
- test.jsonl
- meta.json

Each JSONL row includes:
  query_id, topic_id, query_text, consensus_law, style, issue
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

# -------------------------
# Label universe (5 Triathlon documents)
# -------------------------
LAWS: List[str] = [
    "WT_Competition_Rules",
    "WT_Para_Classification_Rules",
    "WT_Anti_Doping_Rules",
    "ITU_Disciplinary_Rules",
    "TRI_Gender_Regulations",
]

# -------------------------
# Global enrichment pools (Triathlon-specific, English) – used only as fallback
# -------------------------
CITIES_TRI = [
    "Hamburg", "Kona", "Nizza", "Rotterdam", "Edmonton", "Yokohama",
    "Abu Dhabi", "Leeds", "Montreal", "Lausanne", "Pontevedra", "Torremolinos",
    "Cozumel", "Tongyeong", "Chengdu", "Mooloolaba", "Karlovy Vary", "Samarkand",
]

CHANNELS_TRI = [
    "email", "online form", "in person at the race office", "phone",
    "World Triathlon portal", "protest form", "official letter", "athletes' briefing",
]

EVIDENCE_TRI = [
    "start list", "result list", "referee report", "medical certificate",
    "photo finish", "video recording", "timing chip data", "witness statement",
    "GPS data", "course map", "water temperature log", "WBGT measurement log",
    "doping control form", "TUE certificate", "medical diagnostics form",
    "classification evaluation card", "eligibility certification",
]

TIME_PHRASES_TRI = [
    "at the last World Cup", "during the bike segment", "yesterday's race",
    "two weeks ago at the Continental Championships", "at the Olympic Games",
    "during the swim leg", "after the finish", "before the start",
    "at the athletes' briefing", "during the classification evaluation",
    "within 30 minutes of the finish", "last month", "in the previous season",
    "during the winter triathlon", "at the World Championship Finals",
]

AMOUNTS_TRI = [
    100, 200, 500, 1000, 2500, 5000, 3000, 150, 300, 750, 1200, 10000,
]

ACTORS_TRI = [
    "athlete", "coach", "race official", "technical delegate",
    "head referee", "guide", "personal handler", "national federation",
    "team manager", "classifier", "chief classifier", "medical delegate",
    "inclusion officer", "expert panel member", "arbitration tribunal member",
]

COUNTERPARTIES_TRI = [
    "World Triathlon", "race organiser", "jury", "anti-doping panel",
    "national federation", "continental confederation", "CAS", "WADA",
    "ITU Arbitration Tribunal", "Expert Panel", "Classification Panel",
    "Protest Panel", "TRI Tribunal", "Inclusion Officer",
]

AUTHORITIES_TRI = [
    "World Triathlon Technical Committee", "Competition Jury", "CAS",
    "World Triathlon Tribunal", "ITU Arbitration Tribunal", "WADA",
    "IPC Board of Appeal of Classification", "Expert Panel",
    "Head of Classification", "Chief Classifier", "Protest Panel",
    "Classification Advisory Group",
]

FACETS_COMMON = [
    "prerequisites",
    "deadlines",
    "exceptions",
    "penalties",
    "appeal process",
    "required documents",
    "responsible personnel",
    "equipment specifications",
    "distance/time limits",
    "temperature thresholds",
    "notification requirements",
    "confidentiality obligations",
    "fee amounts",
    "monitoring procedures",
    "jurisdiction",
]

# Law-lexicon (no document abbreviations)
LAW_TERMS: Dict[str, List[str]] = {
    "WT_Competition_Rules": [
        "drafting zone", "draft-illegal", "draft-legal", "penalty box",
        "wetsuit mandatory", "wetsuit forbidden", "mount line", "dismount line",
        "transition area", "blue card", "yellow card", "red card",
        "time penalty", "disqualification", "competition jury", "head referee",
        "technical delegate", "pre-race briefing", "body marking", "bike check",
        "wheel station", "outside assistance", "blocking", "false start",
        "swim current", "water quality", "WBGT index", "relay exchange zone",
        "mass start", "interval start", "rolling start", "swimskin",
        "tandem bicycle", "racing wheelchair", "handcycle", "guide",
        "personal handler", "blackout goggles", "PTWC", "PTVI", "PTS",
        "qualifying round", "athletes' briefing", "appeal level 2",
        "protest form", "timing chip", "cut-off time", "split times",
        "invalid results markers",
    ],
    "WT_Para_Classification_Rules": [
        "Eligible Impairment", "Minimum Impairment Criteria", "Athlete Evaluation",
        "Sport Class Status", "Classification Panel", "Observation in Competition",
        "Protest Panel", "Intentional Misrepresentation", "Medical Diagnostics Form",
        "Provisional Classification Status", "Fixed Review Date",
        "Classification Not Complete", "Classification Master List",
        "IPC Athlete Classification Code", "Underlying Health Condition",
        "Eligibility Assessment Panel", "Chief Classifier", "Head of Classification",
        "Sport Class Not Eligible", "Physical Assessment", "Technical Assessment",
        "Medical Review Request", "IPC Board of Appeal of Classification",
        "Remote Assessment", "Classifier Code of Conduct",
    ],
    "WT_Anti_Doping_Rules": [
        "Adverse Analytical Finding", "Prohibited List",
        "Therapeutic Use Exemption", "Registered Testing Pool",
        "Whereabouts Failure", "Tampering", "Trafficking",
        "Provisional Suspension", "Ineligibility", "Substantial Assistance",
        "Specified Substance", "Substance of Abuse", "Contaminated Product",
        "Results Management", "Athlete Biological Passport", "B Sample",
        "Split Sample", "ADAMS", "CAS ADD", "No Fault or Negligence",
        "No Significant Fault or Negligence", "Aggravating Circumstances",
        "Complicity", "Prohibited Association", "Case Resolution Agreement",
        "Public Disclosure", "Standard of Comfortable Satisfaction",
    ],
    "ITU_Disciplinary_Rules": [
        "Arbitration Tribunal", "ordinary proceeding", "appeal proceeding",
        "factum", "claimant", "appellant", "respondent", "provisional measures",
        "ad hoc panel", "recusal", "statute of limitations", "suspensive effect",
        "monetary penalty", "roll down in ranking", "revocation of title",
        "expulsion from official functions", "procedural violation",
        "costs award", "Panel President", "casting vote", "written investigation",
        "hearing by telecommunication", "registered mail", "CAS appeal",
        "Olympic Games ad hoc proceeding", "Paralympic Games ad hoc proceeding",
    ],
    "TRI_Gender_Regulations": [
        "Transgender Female Eligibility Conditions", "Expert Panel",
        "Inclusion Officer", "Academic Research Program", "separate results",
        "cis women results", "testosterone monitoring",
        "gender-affirming hormone therapy", "GnRH agonists",
        "serum testosterone concentration", "AFAB", "AMAB",
        "Gender Identity", "Gender Incongruence", "TRI Tribunal",
        "Puberty blockers", "Oestrogen supplementation", "Anti-androgen",
        "Open Category", "Year 4 pathway", "written declaration",
        "comprehensive medical history", "mutual recognition",
        "confidentiality", "provisional suspension",
    ],
}

# Law-specific context overrides – ALWAYS applied (see --law_context_prob default)
LAW_CONTEXT_OVERRIDES: Dict[str, Dict[str, List[str]]] = {
    "WT_Competition_Rules": {
        "authorities": [
            "World Triathlon Technical Committee", "Competition Jury",
            "World Triathlon Tribunal", "World Triathlon Executive Board",
        ],
        "actors": [
            "athlete", "technical delegate", "head referee", "guide",
            "personal handler", "coach", "team manager",
        ],
        "counterparties": [
            "World Triathlon", "race organiser", "jury", "national federation",
            "continental confederation",
        ],
    },
    "WT_Anti_Doping_Rules": {
        "authorities": [
            "WADA", "CAS ADD", "World Triathlon TUEC", "Hearing Panel",
        ],
        "actors": [
            "athlete", "athlete support person", "coach",
            "doping control officer", "medical personnel",
        ],
        "counterparties": [
            "WADA", "national anti-doping organization", "CAS",
            "World Triathlon", "laboratory",
        ],
    },
    "ITU_Disciplinary_Rules": {
        "authorities": [
            "ITU Arbitration Tribunal", "CAS", "Panel President",
        ],
        "actors": [
            "claimant", "appellant", "respondent", "witness",
            "legal representative", "arbitration tribunal chair",
        ],
        "counterparties": [
            "ITU Arbitration Tribunal", "national federation",
            "continental confederation", "CAS",
        ],
    },
    "TRI_Gender_Regulations": {
        "authorities": [
            "Expert Panel", "TRI Tribunal", "Inclusion Officer",
            "World Triathlon Executive Board",
        ],
        "actors": [
            "transgender athlete", "inclusion officer",
            "expert panel member", "medical expert",
        ],
        "counterparties": [
            "Expert Panel", "TRI Tribunal", "Inclusion Officer",
            "World Triathlon",
        ],
    },
    "WT_Para_Classification_Rules": {
        "authorities": [
            "Classification Panel", "Chief Classifier", "Head of Classification",
            "IPC Board of Appeal of Classification", "Protest Panel",
        ],
        "actors": [
            "athlete", "classifier", "chief classifier", "guide",
            "national federation",
        ],
        "counterparties": [
            "World Triathlon", "Classification Panel",
            "IPC Board of Appeal of Classification", "national federation",
        ],
    },
}

# -------------------------
# Text utilities (adapted to English)
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
        if not tl or tl in STOPWORDS:
            continue
        if len(tl) > 2:
            toks.append(tl)
    return " ".join(toks[:max_tokens]) if toks else source[:50].lower()

def maybe_apply_surface_noise(text: str, rng: random.Random, p: float) -> str:
    if rng.random() >= p:
        return text

    def typo_once(s: str) -> str:
        toks = s.split()
        cand_idx = [i for i, t in enumerate(toks) if len(t) >= 6 and t.isalpha()]
        if not cand_idx:
            return s
        i = rng.choice(cand_idx)
        w = toks[i]
        j = rng.randrange(1, len(w)-1)
        op = rng.choice(["del", "dup", "swap"])
        if op == "del":
            w2 = w[:j] + w[j+1:]
        elif op == "dup":
            w2 = w[:j] + w[j] + w[j:]
        else:
            w2 = w[:j-1] + w[j] + w[j-1] + w[j+1:]
        toks[i] = w2
        return " ".join(toks)

    variants = [
        text.replace("World Triathlon", "WT"),
        text.replace("competition", "race"),
        text.rstrip("?") if text.endswith("?") else text + "?",
        text.lower() if rng.random() < 0.7 else text,
        typo_once(text) if rng.random() < 0.5 else text,
    ]
    v = rng.choice(variants)
    return normalize_ws(v)

def inject_law_hint(text: str, law: str, rng: random.Random) -> str:
    forms = [
        f" (according to {law.replace('_', ' ')})",
        f" - {law.replace('_', ' ')}",
        f" under {law.replace('_', ' ')}",
    ]
    return text + rng.choice(forms)

# -------------------------
# Document-specific specs
# -------------------------

@dataclass
class LawSpec:
    templates: List[str]
    slots: Dict[str, List[str]]

def base_law_specs() -> Dict[str, LawSpec]:
    specs: Dict[str, LawSpec] = {}

    GENERIC_TOPICS_BY_LAW: Dict[str, List[str]] = {
        "WT_Competition_Rules": [
            "Wetsuit thickness and water temperature limits",
            "Eligibility criteria for Elite, U23, Junior, and Age-Group categories",
            "Drafting rules and penalty zones in draft-illegal events",
            "Penalty serving procedures at transition, bike, and run boxes",
            "Bike frame and equipment specifications for draft-legal competitions",
            "Helmet regulations and mandatory fastening during cycling",
            "Swim start procedures: mass start, interval, and time trial",
            "False start and early start penalties",
            "Outside assistance allowed and prohibited during races",
            "Protest initiation timelines and required fees",
            "Composition and decision-making of the Competition Jury",
            "Water quality standards for sea and inland water",
            "Modifications due to heat: WBGT index and flag system",
            "Swim distance modifications due to cold or high water temperatures",
            "Course deviation exceptions and penalties",
            "Transition area conduct: racking, equipment placement, mount/dismount lines",
            "Uniform rules: torso coverage, zipper length, logo restrictions",
            "Race number assignment criteria across event types",
            "Para triathlon sport classes and classification requirements",
            "Guide and tether rules for visually impaired athletes (PTVI)",
            "Handcycle and racing wheelchair specifications for PTWC athletes",
            "Mixed Relay team composition, order, and exchange zone rules",
            "Age-Group Mixed Relay specific age-based team categories",
            "Winter Triathlon: ski, bike, and run equipment and conduct",
            "Cross Triathlon mountain bike and running regulations",
            "Aquabike finish definition and course regulations",
            "Qualifying round format: heat distribution and numbering",
            "Time trial qualifying round: start intervals and bike requirements",
            "Disqualification vs. suspension vs. expulsion criteria",
            "Communication devices and camera use during competition",
            "Littering rules and rubbish disposal on course",
            "Timing chip use, loss, and replacement during race",
            "Results modification bodies and invalid results markers",
            "Appeal procedures: Level 2 to World Triathlon Tribunal and CAS",
            "Athletes' briefing attendance penalties and exceptions",
        ],
        "WT_Para_Classification_Rules": [
            "Eligible impairments for Para triathlon (physical and visual)",
            "Minimum Impairment Criteria for each sport class",
            "Submission of Medical Diagnostics Form 8 weeks before classification event",
            "Process for determining an Eligible Impairment via Eligibility Assessment Panel",
            "Athlete evaluation steps: physical assessment, technical assessment, observation in competition",
            "Allocation of Sport Class and designation of Sport Class Status after evaluation",
            "Sport Class Status types: New, Confirmed, Review, Fixed Review Date",
            "Classification Not Complete (CNC) grounds and consequences",
            "Athlete responsibilities during evaluation (attendance, medical documentation, cooperation)",
            "Roles of Chief Classifier and Classification Panel at a competition",
            "Classification Advisory Group composition and appointment",
            "Observation in Competition assessment and its effect on Sport Class",
            "Provisional Classification Status for athletes without access to classification",
            "Protest procedures: National Protest by Federation or NPC (60-minute and 5-minute deadlines)",
            "World Triathlon Protest at any time if Sport Class is incorrect",
            "Formation and rules of a Protest Panel (no prior evaluators within 12 months)",
            "No protest allowed against Sport Class Not Eligible or Sport Class Status",
            "Appeals to IPC Board of Appeal of Classification for procedural errors only",
            "Intentional Misrepresentation: definition, consequences (12-48 months suspension)",
            "Medical Review Request process for changes in impairment (6 weeks before next classification)",
            "Confidentiality and data protection for classification data",
            "Classification Master List maintenance and public availability",
            "Classifier Code of Conduct and conflict of interest rules",
            "Trainee Classifier participation and supervision",
            "Second classification for athletes allocated NE-MIC with Review status",
            "Athletes with multiple eligible impairments choosing a Sport Class",
            "Remote assessment to obtain Provisional Classification Status",
            "Failure to attend an Evaluation Session and consequences",
            "Notification of classification outcomes to athletes and National Federations",
            "Ad hoc provisions for Paralympic Games and other competitions",
        ],
        "WT_Anti_Doping_Rules": [
            "Definition of doping and anti-doping rule violations (ADRV)",
            "Presence of a Prohibited Substance in an Athlete's Sample (strict liability)",
            "Use or Attempted Use of Prohibited Substances or Methods",
            "Evading, refusing, or failing to submit to Sample collection",
            "Whereabouts failures: missed tests and filing failures",
            "Tampering or Attempted Tampering with any part of Doping Control",
            "Possession of Prohibited Substances by Athletes or Athlete Support Personnel",
            "Trafficking or Attempted Trafficking in Prohibited Substances or Methods",
            "Administration or Attempted Administration of Prohibited Substances/Methods",
            "Complicity (assisting, encouraging, covering up) in an ADRV",
            "Prohibited Association with sanctioned Athlete Support Personnel",
            "Acts to Discourage or Retaliate Against Reporting (whistleblowing)",
            "Proof of doping: burdens and standards of proof (comfortable satisfaction)",
            "Methods of establishing facts: analytical methods and presumptions",
            "Incorporation of WADA Prohibited List and athlete responsibility",
            "Specified Substances, Specified Methods, and Substances of Abuse",
            "Therapeutic Use Exemptions (TUEs): application and recognition",
            "TUEC composition, application process, and retroactive TUEs",
            "TUE reviews and appeals by WADA and CAS",
            "Testing authority: In-Competition and Out-of-Competition",
            "Event Testing authority and coordination during Event Period",
            "Athlete Whereabouts information: Registered Testing Pool obligations",
            "Retired athletes returning to competition: 6-month notice rule",
            "Sample analysis: WADA-accredited laboratories and standards",
            "Further analysis of Samples, split Samples, and WADA's right to take possession",
            "Results Management responsibility and notification procedures",
            "Provisional Suspensions: mandatory, optional, and voluntary acceptance",
            "Right to a fair hearing and CAS ADD jurisdiction for first-instance hearings",
            "Waiver of hearing and automatic admission of violation",
            "Automatic Disqualification of individual results in In-Competition test",
            "Sanctions for Presence, Use, or Possession: 4-year vs 2-year Ineligibility",
            "Ineligibility for Evading, Refusing, or Failing to Submit (2-4 years)",
            "Ineligibility for Whereabouts Failures (2 years, reduced to 1 year)",
            "Ineligibility for Trafficking or Administration (minimum 4 years to lifetime)",
            "Ineligibility for Complicity (minimum 2 years to lifetime)",
            "Ineligibility for Prohibited Association (2 years, reduced to 1 year)",
            "Ineligibility for Discouraging/Retaliating (minimum 2 years to lifetime)",
            "Aggravating circumstances: increase up to 2 additional years",
            "Elimination of Ineligibility for No Fault or Negligence",
            "Reduction of Ineligibility for No Significant Fault or Negligence",
            "Reduction of Ineligibility for Contaminated Products",
            "Reduction of Ineligibility for Protected Persons or Recreational Athletes",
            "Substantial Assistance: suspension of part of Ineligibility period",
            "Early admission and acceptance of sanction (1-year reduction)",
            "Case Resolution Agreement with WADA and World Triathlon",
            "Multiple violations: second violation and third violation (lifetime)",
            "Consequences for Teams in relay events (Disqualification)",
            "Sanctions against National Federations for multiple ADRVs",
            "Appeals from decisions: who may appeal and timelines (21 days to CAS)",
            "Confidentiality and Public Disclosure of anti-doping rule violations",
            "Statistical reporting and ADAMS data entry requirements",
            "Data privacy compliance in processing personal information",
            "Statute of limitations: 10 years to commence proceedings",
            "Education requirements: mandatory anti-doping course for athletes",
            "Roles and responsibilities of National Federations in anti-doping",
            "Roles and responsibilities of Athletes and Athlete Support Personnel",
            "Retroactive application of new rules and transitional provisions",
        ],
        "ITU_Disciplinary_Rules": [
            "Jurisdiction of the ITU Arbitration Tribunal",
            "Composition and appointment of the Arbitration Tribunal",
            "Who may file an ordinary claim with the Arbitration Tribunal",
            "Content required in a claim report (statement of facts, relief sought)",
            "Deadline for filing an ordinary proceeding (5 days after event)",
            "Statutes of limitation for competition infringements (2 years)",
            "Statutes of limitation for manipulation and other infringements (10 years)",
            "Statutes of limitation for anti-doping rule violations (8 years)",
            "Statutes of limitation for corruption (no limit)",
            "Types of disciplinary sanctions available to the Tribunal",
            "Monetary penalty limit ($5,000 USD)",
            "Suspension from competition and maximum duration (48 months)",
            "Combining multiple sanctions and ordering restitution of prizes",
            "Recusal of Panel members for conflict of interest",
            "Confidentiality obligations of Panel members and publication of decisions",
            "Right to be heard and formats (telecommunication, written, in-person)",
            "Admissible evidence in disciplinary proceedings",
            "Representation of parties and requirements for power of attorney",
            "Witnesses and experts: who can testify and how",
            "Conduct of the hearing: examination of parties, witnesses, and experts",
            "Written investigation without a hearing and timelines for submissions",
            "Decision-making by majority vote and tie-breaking by Chair",
            "Deadline to render a decision (3 months, expedited for championships)",
            "Notification of decisions (registered mail, email)",
            "Costs of proceedings ($500 application fee, cost awards)",
            "Procedural violations and fines up to $5,000 USD",
            "How to file an appeal against a competition decision (30 days)",
            "Suspensive effect of an appeal and exceptions",
            "Content requirements for an Appellant's factum",
            "Preliminary examination of appeal compliance and admissibility",
            "Respondent's factum deadline and content",
            "Withdrawal of appeal and cost consequences",
            "Provisional measures in urgent cases: procedure and duration",
            "Ad hoc panel for Olympic and Paralympic Games: 4-hour filing deadline",
            "Ad hoc panel procedure and 24-hour decision timeline",
            "Appeal to CAS from Arbitration Tribunal decisions (21 days)",
            "Appeal to CAS for provisional measures (3 days)",
        ],
        "TRI_Gender_Regulations": [
            "Eligibility conditions for Transgender Male athletes (unrestricted after declaration)",
            "Eligibility pathway for Transgender Female athletes: the 4-year process",
            "Testosterone concentration requirement below 2.5 nmol/L for 3 years",
            "Mandatory participation in the TRI Academic Research Program",
            "Separate results listing in Year 4 elite competition (overall and cis women only)",
            "Prize money allocation rules for Transgender Female athletes in Year 4",
            "TRI Ranking points based on cis women results only",
            "No requirement for legal gender recognition or surgical anatomical changes",
            "No forced medical assessment or treatment",
            "Written declaration of gender identity and Appendix 4 form submission",
            "Six weeks advance notice before first relevant competition",
            "Expert Panel composition, assessment process, and binding decisions",
            "Medical history and evidence required for Expert Panel assessment",
            "Confidentiality of athlete information and data protection",
            "Monitoring of testosterone levels by Expert Panel (random and targeted)",
            "Investigation of potential non-compliance and provisional suspension",
            "Referral to TRI Tribunal and possible sanctions for testosterone violation",
            "Appeal process to TRI Tribunal with medical advisor assistance",
            "All costs of medical assessments and monitoring borne by the athlete",
            "Mutual recognition of other International Federation eligibility decisions",
            "Transgender Male use of Therapeutic Use Exemption for testosterone",
            "Impact of anti-doping rules on hormone therapy (TUEs)",
            "Withdrawal of consent and its effect on eligibility",
            "Para Triathlon specific pathway: Years 1-3 in elite male category",
            "Year 1 requirements: own testosterone monitoring and 2 Age-Group Open races",
            "Year 2-3 requirements: TRI testosterone monitoring and 3 Age-Group Open races",
            "Year 4 requirements: compete in Elite category with 3 TRI races and continued monitoring",
            "Prohibition of stigmatisation, bad faith reporting, and discrimination",
            "Annual review of the Regulations by the TRI Executive Board",
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
        if not keys:
            total += 1
        else:
            prod = 1
            for k in keys:
                prod *= max(1, len(spec.slots.get(k, [])))
            total += prod
    return total

def generate_issues_for_law(law: str, spec: LawSpec, *, min_count: int, seed: int) -> List[str]:
    rng = random.Random((seed + stable_int(f"{law}:issues")) & 0xFFFFFFFF)
    issues: List[str] = []
    seen: Set[str] = set()
    templates = spec.templates[:]
    rng.shuffle(templates)
    per_template_budget = max(60, ceil(min_count / max(1, len(templates))) * 10)

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
            break

    if len(issues) < min_count:
        cap = estimate_max_issues(spec)
        raise RuntimeError(
            f"Unable to generate enough issues for {law}: needed {min_count}, got {len(issues)} (estimated cap ~{cap})."
        )
    rng.shuffle(issues)
    return issues[:]

def expand_spec_with_facets(law: str, base: LawSpec, *, seed: int) -> LawSpec:
    base_cap = estimate_max_issues(base)
    core_seed = min(25, max(8, min(base_cap, 25)))
    core_issues = generate_issues_for_law(law, base, min_count=min(core_seed, base_cap), seed=seed)
    spec = copy.deepcopy(base)
    spec.slots["core"] = core_issues
    spec.slots["facet"] = FACETS_COMMON
    spec.templates.extend([
        "{core}: {facet}",
        "{facet} regarding {core}",
        "{core} - {facet}",
        "Question about {core}: {facet}",
    ])
    return spec

# -------------------------
# Context and query generation
# -------------------------

def topic_context(topic_id: str, law: str, seed: int, law_context_prob: float) -> Dict[str, str]:
    rng = random.Random((seed + stable_int(f"{topic_id}:{law}:ctx")) & 0xFFFFFFFF)
    actor_pool = ACTORS_TRI
    counterparty_pool = COUNTERPARTIES_TRI
    authority_pool = AUTHORITIES_TRI
    ov = LAW_CONTEXT_OVERRIDES.get(law, {})
    # Always use overrides when available (law_context_prob = 1.0)
    if ov and rng.random() < law_context_prob:
        actor_pool = ov.get("actors", actor_pool)
        counterparty_pool = ov.get("counterparties", counterparty_pool)
        authority_pool = ov.get("authorities", authority_pool)
    actor = rng.choice(actor_pool)
    counterparty = rng.choice(counterparty_pool)
    city = rng.choice(CITIES_TRI)
    timep = rng.choice(TIME_PHRASES_TRI)
    amount = rng.choice(AMOUNTS_TRI)
    channel = rng.choice(CHANNELS_TRI)
    evidence = rng.choice(EVIDENCE_TRI)
    authority = rng.choice(authority_pool)
    return {
        "actor": actor,
        "counterparty": counterparty,
        "city": city,
        "time": timep,
        "amount": f"{amount} USD",
        "amount_kw": f"{amount}usd",
        "channel": channel,
        "evidence": evidence,
        "authority": authority,
    }

def build_scenario(issue: str, ctx: Dict[str, str], rng: random.Random, term: str | None = None) -> str:
    amount_part = rng.choice([f"The matter involves {ctx['amount']}.", f"Amount: {ctx['amount']}.", ""])
    contact_part = rng.choice([f"Contact via {ctx['channel']}.", f"Communication through {ctx['channel']}.", ""])
    evidence_part = rng.choice([
        f"Evidence: {ctx['evidence']}.",
        f"Documents: {ctx['evidence']}.",
        f"Supported by {ctx['evidence']}.",
        "",
    ])
    authority_part = rng.choice([
        f"A decision/notice from {ctx['authority']} is involved.",
        f"Jurisdiction unclear ({ctx['authority']} or CAS?).",
        "",
    ])
    term_part = ""
    if term and rng.random() < 0.55:
        term_part = rng.choice([f"Keyword: {term}.", f"Topic: {term}.", f"({term})"])
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
        "{issue} – what are the rules?",
        "What are my rights/obligations regarding {issue}?",
        "What can I do about {issue}?",
        "{issue}: what is the deadline?",
        "{issue}: what are the prerequisites?",
        "{issue} – do I need to submit an application/evidence?",
        "{issue}: which body is responsible?",
        "Are there any exceptions for {issue}?",
        "What are the costs/risks for {issue}?",
        "What sanctions apply for {issue}?",
    ],
    "nl_long": [
        "{scenario} What rules apply and what steps should I take?",
        "{scenario} What claims/consequences are possible and what deadlines apply?",
        "{scenario} What prerequisites are relevant, what evidence do I need, and where do I file?",
        "{scenario} How do I proceed practically (deadline, jurisdiction, evidence, costs)?",
    ],
    "scenario": [
        "Facts: {scenario} Question: {question}",
        "Case: {scenario} {question}",
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
        "For {issue}: Do I go to {authority} or to CAS?",
        "{issue}: Jurisdiction {authority} vs court – and what deadline?",
        "{issue}: How do I submit to {authority} (form/deadline)?",
    ],
    "keyword": [
        "{keywords}",
        "{keywords} deadline jurisdiction",
        "{keywords} procedure appeal",
        "{keywords} evidence costs",
        "{keywords} decision deadline",
    ],
    "fragment": [
        "{issue} {city}",
        "{issue} {time}",
        "{issue} {authority}",
        "{issue} {amount_kw}",
        "{issue} {channel} {evidence}",
        "{issue} deadline",
        "{issue} jurisdiction",
        "{issue} appeal",
    ],
}

QUESTION_FORMS = [
    "What regulations are applicable?",
    "What rights and obligations exist?",
    "What claims can I assert?",
    "What consequences apply in case of a violation?",
    "What deadlines and procedures must be observed?",
]

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
    ctx = topic_context(topic_id, law, seed, law_context_prob)
    base_rng = random.Random((seed + stable_int(f"{topic_id}:{law}:base")) & 0xFFFFFFFF)
    term_pool = LAW_TERMS.get(law, [])
    topic_term = None
    if term_pool and base_rng.random() < topic_term_prob:
        topic_term = base_rng.choice(term_pool)
    scenario = build_scenario(issue, ctx, base_rng, term=topic_term)
    question = base_rng.choice(QUESTION_FORMS)
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
            p = keyword_law_mention_prob if style == "keyword" else law_mention_prob
            if rng.random() < p:
                text = inject_law_hint(text, law, rng)
            text = maybe_apply_surface_noise(text, rng, surface_noise_prob)
            out.append({
                "query_id": f"{topic_id}_{style}_v{v:02d}",
                "topic_id": topic_id,
                "query_text": text,
                "consensus_law": law,
                "style": style,
                "issue": issue,
            })
    return out

# -------------------------
# Allocation and sampling
# -------------------------

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
    styles_list = list(styles)
    n_styles = len(styles_list)
    out: Dict[Tuple[str, str], int] = {}
    for law in sorted(total_by_law):
        total = total_by_law[law]
        base = total // n_styles
        rem = total - base * n_styles
        rng = random.Random((seed + stable_int(f"{law}:style_rem")) & 0xFFFFFFFF)
        order = styles_list[:]
        rng.shuffle(order)
        for style in styles_list:
            out[(law, style)] = base
        for i in range(rem):
            out[(law, order[i])] += 1
    return out

def sample_stratified_grid(
    pool: List[Dict[str, str]],
    target: Dict[Tuple[str, str], int],
    seed: int,
    forbid_texts: Set[str],
) -> List[Dict[str, str]]:
    rng = random.Random(seed)
    keys = sorted(target)
    by_key: Dict[Tuple[str, str], List[Dict[str, str]]] = {k: [] for k in keys}
    for r in pool:
        k = (r["consensus_law"], r["style"])
        if k in by_key:
            by_key[k].append(r)
    for k in keys:
        rng.shuffle(by_key[k])
    selected: List[Dict[str, str]] = []
    used_texts: Set[str] = set(forbid_texts)
    for k in keys:
        need = target[k]
        picks: List[Dict[str, str]] = []
        for r in by_key[k]:
            if len(picks) >= need:
                break
            t = r["query_text"]
            if t in used_texts:
                continue
            used_texts.add(t)
            picks.append(r)
        if len(picks) != need:
            law, style = k
            raise RuntimeError(
                f"Not enough unique candidates for (law={law}, style={style}): need={need}, got={len(picks)}."
            )
        selected.extend(picks)
    rng.shuffle(selected)
    return selected

def split_train_test_stratified_grid_test_topics_in_train(
    pool: List[Dict[str, str]],
    train_target: Dict[Tuple[str, str], int],
    test_target: Dict[Tuple[str, str], int],
    seed: int,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    train_rows = sample_stratified_grid(pool, train_target, seed, forbid_texts=set())
    train_topics_by_law: Dict[str, Set[str]] = {}
    for r in train_rows:
        law = r["consensus_law"]
        train_topics_by_law.setdefault(law, set()).add(r["topic_id"])
    pool_for_test = [
        r for r in pool
        if r["topic_id"] in train_topics_by_law.get(r["consensus_law"], set())
    ]
    forbid = {r["query_text"] for r in train_rows}
    try:
        test_rows = sample_stratified_grid(pool_for_test, test_target, seed + 101, forbid_texts=forbid)
    except RuntimeError as e:
        raise RuntimeError(
            "Not enough candidates for TEST after restricting to topics seen in TRAIN. "
            "Increase --variants_per_style and/or --candidate_oversupply, or switch to --split_mode iid_unrestricted."
        ) from e
    rng = random.Random(seed + 999)
    rng.shuffle(train_rows)
    rng.shuffle(test_rows)
    return train_rows, test_rows

def write_jsonl(path: Path, rows: List[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

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
    ap.add_argument("--law_mention_prob", type=float, default=0.12)
    ap.add_argument("--keyword_law_mention_prob", type=float, default=0.25)
    ap.add_argument("--surface_noise_prob", type=float, default=0.06)
    # ** NEW DEFAULT: 1.0 – always use document-specific context overrides **
    ap.add_argument("--law_context_prob", type=float, default=1.0)
    ap.add_argument("--topic_term_prob", type=float, default=0.30)
    ap.add_argument("--issue_term_prob", type=float, default=0.35)
    ap.add_argument("--keyword_term_prob", type=float, default=0.35)
    ap.add_argument("--candidate_oversupply", type=float, default=2.0)

    args = ap.parse_args()
    seed = args.seed
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    if len(set(LAWS)) != len(LAWS):
        raise RuntimeError("LAWS contains duplicates; fix the label universe.")
    if len(LAWS) < 2:
        raise RuntimeError("LAWS is unexpectedly small.")

    train_target_law = target_counts(args.train_n, LAWS)
    test_target_law = target_counts(args.test_n, LAWS)

    train_target = target_counts_law_style(train_target_law, STYLES, seed + 777)
    test_target = target_counts_law_style(test_target_law, STYLES, seed + 777)

    queries_per_topic = len(STYLES) * args.variants_per_style

    base_specs = base_law_specs()
    topics_by_law: Dict[str, List[Tuple[str, str]]] = {}
    extra_topics_per_law = 8

    if args.split_mode == "topic_disjoint":
        train_topics_per_law: Dict[str, int] = {}
        test_topics_per_law: Dict[str, int] = {}
        for law in sorted(LAWS):
            train_topics_per_law[law] = max(6, ceil((train_target_law[law] * args.candidate_oversupply) / max(1, queries_per_topic)))
            test_topics_per_law[law] = max(3, ceil((test_target_law[law] * args.candidate_oversupply) / max(1, queries_per_topic)))
        for law in sorted(LAWS):
            if law not in base_specs:
                raise RuntimeError(f"Missing base spec for {law}")
            spec = expand_spec_with_facets(law, base_specs[law], seed=seed)
            need_topics = train_topics_per_law[law] + test_topics_per_law[law] + extra_topics_per_law
            issues = generate_issues_for_law(law, spec, min_count=need_topics, seed=seed)
            topics_by_law[law] = [(f"{law}_T{i:03d}", issues[i - 1]) for i in range(1, need_topics + 1)]
        rng = random.Random(seed)
        train_topics: List[Tuple[str, str, str]] = []
        test_topics: List[Tuple[str, str, str]] = []
        for law in sorted(LAWS):
            topics = topics_by_law[law][:]
            rng.shuffle(topics)
            tr = topics[: train_topics_per_law[law]]
            te = topics[train_topics_per_law[law] : train_topics_per_law[law] + test_topics_per_law[law]]
            train_topics.extend([(tid, issue, law) for tid, issue in tr])
            test_topics.extend([(tid, issue, law) for tid, issue in te])
        def build_pool(topics: List[Tuple[str, str, str]], split_seed: int) -> List[Dict[str, str]]:
            pool: List[Dict[str, str]] = []
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
                    keyword_term_prob=args.keyword_term_prob,
                ))
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
        topics_per_law: Dict[str, int] = {}
        for law in sorted(LAWS):
            total_need = train_target_law[law] + test_target_law[law]
            topics_per_law[law] = max(8, ceil((total_need * args.candidate_oversupply) / max(1, queries_per_topic)))
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
                pool.extend(generate_queries_for_topic(
                    topic_id=tid, issue=issue, law=law, seed=split_seed,
                    variants_per_style=args.variants_per_style,
                    law_mention_prob=args.law_mention_prob,
                    keyword_law_mention_prob=args.keyword_law_mention_prob,
                    surface_noise_prob=args.surface_noise_prob,
                    law_context_prob=args.law_context_prob,
                    topic_term_prob=args.topic_term_prob,
                    issue_term_prob=args.issue_term_prob,
                    keyword_term_prob=args.keyword_term_prob,
                ))
            return pool
        pool = build_pool(all_topics, seed + 111)
        if args.split_mode == "iid_unrestricted":
            train_rows, test_rows = split_train_test_stratified_grid(pool, train_target, test_target, seed + 303)
            split_meta = {
                "topics_per_law": topics_per_law,
                "extra_topics_per_law": extra_topics_per_law,
                "test_topics_subset_of_train": False,
            }
        else:
            train_rows, test_rows = split_train_test_stratified_grid_test_topics_in_train(pool, train_target, test_target, seed + 303)
            split_meta = {
                "topics_per_law": topics_per_law,
                "extra_topics_per_law": extra_topics_per_law,
                "test_topics_subset_of_train": True,
            }

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