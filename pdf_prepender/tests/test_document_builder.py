"""Tests for the document builder module."""

import io
from pathlib import Path

import pytest
from pypdf import PdfReader

from pdf_prepender.core.document_builder import DocumentBuilder, prepend_pages
from pdf_prepender.parsers.json_parser import JsonParseError


class TestDocumentBuilder:
    """Tests for DocumentBuilder class."""

    def test_from_dict(self, simple_spec_dict: dict):
        """Test creating builder from dictionary."""
        builder = DocumentBuilder.from_dict(simple_spec_dict)
        assert builder.spec is not None
        assert len(builder.spec.pages) == 1

    def test_from_json_string(self, simple_spec_dict: dict):
        """Test creating builder from JSON string."""
        import json

        json_str = json.dumps(simple_spec_dict)
        builder = DocumentBuilder.from_json_string(json_str)
        assert builder.spec is not None

    def test_from_json_file(self, tmp_path: Path, simple_spec_dict: dict):
        """Test creating builder from JSON file."""
        import json

        json_path = tmp_path / "spec.json"
        json_path.write_text(json.dumps(simple_spec_dict))

        builder = DocumentBuilder.from_json_file(json_path)
        assert builder.spec is not None

    def test_get_prepend_page_count(self, simple_spec_dict: dict):
        """Test counting prepended pages."""
        builder = DocumentBuilder.from_dict(simple_spec_dict)
        count = builder.get_prepend_page_count()
        assert count >= 1

    def test_build_returns_bytes(
        self, simple_spec_dict: dict, sample_pdf_bytes: bytes
    ):
        """Test that build returns PDF bytes when no output specified."""
        builder = DocumentBuilder.from_dict(simple_spec_dict)
        result = builder.build(sample_pdf_bytes)
        assert result is not None
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_build_to_file(
        self, simple_spec_dict: dict, sample_pdf_path: Path, tmp_path: Path
    ):
        """Test building to a file."""
        builder = DocumentBuilder.from_dict(simple_spec_dict)
        output_path = tmp_path / "output.pdf"
        builder.build_to_file(sample_pdf_path, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_build_with_stream_output(
        self, simple_spec_dict: dict, sample_pdf_bytes: bytes
    ):
        """Test building to a stream."""
        builder = DocumentBuilder.from_dict(simple_spec_dict)
        output_stream = io.BytesIO()
        result = builder.build(sample_pdf_bytes, output=output_stream)

        assert result is None
        output_stream.seek(0)
        content = output_stream.read()
        assert content.startswith(b"%PDF")

    def test_prepended_pages_come_first(
        self, simple_spec_dict: dict, sample_pdf_bytes: bytes
    ):
        """Test that prepended pages appear at the beginning."""
        builder = DocumentBuilder.from_dict(simple_spec_dict)
        result = builder.build(sample_pdf_bytes)

        reader = PdfReader(io.BytesIO(result))
        # Original PDF has 10 pages, should now have more
        assert len(reader.pages) > 10

    def test_multi_page_prepend(
        self, multi_page_spec_dict: dict, sample_pdf_bytes: bytes
    ):
        """Test prepending multiple pages."""
        builder = DocumentBuilder.from_dict(multi_page_spec_dict)
        prepend_count = builder.get_prepend_page_count()
        result = builder.build(sample_pdf_bytes)

        reader = PdfReader(io.BytesIO(result))
        # Original had 10, should now have 10 + prepend_count
        assert len(reader.pages) == 10 + prepend_count

    def test_named_destinations_created(
        self, simple_spec_dict: dict, sample_pdf_bytes: bytes
    ):
        """Test that named destinations are created."""
        builder = DocumentBuilder.from_dict(simple_spec_dict)
        result = builder.build(sample_pdf_bytes)

        reader = PdfReader(io.BytesIO(result))
        # Check that named destinations exist
        destinations = reader.named_destinations
        assert destinations is not None
        # Should have destinations for all pages
        total_pages = len(reader.pages)
        for i in range(1, total_pages + 1):
            assert f"page_{i}" in destinations


class TestPrependPagesFunction:
    """Tests for the prepend_pages convenience function."""

    def test_with_dict_spec(self, simple_spec_dict: dict, sample_pdf_bytes: bytes):
        """Test prepend_pages with dict specification."""
        result = prepend_pages(simple_spec_dict, sample_pdf_bytes)
        assert result is not None
        assert result.startswith(b"%PDF")

    def test_with_json_string(self, simple_spec_dict: dict, sample_pdf_bytes: bytes):
        """Test prepend_pages with JSON string."""
        import json

        json_str = json.dumps(simple_spec_dict)
        result = prepend_pages(json_str, sample_pdf_bytes)
        assert result is not None
        assert result.startswith(b"%PDF")

    def test_with_json_file(
        self, tmp_path: Path, simple_spec_dict: dict, sample_pdf_path: Path
    ):
        """Test prepend_pages with JSON file path."""
        import json

        json_path = tmp_path / "spec.json"
        json_path.write_text(json.dumps(simple_spec_dict))

        result = prepend_pages(json_path, sample_pdf_path)
        assert result is not None
        assert result.startswith(b"%PDF")

    def test_with_output_path(
        self,
        tmp_path: Path,
        simple_spec_dict: dict,
        sample_pdf_bytes: bytes,
    ):
        """Test prepend_pages with output path."""
        output_path = tmp_path / "output.pdf"
        result = prepend_pages(simple_spec_dict, sample_pdf_bytes, output=output_path)

        assert result is None
        assert output_path.exists()


class TestLinkOffsetCalculation:
    """Tests for the two-pass link offset algorithm."""

    def test_link_offset_single_page(
        self, sample_pdf_bytes: bytes
    ):
        """Test link offset with single prepended page."""
        spec = {
            "pages": [
                {
                    "pageHeading": {"text": "Contents"},
                    "content": [
                        {
                            "type": "bulletPoint",
                            "label": "Link:",
                            "content": [{"text": "Page 3", "targetPage": 3}],
                        }
                    ],
                }
            ]
        }
        builder = DocumentBuilder.from_dict(spec)

        # Build to set up the link manager properly
        builder.build(sample_pdf_bytes)

        prepend_count = builder.link_manager.prepended_page_count
        # After prepending 1 page, link to original page 3 should go to page 4
        assert prepend_count == 1
        assert builder.link_manager.get_adjusted_page(3) == 4

    def test_link_offset_multi_page(
        self, multi_page_spec_dict: dict, sample_pdf_bytes: bytes
    ):
        """Test link offset with multiple prepended pages."""
        builder = DocumentBuilder.from_dict(multi_page_spec_dict)

        # Build to calculate page count
        builder.build(sample_pdf_bytes)

        # With 2 prepended pages, original page 5 should become page 7
        prepend_count = builder.link_manager.prepended_page_count
        assert prepend_count == 2
        assert builder.link_manager.get_adjusted_page(5) == 7
        assert builder.link_manager.get_adjusted_page(7) == 9
