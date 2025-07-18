# -*- coding: utf-8 -*-
# pylint: disable = R0903

from enum import Enum
from typing import List, Generator

x_sel = lambda x : (x.value[0],x.value[1])
class EnumExt(Enum):

    x_name = lambda x : x.value[0]
    x_value = lambda x : x.value[1]
    x_model = lambda x: x.value[2]

    @classmethod
    def names(cls) -> List[str]:
        return [item.name for item in cls]

    @classmethod
    def keys(cls):
        """Returns a list of all the enum keys."""
        return cls._member_names_

    @classmethod
    def values(cls):
        """Returns a list of all the enum values."""
        return list(cls._value2member_map_.keys())

    @classmethod
    def values_str(cls) -> List[str]:
        return [item.value[1] for item in cls]

    @classmethod
    def values_key(cls) -> List[str]:
        return [item.value[0] for item in cls]

    @classmethod
    def name_values(cls):
        return [(item.name, item.value) for item in cls]

    @staticmethod
    def _get_item(items:object):
        for item in items:
            yield x_sel(item)

    @classmethod
    def get_selection(cls) -> list:
        return list(cls._get_item(cls))

    @classmethod
    def get_dict(cls) -> dict:
        """Get dict with key and empty list
        Returns
        -------
        dict
           {key:[],...:...}
        """
        return { item.value:[] for item in cls}

    @classmethod
    def get_field_and_model(cls, header):
        for item in cls:
            if item.value[0] == header:
                return item.value[1], item.value[2]
        return None, None

    @classmethod
    def get_internal_value(cls, readable_name):
        """Returns the internal value for a given human-readable name."""
        for status in cls:
            if status.value[1] == readable_name:
                return status.value[0]
        return None
        # raise ValueError(f"No matching internal value found for '{readable_name}'")

    @classmethod
    def to_dict(cls):
        """Returns a dictionary representation of the enum."""
        return {e.name: e.value for e in cls}

    @classmethod
    def filter_keys(cls, headers):
        """Filter keys based on the headers present in the file."""
        return [key for key, value in cls.to_dict().items() if value[0] in headers]
