# seed_data.py
from __future__ import annotations
from typing import Iterable, Optional, Tuple
from sqlmodel import select, Session
from db import init_db, engine
from models import (                                    # Catalogi (beheer)
    RiskClass, WorkSubject, WorkArea, WorkType, Tool,
    WorkRiskCat, EnvRiskCat, Risk,
    Measure, ResponsibleRole,
    SiteLocation, DepartmentUnit, Space,
    AreaOwnerMap, SystemOwnerMap,
)

# =========================
#   Brondata 
# =========================
subjects = [
    "Aanleg","Aanpassing","Inspectie – Installatie",
    "Onderhoud","Uitbreiding","Reparatie","Werkopname",
]

areas = [
    "Beveiligingstechniek","Bouwkundig","Fundatie","Infrastructuur",
    "Installatietechniek (GWE)","Informatietechniek (IT)",
    "Schoonmaak","Transport","Veiligheidsvoorziening","HVAC",
]

worktypes = [
    "NA","Autogeen lassen","Betreden Besloten Ruimte","Boren","Branden",
    "Elektrisch lassen","Elektrische werkzaamheden","Graven (handmatig)","Graven (machinaal)",
    "Hijsen en heffen","Hogedruk werkzaamheden","Inspectie werkzaamheden",
    "Monteren/demonteren","Openen van installaties","Slijpen","Sloopwerkzaamheden",
    "Toepassen LoToTo","Werk ATEX ruimtes","Werk op hoogte",
]

tools = [
    "NA","Aggregaat","Elektrisch handgereedschap","Handgereedschap","Hangbak","Hangsteiger",
    "Heftruck","Hijskraan","Hogedrukspuit","Hoogwerker","Ladder","Pneumatisch gereedschap",
    "Reformladder","Rolsteiger","Slijptol","Steiger (vast)","Trap","Verlichting",
    "Waterstofzuiger","Waterzuiger","Werkbak",
]

work_risks = [
    "NA","Beknelling","Brandgevaar-verbranding","Draaiende machines","Elektrocutie","Hoge druk",
    "Lawaai - Geluid > 80 dB","Ontploffing","Restenergie","Stof","Stoom",
    "Valgevaar","Vallende materialen","Verspanende materialen","Verstikking",
    "Wegspringende materialen","Werken op hoogte",
]
env_risks = [
    "NA","3 of meer partijen op 1 werk","Asbest","Draaiende machines","Giftige en gevaarlijke stoffen",
    "Hoge druk leidingen","Intern transport","Klimaat (koude-warme-vochtige werkomgeving)",
    "Lekkende leidingen","Moeilijke aanvoer van materialen (belemmeren vluchtwegen)",
    "Omgevingstemperatuur","Productieomgeving (tussen machines- installaties)",
    "Slecht licht","Slecht of geen toegankelijkheid zonder hulpmiddelen (dak-kelder-besloten ruimte)",
    "Stoom / heet water","Struikelen uitglijden","Vallende voorwerpen","Verbranden",
    "Bevriezen","Vervuilde grond","Werk in gebied met (veel) verkeer en transport",
]

work_measures = [
    "NA","Aanbrengen aarding","Blusmiddelen","Brandwacht inzetten",
    "Communicatiemiddelen","Controleren steiger(s)",
    "Gebruik veilige spanningen","Geforceerde ventilatie","LOTOTO","Mangatwacht inzetten",
    "Putten, goten en/of riool afdekken","Randbeveiliging","Vonkafscherming gebruiken",
    "Vonkvrij gereedschap","Werkplek afzetten","Werkplek - werkstuk nathouden",
]
env_measures = [
    "NA","Afzetten werkplek","Apparatuur elektrisch blokkeren","Apparatuur mechanisch blokkeren",
    "Controle omgeving op brandbaar materiaal","Milieubeschermende maatregelen",
    "Overbruggingsverklaring","Systeem afkoppelen","Systeem aftappen","Systeem drukvrij maken",
    "Systeem inblokken","Systeem produktvrij maken","Systeem spoelen","Systeem stomen",
    "Systeem ventileren","Zekeringen trekken",
]

riskclasses = ["Laag","Middel","Hoog"]

locations = [
    "Kantoor","Productie A","Productie B","Productie C","Magazijn","Buitenterrein",
]

