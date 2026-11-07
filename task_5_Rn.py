"""Фабрика классов неизменяемых точек в n-мерном пространстве Rn.

Модуль содержит дескриптор CoordDescriptor, проверяющий тип координат,
и функцию-фабрику make_point_class, которая создаёт класс точки с
координатами x0, x1, ..., x(n-1). Созданные классы кэшируются, точки
неизменяемы, а «изменение» выполняется созданием новой точки через
метод replace().
"""
from functools import lru_cache

class CoordDescriptor:
    """Дескриптор одной координаты точки.

    Проверяет, что значение — число типа int или float (bool не
    допускается), и разрешает задать координату только один раз —
    при создании точки. Значение хранится в слоте с именем,
    начинающимся с подчёркивания (для x0 это _x0).

    Attributes
    ----------
    public_name : str
        Имя координаты в классе, например "x0".
    private_name : str
        Имя слота, в котором хранится значение, например "_x0".
    """

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.private_name)

    def __set__(self, instance, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Координата {self.public_name} должна иметь числовое значение")
        # Координату можно задать только один раз — в __init__
        try:
            getattr(instance, self.private_name)
        except AttributeError:
            object.__setattr__(instance, self.private_name, value)
        else:
            raise AttributeError(
                f"Точка неизменяема: {self.public_name} нельзя изменить, используйте replace()"
            )


def make_point_class(n, name=None):
    """Создаёт (или берёт из кэша) класс точки в n-мерном пространстве.

    Аргументы проверяются до обращения к кэшу, поэтому вызовы
    make_point_class(3), make_point_class(n=3) и make_point_class(3, None)
    возвращают один и тот же класс.

    Parameters
    ----------
    n : int
        Размерность пространства, натуральное число.
    name : str, optional
        Имя создаваемого класса, по умолчанию f"Point{n}".

    Returns
    -------
    type
        Класс точки с координатами x0, ..., x(n-1) и методами
        to_tuple() и replace().

    Raises
    ------
    TypeError
        Если n не целое число (или bool) либо name не строка и не None.
    ValueError
        Если n меньше 1.

    Examples
    --------
    >>> Point3 = make_point_class(3)
    >>> p = Point3(1, 2.5, -3)
    >>> p.to_tuple()
    (1, 2.5, -3)
    >>> p.replace(x0=10)
    Point3(x0=10, x1=2.5, x2=-3)
    >>> make_point_class(3) is Point3
    True
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n должно быть целым числом")
    if n < 1:
        raise ValueError("n должно быть натуральным числом")
    if name is not None and not isinstance(name, str):
        raise TypeError("name должно быть строкой или None")
    return _make_point_class(n, name)


@lru_cache(maxsize=None)
def _make_point_class(n, name):
    names = tuple(f"x{i}" for i in range(n))

    def __init__(self, *args):
        if len(args) != n:
            raise TypeError(f"Ожидалось {n} координат, было передано {len(args)}")
        for attr, value in zip(names, args):
            setattr(self, attr, value)

    def __setattr__(self, attr, value):
        if attr not in names:
            raise AttributeError(
                f"Нельзя установить атрибут {attr!r}; допустимы: {', '.join(names)}"
            )
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr):
        raise AttributeError(f"Точка неизменяема: нельзя удалить атрибут {attr!r}")

    def to_tuple(self):
        """Возвращает координаты точки в виде кортежа (x0, ..., x(n-1))."""
        return tuple(getattr(self, attr) for attr in names)

    def replace(self, **changes):
        """Возвращает новую точку с заменёнными координатами, например p.replace(x0=10)."""
        unknown = set(changes) - set(names)
        if unknown:
            raise TypeError(f"Неизвестные координаты: {', '.join(sorted(unknown))}")
        return type(self)(*(changes.get(attr, getattr(self, attr)) for attr in names))

    def __repr__(self):
        args = ", ".join(f"{attr}={getattr(self, attr)!r}" for attr in names)
        return f"{type(self).__name__}({args})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.to_tuple() == other.to_tuple()

    def __hash__(self):
        return hash(self.to_tuple())

    namespace = {
        "__doc__": (
            f"Неизменяемая точка в {n}-мерном пространстве "
            f"с координатами {', '.join(names)}."
        ),
        "__slots__": tuple("_" + attr for attr in names),
        "__init__": __init__,
        "__setattr__": __setattr__,
        "__delattr__": __delattr__,
        "__repr__": __repr__,
        "__eq__": __eq__,
        "__hash__": __hash__,
        "to_tuple": to_tuple,
        "replace": replace,
    }
    for attr in names:
        namespace[attr] = CoordDescriptor()
    return type(name or f"Point{n}", (), namespace)


if __name__ == "__main__":
    Point3 = make_point_class(3)
    p = Point3(1, 2.5, -3)
    print(Point3.__name__, p.to_tuple(), p.x1)

    print(make_point_class(3) is Point3)

    for args in [("a", 2, 3), (1, 2)]:
        try:
            Point3(*args)
        except TypeError as e:
            print("TypeError:", e)

    print(make_point_class(3) is make_point_class(n=3) is make_point_class(3, None))
    print(p, p == Point3(1, 2.5, -3))

    for action in (lambda: setattr(p, "_x0", "a"),
                   lambda: setattr(p, "x0", 10),
                   lambda: delattr(p, "_x0")):
        try:
            action()
        except AttributeError as e:
            print("AttributeError:", e)

    q = p.replace(x0=10)
    print(q, p, q is not p)

    for bad_n in [0, -2, 2.5, "3", True, [1]]:
        try:
            make_point_class(bad_n)
        except (TypeError, ValueError) as e:
            print(f"{type(e).__name__}:", e)
