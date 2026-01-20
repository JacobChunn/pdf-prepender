"""JSON parser for converting JSON input to Pydantic models."""

import json
from pathlib import Path
from typing import IO

from pydantic import ValidationError

from pdf_prepender.models.schema import PrependSpecification


class JsonParseError(Exception):
    """Exception raised when JSON parsing fails."""

    def __init__(self, message: str, errors: list | None = None):
        super().__init__(message)
        self.errors = errors or []


def parse_json_file(file_path: str | Path) -> PrependSpecification:
    """
    Parse a JSON file into a PrependSpecification.

    Args:
        file_path: Path to the JSON file

    Returns:
        Validated PrependSpecification model

    Raises:
        JsonParseError: If the file cannot be read or parsed
        FileNotFoundError: If the file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return parse_json_stream(f)
    except json.JSONDecodeError as e:
        raise JsonParseError(f"Invalid JSON syntax: {e}")


def parse_json_stream(stream: IO[str]) -> PrependSpecification:
    """
    Parse a JSON stream into a PrependSpecification.

    Args:
        stream: A file-like object containing JSON data

    Returns:
        Validated PrependSpecification model

    Raises:
        JsonParseError: If the JSON is invalid or doesn't match the schema
    """
    try:
        data = json.load(stream)
        return parse_json_dict(data)
    except json.JSONDecodeError as e:
        raise JsonParseError(f"Invalid JSON syntax: {e}")


def parse_json_string(json_string: str) -> PrependSpecification:
    """
    Parse a JSON string into a PrependSpecification.

    Args:
        json_string: A string containing JSON data

    Returns:
        Validated PrependSpecification model

    Raises:
        JsonParseError: If the JSON is invalid or doesn't match the schema
    """
    try:
        data = json.loads(json_string)
        return parse_json_dict(data)
    except json.JSONDecodeError as e:
        raise JsonParseError(f"Invalid JSON syntax: {e}")


def parse_json_dict(data: dict) -> PrependSpecification:
    """
    Parse a dictionary into a PrependSpecification.

    Args:
        data: A dictionary containing the specification data

    Returns:
        Validated PrependSpecification model

    Raises:
        JsonParseError: If the data doesn't match the schema
    """
    try:
        return PrependSpecification.model_validate(data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"{loc}: {msg}")
        raise JsonParseError(
            f"JSON validation failed with {len(errors)} error(s)",
            errors=errors,
        )
