"""
Item，数据对象需要继承这个
"""


class Item:
    @property
    def values(self):
        return self.__dict__

    @property
    def class_name(self):
        return self.__class__.__name__

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __repr__(self):
        return f"<{self.class_name} {self.values}>"
