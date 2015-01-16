""" Base classes for interfacing with iproute2. """
# -*- coding: utf-8 -*-
from __future__ import print_function

import functools
import netaddr
from netaddr import IPAddress, IPNetwork
import re
import sys

EUI = functools.partial(netaddr.EUI, dialect=netaddr.mac_unix_expanded)

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
                from sh import ip
            except ImportError:
                sys.exit("ERROR: iproute2 not found.")
            cls._ipr = ip.bake('-o')
            cls.root = cls._ipr
            cls.link = cls.root.bake('-0')
            cls.ipv4 = cls.root.bake('-4')
            cls.ipv6 = cls.root.bake('-6')
        return getattr(cls, name)


class IPR(object):
    """ This is a dummy proxy class for interfacing with iproute2. """
    __metaclass__ = IPRouteMeta
    _ipr = None


class classproperty(property):
    """ A hack to do classmethod properties. Normally you'd just use class attributes,
        but in this case we want to do lazy evaluation of the IPR object for interfacing
        with iproute2.
    """
    def __get__(self, instance, cls):
        return classmethod(self.fget).__get__(instance, cls)()


class Base(object):
    """ The base class does generic processing of the output of an iproute2
        `show` command. Each subclass should provide a regex on how to
        interpret lines of output.
    """
    regex = re.compile(r'')
    casts = dict()

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
    def from_string(cls, ipstr):
        """ Every line of output fed by _get() should be converted into an object
            in this method, which may be subclassed if necessary.
        """
        match = cls.regex.match(ipstr)
        if not match:
            msg = "No match found for {!r}: {!r}".format(cls, ipstr)
            raise ValueError(msg)
        result = match.groupdict()
        result = cls.recurse(result, ipstr)
        return cls(**result)

    @classmethod
    def recurse(cls, result, ipstr):
        """ If we need additional parsing, do it here.
            By omission do nothing.
        """
        return result

    @staticmethod
    def _unwind(*args, **kwargs):
        # XXX: this is wrong because kwargs are unordered
        """ Flatten list of args and kwargs into single list of args.
            This is used to build command for iproute2.
        """
        return list(args) + [i for kv in kwargs.items() for i in kv]

    @classmethod
    def get(cls, *args, **kwargs):
        """ Scrape iproute2 output and return filtered list of matches. """
        filt = kwargs.pop('filt', lambda x: True)
        args = cls._unwind(*args, **kwargs)
        func = functools.partial(cls._get, *args) if args else cls._get
        iterator = (cls.from_string(l) for l in func())
        return [i for i in iterator if filt(i)]


class Nexthop(Base):
    regex = re.compile(r'nexthop via (?P<addr>\S+)\s+'
                       r'dev (?P<dev>\S+) '
                       r'weight (?P<weight>\d+)')
    casts = dict(addr=IPAddress)

class Route(Base):
    regex = re.compile(r'(?P<network>\S+)\s+'
                       r'(dev (?P<dev>\S+)\s*)?'
                       r'(proto (?P<proto>\S+)\s*)?'
                       r'(src (?P<src>\S+)\s*)?'
                       r'(metric (?P<metric>\d+)\s*)?'
                       r'(mtu (?P<mtu>\d+)\s*)?'
                       r'(advmss (?P<advmss>\d+)\s*)?')

    casts = dict(network=IPNetwork,
                 src=IPAddress,
                 metric=int,
                 mtu=int,
                 advmss=int)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        if self.network == 'default':
            self.network = '0.0.0.0/0'
        self.network = IPNetwork(self.network)
        if self.src is not None:
            self.src = IPAddress(self.src)
        # cast fields to int
        for field in ('metric', 'mtu', 'advmss'):
            if getattr(self, field) is not None:
                setattr(self, field, int(getattr(self, field)))

    @classmethod
    def _get(cls, *args):
        for line in IPR.ipv4.route.show(*args):
            yield line
        for line in IPR.ipv6.route.show(*args):
            yield line

    @classmethod
    def from_string(cls, ipstr):
        match = cls.regex.match(ipstr)
        if not match:
            raise Exception
        result = match.groupdict()
        nhops = Nexthop.regex.finditer(ipstr)
        result['nexthops'] = [Nexthop(**n.groupdict()) for n in nhops]
        return cls(**result)

