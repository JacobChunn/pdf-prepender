"""Basic usage example for pdf_prepender library.

This script demonstrates how to use the pdf_prepender library to:
1. Create a sample PDF (simulating an original document)
2. Define a JSON specification for pages to prepend
3. Prepend the new pages with clickable links to the original content
"""

import io
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from pdf_prepender import DocumentBuilder, prepend_pages


def create_sample_pdf() -> bytes:
    """Create a sample 10-page PDF to use as the original document."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)

    for i in range(1, 11):
        # Draw page number prominently
        c.setFont("Helvetica-Bold", 72)
        c.drawCentredString(306, 450, str(i))

        # Add page label
        c.setFont("Helvetica", 14)
        c.drawCentredString(306, 380, f"Original Document - Page {i}")

        # Add some content based on page
        c.setFont("Helvetica", 12)
        if i == 3:
            c.drawCentredString(306, 320, "Chapter 1: Introduction")
        elif i == 5:
            c.drawCentredString(306, 320, "Chapter 2: Lab Results - Blood Panel")
        elif i == 7:
            c.drawCentredString(306, 320, "Chapter 3: Analysis")
        elif i == 10:
            c.drawCentredString(306, 320, "Appendix: References")

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def main():
    """Main function demonstrating pdf_prepender usage."""

    # Define the specification for pages to prepend
    spec = {
        "defaults": {
            "fontSize": 11,
            "boldMarker": "**",
            "italicMarker": "_",
            "pageSize": "letter",
        },
        "pages": [
            # First prepended page: Table of Contents
            {
                "pageHeading": {
                    "text": "Table of Contents",
                    "fontSize": 24,
                    "bold": True,
                    "alignment": "center",
                },
                "content": [
                    {
                        "type": "sectionHeading",
                        "text": "Document Sections",
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Introduction:**",
                        "content": [{"text": "Chapter 1", "targetPage": 3}],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Lab Results:**",
                        "content": [
                            {"text": "Blood Panel", "targetPage": 5},
                        ],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Analysis:**",
                        "content": [{"text": "See Chapter 3", "targetPage": 7}],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Appendix:**",
                        "content": [{"text": "References", "targetPage": 10}],
                    },
                ],
            },
            # Second prepended page: Executive Summary
            {
                "pageHeading": {
                    "text": "Executive Summary",
                    "fontSize": 20,
                    "bold": True,
                    "alignment": "center",
                },
                "content": [
                    {
                        "type": "sectionHeading",
                        "text": "Key Findings",
                    },
                    {
                        "type": "sectionSubheading",
                        "text": "Overview of test results and recommendations",
                        "italic": True,
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Primary Results:**",
                        "content": [
                            "All blood work within normal ranges",
                            {"text": "See detailed results", "targetPage": 5},
                        ],
                    },
                    {
                        "type": "bulletPoint",
                        "label": "**Recommendations:**",
                        "content": [
                            "Continue current treatment plan",
                            {"text": "Review analysis", "targetPage": 7},
                        ],
                    },
                    {
                        "type": "indentedBulletPoint",
                        "label": "_Note:_",
                        "content": ["Follow-up recommended in 6 months"],
                    },
                ],
            },
        ],
    }

    # Create the sample PDF
    print("Creating sample 10-page PDF...")
    original_pdf = create_sample_pdf()

    # Method 1: Using DocumentBuilder class
    print("\nMethod 1: Using DocumentBuilder class")
    builder = DocumentBuilder.from_dict(spec)

    # Get the prepend page count before building
    prepend_count = builder.get_prepend_page_count()
    print(f"  - Will prepend {prepend_count} pages")

    # Build to bytes
    result = builder.build(original_pdf)
    print(f"  - Generated PDF: {len(result)} bytes")

    # Save to file
    output_path = Path("output_method1.pdf")
    output_path.write_bytes(result)
    print(f"  - Saved to: {output_path}")

    # Method 2: Using convenience function
    print("\nMethod 2: Using prepend_pages function")
    output_path2 = Path("output_method2.pdf")
    prepend_pages(spec, original_pdf, output=output_path2)
    print(f"  - Saved to: {output_path2}")

    # Method 3: Build to file directly
    print("\nMethod 3: Using build_to_file method")
    original_path = Path("original.pdf")
    original_path.write_bytes(original_pdf)

    output_path3 = Path("output_method3.pdf")
    builder = DocumentBuilder.from_dict(spec)
    builder.build_to_file(original_path, output_path3)
    print(f"  - Saved to: {output_path3}")

    print("\n" + "=" * 50)
    print("All examples completed successfully!")
    print("=" * 50)
    print("\nGenerated files:")
    print(f"  - original.pdf (10 pages)")
    print(f"  - output_method1.pdf ({10 + prepend_count} pages)")
    print(f"  - output_method2.pdf ({10 + prepend_count} pages)")
    print(f"  - output_method3.pdf ({10 + prepend_count} pages)")
    print("\nOpen the output PDFs and click on the links to verify navigation.")
    print("Links should navigate to the correct pages accounting for the")
    print(f"{prepend_count} prepended pages.")


if __name__ == "__main__":
    main()
