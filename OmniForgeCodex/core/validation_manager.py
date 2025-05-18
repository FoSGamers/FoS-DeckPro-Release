from typing import Dict, Any, List, Optional, Union, Tuple, Type, Callable
from pathlib import Path
import json
import jsonschema
import yaml
import re
import datetime
import decimal
import uuid
from dataclasses import dataclass
from enum import Enum
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib
import copy
from collections import defaultdict

class ValidationLevel(Enum):
    STRICT = "strict"
    NORMAL = "normal"
    RELAXED = "relaxed"

class ValidationError(Exception):
    def __init__(self, message: str, field: str = None, value: Any = None, schema: Dict = None):
        super().__init__(message)
        self.field = field
        self.value = value
        self.schema = schema

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError] 