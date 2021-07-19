"""
Item，数据对象需要继承这个
"""
from typing import Dict


class Item:
    def __init__(self, item_name=None, data: Dict = None):
        """
        @param item_name: item名称
        @param data: 字典，可以直接把字典设置到item
        """
        if item_name:
            self.__class__.__name__ = item_name

        if data:
            self.__dict__.update(**data)

    @property
    def values(self):
        return self.__dict__

    @property
    def item_name(self):
        return self.__class__.__name__

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __repr__(self):
        return f"<{self.item_name} {self.values}>"
