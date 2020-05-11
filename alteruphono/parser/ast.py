"""
`AST` class for abstract syntax tree manipulation.

ASTs are here implemented as a custom dictionary that works as a frozen
one (fields/attributes cannot be changed after initialization, but there
is a .copy() method that accepts an `update` dictionary) and which can
be accessed both as dictionary fields (e.g., `ast['grapheme']`) and as
attributes (e.g., `ast.grapheme`).

It is a convenient solution for prototyping and experimenting, besides the
easiness it provides for manipulation during simulations. It might in the
future be replaced by some standard Python solution, probability data
classes.

The implementation extends the one used by the 竜 TatSu library as of
2020.05.09. This module is licensed under the BSD-3 clause license of
竜 TatSu.
"""
# NOTE: it seems unnecessary to sort serialization output (JSON), because
# dictionaries in Python from 3.6 are actually sorted by order of insertion,
# an order preserved during update (new items appended to the end). It
# might be possible in some complex situations with a modification for
# the order to be different, but it seems unlikely and not happening in
# our context and usage (tests should confirm this, however). If this is
# necessary, given how expansive sorting operations can be, this could
# be implemeted as a `.safe_json()` method passing some sorting flag to
# `asjson()`.

# Import Python standard libraries
from collections.abc import Mapping, Iterable


def isiter(value):
    return isinstance(value, Iterable) and not isinstance(value, str)

# TODO: rename function so this is an internal, non-confused one
def asjson(obj, seen=None):
    if isinstance(obj, Mapping) or isiter(obj):
        # prevent traversal of recursive structures
        if seen is None:
            seen = set()
        elif id(obj) in seen:
            return "__RECURSIVE__"
        seen.add(id(obj))

    if hasattr(obj, "__json__") and type(obj) is not type:
        return obj.__json__()
    elif isinstance(obj, Mapping):
        result = {}
        for k, v in obj.items():
            try:
                result[k] = asjson(v, seen)
            except TypeError:
                debug("Unhashable key?", type(k), str(k))
                raise
        return result
    elif isiter(obj):
        return [asjson(e, seen) for e in obj]
    else:
        return obj


# TODO: implement a __hash__ method
class AST(dict):
    _frozen = False

    def __init__(self, *args, **kwargs):
        # Initialize with new data
        super().__init__()
        self.update(*args, **kwargs)

        # Given that the structure is immutable and the serialization is
        # really expansive in terms of computing cycles, compute it once and
        # store it
        self._cache_json = asjson(self)
        self._cache_repr = repr(self._cache_json)
        self._cache_str = str(self._cache_json)

        # Froze the structure
        self._frozen = True

    @property
    def frozen(self):
        return self._frozen

    def copy(self, update={}):
        if update:
            tmp = dict(self)
            tmp.update(update)
            return AST(tmp)

        return self.__copy__()

    def asjson(self):
        return self._cache_json

    def _set(self, key, value, force_list=False):
        key = self._safekey(key)
        previous = self.get(key)

        if previous is None and force_list:
            value = [value]
        elif previous is None:
            pass
        elif isinstance(previous, list):
            value = previous + [value]
        else:
            value = [previous, value]

        super().__setitem__(key, value)

    def _setlist(self, key, value):
        return self._set(key, value, force_list=True)

    def __copy__(self):
        return AST(self)

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        key = self._safekey(key)
        if key in self:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        self._set(key, value)

    def __delitem__(self, key):
        key = self._safekey(key)
        super().__delitem__(key)

    def __setattr__(self, name, value):
        if self._frozen and name not in vars(self):
            raise AttributeError(
                f"{type(self).__name__} attributes are fixed. "
                f' Cannot set attribute "{name}".'
            )
        super().__setattr__(name, value)

    def __getattr__(self, name):
        key = self._safekey(name)
        if key in self:
            return self[key]
        elif name in self:
            return self[name]

        try:
            return super().__getattribute__(name)
        except AttributeError:
            return None

    def __hasattribute__(self, name):
        try:
            super().__getattribute__(name)
        except (TypeError, AttributeError):
            return False
        else:
            return True

    def __reduce__(self):
        return (AST, (), None, None, iter(self.items()))

    def _safekey(self, key):
        while self.__hasattribute__(key):
            key += "_"
        return key

    def _define(self, keys, list_keys=None):
        for key in keys:
            key = self._safekey(key)
            if key not in self:
                super().__setitem__(key, None)

        for key in list_keys or []:
            key = self._safekey(key)
            if key not in self:
                super().__setitem__(key, [])

    def __json__(self):
        return {name: asjson(value) for name, value in self.items()}

    # TODO: could we have a single one?
    def __repr__(self):
        return self._cache_repr

    def __str__(self):
        return self._cache_str