departments = [
    "Entree","Gebouw 10","Gebouw 20","Gebouw 30","Gebouw 40","Gebouw 50",
    "Kantoor","Inkomende goederen","Uitgaande goederen",
    "Technische Ruimte","Technische Vloer",
]

spaces_list = [
    "Alg - Entree","Alg - Outbound","Alg - Inbound","00.0.10 - Fietsenhok","00.0.20 - Parkeerplaats",
    "10.0.51 - Ontvangst","10.0.52 - Opslag",
    "20.0.13 - Technische werkplaats","20.0.13a - Doorgeefsluis","20.0.13b - Voorportaal TD",
    "20.0.21 - Chaufeursontvangst","20.0.21a - Chauffeurs toilet",
    "20.0.24 - Trafo 1","20.0.25 - Trafo 2","20.0.26 - Trafo 3",
    "20.0.27 - Chemicalien opslag","20.0.28 - Pompruimte","20.0.29 - Compressorruimte",
    "20.0.53 - Water opslag","20.0.54 - Container opslag",
    "20.1.16 - Utilities","20.1.17 - Spreekkamer","20.1.18 - Opslag utilities",
    "20.1.20 - Laagspanningsruimte","20.1.21 - MCC ruimte","20.1.22 - Warmtepomp ruimte",
    "20.3.04 - Dak utilities",
    "30.0.01 - Entrée","30.0.02 - Vergaderruimte","30.0.03 - Garderobe",
    "30.0.30 - Voorportaal lift",
]

# PBM's: (naam, default_required, default_responsible)
pbms: list[Tuple[str, bool, Optional[str]]] = [
    ("Helm (veiligheidshelm)", True, "Houder"),
    ("Veiligheidsbril", True, "Houder"),
    ("Gehoorbescherming", True, "Houder"),
    ("Handschoenen (snijbestendig waar nodig)", True, "Houder"),
    ("Veiligheidsschoenen S3", True, "Houder"),
    ("Valbeveiliging (indien van toepassing)", True, "Houder"),
    ("Adembescherming (indien van toepassing)", False, "SHE"),
    ("Signaalvest", False, "Houder"),
]

# Baseline rollen
roles_seed = [
    ("Houder", "Werk", 10, True),
    ("Verstrekker-Gebied", "Omgeving", 20, True),
    ("Verstrekker-Systeem", "Omgeving", 30, True),
    ("SHE", "Beide", 40, True),
    ("Specialist", "Beide", 50, True),
    ("Coördinator", "Beide", 60, True),
]

# =========================
# Upsert helpers
# =========================
def upsert_simple_list(Model, names: Iterable[str], category_field: Optional[str] = None, category_value: Optional[str] = None, start_order: int = 10):
    """Upsert voor tabellen met velden: id, name, active, sort_order (+ optioneel 1 'category' veld)."""
    with Session(engine) as s:
        for i, name in enumerate(names, start=0):
            name = name.strip()
            if not name:
                continue
            rec = s.exec(select(Model).where(Model.name == name)).first()
            if not rec:
                kwargs = dict(name=name, active=True, sort_order=start_order + i*10)
                if category_field and category_value is not None:
                    kwargs[category_field] = category_value
                rec = Model(**kwargs)
                s.add(rec)
            else:
                changed = False
                if hasattr(rec, "active") and rec.active is False:
                    rec.active = True; changed = True
                if hasattr(rec, "sort_order"):
                    desired = start_order + i*10
                    if (rec.sort_order or 0) != desired:
                        rec.sort_order = desired; changed = True
                if category_field and category_value is not None and getattr(rec, category_field, None) != category_value:
                    setattr(rec, category_field, category_value); changed = True
                if changed:
                    s.add(rec)
        s.commit()

def upsert_roles(rows: Iterable[Tuple[str,str,int,bool]]):
    with Session(engine) as s:
        for name, applies_to, sort_order, active in rows:
            name = name.strip()
            rec = s.exec(select(ResponsibleRole).where(ResponsibleRole.name == name)).first()
            if not rec:
                s.add(ResponsibleRole(name=name, applies_to=applies_to, sort_order=sort_order, active=active))
            else:
                changed = False
                if rec.applies_to != applies_to: rec.applies_to = applies_to; changed = True
                if (rec.sort_order or 0) != sort_order: rec.sort_order = sort_order; changed = True
                if rec.active != active: rec.active = active; changed = True
                if changed: s.add(rec)
        s.commit()

