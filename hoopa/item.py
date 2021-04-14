"""
Item，数据对象需要继承这个
"""


class Item:
    def __init__(self, name=None):
        if name:
            self.__class__.__name__ = name

    @property
    def values(self):
        return self.__dict__

    @property
    def name(self):
        return self.__class__.__name__

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __repr__(self):
        return f"<{self.name} {self.values}>"
