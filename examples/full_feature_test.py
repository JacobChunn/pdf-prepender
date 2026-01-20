"""Full feature test for pdf_prepender library.

This script creates a PDF that demonstrates ALL features:
- Page headings (with alignment, bold, italic, font size)
- Section headings
- Section subheadings
- Bullet points with plain text
- Bullet points with linkable items (to specific pages)
- Indented bullet points
- Bold/italic text formatting with markers (**bold**, _italic_)
- Multiple prepended pages
- Overflow behaviors
"""

import io
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from pdf_prepender import DocumentBuilder


def create_sample_document() -> bytes:
    """Create a 10-page sample document with visible content."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)

    pages_content = [
        ("Introduction", "Welcome to the sample document"),
        ("Background", "Historical context and overview"),
        ("Lab Results - Blood Panel", "Complete blood count and analysis"),
        ("Lab Results - Metabolic", "Comprehensive metabolic panel"),
        ("Imaging Studies", "X-ray and MRI findings"),
        ("Clinical Notes", "Physician observations"),
        ("Treatment Plan", "Recommended interventions"),
        ("Medications", "Current prescription list"),
        ("Follow-up Schedule", "Upcoming appointments"),
        ("References", "Supporting documentation"),
    ]

    for i, (title, subtitle) in enumerate(pages_content, 1):
        # Large page number
        c.setFont("Helvetica-Bold", 120)
        c.setFillColorRGB(0.9, 0.9, 0.9)  # Light gray
        c.drawCentredString(306, 500, str(i))

        # Title
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(306, 400, title)

        # Subtitle
        c.setFont("Helvetica", 14)
        c.drawCentredString(306, 370, subtitle)

        # Page indicator
        c.setFont("Helvetica", 10)
        c.drawCentredString(306, 50, f"Original Document - Page {i} of 10")

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def main():
    """Generate a PDF demonstrating all features."""

    # Comprehensive specification using ALL features
    spec = {
        "defaults": {
            "fontSize": 11,
            "boldMarker": "**",
            "italicMarker": "_",
            "pageSize": "letter",
        },
        "pages": [
            # PAGE 1: Table of Contents
            {
                "pageHeading": {
                    "text": "TABLE OF CONTENTS",
                    "fontSize": 22,
                    "bold": True,
                    "alignment": "center",
                },
                "content": [
                    {
                        "type": "sectionHeading",
                        "text": "Document Overview",
                        "bold": True,
                    },
                    {
                        "type": "sectionSubheading",
                        "text": "Quick navigation to key sections",
                        "italic": True,
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Introduction:**",
                        "content": [
                            {"text": "Go to Introduction", "targetPage": 1},
                        ],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Lab Results:**",
                        "content": [
                            {"text": "Blood Panel (p.3)", "targetPage": 3},
                            {"text": "Metabolic Panel (p.4)", "targetPage": 4},
                        ],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Imaging:**",
                        "content": [
                            {"text": "X-ray & MRI Studies", "targetPage": 5},
                        ],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Clinical:**",
                        "content": [
                            {"text": "Notes", "targetPage": 6},
                            {"text": "Treatment", "targetPage": 7},
                            {"text": "Medications", "targetPage": 8},
                        ],
                    },
                    {
                        "type": "indentedBulletPoint",
                        "label": "_Note:_",
                        "content": ["Page numbers refer to the original document"],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Appendix:**",
                        "content": [
                            {"text": "Follow-up Schedule", "targetPage": 9},
                            {"text": "References", "targetPage": 10},
                        ],
                    },
                ],
            },
            # PAGE 2: Executive Summary
            {
                "pageHeading": {
                    "text": "EXECUTIVE SUMMARY",
                    "fontSize": 20,
                    "bold": True,
                    "alignment": "center",
                },
                "content": [
                    {
                        "type": "sectionHeading",
                        "text": "Key Findings",
                        "fontSize": 14,
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Blood Work:**",
                        "content": [
                            "All values within normal ranges",
                            {"text": "See detailed results", "targetPage": 3},
                        ],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Metabolic Panel:**",
                        "content": [
                            "Kidney and liver function normal",
                            {"text": "View panel", "targetPage": 4},
                        ],
                    },
                    {
                        "type": "indentedBulletPoint",
                        "label": "_Glucose:_",
                        "content": ["95 mg/dL (normal range: 70-100)"],
                    },
                    {
                        "type": "indentedBulletPoint",
                        "label": "_Creatinine:_",
                        "content": ["1.0 mg/dL (normal range: 0.7-1.3)"],
                    },
                    {
                        "type": "sectionHeading",
                        "text": "Imaging Results",
                        "fontSize": 14,
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**X-Ray:**",
                        "content": [
                            "No acute findings",
                            {"text": "View images", "targetPage": 5},
                        ],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**MRI:**",
                        "content": [
                            "Minor degenerative changes noted",
                        ],
                    },
                    {
                        "type": "sectionHeading",
                        "text": "Recommendations",
                        "fontSize": 14,
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Treatment:**",
                        "content": [
                            "Continue current medications",
                            {"text": "See treatment plan", "targetPage": 7},
                        ],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Follow-up:**",
                        "content": [
                            "Return in 6 months",
                            {"text": "View schedule", "targetPage": 9},
                        ],
                    },
                    {
                        "type": "indentedBulletPoint",
                        "label": "_Important:_",
                        "content": [
                            "Call immediately if symptoms worsen",
                        ],
                    },
                ],
            },
            # PAGE 3: Formatting Showcase
            {
                "pageHeading": {
                    "text": "Text Formatting Examples",
                    "fontSize": 18,
                    "bold": True,
                    "italic": True,
                    "alignment": "left",
                },
                "content": [
                    {
                        "type": "sectionHeading",
                        "text": "Bold and Italic Markers",
                    },
                    {
                        "type": "sectionSubheading",
                        "text": "Demonstrating **bold** and _italic_ text formatting",
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Bold label:**",
                        "content": ["This label uses **bold** markers"],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "_Italic label:_",
                        "content": ["This label uses _italic_ markers"],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Mixed:**",
                        "content": [
                            "Text with **bold** and _italic_ in the same line"
                        ],
                    },
                    {
                        "type": "sectionHeading",
                        "text": "Links to Original Document",
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Quick Links:**",
                        "content": [
                            {"text": "Page 1", "targetPage": 1},
                            {"text": "Page 5", "targetPage": 5},
                            {"text": "Page 10", "targetPage": 10},
                        ],
                    },
                    {
                        "type": "sectionHeading",
                        "text": "Plain Text Content",
                    },
                    {
                        "type": "bulletPoint",
                        "label": "Simple:",
                        "content": ["Just plain text without any formatting"],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "Multiple items:",
                        "content": ["First item", "Second item", "Third item"],
                    },
                    {
                        "type": "indentedBulletPoint",
                        "label": "Indented:",
                        "content": ["This bullet point is indented"],
                    },
                    {
                        "type": "indentedBulletPoint",
                        "label": "Also indented:",
                        "content": ["With a **bold** word inside"],
                    },
                ],
            },
        ],
    }

    # Create the sample document
    print("Creating 10-page sample document...")
    original_pdf = create_sample_document()

    # Save original for comparison
    original_path = Path("test_original.pdf")
    original_path.write_bytes(original_pdf)
    print(f"  Saved: {original_path} (10 pages)")

    # Build the prepended document
    print("\nBuilding prepended document...")
    builder = DocumentBuilder.from_dict(spec)

    prepend_count = builder.get_prepend_page_count()
    print(f"  Prepending {prepend_count} pages")

    output_path = Path("test_full_features.pdf")
    result = builder.build(original_pdf)
    output_path.write_bytes(result)

    print(f"  Saved: {output_path} ({10 + prepend_count} pages)")

    # Verify the output
    from pypdf import PdfReader

    reader = PdfReader(output_path)
    print(f"\nVerification:")
    print(f"  Total pages: {len(reader.pages)}")
    print(f"  Named destinations: {len(reader.named_destinations)}")

    print("\n" + "=" * 60)
    print("FILES GENERATED:")
    print("=" * 60)
    print(f"  1. {original_path} - Original 10-page document")
    print(f"  2. {output_path} - With {prepend_count} prepended pages")
    print("\nOPEN 'test_full_features.pdf' TO VERIFY:")
    print("  - Page 1: Table of Contents with links")
    print("  - Page 2: Executive Summary with mixed content")
    print("  - Page 3: Formatting examples (bold, italic, links)")
    print("  - Pages 4-13: Original document content")
    print("\nLINK BEHAVIOR:")
    print("  - Links appear as blue underlined text")
    print("  - Named destinations exist for all pages")
    print("=" * 60)


if __name__ == "__main__":
    main()
