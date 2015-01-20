""" Manage neighbors. """
# -*- coding: utf-8 -*-
import re
from ipyroute import base

class Neighbor(base.Base):
    regex = re.compile(r'(?P<ipaddr>[0-9a-f.:]+) '
                        'dev (?P<ifname>\S+) '
                        'lladdr (?P<ifaddr>[0-9a-f.:]+) '
                        '(router)?\s*(?P<nud>\S+)')

    casts = dict(ipaddr=base.IPAddress, ifaddr=base.EUI)
    _validnuds = set(['REACHABLE', 'STALE', 'PERMANENT'])
    _order = ('lladdr', 'nud', 'proxy', 'dev')

    @classmethod
    def _get(cls, *args):
        """ Return neighbors. """
        for line in base.IPR.ipv4.neigh.show(*args):
            yield line
        for line in base.IPR.ipv6.neigh.show(*args):
            yield line

    def __getattr__(self, name):
        """ Map nud types. """
        if name.upper() in self._validnuds:
            return name.upper() == self.nud
        super(Neighbor, self).__getattr__(name)

    @base.classproperty
    def cmd(cls):
        # We load root in IPR class at runtime.
        # pylint: disable=no-member
        return base.IPR.root.neigh

    @base.classproperty
    def add(cls):
        """ Add command for address. """
        return cls.shwrap(cls.cmd.add, cls._order)

    @base.classproperty
    def replace(cls):
        """ Add command for address. """
        return cls.shwrap(cls.cmd.replace, cls._order)

    @base.classproperty
    def delete(cls):
        """ Add command for address. """
        return cls.shwrap(getattr(cls.cmd, 'del'), cls._order)

