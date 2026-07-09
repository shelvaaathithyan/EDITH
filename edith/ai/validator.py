import json
from pathlib import Path
from typing import Dict, Any
from jsonschema import validate, ValidationError
from edith.ai.exceptions import JSONValidationError
from edith.utils.logger import logger

SCHEMAS_DIR = Path("edith/ai/schemas")

class ResponseValidator:
    def __init__(self):
        self.schemas = {}
        self._load_schemas()

    def _load_schemas(self):
        try:
            for schema_name in ["execution", "chat", "error"]:
                path = SCHEMAS_DIR / f"{schema_name}.json"
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        self.schemas[schema_name] = json.load(f)
                else:
                    logger.warning(f"Schema {schema_name}.json not found at {path}")
        except Exception as e:
            logger.error(f"Failed to load schemas: {e}")

    def validate_raw(self, raw_json: str) -> Dict[str, Any]:
        """Parses the raw JSON string and validates it against the schema based on its 'type'."""
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise JSONValidationError(f"Invalid JSON string: {e}")

        if not isinstance(data, dict):
            raise JSONValidationError("Root JSON object must be a dictionary.")

        resp_type = data.get("type")
        if not resp_type:
            raise JSONValidationError("Missing 'type' field in JSON response.")

        schema = self.schemas.get(resp_type)
        if not schema:
            raise JSONValidationError(f"Unknown response type '{resp_type}'. Cannot validate.")

        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            raise JSONValidationError(f"Schema validation failed: {e.message}")

        return data
