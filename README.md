# LegalEase – AI-Powered Legal Document Drafting Assistant

## Overview

LegalEase is a web application that helps users create a first draft of a basic legal document from information they provide. It uses Google Gemini to generate the draft, then lets users review and edit the text and export it in common document formats.

## Problem Statement

Drafting even a basic agreement manually can take time and requires organizing the parties, terms, and effective date into a clear document. People may be unsure how to structure these details or where to begin. LegalEase provides a convenient way to turn supplied information into an editable starting draft; it does not replace legal advice.

## Objectives

- Make it straightforward to provide the information needed for a basic document draft.
- Use an AI model to turn user-provided details into organized draft text.
- Let users review and edit the result before exporting it.
- Support commonly used download formats from one interface.
- Handle invalid input and temporary generation-service availability problems with clear feedback.

## Key Features

- AI-powered legal document generation through the Google Gemini API.
- Multiple preset document types, with a custom document-type option.
- Form inputs for document type, parties, terms, and effective date.
- Loading indicator while a document is being generated.
- Friendly error messages and retry/fallback handling for temporary Gemini unavailability.
- Preview and edit the generated document in the app.
- Export drafts as TXT, DOCX, or PDF.
- Legal disclaimer reminding users that generated drafts require professional review.

Preset types include employment contracts, non-disclosure agreements, lease agreements, freelance work contracts, employment offer letters, service agreements, and general agreements. The custom option allows users to enter another document type.

## Technology Stack

- **Python** - application language
- **Streamlit** - user interface
- **FastAPI** - backend API
- **Google Gemini API** via the Google GenAI Python SDK - draft generation
- **python-docx** - DOCX export
- **fpdf2** - PDF generation
- **pytest** - automated tests

TXT export uses Python's built-in text and file handling.

## System Architecture

```text
User
  -> Streamlit UI
  -> FastAPI backend (/generate)
  -> Google Gemini API
  -> Generated document draft
  -> Review/edit in Streamlit
  -> TXT, DOCX, or PDF export
```

The Streamlit frontend collects and validates user input and sends the generation request to FastAPI. The backend calls Gemini and returns the generated text. The frontend presents the result for review and editing and creates the selected downloadable format.

## Project Structure

```text
LegalEase/
├── assets/
│   ├── legal_ease_logo.png
│   └── legal_ease_logo.svg
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── ai_core/
│   │   ├── __init__.py
│   │   └── gemini_generator.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── services/
│       ├── __init__.py
│       └── document_formatter.py
├── frontend/
│   └── app.py
├── tests/
│   ├── test_api.py
│   └── test_formatters.py
├── .env.example
├── .gitignore
├── .python-version
├── Procfile
├── README.md
└── requirements.txt
```

## Setup Instructions

Python 3.11 is recommended. Run commands from the project root.

### 1. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` in the project root. Add your own Gemini API key to `.env` and confirm the model setting:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FALLBACK_MODEL=gemini-3.5-flash
BACKEND_URL=http://127.0.0.1:8000
```

Keep `.env` private and do not commit it. The Gemini API key is used by the backend; do not place a real key in source code or in a public repository.

### 4. Start the FastAPI backend

In a terminal at the project root with the virtual environment active:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The API health endpoint is available at `http://127.0.0.1:8000/`, and interactive API documentation is at `http://127.0.0.1:8000/docs`.

### 5. Start the Streamlit frontend

Open a second terminal at the project root, activate the same virtual environment, and run:

```bash
streamlit run frontend/app.py
```

Streamlit normally opens at `http://localhost:8501`.

## Testing

The project includes automated API, Gemini-generator, and document-formatting tests. The latest recorded test run passed all 10 tests:

```bash
python -m pytest -q
```

The API tests mock Gemini generation, so running the automated tests does not require a live Gemini API call.

## Usage

1. Enter the document type, parties, terms, and effective date in the form.
2. Select **Generate Document** and wait for generation to complete.
3. Review the draft in the preview and edit it in the editor as needed. Save edits in the app before exporting.
4. Download the reviewed draft as TXT, DOCX, or PDF.

## Disclaimer

LegalEase generates drafts for informational and administrative use. It is not a substitute for advice from a qualified lawyer. LegalEase is a drafting assistant, not a source of legal advice. Generated documents should be reviewed by a qualified legal professional before signing or relying on them.

## Future Enhancements

Possible future improvements include additional document categories and jurisdiction-aware guidance, user accounts and saved draft history, collaborative review, and expanded automated testing of end-to-end workflows. These are suggestions only and are not features currently provided by the application.