def upsert_measures(names: Iterable[str], scope_value: str):
    """Upsert Measure records met gegeven scope (Werk/Omgeving)."""
    with Session(engine) as s:
        for name in names:
            name = name.strip()
            if not name:
                continue
            m = s.exec(select(Measure).where(Measure.name == name)).first()
            if not m:
                m = Measure(name=name, scope=scope_value, default_required=True, active=True)
                s.add(m)
            else:
                changed = False
                if m.scope != scope_value: m.scope = scope_value; changed = True
                if m.active is False: m.active = True; changed = True
                if changed: s.add(m)
        s.commit()

def upsert_pbms(rows: Iterable[Tuple[str,bool,Optional[str]]]):
    """PBM = Measure met scope='PBM' + default_required + default_responsible."""
    with Session(engine) as s:
        for name, req, resp in rows:
            name = (name or "").strip()
            if not name:
                continue
            m = s.exec(select(Measure).where(Measure.name == name)).first()
            if not m:
                m = Measure(name=name, scope="PBM", default_required=bool(req), default_responsible=resp or None, active=True)
                s.add(m)
            else:
                changed = False
                if m.scope != "PBM": m.scope = "PBM"; changed = True
                if m.default_required != bool(req): m.default_required = bool(req); changed = True
                if (m.default_responsible or None) != (resp or None): m.default_responsible = (resp or None); changed = True
                if m.active is False: m.active = True; changed = True
                if changed: s.add(m)
        s.commit()

def seed_owner_maps():
    with Session(engine) as s:
        # voorbeeld gebiedseigenaar
        if not s.exec(select(AreaOwnerMap).where(AreaOwnerMap.location=="Productie A", AreaOwnerMap.department=="Gebouw 10")).first():
            s.add(AreaOwnerMap(location="Productie A", department="Gebouw 10", owner_name="Team Gebied A-10", sort_order=10, active=True))
        # voorbeeld systeemeigenaar (werkgebied=Installatietechniek, asset bevat 'Verlichting')
        if not s.exec(select(SystemOwnerMap).where(SystemOwnerMap.work_area=="Installatietechniek (GWE)")).first():
            s.add(SystemOwnerMap(work_area="Installatietechniek (GWE)", match_type="contains", asset_pattern="Verlichting", owner_name="Team Installatiebeheer", sort_order=10, active=True))
        s.commit()

# =========================
# Main seeding
# =========================
def main():
    print("Initializing DB…")
    init_db()

    print("Seeding Responsible Roles…")
    upsert_roles(roles_seed)

    print("Seeding Subjects (Betreft)…")
    upsert_simple_list(WorkSubject, subjects, start_order=10)

    print("Seeding Work Areas…")
    upsert_simple_list(WorkArea, areas, start_order=10)

    print("Seeding Work Types…")
    upsert_simple_list(WorkType, worktypes, start_order=10)

    print("Seeding Tools…")
    upsert_simple_list(Tool, tools, start_order=10)

    print("Seeding Risk Catalogs (Work/Env)…")
    upsert_simple_list(WorkRiskCat, work_risks, start_order=10)
    upsert_simple_list(EnvRiskCat, env_risks, start_order=10)

    print("Seeding Risks (for mappings: category=Werk/Omgeving)…")
    upsert_simple_list(Risk, work_risks, category_field="category", category_value="Werk", start_order=10)
    upsert_simple_list(Risk, env_risks,  category_field="category", category_value="Omgeving", start_order=10)

    print("Seeding Measures (Werk)…")
    upsert_measures(work_measures, scope_value="Werk")

    print("Seeding Measures (Omgeving)…")
    upsert_measures(env_measures, scope_value="Omgeving")

    print("Seeding PBMs (scope=PBM)…")
    upsert_pbms(pbms)

    print("Seeding Risk Classes…")
    upsert_simple_list(RiskClass, riskclasses, start_order=10)

    print("Seeding Site Locations…")
    upsert_simple_list(SiteLocation, locations, start_order=10)

    print("Seeding Departments…")
    upsert_simple_list(DepartmentUnit, departments, start_order=10)

    print("Seeding Spaces…")
    upsert_simple_list(Space, spaces_list, start_order=10)

    print("Seeding Owners(auto)…")
    seed_owner_maps()

    print("Done.")

if __name__ == "__main__":
    main()
