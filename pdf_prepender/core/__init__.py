"""Core components for PDF generation and merging."""

from pdf_prepender.core.document_builder import DocumentBuilder, prepend_pages
from pdf_prepender.core.link_annotator import LinkAnnotator, add_links_to_pdf
from pdf_prepender.core.link_manager import LinkInfo, LinkManager
from pdf_prepender.core.page_generator import PageGenerator
from pdf_prepender.core.pdf_merger import PdfMerger, count_pdf_pages

__all__ = [
    "DocumentBuilder",
    "prepend_pages",
    "PageGenerator",
    "PdfMerger",
    "count_pdf_pages",
    "LinkManager",
    "LinkInfo",
    "LinkAnnotator",
    "add_links_to_pdf",
]
