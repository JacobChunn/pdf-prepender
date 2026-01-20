"""Link annotator using PyMuPDF for adding clickable links to PDFs."""

import io
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

import fitz  # PyMuPDF

if TYPE_CHECKING:
    from pdf_prepender.core.page_generator import LinkPosition


class LinkAnnotator:
    """Adds clickable link annotations to PDFs using PyMuPDF."""

    def __init__(self):
        """Initialize the link annotator."""
        pass

    def add_links(
        self,
        pdf_bytes: bytes,
        link_positions: list["LinkPosition"],
        output: str | Path | BinaryIO | None = None,
    ) -> bytes | None:
        """
        Add link annotations to a PDF at specified positions.

        This is the second pass of the two-pass system:
        1. First pass: Generate and merge PDF, track link positions
        2. Second pass (this): Add actual clickable links using PyMuPDF

        Args:
            pdf_bytes: The merged PDF bytes (without link annotations)
            link_positions: List of link positions with coordinates and targets
            output: Optional output path or stream. If None, returns bytes.

        Returns:
            PDF bytes if output is None, otherwise None
        """
        if not link_positions:
            # No links to add, just return/write the original
            return self._write_output(pdf_bytes, output)

        # Open PDF with PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        try:
            # Add link annotations for each position
            for link_pos in link_positions:
                self._add_link(doc, link_pos)

            # Get the result
            result_bytes = doc.tobytes()
        finally:
            doc.close()

        return self._write_output(result_bytes, output)

    def _add_link(self, doc: fitz.Document, link_pos: "LinkPosition") -> None:
        """
        Add a single link annotation to the document.

        Uses text search to find the exact position of the link text,
        falling back to estimated coordinates if search fails.

        Args:
            doc: PyMuPDF document
            link_pos: Link position information
        """
        page_idx = link_pos.page_index
        target_page_idx = link_pos.target_page - 1  # Convert to 0-based

        # Validate page indices
        if page_idx < 0 or page_idx >= len(doc):
            return
        if target_page_idx < 0 or target_page_idx >= len(doc):
            return

        page = doc[page_idx]

        # Try to find the exact position using text search
        link_rect = self._find_text_rect(page, link_pos)

        if link_rect is None:
            # Fallback to estimated coordinates
            link_rect = self._get_estimated_rect(page, link_pos)

        # Create internal link to target page
        link_dict = {
            "kind": fitz.LINK_GOTO,
            "from": link_rect,
            "page": target_page_idx,
            "to": fitz.Point(0, 0),  # Top of target page
        }

        try:
            page.insert_link(link_dict)
        except Exception:
            # If link insertion fails, continue without it
            pass

    def _find_text_rect(
        self, page: fitz.Page, link_pos: "LinkPosition"
    ) -> fitz.Rect | None:
        """
        Find the exact rectangle of link text using PyMuPDF text search.

        Args:
            page: PyMuPDF page object
            link_pos: Link position with text to search for

        Returns:
            fitz.Rect if found, None otherwise
        """
        if not link_pos.link_text:
            return None

        # Search for the link text on the page
        text_instances = page.search_for(link_pos.link_text)

        if not text_instances:
            return None

        # If multiple instances found, use the estimated y position to pick the right one
        if len(text_instances) == 1:
            return text_instances[0]

        # Multiple instances - find the one closest to our estimated position
        page_height = page.rect.height
        estimated_y = page_height - link_pos.y  # Convert to PyMuPDF coordinates

        best_rect = None
        best_distance = float("inf")

        for rect in text_instances:
            # Calculate distance from estimated position
            distance = abs(rect.y1 - estimated_y)
            if distance < best_distance:
                best_distance = distance
                best_rect = rect

        return best_rect

    def _get_estimated_rect(
        self, page: fitz.Page, link_pos: "LinkPosition"
    ) -> fitz.Rect:
        """
        Get link rectangle from estimated coordinates.

        Args:
            page: PyMuPDF page object
            link_pos: Link position with estimated coordinates

        Returns:
            fitz.Rect based on estimated position
        """
        page_height = page.rect.height

        # Convert coordinates from ReportLab (origin bottom-left) to PyMuPDF (origin top-left)
        x0 = link_pos.x
        y0 = page_height - (link_pos.y + link_pos.height)  # Top of link area
        x1 = link_pos.x + link_pos.width
        y1 = page_height - link_pos.y  # Bottom of link area

        return fitz.Rect(x0, y0, x1, y1)

    def _write_output(
        self,
        pdf_bytes: bytes,
        output: str | Path | BinaryIO | None,
    ) -> bytes | None:
        """Write PDF bytes to output destination."""
        if output is None:
            return pdf_bytes
        elif isinstance(output, (str, Path)):
            with open(output, "wb") as f:
                f.write(pdf_bytes)
            return None
        else:
            output.write(pdf_bytes)
            return None


def add_links_to_pdf(
    pdf_bytes: bytes,
    link_positions: list["LinkPosition"],
    output: str | Path | BinaryIO | None = None,
) -> bytes | None:
    """
    Convenience function to add link annotations to a PDF.

    Args:
        pdf_bytes: The merged PDF bytes
        link_positions: List of link positions
        output: Optional output path or stream

    Returns:
        PDF bytes if output is None, otherwise None
    """
    annotator = LinkAnnotator()
    return annotator.add_links(pdf_bytes, link_positions, output)
