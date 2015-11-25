from collections import Mapping as __Mapping, Sequence as __Sequence
# utility functions that should be builtins

# we import * this namespace, so might as well
# grab partial, aget, mcall, and iget while we're at it
# ignore pyflakes, we mean to import this to rexport
from functools import partial                   # NOQA
from operator import (attrgetter as aget,       # NOQA
                      itemgetter as iget,       # NOQA
                      methodcaller as mcall, )  # NOQA


class __nil(object):
    """ Implementation detail to make merge_with a little safer. """
    pass


def merge_with(f, *dicts):
    """ Merges dicts using f(old, new) when encountering collision. """
    r = {}
    for d in filter(None, dicts):
        for k, v in d.iteritems():
            tmp = r.get(k, __nil())
            if isinstance(tmp, __nil):
                r[k] = v
            else:
                r[k] = f(tmp, v)
    return r


def deep_merge_with(f, *dicts):
    """ Merges dicts recursively, resolving node conflicts using f """
    def _deep_merge_with(*ds):
        if all([isinstance(d, __Mapping) for d in ds]):
            return merge_with(_deep_merge_with, *ds)
        else:
            return f(*ds)
    return _deep_merge_with(*dicts)


def throw(exception, *args, **kwargs):
    """ Raises an exception (as an expression) """
    raise exception(*args, **kwargs)


def get_in(obj, lookup, default=None):
    """ Walk obj via __getitem__ for each lookup,
    returning the final value of the lookup or default.
    """
    tmp = obj
    for l in lookup:
        try:
            tmp = tmp[l]
        except (KeyError, IndexError, TypeError):
            return default
    return tmp


def get(obj, k, default=None):
    """ Return obj[k] with a default if __getitem__ fails.

    If default is callable, return a call to it passing in obj and k.
    """
    try:
        return obj[k]
    except (KeyError, AttributeError, TypeError, IndexError):
        if callable(default):
            return default(obj, k)
        return default


def is_even(x):
    """ True if obj is even. """
    return (x % 2) == 0


def assoc(obj, *args):
    """Return a copy of obj with k1=v1... via __setitem__.

    Expects *args as k1, v1, k2, v2 ...

    Special-cases None to return {k: v} ala Clojure.
    """
    from copy import deepcopy

    # requires even count of *args
    if not is_even(len(args)):
        raise ValueError("*args count must be even")

    # special case None to work like empty dict
    if obj is None:
        obj = {}
    else:
        obj = deepcopy(obj)

    # iterate args as key value pairs
    for k, v in zip(args[::2], args[1::2]):
        obj[k] = v

    return obj


def assoc_kw(obj, **kwargs):
    """ Copy obj and __setitem__ all kwargs on the new object, return it. """
    from copy import deepcopy

    # special case None to work like empty dict
    if obj is None:
        obj = {}
    else:
        obj = deepcopy(obj)

    for k, v in kwargs.items():
        obj[k] = v

    return obj


def assoc_in(obj, keys, v):
    """ Return a copy of obj with v updated at keys.

    Dictionaries are created when keys don't exist.
    """
    k, ks = keys[0], keys[1:]
    if ks:
        return assoc(obj, k, assoc_in(get(obj, k), ks, v))
    return assoc(obj, k, v)


def update_in(obj, keys, fn, *args, **kwargs):
    """ Return a copy of obj with v updated by
        fn(current_value, *args, **kwargs) at keys.

    Dictionaries are created when keys don't exist.
    """
    k, ks = keys[0], keys[1:]
    if ks:
        return assoc(obj, k, update_in(get(obj, k),
                                       ks,
                                       fn,
                                       *args,
                                       **kwargs))
    return assoc(obj, k, fn(get(obj, k), *args, **kwargs))


def is_iterable(obj):
    """ True if obj is iterable """
    from collections import Iterable
    return isinstance(obj, Iterable)


def dissoc(obj, k):
    """ Return a copy of obj without k """
    from copy import deepcopy
    obj = deepcopy(obj)
    try:
        del obj[k]
    except (KeyError, IndexError):
        pass
    return obj


def dissoc_in(obj, keys):
    """ Return a copy of obj without k at keys. """
    k, ks = keys[0], keys[1:]
    if ks:
        nextmap = get(obj, k)
        if nextmap is not None:
            newmap = dissoc_in(nextmap, ks)
            if is_iterable(obj):
                return assoc(obj, k, newmap)
            return dissoc(obj, k)
        return obj
    return dissoc(obj, k)


def select_keys(keys, d, default=None):
    """ Given a list of keys and a collection that supports __getitem__, return
        a dictionary with only those keys.
    """
    r = {}
    for k in keys:
        r[k] = get(d, k, default)
    return r


