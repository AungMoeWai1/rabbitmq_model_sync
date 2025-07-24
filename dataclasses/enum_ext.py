# pylint: disable = R0903,C3001,C0301,C0103,E1101
"""This file is part of SME intellect Odoo Apps.
Copyright (C) 2023 SME intellect (<https://www.smeintellect.com>).
This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
"""

from enum import Enum
from typing import List

x_sel = lambda x : (x.value[0],x.value[1])
class EnumExt(Enum):
    """Extended Enum class with additional utility methods."""

    x_name = lambda x : x.value[0]
    x_value = lambda x : x.value[1]
    x_model = lambda x: x.value[2]

    @classmethod
    def names(cls) -> List[str]:
        """Returns a list of all the enum names."""
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
        """Returns a list of all the enum values as strings."""
        return [item.value[1] for item in cls]

    @classmethod
    def values_key(cls) -> List[str]:
        """Returns a list of all the enum values as keys."""
        return [item.value[0] for item in cls]

    @classmethod
    def name_values(cls):
        """Returns a list of tuples with name and value."""
        return [(item.name, item.value) for item in cls]

    @staticmethod
    def _get_item(items:object):
        """Get items from enum."""
        for item in items:
            yield x_sel(item)

    @classmethod
    def get_selection(cls) -> list:
        """Get selection list for use in Odoo fields."""
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
        """Get field and model from header."""
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
