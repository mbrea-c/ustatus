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


def get_python_type(type) -> Type:
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
            return List[get_python_type(type["items"])]


def string(description: Optional[str] = None, default=None) -> Dict[str, str]:
    return primitive("string", description, default)


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


# # Optional settings
# self.show_label: bool = config_dict.get("show_label", False)
# self.label: Optional[str] = config_dict.get("label", None)
# self.length: int = config_dict.get("length", 25)

bar = {
    "type": "object",
    "properties": {
        "anchors": array(string()),
        "output": string(description="Force bar to appear in a given output, or leave empty for auto-choose"),
        "orientation": string(),
        "modules_start": array(string(), default=[]),
        "modules_center": array(string(), default=[]),
        "modules_end": array(string(), default=[]),
        "exclusive": boolean(default=False),
        "width": integer(default=25),
        "separators": boolean(default=False),
    },
    "required": ["anchors", "orientation"],
}

module = {
    "type": "object",
    "properties": {
        "type": string(),
        "show_label": boolean(default=False),
        "label": string(default=None),
        "length": integer(default=25),
    },
    "required": ["type"],
}

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/product.schema.json",
    "title": "Pystatus config",
    "description": "Configuration",
    "type": "object",
    "properties": {"bars": {"type": "object", "additionalProperties": bar}},
    "properties": {"modules": {"type": "object", "additionalProperties": module}},
}
