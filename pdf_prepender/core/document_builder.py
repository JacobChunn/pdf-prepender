"""Document builder that orchestrates PDF generation and merging."""

from pathlib import Path
from typing import BinaryIO

from pdf_prepender.core.link_annotator import LinkAnnotator
from pdf_prepender.core.link_manager import LinkManager
from pdf_prepender.core.page_generator import PageGenerator
from pdf_prepender.core.pdf_merger import PdfMerger, count_pdf_pages
from pdf_prepender.models.schema import PrependSpecification
from pdf_prepender.parsers.json_parser import (
    parse_json_dict,
    parse_json_file,
    parse_json_string,
)


class DocumentBuilder:
    """
    Main orchestrator for prepending pages to PDFs.

    Implements the two-pass algorithm:
    1. First pass: Generate prepended content to count pages
    2. Calculate offset for link targets
    3. Second pass: Regenerate with adjusted link targets
    4. Merge and create named destinations with link annotations
    """

    def __init__(self, spec: PrependSpecification):
        """
        Initialize the document builder.

        Args:
            spec: The prepend specification
        """
        self.spec = spec
        self.link_manager = LinkManager()

    @classmethod
    def from_json_file(cls, json_path: str | Path) -> "DocumentBuilder":
        """
        Create a DocumentBuilder from a JSON file.

        Args:
            json_path: Path to the JSON specification file

        Returns:
            DocumentBuilder instance
        """
        spec = parse_json_file(json_path)
        return cls(spec)

    @classmethod
    def from_json_string(cls, json_string: str) -> "DocumentBuilder":
        """
        Create a DocumentBuilder from a JSON string.

        Args:
            json_string: JSON specification string

        Returns:
            DocumentBuilder instance
        """
        spec = parse_json_string(json_string)
        return cls(spec)

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentBuilder":
        """
        Create a DocumentBuilder from a dictionary.

        Args:
            data: Dictionary containing the specification

        Returns:
            DocumentBuilder instance
        """
        spec = parse_json_dict(data)
        return cls(spec)

    def build(
        self,
        original_pdf: str | Path | BinaryIO | bytes,
        output: str | Path | BinaryIO | None = None,
    ) -> bytes | None:
        """
        Build the final PDF with prepended pages.

        This implements a two-pass algorithm:
        1. First pass: Generate prepended pages to count pages
        2. Set link offsets based on page count
        3. Second pass: Regenerate with correct link targets, merge PDFs
        4. Add link annotations using PyMuPDF

        Args:
            original_pdf: The original PDF to prepend to
            output: Optional output path or stream. If None, returns bytes.

        Returns:
            PDF bytes if output is None, otherwise None
        """
        # First pass: Generate to count pages
        generator = PageGenerator(self.spec, self.link_manager)
        _, prepend_page_count, _ = generator.generate()

        # Set the offset in link manager
        self.link_manager.set_prepended_page_count(prepend_page_count)

        # Second pass: Regenerate with adjusted links and merge
        generator = PageGenerator(self.spec, self.link_manager)
        prepend_bytes, _, link_positions = generator.generate()

        # Merge with original PDF (without link annotations)
        merger = PdfMerger()
        merged_bytes = merger.merge_with_destinations(
            prepend_bytes=prepend_bytes,
            original_pdf=original_pdf,
            output=None,  # Get bytes back for link annotation
        )

        # Add link annotations using PyMuPDF (second pass on merged PDF)
        annotator = LinkAnnotator()
        return annotator.add_links(
            pdf_bytes=merged_bytes,
            link_positions=link_positions,
            output=output,
        )

    def build_to_file(
        self,
        original_pdf: str | Path,
        output_path: str | Path,
    ) -> None:
        """
        Build the final PDF and write to a file.

        Args:
            original_pdf: Path to the original PDF
            output_path: Path for the output PDF
        """
        self.build(original_pdf, output=output_path)

    def get_prepend_page_count(self) -> int:
        """
        Get the number of pages that will be prepended.

        Useful for preview or planning purposes.

        Returns:
            Number of pages in the prepended section
        """
        generator = PageGenerator(self.spec, LinkManager())
        _, page_count, _ = generator.generate()
        return page_count


def prepend_pages(
    json_spec: str | Path | dict,
    original_pdf: str | Path | BinaryIO | bytes,
    output: str | Path | BinaryIO | None = None,
) -> bytes | None:
    """
    Convenience function to prepend pages to a PDF.

    Args:
        json_spec: JSON specification (path, string, or dict)
        original_pdf: The original PDF to prepend to
        output: Optional output path or stream

    Returns:
        PDF bytes if output is None, otherwise None
    """
    if isinstance(json_spec, dict):
        builder = DocumentBuilder.from_dict(json_spec)
    elif isinstance(json_spec, Path) or (
        isinstance(json_spec, str) and Path(json_spec).exists()
    ):
        builder = DocumentBuilder.from_json_file(json_spec)
    else:
        builder = DocumentBuilder.from_json_string(json_spec)

    return builder.build(original_pdf, output)
