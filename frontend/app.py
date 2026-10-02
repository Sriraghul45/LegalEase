from __future__ import annotations

import os
from datetime import date
from datetime import datetime

import requests
import streamlit as st
from dotenv import load_dotenv

from backend.services.document_formatter import (
    format_docx,
    format_html_preview,
    format_pdf,
    format_txt,
)

load_dotenv()

st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.markdown(
    """
    <style>
    .block-container {max-width: 1200px; padding-top: 2.5rem; padding-bottom: 3rem;}
    .hero {padding: 1.6rem 1.7rem; border: 1px solid #2d3748; border-radius: 18px;
           background: linear-gradient(135deg, #111827, #1a2333); margin-bottom: 1.1rem;
           box-shadow: 0 10px 25px rgba(15, 23, 42, 0.18);}
    .hero h1 {margin: 0; color: #f8fafc; font-size: 2.4rem; letter-spacing: -0.03em;}
    .hero p {margin: .5rem 0 0; color: #cbd5e1; font-size: 1rem;}
    .notice {padding: .8rem 1rem; border-radius: 12px; background: #2a2110; border: 1px solid #6b511b;
             color: #f4d78a; font-size: 0.96rem; line-height: 1.55; margin-bottom: 1.1rem;}
    .preview {background:#0f172a; border:1px solid #334155; border-radius:14px; padding:1.5rem;
              color:#e2e8f0; max-height:700px; overflow:auto; line-height:1.7; font-size:1.02rem;
              box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.05);}
    .preview p {margin: 0 0 1rem; color: #e2e8f0;}
    .preview h1, .preview h2, .preview h3 {color: #f8fafc; margin-top: 1.1rem; margin-bottom: 0.5rem;}
    .preview strong {color: #f8fafc;}
    div[data-testid="stSidebar"] {background: #0f172a;}
    .stButton > button {border-radius: 12px; font-weight: 600; padding: 0.7rem 1rem;}
    .stButton > button:disabled {opacity: 0.6; cursor: not-allowed;}
    .section-label {color: #cbd5e1; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>⚖️ LegalEase</h1><p>AI-powered legal document drafting, editing and export.</p></div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="notice">Drafting assistant only — review generated documents with a qualified legal professional before signing or relying on them.</div>',
    unsafe_allow_html=True,
)

if "document" not in st.session_state:
    st.session_state.document = ""
if "document_type" not in st.session_state:
    st.session_state.document_type = ""
if "generation_in_progress" not in st.session_state:
    st.session_state.generation_in_progress = False


def parse_effective_date(value: str):
    cleaned = value.strip()
    if not cleaned:
        return None

    for fmt in ("%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(cleaned).date()
    except ValueError:
        return None


def validate_form(document_type: str, parties: str, terms: str, effective_date: str):
    if not document_type or not document_type.strip():
        return "Please choose a document type before generating."
    if not parties or not parties.strip():
        return "Please enter the parties involved."
    if not terms or not terms.strip():
        return "Please enter the terms and conditions."
    if not effective_date or not effective_date.strip():
        return "Please enter an effective date."

    parsed_date = parse_effective_date(effective_date)
    if parsed_date is None:
        return "Effective date is invalid. Please use a valid date like October 2, 2026."

    return None

with st.sidebar:
    st.header("Document Details")
    st.caption("Required fields: document type, parties, terms, and effective date.", unsafe_allow_html=False)
    document_type = st.selectbox(
        "Document type",
        [
            "Employment Contract",
            "Non-Disclosure Agreement (NDA)",
            "Lease Agreement",
            "Freelance Work Contract",
            "Employment Offer Letter",
            "Service Agreement",
            "General Agreement",
            "Custom",
        ],
    )
    if document_type == "Custom":
        document_type = st.text_input("Custom document type", placeholder="e.g. Partnership Agreement")

    parties = st.text_area(
        "Parties involved",
        placeholder="Jane Doe (Service Provider), TechNova Inc. (Client)",
        height=110,
    )
    terms = st.text_area(
        "Terms & conditions",
        placeholder="Payment within 30 days;Confidentiality must be maintained;Either party may terminate with 15 days notice",
        height=170,
        help="Separate each condition with a semicolon.",
    )
    effective_date = st.text_input(
        "Effective date",
        value=date.today().strftime("%B %d, %Y"),
    )

    generate = st.button(
        "✨ Generate Document",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.generation_in_progress,
    )

if generate:
    validation_error = validate_form(document_type, parties, terms, effective_date)
    if validation_error:
        st.error(validation_error)
    else:
        st.session_state.generation_in_progress = True
        payload = {
            "document_type": document_type.strip(),
            "parties": parties.strip(),
            "terms": terms.strip(),
            "effective_date": effective_date.strip(),
        }
        with st.spinner("Generating your legal draft..."):
            try:
                response = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=120)
                if response.ok:
                    data = response.json()
                    st.session_state.document = data["content"]
                    st.session_state.document_type = data["document_type"]
                    st.success("Document generated successfully.")
                else:
                    try:
                        detail = response.json().get("detail", response.text)
                    except ValueError:
                        detail = response.text
                    st.error(f"Backend error ({response.status_code}): {detail}")
            except requests.RequestException:
                st.error("Could not reach the FastAPI backend. Please make sure the backend is running and try again.")
            finally:
                st.session_state.generation_in_progress = False

if st.session_state.document:
    st.subheader("Document Preview")
    tab_preview, tab_edit = st.tabs(["Preview", "Edit"])

    with tab_preview:
        st.markdown(
            f'<div class="preview">{format_html_preview(st.session_state.document)}</div>',
            unsafe_allow_html=True,
        )

    with tab_edit:
        edited = st.text_area(
            "Edit the generated document",
            value=st.session_state.document,
            height=620,
            key="editor",
        )
        if st.button("Save Edits", use_container_width=True):
            st.session_state.document = edited
            st.success("Edits saved to the current session.")

    st.subheader("Download")
    current_text = st.session_state.document
    current_type = st.session_state.document_type or "legal_document"
    safe_name = "".join(ch.lower() if ch.isalnum() else "_" for ch in current_type).strip("_")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "⬇️ Download TXT",
            data=format_txt(current_text),
            file_name=f"{safe_name}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇️ Download DOCX",
            data=format_docx(current_text, current_type, terms),
            file_name=f"{safe_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "⬇️ Download PDF",
            data=format_pdf(current_text, current_type),
            file_name=f"{safe_name}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
else:
    st.info("Enter your details in the sidebar and click Generate Document.")
