"""PDF Prepender - A library for prepending dynamically generated pages to PDFs."""

from pdf_prepender.core.document_builder import DocumentBuilder, prepend_pages
from pdf_prepender.core.link_manager import LinkManager
from pdf_prepender.core.page_generator import PageGenerator
from pdf_prepender.core.pdf_merger import PdfMerger, count_pdf_pages
from pdf_prepender.models.schema import (
    Alignment,
    BulletPoint,
    ContentElement,
    Defaults,
    IndentedBulletPoint,
    LinkableItem,
    OverflowBehavior,
    Page,
    PageHeading,
    PageSize,
    PrependSpecification,
    SectionHeading,
    SectionSubheading,
)
from pdf_prepender.parsers.json_parser import (
    JsonParseError,
    parse_json_dict,
    parse_json_file,
    parse_json_string,
)
from pdf_prepender.parsers.text_formatter import TextFormatter

__version__ = "0.1.0"

__all__ = [
    # Main API
    "DocumentBuilder",
    "prepend_pages",
    # Core components
    "PageGenerator",
    "PdfMerger",
    "LinkManager",
    "count_pdf_pages",
    # Models
    "PrependSpecification",
    "Page",
    "PageHeading",
    "ContentElement",
    "SectionHeading",
    "SectionSubheading",
    "BulletPoint",
    "IndentedBulletPoint",
    "LinkableItem",
    "Defaults",
    "Alignment",
    "OverflowBehavior",
    "PageSize",
    # Parsers
    "parse_json_file",
    "parse_json_string",
    "parse_json_dict",
    "JsonParseError",
    "TextFormatter",
]
