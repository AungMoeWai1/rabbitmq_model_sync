from enum import IntEnum

from typing import Optional
from .enum_ext import EnumExt

from datetime import datetime

from pydantic import BaseModel


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


