# pylint: disable = E0402,C0301,R0903
"""This file is part of SME intellect Odoo Apps.
Copyright (C) 2023 SME intellect (<https://www.smeintellect.com>).
This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
"""
# *- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel

from .enum_ext import EnumExt


class RecordStatus(EnumExt):
    """Enum for record status."""

    NEW = ("new", "New")
    SUCCESS = ("success", "Success")
    FAIL = ("fail", "Fail")


class OperationType(EnumExt):
    """Enum for operation types."""

    CREATE = ("create", "Create")
    WRITE = ("write", "Write")


class RabbitMQConfig(BaseModel):
    """Configuration for RabbitMQ connection."""

    host: str
    port: int
    user: str
    password: str
    queue: str
    virtual_host: Optional[str] = "/"


class LogValues(BaseModel):
    """Data model for RabbitMQ log values."""

    queue_name: str
    data: dict
    operation: str
    model_name: str
    record_id: Optional[int] = None


class ExchangeType(EnumExt):
    """Enum for RabbitMQ exchange types."""

    DIRECT = ("direct", "Direct")
    TOPIC = ("topic", "Topic")
    FANOUT = ("fanout", "Fanout")
    HEADER = ("header", "Header")


class RabbitMQConsumerState(EnumExt):
    """Enum for RabbitMQ consumer states."""

    DRAFT = ("draft", "Draft")
    STOP = ("stop", "Stop")
    RUNNING = ("running", "Running")
