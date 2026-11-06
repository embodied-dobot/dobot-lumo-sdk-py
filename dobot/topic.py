class Topic:
    """一条 DDS 话题。name 是话题字符串，type_name 是消息类型。"""

    def __init__(self, name, type_name):
        self.name = name
        self.type_name = type_name

    def __repr__(self):
        return f"Topic({self.name!r}, {self.type_name!r})"
