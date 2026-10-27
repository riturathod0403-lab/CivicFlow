"""
CivicFlow - Municipal Administrator Portal (pages_admin.py)
Implements:
1. Dashboard and Statistics (Plotly interactive charts)
2. Complaint Management and Department Assignment
3. AI Review and Duplicate Detection
4. Reports and Analytics (CSV export)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database import (
    get_all_complaints, get_complaint_by_id, get_status_history,
    update_department_assignment, update_complaint_status, resolve_ai_review
)

DEPARTMENTS = [
    "Roads & Infrastructure",
    "Solid Waste Management",
    "Electrical & Lighting",
    "Drainage & Stormwater",
    "Water Works & Supply",
    "Public Health & Sanitation",
    "General Administration"
]

CATEGORIES = ["potholes", "garbage", "streetlights", "drainage", "water_supply", "sanitation", "other"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
STATUSES = ["Pending", "Assigned", "In Progress", "Resolved", "Rejected"]

def render_admin_portal(user: dict):
    st.title("🏛️ Municipal Administrator Portal")
    st.caption("Central Operations & Oversight: Real-time city analytics, automated triage audit, and department routing.")

    section = st.sidebar.radio(
        "Admin Navigation",
        [
            "1. Dashboard & Statistics",
            "2. Complaint Management & Assignment",
            "3. AI Review & Duplicate Queue",
            "4. Reports & Analytics"
        ],
        index=0
    )

    all_complaints = get_all_complaints()
    df = pd.DataFrame(all_complaints) if all_complaints else pd.DataFrame()

    # ---------------------------------------------------------
    # SECTION 1: Dashboard and Statistics
    # ---------------------------------------------------------
    if section == "1. Dashboard & Statistics":
        st.subheader("City-wide Municipal Dashboard")

        if df.empty:
            st.info("No complaints found in the database.")
            return

        total = len(df)
        pending = len(df[df["status"] == "Pending"])
        in_progress = len(df[df["status"] == "In Progress"])
        resolved = len(df[df["status"] == "Resolved"])
        review_needed = len(df[(df["needs_review"] == 1) | (df["duplicate_of"].notna())])

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Complaints", total)
        col2.metric("Pending Triage", pending, delta=f"{pending/total*100:.0f}%" if total else "0%")
        col3.metric("In Progress", in_progress)
        col4.metric("Resolved", resolved, delta=f"{resolved/total*100:.0f}% rate" if total else "0%")
        col5.metric("AI Review Queue", review_needed, delta_color="inverse")

        st.markdown("---")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("##### 📊 Complaints by Category")
            cat_counts = df["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            fig_cat = px.bar(cat_counts, x="Category", y="Count", color="Category", title="Distribution by Category")
            st.plotly_chart(fig_cat, use_container_width=True)

        with chart_col2:
            st.markdown("##### 🎯 Complaints by Status")
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig_status = px.pie(status_counts, names="Status", values="Count", title="Resolution Status Pipeline", hole=0.4)
            st.plotly_chart(fig_status, use_container_width=True)

        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            st.markdown("##### ⚡ Priority Distribution")
            prio_counts = df["priority"].value_counts().reindex(PRIORITIES).fillna(0).reset_index()
            prio_counts.columns = ["Priority", "Count"]
            fig_prio = px.bar(prio_counts, x="Priority", y="Count", color="Priority",
                             color_discrete_map={"Low": "#22c55e", "Medium": "#eab308", "High": "#f97316", "Critical": "#ef4444"})
            st.plotly_chart(fig_prio, use_container_width=True)

        with chart_col4:
            st.markdown("##### 🏢 Department Workload")
            dept_counts = df["department"].value_counts().reset_index()
            dept_counts.columns = ["Department", "Tickets"]
            fig_dept = px.bar(dept_counts, x="Tickets", y="Department", orientation="h", title="Workload per Department")
            st.plotly_chart(fig_dept, use_container_width=True)

    # ---------------------------------------------------------
    # SECTION 2: Complaint Management & Department Assignment
    # ---------------------------------------------------------
    elif section == "2. Complaint Management & Assignment":
        st.subheader("Complaint Management & Department Routing")

        if df.empty:
            st.info("No complaints found.")
            return

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            search_query = st.text_input("🔍 Search Title / Location / ID", placeholder="Search...")
        with col_f2:
            dept_filter = st.selectbox("Filter Department", ["All"] + DEPARTMENTS)
        with col_f3:
            status_filter = st.selectbox("Filter Status", ["All"] + STATUSES)

        filtered_df = df.copy()
        if search_query:
            q = search_query.lower()
            filtered_df = filtered_df[
                filtered_df["id"].str.lower().str.contains(q) |
                filtered_df["title"].str.lower().str.contains(q) |
                filtered_df["location"].str.lower().str.contains(q)
            ]
        if dept_filter != "All":
            filtered_df = filtered_df[filtered_df["department"] == dept_filter]
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df["status"] == status_filter]

        st.dataframe(
            filtered_df[["id", "title", "category", "department", "priority", "status", "ward", "created_at"]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.markdown("#### 🛠️ Manage / Reassign Ticket")

        c_options = {f"{c['id']} - {c['title']}": c['id'] for c in all_complaints}
        selected_key = st.selectbox("Select Ticket to Reassign or Update", list(c_options.keys()))
        selected_id = c_options[selected_key]
        c_detail = get_complaint_by_id(selected_id)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(f"**Ticket ID:** `{c_detail['id']}`")
            st.markdown(f"**Citizen:** {c_detail['citizen_name']}")
            st.markdown(f"**Description:** {c_detail['description']}")
            st.markdown(f"**Location:** {c_detail['location']} ({c_detail['ward']})")
            st.markdown(f"**Current Status:** `{c_detail['status']}`")

        with col_m2:
            with st.form("form_reassign"):
                new_dept = st.selectbox(
                    "Assign to Department",
                    DEPARTMENTS,
                    index=DEPARTMENTS.index(c_detail["department"]) if c_detail["department"] in DEPARTMENTS else 0
                )
                override_status = st.selectbox(
                    "Override Status (Optional)",
                    STATUSES,
                    index=STATUSES.index(c_detail["status"])
                )
                admin_notes = st.text_input("Assignment Directive / Notes", placeholder="e.g. Priority dispatch to ward unit.")
                submit_assign = st.form_submit_button("Update Department & Status")

                if submit_assign:
                    if new_dept != c_detail["department"]:
                        update_department_assignment(selected_id, new_dept, user["id"], user["full_name"], admin_notes)
                    if override_status != c_detail["status"]:
                        update_complaint_status(selected_id, override_status, user["id"], user["full_name"], f"Admin status override: {admin_notes}")
                    st.success("Ticket updated successfully!")
                    st.rerun()

    # ---------------------------------------------------------
    # SECTION 3: AI Review and Duplicate Detection
    # ---------------------------------------------------------
    elif section == "3. AI Review & Duplicate Queue":
        st.subheader("🤖 AI Review & Duplicate Resolution Queue")
        st.caption(
            "Tickets flagged because of low AI confidence score (<60%) or high TF-IDF cosine duplicate similarity (>60%)."
        )

        review_queue = [
            c for c in all_complaints
            if (c.get("needs_review") == 1 or c.get("duplicate_of") or c.get("similarity_score", 0) > 0.5)
        ]

        if not review_queue:
            st.success("✅ AI Queue is clean! All tickets have high confidence and no pending duplicate flags.")
            return

        st.warning(f"**{len(review_queue)} tickets require administrator verification.**")

        for c in review_queue:
            with st.expander(f"⚠️ [{c['id']}] {c['title']} — Conf: {c.get('confidence_score', 0)*100:.0f}% | Dup Match: {c.get('duplicate_of') or 'None'}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### 📝 Incoming Ticket Details")
                    st.markdown(f"**Citizen Description:**\n{c['description']}")
                    st.markdown(f"**Location:** {c['location']} ({c['ward']})")
                    st.markdown(f"**AI Predicted Category:** `{c['category']}` (Confidence: {c.get('confidence_score', 0)*100:.1f}%)")
                    st.markdown(f"**Assigned Department:** `{c['department']}`")
                    st.markdown(f"**Calculated Priority:** `{c['priority']}`")

                with col2:
                    st.markdown("##### 🔍 Duplicate Detection Analysis")
                    if c.get("duplicate_of"):
                        parent = get_complaint_by_id(c["duplicate_of"])
                        st.markdown(f"**Linked Parent Ticket:** `{c['duplicate_of']}`")
                        st.markdown(f"**Similarity Score:** `{c.get('similarity_score', 0)*100:.1f}%`")
                        if parent:
                            st.info(f"**Parent Description ({parent['id']}):**\n{parent['description']}\n\n*Status:* {parent['status']}")
                    else:
                        st.markdown("No direct parent match; flagged for manual classification due to ambiguous text.")

                st.markdown("##### ✍️ Administrator Decision")
                col_act1, col_act2, col_act3 = st.columns(3)

                with col_act1:
                    correct_cat = st.selectbox(f"Confirm Category for {c['id']}", CATEGORIES, index=CATEGORIES.index(c['category']) if c['category'] in CATEGORIES else 0, key=f"cat_{c['id']}")
                with col_act2:
                    correct_prio = st.selectbox(f"Confirm Priority for {c['id']}", PRIORITIES, index=PRIORITIES.index(c['priority']) if c['priority'] in PRIORITIES else 1, key=f"prio_{c['id']}")
                with col_act3:
                    correct_dept = st.selectbox(f"Department for {c['id']}", DEPARTMENTS, index=DEPARTMENTS.index(c['department']) if c['department'] in DEPARTMENTS else 0, key=f"dept_{c['id']}")

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button(f"✅ Approve & Dispatch Ticket {c['id']}", key=f"approve_{c['id']}"):
                        resolve_ai_review(c["id"], correct_cat, correct_prio, correct_dept, is_duplicate=False)
                        st.success(f"Ticket {c['id']} approved and dispatched to {correct_dept}.")
                        st.rerun()

                with btn_col2:
                    if c.get("duplicate_of"):
                        if st.button(f"🔗 Merge as Duplicate into {c['duplicate_of']}", key=f"merge_{c['id']}"):
                            resolve_ai_review(c["id"], correct_cat, correct_prio, correct_dept, is_duplicate=True, duplicate_parent_id=c["duplicate_of"])
                            st.warning(f"Ticket {c['id']} marked as duplicate of {c['duplicate_of']} and archived.")
                            st.rerun()

    # ---------------------------------------------------------
    # SECTION 4: Reports and Analytics
    # ---------------------------------------------------------
    elif section == "4. Reports & Analytics":
        st.subheader("Municipal Reports & CSV Export")
        st.caption("Generate operational summaries and export complaint records for civic audits.")

        if df.empty:
            st.info("No complaint records available.")
            return

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            export_dept = st.selectbox("Select Department Scope", ["All Departments"] + DEPARTMENTS)
        with col_r2:
            export_status = st.selectbox("Select Status Scope", ["All Statuses"] + STATUSES)

        export_df = df.copy()
        if export_dept != "All Departments":
            export_df = export_df[export_df["department"] == export_dept]
        if export_status != "All Statuses":
            export_df = export_df[export_df["status"] == export_status]

        st.markdown(f"**Records matching criteria:** {len(export_df)}")

        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Municipal Complaints CSV Report",
            data=csv_data,
            file_name="civicflow_municipal_report.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("##### Summary Table")
        st.dataframe(
            export_df[["id", "title", "category", "department", "priority", "status", "location", "created_at"]],
            use_container_width=True,
            hide_index=True
        )
