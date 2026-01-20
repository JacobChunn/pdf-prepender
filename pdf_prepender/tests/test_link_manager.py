"""Tests for the link manager module."""

import pytest

from pdf_prepender.core.link_manager import LinkInfo, LinkManager


class TestLinkInfo:
    """Tests for LinkInfo dataclass."""

    def test_destination_name_without_adjustment(self):
        """Test destination name without page adjustment."""
        link = LinkInfo(original_page=5)
        assert link.destination_name == "page_5"

    def test_destination_name_with_adjustment(self):
        """Test destination name with page adjustment."""
        link = LinkInfo(original_page=5, adjusted_page=8)
        assert link.destination_name == "page_8"

    def test_original_page_stored(self):
        """Test that original page is stored correctly."""
        link = LinkInfo(original_page=10)
        assert link.original_page == 10
        assert link.adjusted_page is None


class TestLinkManager:
    """Tests for LinkManager class."""

    def test_initial_state(self):
        """Test initial state of link manager."""
        manager = LinkManager()
        assert manager.prepended_page_count == 0
        assert manager.link_count == 0

    def test_register_link(self):
        """Test registering a link."""
        manager = LinkManager()
        link = manager.register_link(5)
        assert link.original_page == 5
        assert manager.link_count == 1

    def test_register_multiple_links(self):
        """Test registering multiple links."""
        manager = LinkManager()
        manager.register_link(3)
        manager.register_link(5)
        manager.register_link(7)
        assert manager.link_count == 3

    def test_set_prepended_page_count(self):
        """Test setting prepended page count."""
        manager = LinkManager()
        manager.set_prepended_page_count(2)
        assert manager.prepended_page_count == 2

    def test_links_updated_on_set_count(self):
        """Test that links are updated when page count is set."""
        manager = LinkManager()
        link = manager.register_link(5)
        manager.set_prepended_page_count(3)
        assert link.adjusted_page == 8

    def test_get_adjusted_page(self):
        """Test getting adjusted page number."""
        manager = LinkManager()
        manager.set_prepended_page_count(2)
        assert manager.get_adjusted_page(5) == 7
        assert manager.get_adjusted_page(1) == 3
        assert manager.get_adjusted_page(10) == 12

    def test_get_adjusted_page_no_prepend(self):
        """Test adjusted page when nothing is prepended."""
        manager = LinkManager()
        assert manager.get_adjusted_page(5) == 5

    def test_get_destination_name(self):
        """Test getting destination name for a page."""
        manager = LinkManager()
        manager.set_prepended_page_count(2)
        assert manager.get_destination_name(5) == "page_7"
        assert manager.get_destination_name(1) == "page_3"

    def test_get_destination_name_no_prepend(self):
        """Test destination name without prepending."""
        manager = LinkManager()
        assert manager.get_destination_name(5) == "page_5"

    def test_clear(self):
        """Test clearing registered links."""
        manager = LinkManager()
        manager.register_link(3)
        manager.register_link(5)
        assert manager.link_count == 2
        manager.clear()
        assert manager.link_count == 0

    def test_generate_all_destinations(self):
        """Test generating destination names for all pages."""
        manager = LinkManager()
        destinations = manager.generate_all_destinations(5)
        assert destinations == ["page_1", "page_2", "page_3", "page_4", "page_5"]

    def test_generate_all_destinations_empty(self):
        """Test generating destinations for zero pages."""
        manager = LinkManager()
        destinations = manager.generate_all_destinations(0)
        assert destinations == []

    def test_two_pass_scenario(self):
        """Test the typical two-pass link adjustment scenario."""
        manager = LinkManager()

        # First pass: register links (page count unknown)
        link1 = manager.register_link(3)
        link2 = manager.register_link(5)
        link3 = manager.register_link(7)

        # Simulate first pass generated 2 prepended pages
        manager.set_prepended_page_count(2)

        # Verify all links are adjusted
        assert link1.adjusted_page == 5  # 3 + 2
        assert link2.adjusted_page == 7  # 5 + 2
        assert link3.adjusted_page == 9  # 7 + 2

        # Verify destination names
        assert link1.destination_name == "page_5"
        assert link2.destination_name == "page_7"
        assert link3.destination_name == "page_9"

    def test_prepend_single_page(self):
        """Test with single page prepended."""
        manager = LinkManager()
        manager.set_prepended_page_count(1)
        assert manager.get_destination_name(1) == "page_2"
        assert manager.get_adjusted_page(10) == 11
