"""
CivicFlow - Department Staff Portal (pages_staff.py)
Implements:
1. Assigned Complaints (Strictly filtered by staff user's department)
2. Update Progress and Resolution Notes
"""

import streamlit as st
import pandas as pd
from database import (
    get_complaints_by_department, get_complaint_by_id,
    get_status_history, update_complaint_status
)

STATUS_OPTIONS = ["In Progress", "Resolved", "Rejected"]

def render_staff_portal(user: dict):
    department = user.get("department", "Roads & Infrastructure")
    st.title(f"🛠️ {department} Portal")
    st.caption(f"Staff Console: Manage field work orders, update resolution stages, and file field notes.")

    section = st.sidebar.radio(
        "Staff Navigation",
        ["1. Assigned Complaints", "2. Update Progress & Notes"],
        index=0
    )

    dept_complaints = get_complaints_by_department(department)

    # ---------------------------------------------------------
    # SECTION 1: Assigned Complaints
    # ---------------------------------------------------------
    if section == "1. Assigned Complaints":
        st.subheader(f"Active Complaints Assigned to {department}")

        if not dept_complaints:
            st.info(f"No complaints currently assigned to {department}. Good job!")
            return

        # Metrics
        c_pending = len([c for c in dept_complaints if c["status"] in ["Pending", "Assigned"]])
        c_progress = len([c for c in dept_complaints if c["status"] == "In Progress"])
        c_resolved = len([c for c in dept_complaints if c["status"] == "Resolved"])

        m1, m2, m3 = st.columns(3)
        m1.metric("Pending Dispatch / Action", c_pending)
        m2.metric("Under Field Work", c_progress)
        m3.metric("Resolved", c_resolved)

        st.markdown("---")

        # Filters
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            status_f = st.selectbox("Filter Status", ["All", "Pending", "Assigned", "In Progress", "Resolved", "Rejected"])
        with f_col2:
            prio_f = st.selectbox("Filter Priority", ["All", "Critical", "High", "Medium", "Low"])

        filtered = dept_complaints
        if status_f != "All":
            filtered = [c for c in filtered if c["status"] == status_f]
        if prio_f != "All":
            filtered = [c for c in filtered if c["priority"] == prio_f]

        st.caption(f"Showing {len(filtered)} complaints")

        for c in filtered:
            with st.expander(f"📍 [{c['id']}] {c['title']} — Priority: {c['priority']} | Status: {c['status']}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Citizen Description:**\n{c['description']}")
                    st.markdown(f"**Location / Landmark:** {c['location']} ({c['ward']})")
                with col2:
                    st.markdown(f"**Reported by:** {c['citizen_name']}")
                    st.markdown(f"**Date Reported:** {c['created_at']}")
                    if c.get("resolution_notes"):
                        st.markdown(f"**Latest Field Note:**\n_{c['resolution_notes']}_")

    # ---------------------------------------------------------
    # SECTION 2: Update Progress and Resolution Notes
    # ---------------------------------------------------------
    elif section == "2. Update Progress & Notes":
        st.subheader("Update Ticket Progress & Field Action")

        active_tickets = [c for c in dept_complaints if c["status"] != "Resolved"]
        all_options = active_tickets if active_tickets else dept_complaints

        if not all_options:
            st.info("No tickets available for status updates.")
            return

        t_map = {f"{c['id']} - {c['title']} ({c['status']})": c['id'] for c in all_options}
        chosen_key = st.selectbox("Select Complaint to Update", list(t_map.keys()))
        chosen_id = t_map[chosen_key]
        comp = get_complaint_by_id(chosen_id)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**Ticket ID:** `{comp['id']}`")
            st.markdown(f"**Citizen:** {comp['citizen_name']}")
            st.markdown(f"**Description:** {comp['description']}")
            st.markdown(f"**Location:** {comp['location']} ({comp['ward']})")
            st.markdown(f"**Current Status:** `{comp['status']}`")
            st.markdown(f"**Priority:** `{comp['priority']}`")

        with col_d2:
            with st.form("form_update_progress"):
                new_status = st.selectbox("Update Status", STATUS_OPTIONS, index=0)
                resolution_notes = st.text_area(
                    "Field Work Notes / Action Report *",
                    placeholder="e.g. Crew arrived on site at 10:30 AM. Repair completed using 2.5 tons cold asphalt mix. Area restored to safe traffic.",
                    height=120
                )
                submit_update = st.form_submit_button("Submit Work Order Update", type="primary")

                if submit_update:
                    if not resolution_notes.strip():
                        st.error("Please enter descriptive field notes explaining the work undertaken.")
                    else:
                        ok, msg = update_complaint_status(
                            chosen_id,
                            new_status,
                            user["id"],
                            f"{user['full_name']} ({department})",
                            resolution_notes.strip()
                        )
                        if ok:
                            st.success(f"Ticket {chosen_id} successfully updated to '{new_status}'!")
                            st.rerun()
                        else:
                            st.error(msg)

        # Audit History
        st.markdown("##### ⏱️ Complaint Audit History")
        hist = get_status_history(chosen_id)
        if hist:
            for h in hist:
                st.caption(f"• **{h['timestamp']}** — `{h.get('previous_status') or 'Created'}` ➔ `{h['new_status']}` by *{h['updated_by_name']}*: {h.get('notes', '')}")
