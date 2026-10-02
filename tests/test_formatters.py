from backend.services.document_formatter import (
    format_docx,
    format_html_preview,
    format_pdf,
    format_txt,
    sanitize_text,
)


def test_sanitize_text():
    assert sanitize_text("Hello — “world”") == 'Hello - "world"'


def test_txt_export():
    assert format_txt("Hello") == b"Hello"


def test_html_escapes_user_content():
    html = format_html_preview("<script>alert(1)</script>")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_docx_export_returns_bytes():
    data = format_docx("SECTION 1\nHello world", "Test Agreement", "Payment within 30 days")
    assert data[:2] == b"PK"
    assert len(data) > 1000


def test_pdf_export_returns_pdf():
    data = format_pdf("SECTION 1\nHello world", "Test Agreement")
    assert data.startswith(b"%PDF")
    assert len(data) > 500
