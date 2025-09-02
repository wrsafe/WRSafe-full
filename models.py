# models.py
from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey

# ===== Kern =====
class Permit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    location: Optional[str] = None
    department: Optional[str] = None
    work_area: Optional[str] = None
    applicant_name: Optional[str] = None
    applicant_team: Optional[str] = None
    applicant_org: Optional[str] = None
    reason: Optional[str] = None
    subject: Optional[str] = None
    asset: Optional[str] = None
    area_owner: Optional[str] = None
    system_owner: Optional[str] = None
    start_dt: datetime
    end_dt: datetime
    status: str = "Concept"
    risk_class: Optional[str] = None

# ===== Beheertabellen =====
class PermitMeasure(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    permit_id: int = Field(foreign_key="permit.id")
    description: str
    required: bool = True
    checked_at: Optional[datetime] = None

class WorkSubject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

class WorkArea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

# ===== Lookups =====
class SiteLocation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

class WorkRiskClass(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

class DepartmentUnit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

class Space(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

class PermitSpace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    permit_id: int = Field(foreign_key="permit.id")
    space_id: Optional[int] = Field(default=None, foreign_key="space.id")
    custom_name: Optional[str] = None

class WorkType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

class RiskClass(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

class Tool(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

class Risk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str = "Werk"                      # "Werk" of "Omgeving"
    active: bool = True
    sort_order: int = 100

class Measure(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    default_required: bool = True
    active: bool = True
    scope: str = "Werk"                         # "Werk", "Omgeving", "PBM"
    default_responsible: Optional[str] = None

class ResponsibleRole(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str                                   # bv. "Houder", "Verstrekker-Gebied", ...
    applies_to: str = "Beide"                   # "Werk" | "Omgeving" | "Beide"
    active: bool = True
    sort_order: int = 100

# Relaties (permit details)
class PermitWorkType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    permit_id: int = Field(foreign_key="permit.id")
    worktype_id: Optional[int] = Field(default=None, foreign_key="worktype.id")
    custom_name: Optional[str] = None

class PermitTool(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    permit_id: int = Field(foreign_key="permit.id")
    tool_id: Optional[int] = Field(default=None, foreign_key="tool.id")
    custom_name: Optional[str] = None

class PermitRisk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    permit_id: int = Field(foreign_key="permit.id")
    risk_id: int = Field(foreign_key="risk.id")
    category: str = "Werk"

# --- Catalogi voor risico's ---
class WorkRiskCat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

class EnvRiskCat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    sort_order: int = 100

# --- Regeltabellen: risico (catalogus) → maatregel ---
class WorkRiskRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Python-attribute heet risk_id, maar kolom blijft "workrisk_id" (backwards compatible)
    risk_id: int = Field(sa_column=Column("workrisk_id", ForeignKey("workriskcat.id")))
    measure_id: int = Field(foreign_key="measure.id")
    required_override: Optional[bool] = None
    weight: int = 100

class EnvRiskRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Python-attribute heet risk_id, maar kolom blijft "envrisk_id" (backwards compatible)
    risk_id: int = Field(sa_column=Column("envrisk_id", ForeignKey("envriskcat.id")))
    measure_id: int = Field(foreign_key="measure.id")
    required_override: Optional[bool] = None
    weight: int = 100

# Mapping Werkwijze ↔ Risico
class WorkTypeRisk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    worktype_id: int = Field(foreign_key="worktype.id")
    risk_id: int = Field(foreign_key="risk.id")

# Regels: Maatregelen aan Risico (eenduidig)
class MeasureRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    measure_id: int = Field(foreign_key="measure.id")
    risk_id: int = Field(foreign_key="risk.id")
    required_override: Optional[bool] = None
    weight: int = 100

# Rijen uit Tab 3 (Werk/Omgeving)
class PermitRiskAction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    permit_id: int = Field(foreign_key="permit.id")
    category: str = "Werk"              # "Werk" of "Omgeving"
    risk_name: str                      # tekst (beheer of vrije invoer)
    measure_name: str                   # tekst (beheer of vrije invoer)
    responsible: str                    # gekozen verantwoordelijke
    source: str = "manual"              # "rule" of "manual"
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Goedkeuringen
class ApprovalStep(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    permit_id: int = Field(foreign_key="permit.id")
    step_order: int = 0
    role_type: str
    display_name: str
    required: bool = True

class ApprovalLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    permit_id: int = Field(foreign_key="permit.id")
    step_order: int
    approver_name: str
    decision: str               # 'Approved' | 'Rejected'
    comment: Optional[str] = None
    at: datetime = Field(default_factory=datetime.utcnow)

class PermitStep(SQLModel, table=True):
    """Werkstappen / deeltaken per vergunning."""
    id: Optional[int] = Field(default=None, primary_key=True)
    permit_id: int = Field(foreign_key="permit.id")
    order: int = 0
    description: str

# === Eigenaren-mapping ===
class AreaOwnerMap(SQLModel, table=True):
    """Koppelt (location, department) → eigenaar (vrije tekst)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    location: str                                    # exact match
    department: str                                  # exact match
    owner_name: str                                  # bv. "Gebiedseigenaar: Jan Jansen"
    active: bool = True
    sort_order: int = 100
    notes: Optional[str] = None

class SystemOwnerMap(SQLModel, table=True):
    """Koppelt (work_area, asset) → eigenaar met patroon-matching en prioriteit."""
    id: Optional[int] = Field(default=None, primary_key=True)
    work_area: str                                   # exact match op werkgebied
    match_type: str = "contains"                     # "exact" | "startswith" | "contains" | "glob" | "regex"
    asset_pattern: str                               # patroon voor asset
    owner_name: str
    active: bool = True
    sort_order: int = 100                            # lagere waarde = hogere prioriteit
    notes: Optional[str] = None
