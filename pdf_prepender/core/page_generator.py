"""Page generator using ReportLab for PDF content generation."""

import io
from dataclasses import dataclass, field
from typing import BinaryIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, LEGAL, LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)
from reportlab.platypus.flowables import Flowable

from pdf_prepender.core.link_manager import LinkManager
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
from pdf_prepender.parsers.text_formatter import TextFormatter


# Map alignment enum to ReportLab constants
ALIGNMENT_MAP = {
    Alignment.LEFT: TA_LEFT,
    Alignment.CENTER: TA_CENTER,
    Alignment.RIGHT: TA_RIGHT,
    Alignment.JUSTIFY: TA_JUSTIFY,
}

# Map page size enum to ReportLab page sizes
PAGE_SIZE_MAP = {
    PageSize.LETTER: LETTER,
    PageSize.A4: A4,
    PageSize.LEGAL: LEGAL,
}


@dataclass
class LinkPosition:
    """Position information for a link to be added after PDF generation."""
    page_index: int  # 0-based page in prepended section
    target_page: int  # 1-based target page (already adjusted for offset)
    link_text: str  # The visible link text (for text search fallback)
    x: float  # X position of link (estimated)
    y: float  # Y position of link from bottom (estimated)
    width: float  # Estimated width
    height: float  # Estimated height


@dataclass
class LinkInfo:
    """Information about a link's position within text."""
    text: str  # The link text
    target_page: int  # Adjusted target page
    char_start: int  # Character offset where link starts in plain text
    char_end: int  # Character offset where link ends in plain text


class LinkTrackingParagraph(Flowable):
    """A paragraph that tracks its position for link placement."""

    def __init__(self, text: str, links: list[LinkInfo], style: ParagraphStyle,
                 link_positions: list[LinkPosition], plain_text: str):
        """
        Args:
            text: The formatted paragraph text (with XML tags)
            links: List of LinkInfo objects with position data
            style: Paragraph style
            link_positions: List to append link position info to
            plain_text: The plain text version (without XML tags) for position calculation
        """
        Flowable.__init__(self)
        self.text = text
        self.links = links
        self.style = style
        self.link_positions = link_positions
        self.plain_text = plain_text
        self._para = Paragraph(text, style)

    def wrap(self, availWidth, availHeight):
        w, h = self._para.wrap(availWidth, availHeight)
        self.width = w
        self.height = h
        self._avail_width = availWidth
        return w, h

    def draw(self):
        # Draw the paragraph
        self._para.drawOn(self.canv, 0, 0)

        # Record position for each link
        if self.links:
            page_idx = self.canv.getPageNumber() - 1  # 0-based

            # Get the absolute position on the page
            x, y = self.canv.absolutePosition(0, 0)

            # Calculate average character width based on paragraph width and plain text length
            plain_len = len(self.plain_text) if self.plain_text else 1
            avg_char_width = self.width / max(plain_len, 1)

            for link_info in self.links:
                # Estimate link position based on character offsets
                link_x = x + (link_info.char_start * avg_char_width)
                link_width = (link_info.char_end - link_info.char_start) * avg_char_width

                # Ensure minimum clickable width
                link_width = max(link_width, 20)

                self.link_positions.append(LinkPosition(
                    page_index=page_idx,
                    target_page=link_info.target_page,
                    link_text=link_info.text,  # Include text for search fallback
                    x=link_x,
                    y=y,
                    width=link_width,
                    height=self.height,
                ))


