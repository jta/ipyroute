""" Base classes for interfacing with iproute2. """
# -*- coding: utf-8 -*-
from __future__ import print_function

import functools
import netaddr
import re
import sys
import time

from sh import ErrorReturnCode

EUI = functools.partial(netaddr.EUI, dialect=netaddr.mac_unix_expanded)
IPAddress = netaddr.IPAddress
IPNetwork = netaddr.IPNetwork

class IPRouteMeta(type):
    """ This is a relatively dense way of only requiring iproute2 at runtime.
        We want to be able to load ipyroute without iproute2 for mock testing on any
        platform. To do so, we have an IPR class which acts as a proxy for iproute2.

        This is the metaclass for IPR, which intercepts missing attributes and loads
        them on first miss with the appropriate bindings.
    """
    def __getattr__(cls, name):
        if name not in ('link', 'ipv4', 'ipv6'):
            msg = "{0!r} object has no attribute {1!r}".format(type(cls).__name__, name)
            raise AttributeError(msg)

        if cls._ipr is None:
            try:
                # pylint: disable=no-name-in-module
                from sh import ip
            except ImportError:
                sys.exit("ERROR: iproute2 not found.")

            # pylint: disable=attribute-defined-outside-init
            cls._ipr = ip.bake('-o')
            cls.root = cls._ipr
            cls.link = cls.root.bake('-0')
            cls.ipv4 = cls.root.bake('-4')
            cls.ipv6 = cls.root.bake('-6')
        return getattr(cls, name)


class IPR(object):
    """ This is a dummy proxy class for interfacing with iproute2. """
    # pylint: disable=too-few-public-methods
    __metaclass__ = IPRouteMeta
    _ipr = None


class Cache(dict):
    """ Cache dictionary with timeout for storing results of iproute show. """
    def __init__(self, timeout=0):
        self._timeout = timeout
        self._time = {}

    def __setitem__(self, key, val):
        super(Cache, self).__setitem__(key, val)
        self._time[key] = time.time()

    def __contains__(self, key):
        return key in self._time and time.time() < self._time[key] + self._timeout

    def clear(self):
        super(Cache, self).clear()
        self._time.clear()


# pylint: disable=invalid-name
class classproperty(property):
    """ A hack to do classmethod properties. Normally you'd just use class attributes,
        but in this case we want to do lazy evaluation of the IPR object for interfacing
        with iproute2.
    """
    # pylint: disable=too-few-public-methods
    def __get__(self, instance, cls):
        return classmethod(self.fget).__get__(instance, cls)()



class Base(object):
    """ The base class does generic processing of the output of an iproute2
        `show` command. Each subclass should provide a regex on how to
        interpret lines of output.
    """
    regex = re.compile(r'')
    casts = dict()
    cache = Cache(0)

    def __init__(self, **kwargs):
        """ We receive a dict of key/value pairs, which we should set as object
            attributes. If specified, we should also cast the values.
        """
        for key, value in kwargs.items():
            if value is not None and key in self.casts:
                value = self.casts[key](value)
            setattr(self, key, value)

    @classmethod
    def _get(cls, *args):
        """ The method determines what iproute2 command retrieves info, and
            how the output is fed back.
        """
        raise NotImplementedError

    @classmethod
    def from_string(cls, ipstr, *args):
        """ Every line of output fed by _get(*args) should be converted into an object
            in this method, which may be subclassed if necessary.
        """
        match = cls.regex.match(ipstr)
        if not match:
            msg = "No match found for {!r}: {!r}".format(cls, ipstr)
            raise ValueError(msg)
        result = match.groupdict()
        return cls.construct(result, ipstr, *args)

    @classmethod
    def construct(cls, result, ipstr, *args):
        """ If we need additional parsing, do it here.
            By omission do nothing.
        """
        return cls(**result)

    @staticmethod
    def _unwind(*args, **kwargs):
        # XXX: this is wrong because kwargs are unordered
        """ Flatten list of args and kwargs into single list of args.
            This is used to build command for iproute2.
        """
        return tuple(list(args) + [i for kv in kwargs.items() for i in kv])

    @staticmethod
    def shwrap(func, order):
        """ Wraps a shell command so we can unwind the command arguments in
            the correct order. This won't matter in Python3.5 since kwargs are
            an ordered dict.
        """
        def wrapped(*args, **kwargs):
            args = list(args)
            for key in order:
                if key in kwargs:
                    if key:
                        args.append(key)
                    value = kwargs.pop(key)
                    if isinstance(value, (list, tuple)):
                        args.extend(value)
                    else:
                        args.append(value)
            # remaining kwargs are unordered
            for item in kwargs.items():
                args.extend(item)

            return func(*args)
        return wrapped


    @classmethod
    def get(cls, *args, **kwargs):
        """ Scrape iproute2 output and return filtered list of matches. """
        filt = kwargs.pop('filt', lambda x: True)
        args = cls._unwind(*args, **kwargs)

        if cls.cache and args in cls.cache:
            return cls.cache[args][:]

        func = functools.partial(cls._get, *args) if args else cls._get
        iterator = (cls.from_string(l, *args) for l in func())
        result = [i for i in iterator if filt(i)]
        if cls.cache is not None:
            # save copy in cache.
            cls.cache[args] = result[:]
        return result

    def __getattr__(self, name):
        """ Check for missing attributes. Override in subclass. """
        errmsg = "type object {0.__class__!r} has no attribute {1!r}"
        raise AttributeError(errmsg.format(self, name))

    def __str__(self):
        return str(dict((k, v) for k, v in sorted(self.__dict__.items()) if v is not None))

    def __eq__(self, other):
        if not other:
            return False
        return self.__str__() == other.__str__()

    @classmethod
    def set_cache(cls, timeout = 0):
        """ Cache show results."""
        cls.cache = Cache(timeout)



