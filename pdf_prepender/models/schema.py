"""Pydantic models for PDF prepender JSON schema validation."""

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator


class OverflowBehavior(str, Enum):
    """Defines how content should behave when it exceeds available space."""

    NO_WRAP = "noWrap"
    WRAP = "wrap"
    WRAP_WITH_PAGE_BREAK = "wrapWithPageBreak"


class Alignment(str, Enum):
    """Text alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class PageSize(str, Enum):
    """Supported page sizes."""

    LETTER = "letter"
    A4 = "a4"
    LEGAL = "legal"


class Defaults(BaseModel):
    """Default settings for the document."""

    font_size: int = Field(default=11, alias="fontSize", ge=6, le=72)
    bold_marker: str = Field(default="**", alias="boldMarker")
    italic_marker: str = Field(default="_", alias="italicMarker")
    page_size: PageSize = Field(default=PageSize.LETTER, alias="pageSize")
    left_margin: float = Field(default=72.0, alias="leftMargin")
    right_margin: float = Field(default=72.0, alias="rightMargin")
    top_margin: float = Field(default=72.0, alias="topMargin")
    bottom_margin: float = Field(default=72.0, alias="bottomMargin")

    model_config = {"populate_by_name": True}


class PageHeading(BaseModel):
    """Page heading that forces a new page."""

    text: str
    font_size: int | None = Field(default=None, alias="fontSize", ge=6, le=72)
    bold: bool = False
    italic: bool = False
    alignment: Alignment = Alignment.LEFT

    model_config = {"populate_by_name": True}


class LinkableItem(BaseModel):
    """A clickable item that links to a page in the original document."""

    text: str
    target_page: int = Field(alias="targetPage", ge=1)

    model_config = {"populate_by_name": True}


class SectionHeading(BaseModel):
    """Main section heading."""

    type: Literal["sectionHeading"]
    text: str
    font_size: int | None = Field(default=None, alias="fontSize", ge=6, le=72)
    bold: bool = True
    italic: bool = False
    alignment: Alignment = Alignment.LEFT

    model_config = {"populate_by_name": True}


class SectionSubheading(BaseModel):
    """Subheading that provides context under a section heading."""

    type: Literal["sectionSubheading"]
    text: str
    font_size: int | None = Field(default=None, alias="fontSize", ge=6, le=72)
    bold: bool = False
    italic: bool = True
    alignment: Alignment = Alignment.LEFT

    model_config = {"populate_by_name": True}


class BulletPoint(BaseModel):
    """Bullet point with label and content (plain text or linkable items)."""

    type: Literal["bulletPoint"]
    label: str
    content: list[str | LinkableItem]
    font_size: int | None = Field(default=None, alias="fontSize", ge=6, le=72)
    overflow_behavior: OverflowBehavior = Field(
        default=OverflowBehavior.WRAP, alias="overflowBehavior"
    )

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_content(self) -> "BulletPoint":
        """Ensure content list is not empty."""
        if not self.content:
            raise ValueError("content list cannot be empty")
        return self


class IndentedBulletPoint(BaseModel):
    """Indented bullet point with label and content."""

    type: Literal["indentedBulletPoint"]
    label: str
    content: list[str | LinkableItem]
    font_size: int | None = Field(default=None, alias="fontSize", ge=6, le=72)
    overflow_behavior: OverflowBehavior = Field(
        default=OverflowBehavior.WRAP, alias="overflowBehavior"
    )

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_content(self) -> "IndentedBulletPoint":
        """Ensure content list is not empty."""
        if not self.content:
            raise ValueError("content list cannot be empty")
        return self


# Discriminated union for content elements
ContentElement = Annotated[
    Union[SectionHeading, SectionSubheading, BulletPoint, IndentedBulletPoint],
    Field(discriminator="type"),
]


class Page(BaseModel):
    """A single page specification."""

    page_heading: PageHeading | None = Field(default=None, alias="pageHeading")
    content: list[ContentElement] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class PrependSpecification(BaseModel):
    """Root model for the complete prepend specification."""

    defaults: Defaults = Field(default_factory=Defaults)
    pages: list[Page] = Field(min_length=1)

    model_config = {"populate_by_name": True}
