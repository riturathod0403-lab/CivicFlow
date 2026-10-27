"""
CivicFlow - Citizen Portal (pages_citizen.py)
Implements:
1. Home and Submit Complaint (AI Classification, Priority & Duplicate Check)
2. My Complaints and Status Tracking
3. Complaint Details and Citizen Feedback
"""

import streamlit as st
import pandas as pd
from database import (
    insert_complaint, get_complaints_by_user, get_all_complaints,
    get_complaint_by_id, get_status_history, add_citizen_feedback
)
from classifier import classify_complaint
from priority_engine import estimate_priority
from duplicate_detector import find_duplicates

WARDS = [
    "Ward 1 - Central Commercial",
    "Ward 2 - Industrial Zone",
    "Ward 3 - North Suburbs",
    "Ward 4 - Downtown Historic",
    "Ward 5 - South Riverside",
    "Ward 6 - University Quarter",
    "Ward 7 - Westside Residential",
    "Ward 8 - Tech Park Corridor",
    "Ward 9 - East Hills",
    "Ward 10 - Lakeview District"
]

def render_citizen_portal(user: dict):
    st.title("Citizen Civic Portal")
    st.caption("Submit civic issues, track real-time resolution progress, and provide service feedback.")

    section = st.sidebar.radio(
        "Navigation",
        ["1. Submit Complaint", "2. My Complaints & Tracking", "3. Complaint Feedback"],
        index=0
    )

    # ---------------------------------------------------------
    # SECTION 1: Home & Submit Complaint
    # ---------------------------------------------------------
    if section == "1. Submit Complaint":
        st.subheader("Submit a Municipal Complaint")
        st.markdown(
            "Submit your civic grievance directly to the municipal administration. "
            "Our municipal service dispatch will route it to the appropriate ward and field crew."
        )

        with st.form("form_submit_complaint"):
            title = st.text_input("Complaint Title *", placeholder="e.g., Deep dangerous pothole on 5th Cross Road")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                category_opt = st.selectbox(
                    "Complaint Category (Optional)",
                    ["Auto-assign based on description", "Potholes & Road Damage", "Garbage & Solid Waste", "Streetlights & Electricity", "Drainage & Sewerage", "Drinking Water Supply", "Sanitation & Public Health", "Other Municipal Issue"]
                )
            with col_c2:
                ward = st.selectbox("Municipal Ward *", WARDS)

            location = st.text_input("Specific Landmark / Street Address *", placeholder="e.g. Near St. Jude School Gate, 8th Avenue")
            description = st.text_area(
                "Detailed Description *",
                placeholder="Describe the civic issue, visible hazards, approximate dimensions, and how long it has persisted...",
                height=140
            )

            submit_btn = st.form_submit_button("🚀 Register Municipal Complaint", type="primary", use_container_width=True)

        if submit_btn:
            if not title or not description or not location:
                st.error("Please fill in all mandatory fields (Title, Description, and Location).")
            else:
                cat_map = {
                    "Potholes & Road Damage": "potholes",
                    "Garbage & Solid Waste": "garbage",
                    "Streetlights & Electricity": "streetlights",
                    "Drainage & Sewerage": "drainage",
                    "Drinking Water Supply": "water_supply",
                    "Sanitation & Public Health": "sanitation",
                    "Other Municipal Issue": "other"
                }
                cls_result = classify_complaint(description)
                cat = cat_map.get(category_opt, cls_result["category"])
                dept = cls_result["department"]
                pri_result = estimate_priority(description, cat)
                active_complaints = get_all_complaints()
                dup_result = find_duplicates(f"{title} {description}", active_complaints, threshold=0.60)

                complaint_payload = {
                    "user_id": user["id"],
                    "citizen_name": user["full_name"],
                    "title": title.strip(),
                    "description": description.strip(),
                    "category": cat,
                    "department": dept,
                    "priority": pri_result["priority"],
                    "status": "Pending",
                    "confidence_score": cls_result["confidence"],
                    "needs_review": cls_result["needs_review"],
                    "duplicate_of": dup_result["parent_id"] if dup_result["is_duplicate"] else None,
                    "similarity_score": dup_result["top_similarity"] if dup_result["is_duplicate"] else 0.0,
                    "location": location.strip(),
                    "ward": ward
                }

                cid = insert_complaint(complaint_payload)
                st.success(f"🎉 Complaint successfully registered! Your Tracking ID is: **{cid}**")
                st.info("You can view and track updates under 'My Complaints & Status Tracking'.")

    # ---------------------------------------------------------
    # SECTION 2: My Complaints and Status Tracking
    # ---------------------------------------------------------
    elif section == "2. My Complaints & Tracking":
        st.subheader("My Registered Complaints")
        user_complaints = get_complaints_by_user(user["id"])

        if not user_complaints:
            st.info("You have not filed any complaints yet. Use the 'Submit Complaint' section to file your first ticket.")
            return

        # Filters
        statuses = ["All"] + sorted(list(set(c["status"] for c in user_complaints)))
        filter_status = st.selectbox("Filter by Status", statuses)

        filtered = [c for c in user_complaints if filter_status == "All" or c["status"] == filter_status]

        st.caption(f"Showing {len(filtered)} complaints")

        for c in filtered:
            with st.expander(f"📌 [{c['id']}] {c['title']} — Status: {c['status']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Category:** {c['category'].title()}")
                    st.markdown(f"**Department:** {c['department']}")
                with col2:
                    st.markdown(f"**Priority:** {c['priority']}")
                    st.markdown(f"**Ward:** {c['ward']}")
                with col3:
                    st.markdown(f"**Filed on:** {c['created_at']}")
                    st.markdown(f"**Last Updated:** {c['updated_at']}")

                st.markdown(f"**Description:**\n{c['description']}")
                st.markdown(f"**Location:** {c['location']}")

                if c.get("resolution_notes"):
                    st.info(f"**Staff Resolution Notes:**\n{c['resolution_notes']}")

                # Status History Timeline
                st.markdown("##### ⏱️ Lifecycle Audit Trail")
                history = get_status_history(c["id"])
                if history:
                    for h in history:
                        prev = h["previous_status"] or "Created"
                        st.caption(f"• **{h['timestamp']}** — `{prev}` ➔ `{h['new_status']}` by *{h['updated_by_name']}* ({h.get('notes', '')})")

    # ---------------------------------------------------------
    # SECTION 3: Complaint Details and Feedback
    # ---------------------------------------------------------
    elif section == "3. Complaint Feedback":
        st.subheader("Complaint Resolution Feedback")
        st.caption("Provide citizen satisfaction ratings and comments on resolved municipal issues.")

        resolved = [c for c in get_complaints_by_user(user["id"]) if c["status"] == "Resolved"]

        if not resolved:
            st.info("You do not have any complaints in 'Resolved' status yet.")
            return

        complaint_opts = {f"{c['id']} - {c['title']}": c['id'] for c in resolved}
        selected_key = st.selectbox("Select Resolved Complaint to Review", list(complaint_opts.keys()))
        selected_id = complaint_opts[selected_key]
        comp = get_complaint_by_id(selected_id)

        st.markdown(f"**Complaint ID:** `{comp['id']}`")
        st.markdown(f"**Department:** `{comp['department']}`")
        st.markdown(f"**Staff Resolution Note:** {comp.get('resolution_notes', 'Resolved by department.')}")

        existing_rating = comp.get("citizen_rating")
        existing_feedback = comp.get("citizen_feedback")

        if existing_rating:
            st.success(f"Feedback already submitted: Rated {existing_rating} ⭐ with notes: \"{existing_feedback}\"")

        with st.form("form_feedback"):
            rating = st.slider("Citizen Satisfaction Rating (1: Very Unsatisfied, 5: Highly Satisfied)", 1, 5, existing_rating or 4)
            comments = st.text_area("Your Feedback / Remarks", value=existing_feedback or "")
            submit_feedback = st.form_submit_button("Submit Rating & Feedback")

            if submit_feedback:
                ok, msg = add_citizen_feedback(selected_id, user["id"], rating, comments)
                if ok:
                    st.success("Thank you! Your feedback helps us improve municipal service quality.")
                    st.rerun()
                else:
                    st.error(msg)
