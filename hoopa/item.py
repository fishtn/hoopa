"""
Item，数据对象需要继承这个
"""


class Item:
    def __init__(self, item_name=None):
        if item_name:
            self.__class__.__name__ = item_name

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
