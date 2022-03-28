from typing import Union, Callable


class hybridmethod:
    def __init__(self, fclass: Union[Callable, property], finstance: Union[Callable, property] = None, doc=None):
        self.class_method = fclass
        self.instance_method = finstance
        self.__doc__ = doc or fclass.__doc__
        # support use on abstract base classes
        self.__isabstractmethod__ = bool(
            getattr(fclass, '__isabstractmethod__', False)
        )

    def classmethod(self, fclass):
        return type(self)(fclass, self.instance_method, None)

    def instancemethod(self, finstance):
        return type(self)(self.class_method, finstance, self.__doc__)

    def __get__(self, instance, cls):
        if instance is None or self.instance_method is None:
            # either bound to the class, or no instance method available
            return self.class_method.__get__(cls, None)
        return self.instance_method.__get__(instance, cls)
