""" Lookup rules """
import functools
import re
import six
from ipyroute import base

class Nexthop(base.Base):
    regex = re.compile(r'nexthop via (?P<via>\S+)\s+'
                       r'dev (?P<dev>\S+) '
                       r'weight (?P<weight>\d+)')
    casts = dict(via=base.IPAddress,
                 dev=unicode if not six.PY3 else lambda x: x,
                 weight=int)


class Route(base.Base):
    types = ('unicast',
             'local',
             'broadcast',
             'multicast',
             'throw',
             'unreachable',
             'prohibit',
             'blackhole',
             'nat')

    regex = re.compile(r'((?P<type>('+'|'.join(types)+'))\s+)?'
                       r'(?P<network>\S+)\s+'
                       r'(via (?P<via>\S+)\s*)?'
                       r'(dev (?P<dev>\S+)\s*)?'
                       r'(proto (?P<proto>\S+)\s*)?'
                       r'(src (?P<src>\S+)\s*)?'
                       r'(metric (?P<metric>\d+)\s*)?'
                       r'(mtu (?P<mtu>\d+)\s*)?'
                       r'(advmss (?P<advmss>\d+)\s*)?'
                       r'(error (?P<error>-?\d+)\s*)?')

    casts = dict(network=base.IPNetwork,
                 src=base.IPAddress,
                 via=base.IPAddress,
                 metric=int,
                 mtu=int,
                 advmss=int,
                 error=int)

    @classmethod
    def _get(cls, *args):
        for line in cls.cmd.show(*args):
            yield line

    @base.classproperty
    def flush(cls):
        cls.cache.clear()
        return cls.shwrap(cls.cmd.flush, ('table', 'label'))


    @classmethod
    def add(cls, network, **kwargs):
        """ Add command for route. """
        cls.cache.clear()
        kwargs = dict((k, v) for k, v in kwargs.items() if v is not None)
        if 'nexthops' in kwargs:
            kwargs[''] = cls._convert_nexthops(kwargs.pop('nexthops'))
        func = cls.shwrap(cls.cmd.add, ('table', 'src', 'advmss', 'mtu', ''))
        if 'type' in kwargs:
            func = functools.partial(func, kwargs.pop('type'))
        return func(network, **kwargs)

    @classmethod
    def delete(cls, network, **kwargs):
        """ Add command for route. """
        cls.cache.clear()
        if 'nexthops' in kwargs:
            kwargs[''] = cls._convert_nexthops(kwargs.pop('nexthops'))
        func = cls.shwrap(cls.cmd.delete, ('table', 'src', 'advmss', 'mtu', ''))
        if 'type' in kwargs:
            func = functools.partial(func, kwargs.pop('type'))
        return func(network, **kwargs)

    @classmethod
    def replace(cls, network, **kwargs):
        """ Replace command for route. """
        cls.cache.clear()
        if 'nexthops' in kwargs:
            kwargs[''] = cls._convert_nexthops(kwargs.pop('nexthops'))
        func = cls.shwrap(cls.cmd.replace, ('table', 'src', 'advmss', 'mtu', ''))
        if 'type' in kwargs:
            func = functools.partial(func, kwargs.pop('type'))
        return func(network, **kwargs)

    @classmethod
    def _convert_nexthops(cls, nexthops):
        """ Convert list of nexthop objects into command list. """
        nextargs = []
        for nexthop in nexthops:
            nextargs.append('nexthop')
            for key in ('via', 'dev', 'weight'):
                nextargs.append(key)
                nextargs.append(str(getattr(nexthop, key)))
        return nextargs

    @classmethod
    def construct(cls, result, ipstr, *args):
        nhops = Nexthop.regex.finditer(ipstr)
        result['nexthops'] = [Nexthop(**n.groupdict()) for n in nhops]
        if result.get('network') == 'default':
            result['network'] = cls.anyaddr
        return cls(**result)

    def __hash__(self):
        """ Needed for constructing sets. """
        return self.network

    def __getattr__(self, name):
        if not name.startswith('is_'):
            return super(Route, self).__getattr__(name)
        return self.type is not None and self.type == name[3:]


class Route4(Route):
    anyaddr = "0.0.0.0/0"

    @base.classproperty
    def cmd(cls, *args):
        return base.IPR.ipv4.route

class Route6(Route):
    anyaddr = "::/0"

    @base.classproperty
    def cmd(cls, *args):
        return base.IPR.ipv6.route


