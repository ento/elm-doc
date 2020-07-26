from types import FunctionType


class NamespaceMeta(type):
    def __new__(cls, name, bases, namespaces):
        wrapped_namespaces = {k: staticmethod(v) if type(v) is FunctionType else v
                              for k, v in namespaces.items()}
        return type.__new__(cls, name, bases, wrapped_namespaces)


class Namespace:
    __metaclass__ = NamespaceMeta
