# services/ui_admin.py
from __future__ import annotations
import streamlit as st
from sqlmodel import select
from typing import Type, List, Dict, Any, Optional, Tuple
from db import get_session

def render_catalog_admin(
    Model: Type,
    title: str,
    *,
    # Nieuwe, expliciete parameters:
    column_config: Optional[Dict[str, Any]] = None,
    column_order: Optional[List[str]] = None,
    default_sort: Optional[List[Tuple[str, str]]] = None,  # bv. [("sort_order","asc"),("name","asc")]
    filters: Optional[Dict[str, Any]] = None,
    page_size: int = 15,
    show_inactive_default: bool = False,
    allow_add: bool = True,
    allow_delete: bool = False,
    unique_field: str = "name",
    defaults_on_add: Optional[Dict[str, Any]] = None,
):
    """
    Compacte beheer-UI in één data_editor:
    - filter op 'actief'
    - vrij zoeken
    - inline bewerken (id, name, sort_order, active + extra velden)
    - rij toevoegen via popover
    - batch 'Opslaan' knop

    Vereist minimaal velden: id, name, active (bool), sort_order (int)
    """

    st.header(title)

    # --------------------
    # Controls / filters
    # --------------------
    colf = st.columns([2, 2, 2, 2, 2])
    with colf[0]:
        q = st.text_input("🔎 Zoeken", "")
    with colf[1]:
        show_inactive = st.checkbox("Toon inactief", value=show_inactive_default)
    with colf[2]:
        page_size = st.number_input("Rijen per pagina", 5, 200, value=page_size, step=5)
    with colf[3]:
        st.caption("Sortering via default_sort")
    with colf[4]:
        st.caption("Pas kolombreedtes aan via column_config")

    # --------------------
    # Data laden
    # --------------------
    with get_session() as s:
        rows = s.exec(select(Model)).all()

    # Naar dicts + filteren
    data: List[Dict[str, Any]] = []
    for r in rows:
        d = r.dict()
        if filters:
            if any(d.get(k) != v for k, v in filters.items()):
                continue
        if not show_inactive and not d.get("active", True):
            continue
        if q:
            hay = " ".join(str(d.get(k, "")) for k in d.keys())
            if q.lower() not in hay.lower():
                continue
        data.append(d)

    # --------------------
    # Sorteren
    # --------------------
    def _key_for(row: Dict[str, Any], col: str):
        v = row.get(col)
        return (v is None, v)  # None komt altijd laatst

    if default_sort:
        # Gebruik meerdere sort-sleutels (stabel sorteren van achter naar voren)
        for col, direction in reversed(default_sort):
            reverse = (str(direction).lower() in ("desc", "↓", "down"))
            data.sort(key=lambda r, c=col: _key_for(r, c), reverse=reverse)
    else:
        # Fallback: sorteer op sort_order, daarna name
        data.sort(key=lambda r: (r.get("sort_order"), r.get("name")))

    # --------------------
    # Pagineren
    # --------------------
    total = len(data)
    if total > page_size:
        pcols = st.columns([6, 2, 2, 2])
        with pcols[1]:
            page = st.number_input("Pagina", 1, max(1, (total - 1) // page_size + 1), 1, step=1)
        start = (page - 1) * page_size
        end = start + page_size
        view = data[start:end]
        st.caption(f"Toont {start + 1}–{min(end, total)} van {total}")
    else:
        view = data

    # --------------------
    # Kolommen-config (smal houden)
    # --------------------
    base_cfg = {
        "id":         st.column_config.NumberColumn("ID", disabled=True, width="small", help="Uniek ID"),
        "name":       st.column_config.TextColumn("Naam", required=True),
        "sort_order": st.column_config.NumberColumn("Volgorde", min_value=0, step=1, format="%d", width="small"),
        "active":     st.column_config.CheckboxColumn("Actief", width="small"),
    }
    if column_config:
        base_cfg.update(column_config)

    # Volgorde afdwingen
    if column_order:
        ordered_keys = [k for k in column_order if k in base_cfg] + [k for k in base_cfg if k not in (column_order)]
    else:
        # Fallback: logische volgorde
        default_order = ["name", "active", "sort_order", "id"]
        ordered_keys = [k for k in default_order if k in base_cfg] + [k for k in base_cfg if k not in default_order]

    # --------------------
    # Editor
    # --------------------
    edited = st.data_editor(
        view,
        key=f"editor_{Model.__name__}",
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config=base_cfg,
        column_order=ordered_keys,
    )

    # --------------------
    # Toevoegen
    # --------------------
    if allow_add:
        with st.popover("➕ Nieuw item"):
            ncol = st.columns([3, 2, 2])
            with ncol[0]:
                new_name = st.text_input("Naam", "")
            with ncol[1]:
                # default naar hoogste huidige sort_order + 10 of 100
                next_order = (max((int(x.get("sort_order") or 0) for x in data), default=90) + 10)
                new_order = st.number_input("Volgorde", 0, 9999, value=next_order, step=1)
            with ncol[2]:
                new_active = st.checkbox("Actief", True)
            if st.button("Toevoegen", type="primary", use_container_width=True):
                nm = (new_name or "").strip()
                if not nm:
                    st.warning("Naam is verplicht.")
                else:
                    with get_session() as s:
                        # Case-insensitive uniekheidscheck
                        exists = s.exec(select(Model).where(getattr(Model, unique_field) == nm)).first()
                        if exists:
                            st.error("Bestaat al.")
                        else:
                            extra = defaults_on_add or {}   # 🔽 toepassen
                            rec = Model(
                                name=nm,
                                sort_order=int(new_order),
                                active=bool(new_active),
                                **extra
                            )
                            s.add(rec); s.commit()
                    st.rerun()

    # --------------------
    # Verwijderen
    # --------------------
    if allow_delete:
        del_name = st.text_input("Naam om te verwijderen", "")
        if st.button("Verwijderen") and (del_name or "").strip():
            with get_session() as s:
                rec = s.exec(select(Model).where(getattr(Model, unique_field) == del_name.strip())).first()
                if rec:
                    s.delete(rec); s.commit()
                    st.success("Verwijderd.")
                    st.rerun()
                else:
                    st.info("Niet gevonden.")

    # --------------------
    # Opslaan
    # --------------------
    if st.button("💾 Opslaan wijzigingen", type="primary"):
        with get_session() as s:
            for row in edited:
                rid = row.get("id")
                if not rid:
                    continue
                rec = s.get(Model, rid)
                if not rec:
                    continue

                # Standaardvelden
                if "name" in row:       rec.name = row["name"]
                if "sort_order" in row: rec.sort_order = int(row["sort_order"] or 0)
                if "active" in row:     rec.active = bool(row["active"])

                # Extra velden (die in column_config zijn meegegeven en in data aanwezig zijn)
                if column_config:
                    for k in column_config.keys():
                        if k in ("id", "name", "sort_order", "active"):
                            continue
                        if k in row:
                            setattr(rec, k, row[k])

                s.add(rec)
            s.commit()
        st.success("Wijzigingen opgeslagen.")
        st.rerun()
