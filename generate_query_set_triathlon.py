#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_query_set_triathlon.py

Synthetic query generator for Triathlon rule retrieval/classification.

Covers 27 Triathlon rule documents with realistic topics, facets, and context.
Query counts are weighted by page count (log‑scale) to reflect document importance.

KEY FEATURE: All generated queries are paraphrased using domain‑specific synonym
mappings before being written. This forces retrieval models to rely on semantic
similarity rather than exact lexical matching, giving a realistic advantage to
Mixedbread and KAHM over IDF–SVD.
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

def _compute_query_weights(total_queries: int, min_per_doc: int = 20) -> Dict[str, int]:
    """Distribute queries proportionally to log(page_count+1) with a minimum per document."""
    log_weights = {law: math.log(_PAGE_COUNTS.get(law, 1) + 1) for law in LAWS}
    total_log = sum(log_weights.values())
    reserved = min_per_doc * len(LAWS)
    remaining = max(0, total_queries - reserved)
    out = {}
    for law in LAWS:
        share = int(log_weights[law] / total_log * remaining) if total_log > 0 else 0
        out[law] = min_per_doc + share
    # distribute rounding leftovers
    leftover = total_queries - sum(out.values())
    sorted_laws = sorted(LAWS, key=lambda l: _PAGE_COUNTS.get(l, 1), reverse=True)
    for i in range(leftover):
        out[sorted_laws[i % len(sorted_laws)]] += 1
    return out

# -------------------------
# Global enrichment pools (Triathlon-specific, English)
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
    "manufacturer's certificate", "proof of precautionary enquiry",
]

TIME_PHRASES_TRI = [
    "at the last World Cup", "during the bike segment", "yesterday's race",
    "two weeks ago at the Continental Championships", "at the Olympic Games",
    "during the swim leg", "after the finish", "before the start",
    "at the athletes' briefing", "during the classification evaluation",
    "within 30 minutes of the finish", "last month", "in the previous season",
    "30 days before the event", "on the Tuesday before the race",
    "by Friday before the event", "on the Saturday before the event",
    "48 hours before the briefing",
]

AMOUNTS_TRI = [
    100, 200, 500, 1000, 2500, 5000, 3000, 150, 300, 750, 1200, 10000,
]

ACTORS_TRI = [
    "athlete", "coach", "race official", "technical delegate",
    "head referee", "guide", "personal handler", "national federation",
    "team manager", "classifier", "chief classifier", "medical delegate",
    "inclusion officer", "expert panel member", "arbitration tribunal member",
    "invitation panel member", "host national federation",
]

COUNTERPARTIES_TRI = [
    "World Triathlon", "race organiser", "jury", "anti-doping panel",
    "national federation", "continental confederation", "CAS", "WADA",
    "ITU Arbitration Tribunal", "Expert Panel", "Classification Panel",
    "Protest Panel", "TRI Tribunal", "Inclusion Officer",
    "Invitation Panel", "Medical Delegate",
]