def select_keys_flat(keys, d, default=None):
    """ Given a list of keys and a collection that supports __getitem__, return
       a list with those keys. """
    return [get(d, k, default) for k in keys]


def identity(x):
    """ Identity functions x -> x """
    return x


def compose(*fns):
    "compose(foo, bar, baz)(x) = foo(bar(baz(x)))"
    return reduce(lambda f, g: lambda *xs, **ys: f(g(*xs, **ys)), fns)


def pipeline(*fns):
    """
    five = partial(operator.add, 5)
    ten = partial(operator.add, 10)
    one = partial(operator.add, 1)

    pipeline(five,
             ten,
             one)(0)
    = one(ten(five(0))) => 16
    """
    return reduce(lambda f, g: lambda *xs, **ys: g(f(*xs, **ys)), fns)


def thread(*args):
    """ Threads args[0] through the fns args[-1:1].

    an example:
    >>> thread(10, lambda x: x+1, lambda x: x * 2)
    => (lambda x: x*2)((lambda x: x+1)(10))
    """
    return reduce(lambda f, g: g(f), args)


def trap_exception(e, f, default=None):
    """ Call f(), trapping e, default to default (which might be callable) """
    try:
        return f()
    except e:
        if callable(default):
            return default(e)
        else:
            return default


def prepend(v, l):
    """ Given a value, prepend it to an iterable or a list

    Returns a concrete list if given a list and a generator otherwise.
    """
    if isinstance(v, list):
        tmp = [v]
        tmp.extend(l)
        return tmp
    else:
        def generator():
            yield v
            for x in l:
                yield x
        return generator()

cons = prepend


def append(l, v):
    """ Given an iterable or a  list, append a value to it.

    Returns a concrete list if given a list, otherwise a generator.
    """
    if isinstance(l, list):
        l.append(v)
        return l
    else:
        def generator():
            for x in l:
                yield x
            yield v
        return generator()

conj = append


def concat(*items):
    for item in items:
        if is_iterable(item) and not is_str_or_bytes(item):
            for x in item:
                yield x
        else:
            yield item

flatten1 = compose(list, concat)


def if_let(expression, if_callable, else_callable=None):
    """ (if-let [tmp expression] (if-callable tmp) (else-callable tmp))

    if_callable/else_callable can also be just a value. if it's not callable(),
    then we just return the value.
    """
    if expression:
        if callable(if_callable):
            return if_callable(expression)
        else:
            return if_callable
    elif callable(else_callable):
        return else_callable(expression)
    else:
        return else_callable


def rpartial(func, *args):
    """ partial that returns a fn that concats the args to the funcs with args

        e.g.: rpartial(get, 0) => lambda x: get(x, 0)
    """
    return lambda *xtra: func(*flatten1(xtra, args))


first = rpartial(get, 0)
second = rpartial(get, 1)
third = rpartial(get, 2)
fourth = rpartial(get, 3)
fifth = rpartial(get, 4)
sixth = rpartial(get, 5)
seventh = rpartial(get, 6)
eighth = rpartial(get, 7)
ninth = rpartial(get, 8)
tenth = rpartial(get, 9)

last = rpartial(get, -1)


def is_str_or_bytes(x):
    """ True if x is str or bytes.
    This doesn't use rpartial to avoid infinite recursion.
    """
    return isinstance(x, (basestring, bytes, bytearray))


def flatten(xs):
    """ Recursively flatten the argument """
    for x in xs:
        if is_iterable(x) and not is_str_or_bytes(x):
            for y in flatten(x):
                yield y
        else:
            yield x


def group_by_and_transform(grouper, transformer, iterable):
        """ Sort & Group iterable by grouper, apply transformer to each group.

        Grouper must be a function that takes an item in the iterable and
        returns a sort key.

        Returns a dictionary of group keys matched to lists.
        """
        from itertools import groupby
        return {key: map(transformer, group)
                for key, group in groupby(sorted(iterable, key=grouper),
                                          key=grouper)}


def group_by(f, i):
    """ Groups i by f, returning a dictionary keyed by f. """
    return group_by_and_transform(f, identity, i)


dedup = compose(list, set)
dedup.__doc__ = """ Remove duplicates in an iterable """


def is_map(x):
    """ True if x is a Mapping (dict-like) """
    return isinstance(x, __Mapping)


def is_seq(x):
    """ True if x is a Sequence (ordered iterable, list-like) """
    return isinstance(x, __Sequence)


def transform_tree(f, t):
    """ Walks a tree (dict of dicts), depth-first, calling f(k, v) to transform

    The function should take two arguments, the key and value,
    and return a 2-tuple with the new key and new value. A sample
    identity is below:

        def f(k, v):
            return (k, v)

    """
    if not is_map(t):
        return t
    d = {}
    for k, v in t.iteritems():
        nk, nv = f(k, transform_tree(f, v))
        d[nk] = nv
    return d