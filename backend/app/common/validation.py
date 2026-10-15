"""Consistent HTTP validation for shared workflow inputs."""

import math

from fastapi import HTTPException
from pydantic import ValidationError


def parsed(schema, **values):
    try:
        return schema.model_validate(values)
    except ValidationError as error:
        raise HTTPException(422, error.errors(include_context=False)) from error


def number_detail(details, key, default=0, minimum=0):
    try:
        raw = details.get(key, default)
        value = float(default if raw is None or raw == "" else raw)
        if value < minimum or not math.isfinite(value):
            raise ValueError()
    except (TypeError, ValueError) as error:
        raise HTTPException(400, f"{key} için geçerli bir sayı girin.") from error
    return value