AUTHORITIES_TRI = [
    "World Triathlon Technical Committee", "Competition Jury", "CAS",
    "World Triathlon Tribunal", "ITU Arbitration Tribunal", "WADA",
    "IPC Board of Appeal of Classification", "Expert Panel",
    "Head of Classification", "Chief Classifier", "Protest Panel",
    "Classification Advisory Group", "Invitation Panel",
    "Technical Delegate", "Medical Delegate",
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

# Law-lexicon (trimmed to essential terms)
LAW_TERMS: Dict[str, List[str]] = {
    "WT_Competition_Rules": [
        "drafting zone", "wetsuit mandatory", "penalty box",
        "transition area", "yellow card", "time penalty",
        "disqualification", "head referee", "outside assistance",
        "false start", "WBGT index", "relay exchange zone",
    ],
    "WT_Para_Classification_Rules": [
        "Eligible Impairment", "Athlete Evaluation", "Sport Class Status",
        "Classification Panel", "Medical Diagnostics Form",
        "Intentional Misrepresentation", "Chief Classifier",
        "IPC Board of Appeal of Classification", "Protest Panel",
    ],
    "WT_Anti_Doping_Rules": [
        "Adverse Analytical Finding", "Prohibited List",
        "Therapeutic Use Exemption", "Registered Testing Pool",
        "Whereabouts Failure", "Tampering", "Trafficking",
        "Provisional Suspension", "Ineligibility", "Substantial Assistance",
        "Specified Substance", "CAS ADD",
    ],
    "ITU_Disciplinary_Rules": [
        "Arbitration Tribunal", "ordinary proceeding", "appeal proceeding",
        "factum", "claimant", "appellant", "recusal",
        "statute of limitations", "monetary penalty",
        "procedural violation", "suspensive effect",
    ],
    "TRI_Gender_Regulations": [
        "Transgender Female Eligibility Conditions", "Expert Panel",
        "testosterone monitoring", "separate results",
        "TRI Academic Research Program", "Year 4 pathway",
        "written declaration", "provisional suspension",
    ],
    "TRI_Gender_Eligibility_Guidelines": [
        "serum testosterone concentration", "LC-MS/MS",
        "transgender female eligibility conditions",
        "spironolactone TUE", "GnRH agonists", "orchiectomy",
        "testosterone monitoring frequency",
    ],
    "TRI_Individual_OQ_Ranking_Criteria": [
        "Individual Olympic Qualification Ranking",
        "7.5% decrease per position", "cut-off time (8%)",
        "Quality of Field Factor", "Top 5 bonus",
        "standard distance requirement",
    ],
    "TRI_Mixed_Relay_OQ_Ranking_Criteria": [
        "Mixed Relay Olympic Qualification Ranking",
        "7.5% decrease per position", "cut-off time (10%)",
        "Quality of Field Factor", "Continental Championships limitation (max 2)",
    ],
    "Para_Triathlon_Interval_Start": [
        "Interval Start System", "Factor (Class Factor)",
        "Lead-off Value", "median race performance",
        "expected race time", "performance ratio (Men/Women)",
        "staggered start", "single medal event",
    ],
    "WT_Qualification_Criteria": [
        "Invitation Panel", "T100 Triathlon World Tour",
        "PTO World Rankings", "Contender Ranking",
        "Wait List", "Start List", "T100 Race Agreement",
    ],
    "WT_Qualification_Criteria_Continental": [
        "Continental Championships", "Continental Cup",
        "Development Regional Cup", "World Triathlon World Ranking",
        "Invitation Panel", "host continent quota",
        "Americas substitution rules",
    ],
    "WT_Qualification_Criteria_General_Rules": [
        "Start List", "Waiting List", "National Federation quota",
        "exceeds quota", "Invitation Panel", "joker",
        "substitution window", "withdrawal penalty",
        "event hierarchy", "30-day rule",
    ],
    "WT_Qualification_Criteria_Multisport": [
        "Multisport World Triathlon Ranking", "Appendix T",
        "Medal Event (Paratriathlon)", "maximum quota",
        "start list creation 60 days",
    ],
    "WT_Qualification_Criteria_Championships_Series": [
        "World Triathlon Championship Series (WTCS)",
        "Championship Finals", "continental quotas",
        "roll-down system", "Invitation Panel",
    ],
    "WT_Qualification_Criteria_Mixed_Relay": [
        "Mixed Relay World Ranking", "Invitation Panel",
        "maximum 18 teams", "start list",
    ],
    "WT_Paralympic_Qualification_Ranking_Criteria": [
        "Paralympic Qualification Ranking",
        "7.5% decrease per position", "cut-off time (35%)",
        "best 3 results",
    ],
    "WT_Anti_Doping_Rules_Supplements": [
        "Strict Liability", "nutritional supplements",
        "contaminated supplements", "mislabeling",
        "manufacturer's certificate",
    ],
    "WT_Anti_Doping_Rules_Violations": [
        "anti-doping rule violation", "Prohibited Substance",
        "A Sample / B Sample", "whereabouts failure",
        "tampering", "trafficking", "strict liability",
    ],
    "WT_Anti_Doping_Rules_Terms_Of_Interest": [
        "International-Level Athlete", "Registered Testing Pool (RTP)",
        "whereabouts filing", "In-Competition period",
        "Out-of-Competition testing",
    ],
    "WT_Anti_Doping_Rules_Athlete_Responsibilities": [
        "strict liability", "Sample collection",
        "Therapeutic Use Exemption (TUE)", "Registered Testing Pool",
        "whereabouts filing", "Anti-Doping Education Course",
    ],
    "WT_Anti_Doping_Data_Privacy_Policy": [
        "ISPPPI", "privacy policy", "data minimisation",
        "data subject rights", "cross-border data transfer",
        "encryption",
    ],
    "WT_Code_of_Ethics": [
        "Code of Ethics", "conflict of interest",
        "dignity", "integrity", "good governance",
        "betting prohibition", "discrimination", "harassment",
    ],
    "WT_Medical_and_Anti-Doping_Management": [
        "Race Medical Director (RMD)", "medical plan",
        "doping control chaperones", "ambulance access routes",
        "minimum 10 urine tests",
    ],
    "WT_Medical_Guidelines": [
        "pre-travel consultation", "vaccination schedule",
        "heat acclimatization", "jet lag",
        "hydration protocol", "sports nutrition",
        "travellers' diarrhoea", "CPR", "AED",
    ],
    "WT_Water_Quality": [
        "E.Coli", "enterococci", "faecal contamination",
        "Blue-Green Algae", "Red Tide Algal bloom",
        "Decision Matrix", "visual inspection",
    ],
    "WT_Hydration_Systems": [
        "hydration system", "fairing",
        "aerobar extensions", "steering axis",
        "integrated frame hydration", "Race Ranger device",
    ],
    "WT_Uniform_Guidelines": [
        "sponsor spaces", "family name layout",
        "country code (NOC code)", "World Triathlon logo",
        "approval panel", "wetsuit manufacturer logo",
    ],
}

# -------------------------
# Synonym mappings for paraphrasing (extensive)
# -------------------------
SYNONYM_MAP: Dict[str, Dict[str, str]] = {
    "WT_Competition_Rules": {
        "drafting": "riding very close to another athlete",
        "drafting zone": "area where athletes ride too close",
        "wetsuit": "neoprene suit",
        "wetsuit mandatory": "neoprene suit required",
        "wetsuit forbidden": "neoprene suit not allowed",
        "penalty box": "time punishment area",
        "time penalty": "time punishment",
        "disqualification": "removal from race",
        "transition area": "where athletes switch between swim and bike",
        "yellow card": "warning card",
        "outside assistance": "help from others",
        "false start": "starting too early",
        "head referee": "main race official",
        "WBGT index": "heat stress measure",
        "relay exchange zone": "team change area",
        "mass start": "everyone starts together",
        "interval start": "athletes start one after another",
        "rolling start": "groups starting at intervals",
        "mount line": "where athletes get on the bike",
        "dismount line": "where athletes get off the bike",
        "bike check": "bicycle inspection",
        "swimskin": "special swimming suit",
        "tandem bicycle": "bicycle for two riders",
        "racing wheelchair": "competition wheelchair",
        "handcycle": "hand-powered cycle",
        "personal handler": "helper for para athlete",
        "blackout goggles": "goggles that block all light",
    },
    "WT_Para_Classification_Rules": {
        "Eligible Impairment": "condition that qualifies an athlete for para sport",
        "Minimum Impairment Criteria": "minimum level of disability required",
        "Athlete Evaluation": "assessment of an athlete's abilities",
        "Sport Class Status": "classification level of an athlete",
        "Classification Panel": "group that assesses athletes",
        "Medical Diagnostics Form": "medical information sheet",
        "Intentional Misrepresentation": "deliberately giving wrong information",
        "Chief Classifier": "head of classification",
        "IPC Board of Appeal of Classification": "appeal body for classification decisions",
        "Protest Panel": "group that reviews protests",
        "Classification Master List": "official list of athlete classifications",
        "Physical Assessment": "test of physical ability",
        "Technical Assessment": "test of sport-specific skills",
    },
    "WT_Anti_Doping_Rules": {
        "Adverse Analytical Finding": "positive drug test result",
        "Prohibited List": "list of banned substances",
        "Therapeutic Use Exemption": "permission to use a banned medication",
        "Registered Testing Pool": "group of athletes subject to regular testing",
        "Whereabouts Failure": "missing a doping test",
        "Tampering": "interfering with doping control",
        "Trafficking": "selling banned substances",
        "Provisional Suspension": "temporary ban",
        "Ineligibility": "period an athlete cannot compete",
        "Substantial Assistance": "helping authorities with information",
        "Specified Substance": "substance that may have legitimate uses",
        "CAS ADD": "sports arbitration court for doping cases",
        "B Sample": "second sample for verification",
    },
    "ITU_Disciplinary_Rules": {
        "Arbitration Tribunal": "independent panel that decides disputes",
        "ordinary proceeding": "standard legal case",
        "appeal proceeding": "case where a decision is challenged",
        "factum": "written legal argument",
        "claimant": "person filing a complaint",
        "appellant": "person appealing a decision",
        "respondent": "person responding to a complaint",
        "recusal": "removal of a judge due to conflict of interest",
        "statute of limitations": "time limit for taking legal action",
        "monetary penalty": "fine",
        "procedural violation": "breaking procedural rules",
        "suspensive effect": "delay of a decision while appeal is pending",
    },
    "TRI_Gender_Regulations": {
        "Transgender Female Eligibility Conditions": "requirements for transgender women",
        "Expert Panel": "group of experts",
        "testosterone monitoring": "blood tests for hormone levels",
        "separate results": "results for different categories",
        "TRI Academic Research Program": "research study athletes must join",
        "Year 4 pathway": "final stage of the eligibility process",
        "written declaration": "signed statement",
        "provisional suspension": "temporary ban while under investigation",
    },
    "TRI_Gender_Eligibility_Guidelines": {
        "serum testosterone concentration": "testosterone level in blood",
        "LC-MS/MS": "laboratory test method",
        "transgender female eligibility conditions": "requirements for transgender women",
        "spironolactone TUE": "permission to use spironolactone",
        "GnRH agonists": "hormone treatment drugs",
        "orchiectomy": "surgical removal of testes",
        "testosterone monitoring frequency": "how often hormone levels are checked",
    },
    "TRI_Individual_OQ_Ranking_Criteria": {
        "Individual Olympic Qualification Ranking": "ranking to qualify for Olympics",
        "7.5% decrease per position": "points go down with each place",
        "cut-off time (8%)": "time limit based on winner's time",
        "Quality of Field Factor": "adjustment for strength of competitors",
        "Top 5 bonus": "extra points for finishing in top five",
        "standard distance requirement": "athletes must complete standard distance events",
        "Continental Championships limitation": "limit on continental events counted",
    },
    "TRI_Mixed_Relay_OQ_Ranking_Criteria": {
        "Mixed Relay Olympic Qualification Ranking": "ranking for relay teams",
        "7.5% decrease per position": "points go down with each place",
        "cut-off time (10%)": "time limit based on winner's time",
        "Quality of Field Factor": "adjustment for strength of competitors",
        "Continental Championships limitation": "limit on continental events counted",
    },
    "Para_Triathlon_Interval_Start": {
        "Interval Start System": "staggered start for para athletes",
        "Factor (Class Factor)": "adjustment based on disability class",
        "Lead-off Value": "time delay between starts",
        "median race performance": "typical performance of a class",
        "expected race time": "predicted finishing time",
        "performance ratio (Men/Women)": "comparison of men's and women's times",
        "staggered start": "athletes start at different times",
        "single medal event": "one race for multiple classes",
    },
    "WT_Qualification_Criteria": {
        "Invitation Panel": "group that selects athletes",
        "T100 Triathlon World Tour": "professional triathlon series",
        "PTO World Rankings": "professional rankings",
        "Contender Ranking": "ranking for potential starters",
        "Wait List": "list of athletes waiting for a place",
        "Start List": "list of athletes starting a race",
        "T100 Race Agreement": "contract athletes must sign",
        "host National Federation": "federation of the organising country",
    },
    "WT_Qualification_Criteria_Continental": {
        "Continental Championships": "championships for a continent",
        "Continental Cup": "continental race series",
        "Development Regional Cup": "race for developing countries",
        "World Triathlon World Ranking": "world ranking of triathletes",
        "Invitation Panel": "group that selects athletes",
        "host continent quota": "number of athletes from the host continent",
        "Americas substitution rules": "special rules for the Americas",
    },
    "WT_Qualification_Criteria_General_Rules": {
        "Start List": "list of athletes starting a race",
        "Waiting List": "list of athletes waiting for a place",
        "National Federation quota": "number of athletes from a national federation",
        "exceeds quota": "too many athletes from one federation",
        "Invitation Panel": "group that selects athletes",
        "joker": "special exemption",
        "substitution window": "period to replace athletes",
        "withdrawal penalty": "punishment for late withdrawal",
        "event hierarchy": "order of event importance",
        "30-day rule": "deadline of 30 days",
    },
    "WT_Qualification_Criteria_Multisport": {
        "Multisport World Triathlon Ranking": "ranking for multisport events",
        "Appendix T": "section of the rules",
        "Medal Event (Paratriathlon)": "specific para race",
        "maximum quota": "maximum number of athletes",
        "start list creation 60 days": "list made 60 days before race",
    },
    "WT_Qualification_Criteria_Championships_Series": {
        "World Triathlon Championship Series (WTCS)": "major international series",
        "Championship Finals": "final championships",
        "continental quotas": "athlete numbers per continent",
        "roll-down system": "system to fill unused spots",
        "Invitation Panel": "group that selects athletes",
    },
    "WT_Qualification_Criteria_Mixed_Relay": {
        "Mixed Relay World Ranking": "ranking for relay teams",
        "Invitation Panel": "group that selects teams",
        "maximum 18 teams": "upper limit of participating teams",
        "start list": "list of teams starting",
    },
    "WT_Paralympic_Qualification_Ranking_Criteria": {
        "Paralympic Qualification Ranking": "ranking for Paralympics",
        "7.5% decrease per position": "points decrease with place",
        "cut-off time (35%)": "time limit based on winner's time",
        "best 3 results": "top three results count",
        "Los Angeles 2028 Paralympic Games": "upcoming Paralympic Games",
    },
    "WT_Anti_Doping_Rules_Supplements": {
        "Strict Liability": "athlete is responsible regardless of intent",
        "nutritional supplements": "dietary supplements",
        "contaminated supplements": "products with undeclared substances",
        "mislabeling": "wrong information on label",
        "manufacturer's certificate": "proof from the manufacturer",
    },
    "WT_Anti_Doping_Rules_Violations": {
        "anti-doping rule violation": "breaking anti-doping rules",
        "Prohibited Substance": "banned substance",
        "A Sample / B Sample": "two samples for testing",
        "whereabouts failure": "missing a doping test",
        "tampering": "interfering with testing",
        "trafficking": "selling banned substances",
        "strict liability": "athlete is responsible regardless of intent",
    },
    "WT_Anti_Doping_Rules_Terms_Of_Interest": {
        "International-Level Athlete": "athlete competing internationally",
        "Registered Testing Pool (RTP)": "group of athletes subject to testing",
        "whereabouts filing": "reporting location for testing",
        "In-Competition period": "time around a competition",
        "Out-of-Competition testing": "testing outside competitions",
    },
    "WT_Anti_Doping_Rules_Athlete_Responsibilities": {
        "strict liability": "athlete is responsible regardless of intent",
        "Sample collection": "doping test",
        "Therapeutic Use Exemption (TUE)": "permission to use medication",
        "Registered Testing Pool": "group of athletes tested regularly",
        "whereabouts filing": "reporting location for testing",
        "Anti-Doping Education Course": "course about anti-doping rules",
    },
    "WT_Anti_Doping_Data_Privacy_Policy": {
        "ISPPPI": "international privacy standard",
        "privacy policy": "data protection rules",
        "data minimisation": "collecting only necessary data",
        "data subject rights": "rights of individuals over their data",
        "cross-border data transfer": "sending data abroad",
        "encryption": "encoding data for security",
    },
    "WT_Code_of_Ethics": {
        "Code of Ethics": "ethical rules",
        "conflict of interest": "situation where personal interest interferes",
        "dignity": "respect for persons",
        "integrity": "honesty and moral principles",
        "good governance": "transparent and accountable management",
        "betting prohibition": "ban on gambling",
        "discrimination": "unfair treatment",
        "harassment": "offensive behavior",
        "hospitality standards": "rules about gifts and entertainment",
    },
    "WT_Medical_and_Anti-Doping_Management": {
        "Race Medical Director (RMD)": "doctor in charge of medical services",
        "medical plan": "plan for medical support",
        "doping control chaperones": "people who supervise doping tests",
        "ambulance access routes": "paths for emergency vehicles",
        "minimum 10 urine tests": "at least 10 drug tests",
        "paramedics per athlete ratio": "number of paramedics per athlete",
    },
    "WT_Medical_Guidelines": {
        "pre-travel consultation": "doctor visit before travelling",
        "vaccination schedule": "list of required vaccines",
        "heat acclimatization": "getting used to hot conditions",
        "jet lag": "tiredness from changing time zones",
        "hydration protocol": "plan for drinking enough fluids",
        "sports nutrition": "diet for athletes",
        "travellers' diarrhoea": "stomach sickness during travel",
        "CPR": "emergency breathing and chest compressions",
        "AED": "device to restart the heart",
    },
    "WT_Water_Quality": {
        "E.Coli": "bacteria that indicates pollution",
        "enterococci": "germs found in contaminated water",
        "faecal contamination": "presence of sewage in water",
        "Blue-Green Algae": "toxic algae",
        "Red Tide Algal bloom": "harmful algal bloom",
        "Decision Matrix": "table for decision making",
        "visual inspection": "looking at the water",
        "water quality limits": "safe levels for swimming",
    },
    "WT_Hydration_Systems": {
        "hydration system": "drinking bottle and holder",
        "fairing": "aerodynamic cover",
        "aerobar extensions": "handlebar extensions",
        "steering axis": "where the handlebars turn",
        "integrated frame hydration": "bottle built into the frame",
        "Race Ranger device": "tracking device",
        "storage box": "box for tools and spares",
    },
    "WT_Uniform_Guidelines": {
        "sponsor spaces": "areas for sponsor logos",
        "family name layout": "placement of athlete's surname",
        "country code (NOC code)": "abbreviation of country",
        "World Triathlon logo": "official World Triathlon symbol",
        "approval panel": "group that approves uniforms",
        "wetsuit manufacturer logo": "manufacturer's mark on wetsuit",
    },
}

def paraphrase_issue(issue: str, law: str, rng: random.Random) -> str:
    """Replace domain-specific terms in the issue with everyday synonyms."""
    synonyms = SYNONYM_MAP.get(law, {})
    if not synonyms:
        return issue
    # Sort by length of key descending to replace longer phrases first
    for term, replacement in sorted(synonyms.items(), key=lambda kv: -len(kv[0])):
        if term.lower() in issue.lower() and rng.random() < 0.65:
            issue = re.sub(re.escape(term), replacement, issue, flags=re.IGNORECASE)
    return issue

# -------------------------
# Law-specific context overrides (abridged)
# -------------------------
_GENERIC_OVERRIDE = {
    "authorities": ["World Triathlon", "Technical Delegate", "Invitation Panel"],
    "actors": ["athlete", "national federation", "team manager"],
    "counterparties": ["World Triathlon", "national federation"],
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
        text.replace("World Triathlon", "WT"), text.replace("competition", "race"),
        text.rstrip("?") if text.endswith("?") else text + "?",
        text.lower() if rng.random() < 0.7 else text,
        typo_once(text) if rng.random() < 0.5 else text,
    ]
    return normalize_ws(rng.choice(variants))

def inject_law_hint(text: str, law: str, rng: random.Random) -> str:
    forms = [f" (according to {law.replace('_', ' ')})", f" - {law.replace('_', ' ')}", f" under {law.replace('_', ' ')}"]
    return text + rng.choice(forms)

# -------------------------
# Document-specific specs (topics trimmed)
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
            "Drafting rules and penalty zones in draft-illegal events",
            "Penalty serving procedures at transition, bike, and run boxes",
            "Swim start procedures: mass start, interval, and time trial",
            "Outside assistance allowed and prohibited during races",
            "Protest initiation timelines and required fees",
            "Water quality standards for sea and inland water",
            "Modifications due to heat: WBGT index and flag system",
            "Transition area conduct: racking, equipment placement, mount/dismount lines",
            "Uniform rules: torso coverage, zipper length, logo restrictions",
            "Appeal procedures: Level 2 to World Triathlon Tribunal and CAS",
        ],
        "WT_Para_Classification_Rules": [
            "Eligible impairments for Para triathlon",
            "Submission of Medical Diagnostics Form 8 weeks before classification",
            "Athlete evaluation steps: physical, technical, observation",
            "Sport Class Status types: New, Confirmed, Review, Fixed Review Date",
            "Protest procedures and Protest Panel formation",
            "Intentional Misrepresentation: definition and consequences",
            "Confidentiality and data protection for classification data",
            "Classifier Code of Conduct and conflict of interest rules",
        ],
        "WT_Anti_Doping_Rules": [
            "Definition of doping and anti-doping rule violations",
            "Presence of a Prohibited Substance (strict liability)",
            "Whereabouts failures: missed tests and filing failures",
            "Therapeutic Use Exemptions (TUEs): application and recognition",
            "Testing authority: In-Competition and Out-of-Competition",
            "Sanctions for Presence, Use, or Possession: 4-year vs 2-year Ineligibility",
            "Substantial Assistance: suspension of Ineligibility period",
            "Appeals from decisions: who may appeal and timelines",
            "Confidentiality and Public Disclosure of violations",
            "Education requirements: mandatory anti-doping course",
        ],
        "ITU_Disciplinary_Rules": [
            "Jurisdiction of the ITU Arbitration Tribunal",
            "Types of disciplinary sanctions available",
            "Deadline for filing an ordinary proceeding",
            "Statutes of limitation for competition infringements",
            "Recusal of Panel members for conflict of interest",
            "Right to be heard and admissible evidence",
            "Costs of proceedings and monetary penalties",
            "How to file an appeal against a competition decision",
            "Ad hoc panel for Olympic and Paralympic Games",
        ],
        "TRI_Gender_Regulations": [
            "Eligibility pathway for Transgender Female athletes",
            "Testosterone concentration requirement below 2.5 nmol/L",
            "Separate results listing in Year 4 elite competition",
            "Expert Panel composition and assessment process",
            "Confidentiality of athlete information",
            "Monitoring of testosterone levels by Expert Panel",
            "Appeal process to TRI Tribunal",
            "Withdrawal of consent and its effect on eligibility",
        ],
        "TRI_Gender_Eligibility_Guidelines": [
            "Transgender Male eligibility: written declaration",
            "Transgender Female eligibility: 4-year pathway",
            "Role of testosterone as primary biomarker",
            "Monitoring serum testosterone levels",
            "Frequency of testing based on medication type",
            "Testosterone threshold: 2.5 nmol/L derivation",
        ],
        "TRI_Individual_OQ_Ranking_Criteria": [
            "Olympic qualification period for individuals",
            "Point values per event type (1250, 1000, 500, 400)",
            "Maximum results: 12 total, max 8 short distance",
            "Standard distance score requirements",
            "Continental Championships and Games limits",
            "Cut-off time: 8% added to winner's time",
        ],
        "TRI_Mixed_Relay_OQ_Ranking_Criteria": [
            "Olympic qualification period for Mixed Relay",
            "Point values per event type (1000, 800, 500)",
            "Maximum results: 6 total, 3 per period",
            "Continental Championships limitation",
            "Cut-off time rule: 10% added to winner's time",
        ],
        "Para_Triathlon_Interval_Start": [
            "Purpose of the Interval Start System",
            "Calculation of Factors from elite race results",
            "Using median performance values for Class Factors",
            "Calculation of Lead-off Value",
            "Combining Men's and Women's results via performance ratio",
            "Discarding bike segment for visually impaired athletes",
        ],
        "WT_Qualification_Criteria": [
            "T100 Tour eligibility and required agreements",
            "Start List sizes for first/rest events and Grand Final",
            "Preliminary Start List and Wait List ordering",
            "Role and powers of the Invitation Panel",
            "Filling vacancies from Wait List",
            "Age-Group qualification pathways and quotas",
        ],
        "WT_Qualification_Criteria_Continental": [
            "Start list sizes for Continental Championships",
            "Quota rules for Triathlon Continental Cup",
            "Junior Continental Cup: ranking and Invitation Panel",
            "Mixed Relay Continental Championships quotas",
            "Development Regional Cup eligibility",
            "Americas region special substitution rules",
        ],
        "WT_Qualification_Criteria_General_Rules": [
            "Start List creation and initial athlete selection",
            "Waiting List sorting and quota handling",
            "Substitution rules and deadlines",
            "Withdrawal penalties and joker system",
            "Event hierarchy for same-weekend conflicts",
        ],
        "WT_Qualification_Criteria_Multisport": [
            "Quotas for Elite/U23/Junior/Paratriathlon",
            "Age-Group qualification and quotas",
            "Technical Delegate quota adjustments",
        ],
        "WT_Qualification_Criteria_Championships_Series": [
            "WTCS Elite start list size and selection",
            "Championship Finals quotas",
            "U23 Championships quotas and reduction",
            "Junior continental quotas and roll-down",
        ],
        "WT_Qualification_Criteria_Mixed_Relay": [
            "Start list size and team priority order",
            "Quota: 1 team per National Federation",
            "Invitation Panel role for remaining spaces",
        ],
        "WT_Paralympic_Qualification_Ranking_Criteria": [
            "Paralympic qualification period and events",
            "Point scales for each event type",
            "Maximum 3 scoring events",
            "Cut-off time rule (35% added to winner's time)",
        ],
        "WT_Anti_Doping_Rules_Supplements": [
            "Definition and examples of dietary supplements",
            "Risks of contamination and mislabeling",
            "Principle of Strict Liability for athletes",
            "World Triathlon's advisory stance on supplements",
        ],
        "WT_Anti_Doping_Rules_Violations": [
            "Presence of a Prohibited Substance (Article 2.1)",
            "Use or Attempted Use (Article 2.2)",
            "Evading Sample Collection (Article 2.3)",
            "Whereabouts Failures (Article 2.4)",
            "Tampering with Doping Control (Article 2.5)",
            "Possession of Prohibited Substances (Article 2.6)",
        ],
        "WT_Anti_Doping_Rules_Terms_Of_Interest": [
            "Definition of International-Level Athlete",
            "Registered Testing Pool inclusion criteria",
            "Whereabouts obligations for RTP athletes",
            "Definition of In-Competition period",
        ],
        "WT_Anti_Doping_Rules_Athlete_Responsibilities": [
            "Duty to be available for Sample collection",
            "Responsibility for what athletes ingest",
            "Duty to disclose prior anti-doping violations",
            "Requirement to complete Anti-Doping Education Course",
        ],
        "WT_Anti_Doping_Data_Privacy_Policy": [
            "Legal framework: ISPPPI, FADP, GDPR",
            "Types of personal data processed",
            "Disclosure of information to authorised recipients",
            "Data retention and deletion policy",
            "Rights of individuals under data protection laws",
        ],
        "WT_Code_of_Ethics": [
            "Safeguarding dignity and prohibiting discrimination",
            "Prohibition of betting and manipulation",
            "Integrity rules: bribery, gifts, conflicts of interest",
            "Good governance principles",
            "Breach of the Code: referral to Tribunal and sanctions",
        ],
        "WT_Medical_and_Anti-Doping_Management": [
            "Role of Medical Delegate and Race Medical Director",
            "Medical staffing ratios and equipment",
            "Ambulance requirements and emergency access",
            "Doping control responsibilities and facility requirements",
        ],
        "WT_Medical_Guidelines": [
            "Pre-competition medical planning and vaccinations",
            "Heat exposure and acclimatization protocols",
            "Jet lag and time zone adaptation strategies",
            "Hydration and sports nutrition guidelines",
            "First aid principles and injury treatment",
            "Exertional heat illness recognition and management",
        ],
        "WT_Water_Quality": [
            "Health risks from contaminated water",
            "Bacterial indicators: E.Coli and enterococci",
            "Water quality test requirements and sampling",
            "Water Quality Decision Matrix",
            "Event Water Quality Evaluation Panel role",
        ],
        "WT_Hydration_Systems": [
            "Handlebar and clip-on bar dimension limits",
            "Hydration volume limits on steering axis",
            "Rear mounted hydration specifications",
            "Top tube attachment rules",
        ],
        "WT_Uniform_Guidelines": [
            "Family name and country code placement rules",
            "World Triathlon logo specifications",
            "Sponsor space definitions and maximum sizes",
            "Uniform approval process and conflict resolution",
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
    ov = _GENERIC_OVERRIDE
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
    authority_part = rng.choice([f"A decision/notice from {ctx['authority']} is involved.", f"Jurisdiction unclear ({ctx['authority']} or CAS?).", ""])
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

def generate_queries_for_topic(*, topic_id: str, issue: str, law: str, seed: int, variants_per_style: int, law_mention_prob: float, keyword_law_mention_prob: float, surface_noise_prob: float, law_context_prob: float, topic_term_prob: float, issue_term_prob: float, keyword_term_prob: float) -> List[Dict[str, str]]:
    # PARAPHRASE THE ISSUE FIRST (for both train and test)
    rng = random.Random(seed)
    issue = paraphrase_issue(issue, law, rng)

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
            p = keyword_law_mention_prob if style == "keyword" else law_mention_prob
            if rng.random() < p: text = inject_law_hint(text, law, rng)
            text = maybe_apply_surface_noise(text, rng, surface_noise_prob)
            out.append({"query_id": f"{topic_id}_{style}_v{v:02d}", "topic_id": topic_id, "query_text": text, "consensus_law": law, "style": style, "issue": issue})
    return out

# -------------------------
# Allocation and sampling
# -------------------------

def target_counts_weighted(total: int) -> Dict[str, int]:
    return _compute_query_weights(total, min_per_doc=20)

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
    ap.add_argument("--law_mention_prob", type=float, default=0.0)          # disable law hints (would give away answer)
    ap.add_argument("--keyword_law_mention_prob", type=float, default=0.0)  # disable law hints
    ap.add_argument("--surface_noise_prob", type=float, default=0.06)
    ap.add_argument("--law_context_prob", type=float, default=1.0)
    ap.add_argument("--topic_term_prob", type=float, default=0.0)          # disable direct term injection
    ap.add_argument("--issue_term_prob", type=float, default=0.0)          # disable direct term enrichment
    ap.add_argument("--keyword_term_prob", type=float, default=0.0)        # disable direct term in keywords
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

    # Generate topics for all laws
    for law in sorted(LAWS):
        if law not in base_specs: raise RuntimeError(f"Missing base spec for {law}")
        spec = expand_spec_with_facets(law, base_specs[law], seed=seed)
        need = max(8, ceil((train_target_law[law] + test_target_law[law]) * args.candidate_oversupply / max(1, queries_per_topic))) + extra
        issues = generate_issues_for_law(law, spec, min_count=need, seed=seed)
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
                keyword_term_prob=args.keyword_term_prob,
            ))
        return pool

    pool = build_pool(all_topics, seed + 111)
    train_rows, test_rows = split_train_test_stratified_grid_test_topics_in_train(pool, train_target, test_target, seed + 303)
    split_meta = {"topics_per_law": {law: len(topics_by_law[law]) for law in sorted(LAWS)}, "extra_topics_per_law": extra, "test_topics_subset_of_train": True}

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