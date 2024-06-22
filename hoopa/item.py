"""
Item，数据对象需要继承这个
"""
from copy import deepcopy
from typing import Dict


class Item:
    def __init__(self, item_name=None, data: Dict = None):
        """
        @param item_name: item名称
        @param data: 字典，可以直接把字典设置到item
        """

        self._item_name = item_name if item_name else type(self).__name__  # 使用类名作为默认值

        if data:
            self.__dict__.update(**data)

    @property
    def values(self):
        data = deepcopy(self.__dict__)
        data.pop("_item_name")
        return data

    @property
    def item_name(self):
        return self._item_name

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __repr__(self):
        return f"<{self.item_name} {self.values}>"
