"""PDF merger using pypdf for prepending and named destination creation."""

import io
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    Fit,
    NameObject,
    NumberObject,
)

if TYPE_CHECKING:
    from pdf_prepender.core.page_generator import LinkPosition


class PdfMerger:
    """Handles PDF merging, prepending, and named destination creation."""

    def __init__(self):
        """Initialize the PDF merger."""
        self.writer = PdfWriter()

    def get_page_count(self, pdf_source: str | Path | BinaryIO | bytes) -> int:
        """
        Get the page count of a PDF.

        Args:
            pdf_source: Path to PDF file, file object, or bytes

        Returns:
            Number of pages in the PDF
        """
        reader = self._create_reader(pdf_source)
        return len(reader.pages)

    def _create_reader(self, pdf_source: str | Path | BinaryIO | bytes) -> PdfReader:
        """
        Create a PdfReader from various source types.

        Args:
            pdf_source: Path to PDF file, file object, or bytes

        Returns:
            PdfReader instance
        """
        if isinstance(pdf_source, bytes):
            return PdfReader(io.BytesIO(pdf_source))
        elif isinstance(pdf_source, (str, Path)):
            return PdfReader(str(pdf_source))
        else:
            return PdfReader(pdf_source)

    def prepend_pages(
        self,
        prepend_pdf: str | Path | BinaryIO | bytes,
        original_pdf: str | Path | BinaryIO | bytes,
        output: str | Path | BinaryIO | None = None,
        create_destinations: bool = True,
    ) -> bytes | None:
        """
        Prepend pages from one PDF to another.

        Args:
            prepend_pdf: PDF to prepend (new pages at the beginning)
            original_pdf: Original PDF to append to
            output: Optional output path or stream (if None, returns bytes)
            create_destinations: Whether to create named destinations for all pages

        Returns:
            PDF bytes if output is None, otherwise None
        """
        self.writer = PdfWriter()

        # Read both PDFs
        prepend_reader = self._create_reader(prepend_pdf)
        original_reader = self._create_reader(original_pdf)

        # Add prepended pages first
        for page in prepend_reader.pages:
            self.writer.add_page(page)

        prepend_count = len(prepend_reader.pages)

        # Add original pages
        for page in original_reader.pages:
            self.writer.add_page(page)

        total_pages = len(self.writer.pages)

        # Create named destinations for all pages
        if create_destinations:
            self._create_named_destinations(total_pages)

        # Output the result
        if output is None:
            buffer = io.BytesIO()
            self.writer.write(buffer)
            buffer.seek(0)
            return buffer.getvalue()
        elif isinstance(output, (str, Path)):
            with open(output, "wb") as f:
                self.writer.write(f)
            return None
        else:
            self.writer.write(output)
            return None

    def _create_named_destinations(self, total_pages: int) -> None:
        """
        Create named destinations for all pages.

        Args:
            total_pages: Total number of pages in the document
        """
        for i in range(total_pages):
            dest_name = f"page_{i + 1}"
            self.writer.add_named_destination(
                title=dest_name,
                page_number=i,
            )

    def merge_with_destinations_and_links(
        self,
        prepend_bytes: bytes,
        original_pdf: str | Path | BinaryIO | bytes,
        link_positions: list["LinkPosition"] | None = None,
        output: str | Path | BinaryIO | None = None,
    ) -> bytes | None:
        """
        Merge prepended pages with original PDF, create destinations, and add link annotations.

        This is the main method for the two-pass generation approach.

        Args:
            prepend_bytes: Bytes of the prepended PDF (already generated)
            original_pdf: Original PDF to append to
            link_positions: List of link positions for creating clickable links
            output: Optional output path or stream

        Returns:
            PDF bytes if output is None, otherwise None
        """
        self.writer = PdfWriter()

        # Read both PDFs
        prepend_reader = PdfReader(io.BytesIO(prepend_bytes))
        original_reader = self._create_reader(original_pdf)

        prepend_count = len(prepend_reader.pages)
        original_count = len(original_reader.pages)

        # Add prepended pages
        for page in prepend_reader.pages:
            self.writer.add_page(page)

        # Add original pages
        for page in original_reader.pages:
            self.writer.add_page(page)

        total_pages = prepend_count + original_count

        # Create named destinations for all pages
        for i in range(total_pages):
            dest_name = f"page_{i + 1}"
            self.writer.add_named_destination(
                title=dest_name,
                page_number=i,
            )

        # Add link annotations at exact positions
        if link_positions:
            self._add_link_annotations(link_positions)

        # Output the result
        if output is None:
            buffer = io.BytesIO()
            self.writer.write(buffer)
            buffer.seek(0)
            return buffer.getvalue()
        elif isinstance(output, (str, Path)):
            with open(output, "wb") as f:
                self.writer.write(f)
            return None
        else:
            self.writer.write(output)
            return None

    def _add_link_annotations(self, link_positions: list["LinkPosition"]) -> None:
        """
        Add link annotations to pages at exact positions.

        Args:
            link_positions: List of link positions with coordinates
        """
        for link_pos in link_positions:
            page_idx = link_pos.page_index
            target_page_idx = link_pos.target_page - 1  # Convert to 0-based

            if page_idx >= len(self.writer.pages):
                continue
            if target_page_idx < 0 or target_page_idx >= len(self.writer.pages):
                continue

            # Use the exact coordinates from the link position
            rect = (
                link_pos.x,  # x1 (left)
                link_pos.y,  # y1 (bottom)
                link_pos.x + link_pos.width,  # x2 (right)
                link_pos.y + link_pos.height,  # y2 (top)
            )

            # Create link annotation
            try:
                link_annotation = Link(
                    rect=rect,
                    target_page_index=target_page_idx,
                    fit=Fit.fit(),
                )
                self.writer.add_annotation(page_number=page_idx, annotation=link_annotation)
            except Exception:
                # If annotation fails, continue without it
                pass

    def merge_with_destinations(
        self,
        prepend_bytes: bytes,
        original_pdf: str | Path | BinaryIO | bytes,
        output: str | Path | BinaryIO | None = None,
    ) -> bytes | None:
        """
        Merge prepended pages with original PDF and create proper destinations.

        Legacy method without link annotations.

        Args:
            prepend_bytes: Bytes of the prepended PDF (already generated)
            original_pdf: Original PDF to append to
            output: Optional output path or stream

        Returns:
            PDF bytes if output is None, otherwise None
        """
        return self.merge_with_destinations_and_links(
            prepend_bytes=prepend_bytes,
            original_pdf=original_pdf,
            link_positions=None,
            output=output,
        )


def count_pdf_pages(pdf_source: str | Path | BinaryIO | bytes) -> int:
    """
    Convenience function to count pages in a PDF.

    Args:
        pdf_source: Path to PDF file, file object, or bytes

    Returns:
        Number of pages in the PDF
    """
    merger = PdfMerger()
    return merger.get_page_count(pdf_source)
