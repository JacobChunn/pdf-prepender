"""Pytest fixtures for pdf_prepender tests."""

import io
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Create a simple multi-page PDF for testing."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)

    # Create 10 pages with visible page numbers
    for i in range(1, 11):
        c.setFont("Helvetica-Bold", 48)
        c.drawCentredString(306, 400, f"Page {i}")
        c.setFont("Helvetica", 12)
        c.drawCentredString(306, 350, f"This is the original document page {i}")
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_pdf_path(tmp_path: Path, sample_pdf_bytes: bytes) -> Path:
    """Create a sample PDF file and return its path."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(sample_pdf_bytes)
    return pdf_path


@pytest.fixture
def simple_spec_dict() -> dict:
    """Create a simple specification dictionary for testing."""
    return {
        "defaults": {
            "fontSize": 11,
            "boldMarker": "**",
            "italicMarker": "_",
            "pageSize": "letter",
        },
        "pages": [
            {
                "pageHeading": {
                    "text": "Document Summary",
                    "fontSize": 18,
                    "bold": True,
                    "alignment": "center",
                },
                "content": [
                    {"type": "sectionHeading", "text": "Key References"},
                    {
                        "type": "bulletPoint",
                        "label": "**Lab Results:**",
                        "content": [
                            {"text": "Blood Panel", "targetPage": 5},
                            {"text": "Metabolic Panel", "targetPage": 8},
                        ],
                        "overflowBehavior": "wrap",
                    },
                ],
            }
        ],
    }


@pytest.fixture
def multi_page_spec_dict() -> dict:
    """Create a multi-page specification dictionary for testing."""
    return {
        "defaults": {"fontSize": 11},
        "pages": [
            {
                "pageHeading": {"text": "Table of Contents", "bold": True},
                "content": [
                    {"type": "sectionHeading", "text": "Introduction"},
                    {
                        "type": "bulletPoint",
                        "label": "Overview:",
                        "content": [{"text": "See page 3", "targetPage": 3}],
                    },
                ],
            },
            {
                "pageHeading": {"text": "Summary"},
                "content": [
                    {"type": "sectionHeading", "text": "Key Findings"},
                    {
                        "type": "bulletPoint",
                        "label": "Results:",
                        "content": [
                            {"text": "Page 5", "targetPage": 5},
                            {"text": "Page 7", "targetPage": 7},
                        ],
                    },
                ],
            },
        ],
    }


@pytest.fixture
def spec_with_all_elements() -> dict:
    """Create a specification with all element types for testing."""
    return {
        "defaults": {
            "fontSize": 11,
            "boldMarker": "**",
            "italicMarker": "_",
        },
        "pages": [
            {
                "pageHeading": {
                    "text": "Complete Example",
                    "fontSize": 20,
                    "bold": True,
                    "alignment": "center",
                },
                "content": [
                    {
                        "type": "sectionHeading",
                        "text": "Section One",
                        "bold": True,
                    },
                    {
                        "type": "sectionSubheading",
                        "text": "Additional context here",
                        "italic": True,
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Important:**",
                        "content": ["Plain text item"],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "Links:",
                        "content": [
                            {"text": "First link", "targetPage": 2},
                            {"text": "Second link", "targetPage": 4},
                        ],
                    },
                    {
                        "type": "indentedBulletPoint",
                        "label": "Sub-item:",
                        "content": ["Indented content"],
                    },
                ],
            }
        ],
    }
