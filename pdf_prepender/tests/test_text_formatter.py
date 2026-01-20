"""Tests for the text formatter module."""

import pytest

from pdf_prepender.parsers.text_formatter import TextFormatter


class TestTextFormatter:
    """Tests for TextFormatter class."""

    def test_default_markers(self):
        """Test that default markers are set correctly."""
        formatter = TextFormatter()
        assert formatter.bold_marker == "**"
        assert formatter.italic_marker == "_"

    def test_custom_markers(self):
        """Test custom markers can be set."""
        formatter = TextFormatter(bold_marker="__", italic_marker="*")
        assert formatter.bold_marker == "__"
        assert formatter.italic_marker == "*"

    def test_escape_xml_basic(self):
        """Test basic XML character escaping."""
        formatter = TextFormatter()
        assert formatter.escape_xml("Hello & Goodbye") == "Hello &amp; Goodbye"
        assert formatter.escape_xml("<tag>") == "&lt;tag&gt;"
        assert formatter.escape_xml("a > b") == "a &gt; b"

    def test_escape_xml_no_change(self):
        """Test that normal text is unchanged."""
        formatter = TextFormatter()
        assert formatter.escape_xml("Hello World") == "Hello World"
        assert formatter.escape_xml("Test 123") == "Test 123"

    def test_format_bold_text(self):
        """Test bold marker conversion."""
        formatter = TextFormatter()
        result = formatter.format_text("This is **bold** text")
        assert "<b>bold</b>" in result
        assert "**" not in result

    def test_format_italic_text(self):
        """Test italic marker conversion."""
        formatter = TextFormatter()
        result = formatter.format_text("This is _italic_ text")
        assert "<i>italic</i>" in result
        assert result.count("_") == 0 or "_" not in result.replace("<i>", "").replace(
            "</i>", ""
        )

    def test_format_bold_and_italic(self):
        """Test both bold and italic markers in same text."""
        formatter = TextFormatter()
        result = formatter.format_text("**Bold** and _italic_ text")
        assert "<b>Bold</b>" in result
        assert "<i>italic</i>" in result

    def test_format_multiple_bold_sections(self):
        """Test multiple bold sections in same text."""
        formatter = TextFormatter()
        result = formatter.format_text("**First** and **Second** bold")
        assert result.count("<b>") == 2
        assert result.count("</b>") == 2

    def test_format_with_xml_escaping(self):
        """Test formatting with XML characters that need escaping."""
        formatter = TextFormatter()
        result = formatter.format_text("**Bold & Important**")
        assert "<b>" in result
        assert "&amp;" in result

    def test_format_no_bold(self):
        """Test disabling bold formatting."""
        formatter = TextFormatter()
        result = formatter.format_text("**Not bold**", apply_bold=False)
        assert "<b>" not in result
        assert "**" not in result  # Markers should still be removed

    def test_format_no_italic(self):
        """Test disabling italic formatting."""
        formatter = TextFormatter()
        result = formatter.format_text("_Not italic_", apply_italic=False)
        assert "<i>" not in result

    def test_apply_style_bold(self):
        """Test wrapping text in bold."""
        formatter = TextFormatter()
        result = formatter.apply_style("Hello", bold=True)
        assert result == "<b>Hello</b>"

    def test_apply_style_italic(self):
        """Test wrapping text in italic."""
        formatter = TextFormatter()
        result = formatter.apply_style("Hello", italic=True)
        assert result == "<i>Hello</i>"

    def test_apply_style_both(self):
        """Test wrapping text in both bold and italic."""
        formatter = TextFormatter()
        result = formatter.apply_style("Hello", bold=True, italic=True)
        assert result == "<i><b>Hello</b></i>"

    def test_apply_style_neither(self):
        """Test no styling applied."""
        formatter = TextFormatter()
        result = formatter.apply_style("Hello", bold=False, italic=False)
        assert result == "Hello"

    def test_create_link_styled(self):
        """Test creating a styled link (default mode)."""
        formatter = TextFormatter()
        result = formatter.create_link("Click here", "page_5")
        assert "Click here" in result
        assert 'color="blue"' in result
        assert "<u>" in result  # Underlined to indicate link

    def test_create_link_actual(self):
        """Test creating an actual PDF link."""
        formatter = TextFormatter()
        result = formatter.create_link("Click here", "page_5", styled_only=False)
        assert 'href="#page_5"' in result
        assert "Click here" in result

    def test_create_link_escapes_text(self):
        """Test that link text is escaped."""
        formatter = TextFormatter()
        result = formatter.create_link("Click & go", "page_1")
        assert "&amp;" in result

    def test_format_empty_string(self):
        """Test formatting empty string."""
        formatter = TextFormatter()
        result = formatter.format_text("")
        assert result == ""

    def test_format_no_markers(self):
        """Test text without any markers."""
        formatter = TextFormatter()
        result = formatter.format_text("Plain text without markers")
        assert result == "Plain text without markers"

    def test_custom_bold_marker(self):
        """Test with custom bold marker."""
        formatter = TextFormatter(bold_marker="__")
        result = formatter.format_text("This is __bold__ text")
        assert "<b>bold</b>" in result
        assert "__" not in result

    def test_special_regex_chars_in_markers(self):
        """Test markers with special regex characters.

        Note: Markers work as paired delimiters, so [[text[[ becomes bold,
        not [[text]]. If you want [[text]], you'd need single-char markers.
        """
        formatter = TextFormatter(bold_marker="[[", italic_marker="//")
        # Bold markers are paired: [[text[[
        result = formatter.format_text("[[bold[[ text")
        assert "<b>bold</b>" in result

        # Test with different special chars
        formatter2 = TextFormatter(bold_marker="$$", italic_marker="%%")
        result2 = formatter2.format_text("$$bold$$ and %%italic%% text")
        assert "<b>bold</b>" in result2
        assert "<i>italic</i>" in result2
