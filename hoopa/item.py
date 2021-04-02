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

    def __repr__(self):
        return f"<{self.class_name} {self.values}>"