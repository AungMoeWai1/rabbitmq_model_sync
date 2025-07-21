# *- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel

from .enum_ext import EnumExt


class RecordStatus(EnumExt):
    NEW = ('new', 'New')
    SUCCESS = ('success', 'Success')
    FAIL = ('fail', 'Fail')

class OperationType(EnumExt):
    CREATE = ('create', 'Create')
    WRITE = ('write', 'Write')

class RabbitMQConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    queue: str
    virtual_host: Optional[str] = '/'

class LogValues(BaseModel):
    queue_name: str
    data: dict
    operation: str
    model_name: str
    record_id: Optional[int] = None

class ExchangeType(EnumExt):
    DIRECT = ('direct', 'Direct')
    TOPIC = ('topic', 'Topic')
    FANOUT = ('fanout', 'Fanout')
    HEADER = ('header', 'Header')

class RabbitMQConsumerState(EnumExt):
    DRAFT = ('draft', 'Draft')
    STOP = ('stop', 'Stop')
    RUNNING = ('running', 'Running')
