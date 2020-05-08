# modified from TatSu, under BSD-3 clause license


from collections.abc import Mapping, Iterable

def isiter(value):
    return (
        isinstance(value, Iterable) and
        not isinstance(value, str)
    )

def asjson(obj, seen=None):
    if isinstance(obj, Mapping) or isiter(obj):
        # prevent traversal of recursive structures
        if seen is None:
            seen = set()
        elif id(obj) in seen:
            return '__RECURSIVE__'
        seen.add(id(obj))

    if hasattr(obj, '__json__') and type(obj) is not type:
        return obj.__json__()
    elif isinstance(obj, Mapping):
        result = {}
        for k, v in obj.items():
            try:
                result[k] = asjson(v, seen)
            except TypeError:
                debug('Unhashable key?', type(k), str(k))
                raise
        return result
    elif isiter(obj):
        return [asjson(e, seen) for e in obj]
    else:
        return obj

class AST(dict):
    _frozen = False

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs)
        self._frozen = True

    @property
    def frozen(self):
        return self._frozen

    def copy(self):
        return self.__copy__()

    def asjson(self):
        return asjson(self)

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
                f'{type(self).__name__} attributes are fixed. '
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
            key += '_'
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
        return {
            name: asjson(value)
            for name, value in self.items()
        }

    def __repr__(self):
        return repr(self.asjson())

    def __str__(self):
        return str(self.asjson())

########################################

# TODO: add __str__ and __repr__
class Features:
    def __init__(self, positive, negative, custom=None):
        self.positive = positive
        self.negative = negative
        if not custom:
            self.custom = {}
        else:
            self.custom = custom

    def __eq__(self, other):
        if tuple(sorted(self.positive)) != tuple(sorted(other.positive)):
            return False

        if tuple(sorted(self.negative)) != tuple(sorted(other.negative)):
            return False

        return self.custom == other.custom
