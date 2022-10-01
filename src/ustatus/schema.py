from argparse import ArgumentError
from typing import Dict, List, Optional, Type


def primitive(
    type: str = "string", description: Optional[str] = None, default=None
) -> Dict[str, str]:
    obj = dict({"type": type})
    if description is not None:
        obj["description"] = description
    if default is not None:
        obj["default"] = default
    return obj


def cmdline_friendly(type: Dict) -> bool:
    if "type" in type:
        match type["type"]:
            case "string":
                return True
            case "boolean":
                return True
            case "integer":
                return True
            case "integer":
                return True
            case "array":
                match type["items"]["type"]:
                    case "string":
                        return True
    return False


def get_python_type(type: Dict) -> Type:
    if "type" in type:
        match type["type"]:
            case "string":
                return str
            case "boolean":
                return bool
            case "integer":
                return int
            case "integer":
                return int
            case "array":
                match type["items"]["type"]:
                    case "string":
                        return lambda string: string.split(",")


def string(description: Optional[str] = None, default=None) -> Dict:
    return primitive("string", description, default)


def string_enum(values: List[str], description: Optional[str] = None, default=None):
    obj = string(description=description, default=default)
    obj["enum"] = values
    return obj


def any_of(types: List, description: Optional[str] = None, default=None) -> Dict:
    obj: Dict = dict()
    obj["anyOf"] = types
    if description is not None:
        obj["description"] = description
    if default is not None:
        obj["default"] = default
    return obj


def boolean(description: Optional[str] = None, default=None) -> Dict[str, str]:
    return primitive("boolean", description, default)


def integer(description: Optional[str] = None, default=None) -> Dict[str, str]:
    return primitive("integer", description, default)


def array(items=string(), description: Optional[str] = None, default=None):
    obj = dict({"type": "array", "items": items})
    if description is not None:
        obj["description"] = description
    if default is not None:
        obj["default"] = default
    return obj


bar_size = any_of([integer(), string_enum(["auto"])], default="auto")

bar = {
    "type": "object",
    "properties": {
        "anchors": array(string()),
        "output": string(
            description="Force bar to appear in a given output, or leave empty for auto-choose"
        ),
        "orientation": string(),
        "modules_start": array(string(), default=[]),
        "modules_center": array(string(), default=[]),
        "modules_end": array(string(), default=[]),
        "exclusive": boolean(default=False),
        "width": bar_size,
        "height": bar_size,
        "separators": boolean(default=False),
        "theme_override": string(),
    },
    "required": ["anchors", "orientation"],
}

module = {
    "type": "object",
    "properties": {
        "type": string(),
        "show_label": boolean(default=False),
        "label": string(default="Label"),
        "length": integer(default=25),
    },
    "required": ["type"],
}

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/product.schema.json",
    "title": "Ustatus config",
    "description": "Configuration",
    "type": "object",
    "properties": {"bars": {"type": "object", "additionalProperties": bar}},
    "properties": {"modules": {"type": "object", "additionalProperties": module}},
}
