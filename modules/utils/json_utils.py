import ast
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import pandas as pd


class JSONUtils:
    class EnhancedEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.replace(tzinfo=None).isoformat()
            elif isinstance(obj, timedelta):
                return str(obj)
            elif isinstance(obj, pd.Series):
                return obj.to_dict()
            return super().default(obj)

    @staticmethod
    def dumps(*args, **kwargs) -> str:
        return json.dumps(*args, **kwargs, cls=JSONUtils.EnhancedEncoder)

    @staticmethod
    def flatten(d: dict, parent_key: str = "", sep: str = ".") -> dict:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(JSONUtils.flatten(v, new_key, sep=sep).items())
            elif isinstance(v, pd.Series):
                items.append((new_key, v.to_dict()))
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def load_json_like(json_like_str: Optional[str]) -> dict:
        """
        Load a string that looks like a JSON object into a Python dictionary.
        Compatible with trailing commas and single quotes.
        """
        if json_like_str is None or not json_like_str.strip():
            return {}
        py_dict = {}
        try:
            # to prevent trailing commas
            py_dict = ast.literal_eval(f'{{"k": {json_like_str}}}')["k"]
        except (ValueError, SyntaxError) as e1:
            try:
                py_dict = json.loads(json_like_str)
            except json.JSONDecodeError as e2:
                raise ValueError(f"Invalid value: {e1} or {e2}")
        return py_dict
