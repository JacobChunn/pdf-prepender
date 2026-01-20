"""Text formatter for processing bold/italic markers and XML escaping."""

import re
from html import escape as html_escape


class TextFormatter:
    """Handles conversion of text markers to ReportLab XML tags."""

    def __init__(self, bold_marker: str = "**", italic_marker: str = "_"):
        """
        Initialize the text formatter.

        Args:
            bold_marker: The marker used to denote bold text (e.g., "**")
            italic_marker: The marker used to denote italic text (e.g., "_")
        """
        self.bold_marker = bold_marker
        self.italic_marker = italic_marker
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for the markers."""
        # Escape special regex characters in markers
        bold_escaped = re.escape(self.bold_marker)
        italic_escaped = re.escape(self.italic_marker)

        # Pattern for bold: **text** -> <b>text</b>
        # Non-greedy match to handle multiple bold sections
        self._bold_pattern = re.compile(
            rf"{bold_escaped}(.+?){bold_escaped}"
        )

        # Pattern for italic: _text_ -> <i>text</i>
        # Non-greedy match to handle multiple italic sections
        self._italic_pattern = re.compile(
            rf"{italic_escaped}(.+?){italic_escaped}"
        )

    def escape_xml(self, text: str) -> str:
        """
        Escape special XML characters in text.

        Args:
            text: The text to escape

        Returns:
            Text with XML special characters escaped
        """
        return html_escape(text, quote=False)

    def format_text(
        self,
        text: str,
        escape_first: bool = True,
        apply_bold: bool = True,
        apply_italic: bool = True,
    ) -> str:
        """
        Convert text markers to ReportLab XML tags.

        Args:
            text: The text to format
            escape_first: Whether to escape XML characters before processing markers
            apply_bold: Whether to apply bold formatting
            apply_italic: Whether to apply italic formatting

        Returns:
            Formatted text with ReportLab XML tags
        """
        result = text

        if escape_first:
            # We need to preserve markers during escaping, so we temporarily
            # replace them with placeholders
            bold_placeholder = "\x00BOLD\x00"
            italic_placeholder = "\x00ITALIC\x00"

            # Find all bold sections and replace markers with placeholders
            bold_matches = list(self._bold_pattern.finditer(result))
            for match in reversed(bold_matches):
                inner_text = self.escape_xml(match.group(1))
                result = (
                    result[: match.start()]
                    + f"{bold_placeholder}{inner_text}{bold_placeholder}"
                    + result[match.end() :]
                )

            # Find all italic sections and replace markers with placeholders
            italic_matches = list(self._italic_pattern.finditer(result))
            for match in reversed(italic_matches):
                inner_text = self.escape_xml(match.group(1))
                result = (
                    result[: match.start()]
                    + f"{italic_placeholder}{inner_text}{italic_placeholder}"
                    + result[match.end() :]
                )

            # Escape remaining text (outside markers)
            # Split by placeholders and escape parts that aren't inside markers
            parts = re.split(
                rf"({re.escape(bold_placeholder)}|{re.escape(italic_placeholder)})",
                result,
            )
            in_bold = False
            in_italic = False
            escaped_parts = []

            for part in parts:
                if part == bold_placeholder:
                    in_bold = not in_bold
                    escaped_parts.append(part)
                elif part == italic_placeholder:
                    in_italic = not in_italic
                    escaped_parts.append(part)
                elif in_bold or in_italic:
                    # Already escaped above
                    escaped_parts.append(part)
                else:
                    escaped_parts.append(self.escape_xml(part))

            result = "".join(escaped_parts)

            # Convert placeholders to XML tags
            if apply_bold:
                result = result.replace(bold_placeholder, "<b>", 1)
                while bold_placeholder in result:
                    result = result.replace(bold_placeholder, "</b>", 1)
                    if bold_placeholder in result:
                        result = result.replace(bold_placeholder, "<b>", 1)
            else:
                result = result.replace(bold_placeholder, "")

            if apply_italic:
                result = result.replace(italic_placeholder, "<i>", 1)
                while italic_placeholder in result:
                    result = result.replace(italic_placeholder, "</i>", 1)
                    if italic_placeholder in result:
                        result = result.replace(italic_placeholder, "<i>", 1)
            else:
                result = result.replace(italic_placeholder, "")

        else:
            # No escaping, just replace markers with tags
            if apply_bold:
                result = self._bold_pattern.sub(r"<b>\1</b>", result)
            if apply_italic:
                result = self._italic_pattern.sub(r"<i>\1</i>", result)

        return result

    def apply_style(self, text: str, bold: bool = False, italic: bool = False) -> str:
        """
        Wrap entire text in bold and/or italic tags.

        Args:
            text: The text to wrap
            bold: Whether to wrap in bold tags
            italic: Whether to wrap in italic tags

        Returns:
            Text wrapped in appropriate tags
        """
        result = text
        if bold:
            result = f"<b>{result}</b>"
        if italic:
            result = f"<i>{result}</i>"
        return result

    def create_link(self, text: str, destination: str, styled_only: bool = True) -> str:
        """
        Create link text for internal navigation.

        Args:
            text: The display text for the link
            destination: The internal destination (e.g., "page_5")
            styled_only: If True, return styled text without actual link markup.
                        This is needed because ReportLab requires destinations
                        to be defined in the same document, but we're generating
                        prepended pages separately. The actual PDF links are
                        added during the merge phase.

        Returns:
            Styled text indicating a link
        """
        # Escape the text for XML safety
        escaped_text = self.escape_xml(text)
        if styled_only:
            # Return blue underlined text that looks like a link
            # The actual PDF link annotation will be added after merging
            return f'<font color="blue"><u>{escaped_text}</u></font>'
        else:
            # Use actual ReportLab link syntax (requires destination to exist)
            return f'<a href="#{destination}" color="blue">{escaped_text}</a>'
