"""Link manager for handling internal link page offset calculations."""

from dataclasses import dataclass, field


@dataclass
class LinkInfo:
    """Information about a link to a page in the original document."""

    original_page: int
    adjusted_page: int | None = None

    @property
    def destination_name(self) -> str:
        """Get the named destination for this link."""
        page = self.adjusted_page if self.adjusted_page is not None else self.original_page
        return f"page_{page}"


@dataclass
class LinkManager:
    """Manages internal links and their page offset adjustments."""

    prepended_page_count: int = 0
    _links: list[LinkInfo] = field(default_factory=list)

    def register_link(self, original_page: int) -> LinkInfo:
        """
        Register a link to a page in the original document.

        Args:
            original_page: The 1-indexed page number in the original document

        Returns:
            LinkInfo object for this link
        """
        link = LinkInfo(original_page=original_page)
        self._links.append(link)
        return link

    def set_prepended_page_count(self, count: int) -> None:
        """
        Set the number of prepended pages and update all link targets.

        Args:
            count: The number of pages being prepended
        """
        self.prepended_page_count = count
        self._update_all_links()

    def _update_all_links(self) -> None:
        """Update all registered links with adjusted page numbers."""
        for link in self._links:
            link.adjusted_page = link.original_page + self.prepended_page_count

    def get_adjusted_page(self, original_page: int) -> int:
        """
        Calculate the adjusted page number after prepending.

        Args:
            original_page: The 1-indexed page number in the original document

        Returns:
            The adjusted page number in the final document
        """
        return original_page + self.prepended_page_count

    def get_destination_name(self, original_page: int) -> str:
        """
        Get the named destination for a page in the original document.

        Args:
            original_page: The 1-indexed page number in the original document

        Returns:
            The destination name (e.g., "page_5" after adjusting for offset)
        """
        adjusted = self.get_adjusted_page(original_page)
        return f"page_{adjusted}"

    def clear(self) -> None:
        """Clear all registered links."""
        self._links.clear()

    @property
    def link_count(self) -> int:
        """Get the number of registered links."""
        return len(self._links)

    def generate_all_destinations(self, total_pages: int) -> list[str]:
        """
        Generate destination names for all pages in the final document.

        Args:
            total_pages: Total number of pages in the final document

        Returns:
            List of destination names for all pages
        """
        return [f"page_{i}" for i in range(1, total_pages + 1)]
