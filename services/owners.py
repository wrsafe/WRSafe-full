# services/owners.py
from __future__ import annotations
import re, fnmatch
from typing import Optional
from sqlmodel import Session, select
from db import engine
from models import AreaOwnerMap, SystemOwnerMap

def resolve_area_owner(location: Optional[str], department: Optional[str]) -> Optional[str]:
    """Zoek gebiedseigenaar op basis van exacte (location, department). Keer terug met hoogste prioriteit (laagste sort_order)."""
    if not location or not department:
        return None
    with Session(engine) as s:
        rows = s.exec(
            select(AreaOwnerMap)
            .where((AreaOwnerMap.active == True) &
                   (AreaOwnerMap.location == location) &
                   (AreaOwnerMap.department == department))
            .order_by(AreaOwnerMap.sort_order, AreaOwnerMap.id)
        ).all()
        return rows[0].owner_name if rows else None

def _asset_matches(asset: str, match_type: str, pattern: str) -> bool:
    a = asset or ""
    p = pattern or ""
    mt = (match_type or "contains").lower()
    if mt == "exact":
        return a == p
    if mt == "startswith":
        return a.startswith(p)
    if mt == "contains":
        return p in a
    if mt == "glob":
        return fnmatch.fnmatch(a, p)
    if mt == "regex":
        try:
            return re.search(p, a) is not None
        except re.error:
            return False
    return False

def resolve_system_owner(work_area: Optional[str], asset: Optional[str]) -> Optional[str]:
    """Zoek systeemeigenaar:
       1) probeer eerst regels met NIET-lege pattern die matchen (volgorde = sort_order)
       2) anders gebruik 1e algemene regel (lege pattern) binnen werkgebied
    """
    if not work_area:
        return None
    with Session(engine) as s:
        rows = s.exec(
            select(SystemOwnerMap)
            .where((SystemOwnerMap.active == True) &
                   (SystemOwnerMap.work_area == work_area))
            .order_by(SystemOwnerMap.sort_order, SystemOwnerMap.id)
        ).all()

        general_owner = None  # lege pattern fallback
        a = asset or ""

        for r in rows:
            patt = (r.asset_pattern or "").strip()
            if not patt:
                # algemene regel onthouden als fallback
                if general_owner is None:
                    general_owner = r.owner_name
                continue
            if _asset_matches(a, r.match_type, patt):
                return r.owner_name

        return general_owner