class PageGenerator:
    """Generates PDF pages from a PrependSpecification using ReportLab."""

    def __init__(
        self,
        spec: PrependSpecification,
        link_manager: LinkManager | None = None,
    ):
        """
        Initialize the page generator.

        Args:
            spec: The prepend specification defining page content
            link_manager: Optional link manager for handling page offsets
        """
        self.spec = spec
        self.defaults = spec.defaults
        self.link_manager = link_manager or LinkManager()
        self.text_formatter = TextFormatter(
            bold_marker=self.defaults.bold_marker,
            italic_marker=self.defaults.italic_marker,
        )
        self.link_positions: list[LinkPosition] = []
        self._setup_styles()

    def _setup_styles(self) -> None:
        """Set up ReportLab paragraph styles."""
        self.styles = getSampleStyleSheet()

        # Base style for normal text
        self.styles.add(
            ParagraphStyle(
                name="PrependNormal",
                parent=self.styles["Normal"],
                fontSize=self.defaults.font_size,
                leading=self.defaults.font_size * 1.2,
                spaceAfter=6,
            )
        )

        # Page heading style
        self.styles.add(
            ParagraphStyle(
                name="PrependPageHeading",
                parent=self.styles["PrependNormal"],
                fontSize=18,
                leading=22,
                spaceAfter=12,
                spaceBefore=0,
            )
        )

        # Section heading style
        self.styles.add(
            ParagraphStyle(
                name="PrependSectionHeading",
                parent=self.styles["PrependNormal"],
                fontSize=14,
                leading=18,
                spaceBefore=12,
                spaceAfter=6,
            )
        )

        # Section subheading style
        self.styles.add(
            ParagraphStyle(
                name="PrependSectionSubheading",
                parent=self.styles["PrependNormal"],
                fontSize=12,
                leading=15,
                spaceBefore=6,
                spaceAfter=6,
            )
        )

        # Bullet point style
        self.styles.add(
            ParagraphStyle(
                name="PrependBullet",
                parent=self.styles["PrependNormal"],
                leftIndent=20,
                bulletIndent=0,
                spaceBefore=3,
                spaceAfter=3,
            )
        )

        # Indented bullet point style
        self.styles.add(
            ParagraphStyle(
                name="PrependIndentedBullet",
                parent=self.styles["PrependBullet"],
                leftIndent=40,
                bulletIndent=20,
            )
        )

    def _get_style(
        self,
        base_style_name: str,
        font_size: int | None = None,
        alignment: Alignment = Alignment.LEFT,
    ) -> ParagraphStyle:
        """Get a paragraph style, optionally modified."""
        base = self.styles[base_style_name]

        if font_size is None and alignment == Alignment.LEFT:
            return base

        return ParagraphStyle(
            name=f"{base_style_name}_modified",
            parent=base,
            fontSize=font_size or base.fontSize,
            leading=(font_size or base.fontSize) * 1.2,
            alignment=ALIGNMENT_MAP.get(alignment, TA_LEFT),
        )

    def _build_page_heading(self, heading: PageHeading) -> list[Flowable]:
        """Build flowables for a page heading."""
        flowables: list[Flowable] = []

        style = self._get_style(
            "PrependPageHeading",
            font_size=heading.font_size,
            alignment=heading.alignment,
        )

        text = self.text_formatter.escape_xml(heading.text)
        text = self.text_formatter.apply_style(text, bold=heading.bold, italic=heading.italic)

        flowables.append(Paragraph(text, style))
        flowables.append(Spacer(1, 12))

        return flowables

    def _build_section_heading(self, element: SectionHeading) -> list[Flowable]:
        """Build flowables for a section heading."""
        style = self._get_style(
            "PrependSectionHeading",
            font_size=element.font_size,
            alignment=element.alignment,
        )

        text = self.text_formatter.format_text(element.text)
        if element.bold:
            text = f"<b>{text}</b>"
        if element.italic:
            text = f"<i>{text}</i>"

        return [Paragraph(text, style)]

    def _build_section_subheading(self, element: SectionSubheading) -> list[Flowable]:
        """Build flowables for a section subheading."""
        style = self._get_style(
            "PrependSectionSubheading",
            font_size=element.font_size,
            alignment=element.alignment,
        )

        text = self.text_formatter.format_text(element.text)
        if element.bold:
            text = f"<b>{text}</b>"
        if element.italic:
            text = f"<i>{text}</i>"

        return [Paragraph(text, style)]

    def _build_content_items(self, content: list[str | LinkableItem]) -> tuple[str, list[LinkInfo], str]:
        """
        Build formatted content string from content items.

        Returns:
            Tuple of (formatted string, list of LinkInfo, plain text for position calculation)
        """
        formatted_parts = []
        plain_parts = []
        links = []
        current_pos = 0  # Track position in plain text

        for i, item in enumerate(content):
            # Add separator before this item (except first)
            if i > 0:
                formatted_parts.append(", ")
                plain_parts.append(", ")
                current_pos += 2

            if isinstance(item, LinkableItem):
                adjusted_page = self.link_manager.get_adjusted_page(item.target_page)
                escaped_text = self.text_formatter.escape_xml(item.text)
                # Style as blue underlined text
                formatted_parts.append(f'<font color="blue"><u>{escaped_text}</u></font>')
                plain_parts.append(item.text)
                # Record link position
                links.append(LinkInfo(
                    text=item.text,
                    target_page=adjusted_page,
                    char_start=current_pos,
                    char_end=current_pos + len(item.text),
                ))
                current_pos += len(item.text)
            elif isinstance(item, dict):
                if "targetPage" in item or "target_page" in item:
                    target = item.get("targetPage") or item.get("target_page")
                    adjusted_page = self.link_manager.get_adjusted_page(target)
                    link_text = item["text"]
                    escaped_text = self.text_formatter.escape_xml(link_text)
                    formatted_parts.append(f'<font color="blue"><u>{escaped_text}</u></font>')
                    plain_parts.append(link_text)
                    links.append(LinkInfo(
                        text=link_text,
                        target_page=adjusted_page,
                        char_start=current_pos,
                        char_end=current_pos + len(link_text),
                    ))
                    current_pos += len(link_text)
                else:
                    text = str(item)
                    formatted_parts.append(self.text_formatter.escape_xml(text))
                    plain_parts.append(text)
                    current_pos += len(text)
            else:
                text = str(item)
                formatted_parts.append(self.text_formatter.format_text(text))
                plain_parts.append(text)
                current_pos += len(text)

        return "".join(formatted_parts), links, "".join(plain_parts)

    def _build_bullet_point(
        self,
        element: BulletPoint | IndentedBulletPoint,
        indented: bool = False,
    ) -> list[Flowable]:
        """Build flowables for a bullet point."""
        style_name = "PrependIndentedBullet" if indented else "PrependBullet"
        style = self._get_style(style_name, font_size=element.font_size)

        label = self.text_formatter.format_text(element.label)
        # Get plain label text (strip XML tags for position calculation)
        plain_label = self._strip_xml_tags(element.label)

        content_str, links, plain_content = self._build_content_items(element.content)
        bullet_text = f"\u2022 {label} {content_str}"

        # Build plain text for position calculation
        # Account for bullet, space, label, space before content
        bullet_prefix = f"\u2022 {plain_label} "
        plain_text = bullet_prefix + plain_content

        # Adjust link positions to account for the bullet prefix
        prefix_len = len(bullet_prefix)
        adjusted_links = [
            LinkInfo(
                text=link.text,
                target_page=link.target_page,
                char_start=link.char_start + prefix_len,
                char_end=link.char_end + prefix_len,
            )
            for link in links
        ]

        if adjusted_links:
            # Use tracking paragraph to record position for links
            flowable = LinkTrackingParagraph(
                bullet_text, adjusted_links, style, self.link_positions, plain_text
            )
        else:
            flowable = Paragraph(bullet_text, style)

        if element.overflow_behavior == OverflowBehavior.WRAP_WITH_PAGE_BREAK:
            return [KeepTogether([flowable])]
        elif element.overflow_behavior == OverflowBehavior.NO_WRAP:
            no_wrap_style = ParagraphStyle(
                name=f"{style_name}_nowrap",
                parent=style,
            )
            if adjusted_links:
                return [LinkTrackingParagraph(
                    bullet_text, adjusted_links, no_wrap_style, self.link_positions, plain_text
                )]
            return [Paragraph(bullet_text, no_wrap_style)]
        else:
            return [flowable]

    def _strip_xml_tags(self, text: str) -> str:
        """Remove XML tags from text for position calculation."""
        import re
        # Remove bold/italic markers first
        result = self.text_formatter.format_text(text)
        # Then remove any XML tags
        result = re.sub(r'<[^>]+>', '', result)
        return result

    def _build_content_element(self, element: ContentElement) -> list[Flowable]:
        """Build flowables for a content element."""
        if isinstance(element, SectionHeading):
            return self._build_section_heading(element)
        elif isinstance(element, SectionSubheading):
            return self._build_section_subheading(element)
        elif isinstance(element, BulletPoint):
            return self._build_bullet_point(element, indented=False)
        elif isinstance(element, IndentedBulletPoint):
            return self._build_bullet_point(element, indented=True)
        else:
            return []

    def _build_page(self, page: Page, is_first: bool = False) -> list[Flowable]:
        """Build flowables for a page."""
        flowables: list[Flowable] = []

        if not is_first:
            flowables.append(PageBreak())

        if page.page_heading:
            flowables.extend(self._build_page_heading(page.page_heading))

        for element in page.content:
            flowables.extend(self._build_content_element(element))

        return flowables

    def generate(self) -> tuple[bytes, int, list[LinkPosition]]:
        """
        Generate the PDF content.

        Returns:
            Tuple of (PDF bytes, page count, list of link positions)
        """
        self.link_positions.clear()
        buffer = io.BytesIO()

        page_size = PAGE_SIZE_MAP.get(self.defaults.page_size, LETTER)

        doc = BaseDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=self.defaults.left_margin,
            rightMargin=self.defaults.right_margin,
            topMargin=self.defaults.top_margin,
            bottomMargin=self.defaults.bottom_margin,
        )

        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="normal",
        )

        template = PageTemplate(id="main", frames=frame)
        doc.addPageTemplates([template])

        flowables: list[Flowable] = []
        for i, page in enumerate(self.spec.pages):
            flowables.extend(self._build_page(page, is_first=(i == 0)))

        doc.build(flowables)
        page_count = doc.page

        buffer.seek(0)
        return buffer.getvalue(), page_count, list(self.link_positions)

    def generate_to_stream(self, stream: BinaryIO) -> int:
        """
        Generate the PDF content to a stream.

        Args:
            stream: Binary stream to write to

        Returns:
            Number of pages generated
        """
        pdf_bytes, page_count, _ = self.generate()
        stream.write(pdf_bytes)
        return page_count
