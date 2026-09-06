"""Dependency-free JSON Schema validation for GEO diagnostic artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SchemaValidator:
    """Validates the JSON Schema subset used by the repository schemas."""

    def __init__(self, schema: dict[str, Any], base_dir: str | Path | None = None) -> None:
        self.schema = schema
        self.base_dir = Path(base_dir) if base_dir is not None else None
        self._external: dict[str, dict[str, Any]] = {}

    def validate(self, instance: Any) -> list[str]:
        errors: list[str] = []
        self._validate(instance, self.schema, self.schema, "$", errors)
        return errors

    def _validate(
        self,
        instance: Any,
        schema: Any,
        root: dict[str, Any],
        path: str,
        errors: list[str],
    ) -> None:
        if not isinstance(schema, dict):
            return

        ref = schema.get("$ref")
        if isinstance(ref, str):
            resolved = None
            resolved_root = root
            if ref.startswith("#/"):
                resolved = _resolve_pointer(root, ref)
            elif self.base_dir is not None:
                resolved = _resolve_external(self, ref)
                if resolved is not None:
                    resolved_root = resolved
            if resolved is None:
                errors.append(f"{path}: unresolved $ref {ref}")
                return
            self._validate(instance, resolved, resolved_root, path, errors)

        expected = schema.get("type")
        if expected is not None and not _matches_type(instance, expected):
            errors.append(f"{path}: expected {expected}, got {_type_name(instance)}")

        if "enum" in schema and instance not in schema["enum"]:
            errors.append(f"{path}: value must be one of {schema['enum']}")

        if isinstance(instance, dict):
            properties = schema.get("properties")
            if isinstance(properties, dict):
                for key, subschema in properties.items():
                    if key in instance:
                        self._validate(
                            instance[key],
                            subschema,
                            root,
                            f"{path}.{key}",
                            errors,
                        )
            required = schema.get("required")
            if isinstance(required, list):
                for key in required:
                    if key not in instance:
                        errors.append(f"{path}: missing required property '{key}'")
            if schema.get("additionalProperties") is False:
                allowed = set(properties) if isinstance(properties, dict) else set()
                for key in instance:
                    if key not in allowed:
                        errors.append(f"{path}: unexpected property '{key}'")

        if isinstance(instance, list):
            items = schema.get("items")
            if isinstance(items, dict):
                for index, value in enumerate(instance):
                    self._validate(value, items, root, f"{path}[{index}]", errors)
            min_items = schema.get("minItems")
            if isinstance(min_items, int) and len(instance) < min_items:
                errors.append(f"{path}: expected at least {min_items} items")

        if isinstance(instance, str):
            min_length = schema.get("minLength")
            if isinstance(min_length, int) and len(instance) < min_length:
                errors.append(f"{path}: expected at least {min_length} characters")

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")
            if isinstance(minimum, (int, float)) and instance < minimum:
                errors.append(f"{path}: expected >= {minimum}")
            if isinstance(maximum, (int, float)) and instance > maximum:
                errors.append(f"{path}: expected <= {maximum}")

        all_of = schema.get("allOf")
        if isinstance(all_of, list):
            for subschema in all_of:
                self._validate(instance, subschema, root, path, errors)

    def errors_text(self, errors: list[str]) -> str:
        return "\n".join(errors)


def validate_against_schema(instance: Any, schema: dict[str, Any]) -> list[str]:
    return SchemaValidator(schema).validate(instance)


def validate_against_schema_file(instance: Any, schema_path: str | Path) -> list[str]:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError("schema file must contain a JSON object")
    return SchemaValidator(schema, base_dir=Path(schema_path).resolve().parent).validate(instance)


def _matches_type(instance: Any, expected: Any) -> bool:
    expectations = expected if isinstance(expected, list) else [expected]
    for expectation in expectations:
        if expectation == "object":
            if isinstance(instance, dict):
                return True
        elif expectation == "array":
            if isinstance(instance, list):
                return True
        elif expectation == "string":
            if isinstance(instance, str):
                return True
        elif expectation == "number":
            if isinstance(instance, (int, float)) and not isinstance(instance, bool):
                return True
        elif expectation == "integer":
            if isinstance(instance, int) and not isinstance(instance, bool):
                return True
        elif expectation == "boolean":
            if isinstance(instance, bool):
                return True
        elif expectation == "null":
            if instance is None:
                return True
    return False


def _type_name(instance: Any) -> str:
    if instance is None:
        return "null"
    if isinstance(instance, bool):
        return "boolean"
    if isinstance(instance, dict):
        return "object"
    if isinstance(instance, list):
        return "array"
    return type(instance).__name__


def _resolve_pointer(root: dict[str, Any], ref: str) -> Any | None:
    if not ref.startswith("#/"):
        return None
    current: Any = root
    for raw_part in ref[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            current = current[index] if index < len(current) else None
        else:
            return None
    return current


def _resolve_external(
    validator: SchemaValidator,
    ref: str,
) -> dict[str, Any] | None:
    if validator.base_dir is None or not ref or ref.startswith("#/"):
        return None
    path = validator.base_dir / ref
    if path in validator._external:
        return validator._external[str(path)]
    if not path.exists():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return None
    validator._external[str(path)] = loaded
    return loaded
