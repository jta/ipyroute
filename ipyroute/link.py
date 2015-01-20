""" Manage links. """
# -*- coding: utf-8 -*-
from __future__ import print_function

import re

from ipyroute import base

class Link(base.Base):
    """ Interact with `ip link`. """
    regex = re.compile(r'(?P<num>\d+): '
                       r'(?P<name>\S+?)(@(?P<phy>\S+))?: '
                       r'<(?P<flags>\S+)> '
                       r'(mtu (?P<mtu>\d+)\s*)?'
                       r'(qdisc (?P<qdisc>\S+)\s*)?'
                       r'(state (?P<state>\S+)\s*)?'
                       r'(qlen (?P<qlen>\S+)\s*)?'
                       r'\\\s+link/(?P<type>\S+) '
                       r'(?P<addr>[a-f\d.:]+) '
                       r'brd (?P<brd>[a-f\d.:]+)')

    casts = dict(num=int, mtu=int)

    _validflags = set(['UP', 'LOWER_UP', 'LOOPBACK', 'BROADCAST',
                       'POINTTOPOINT', 'MULTICAST', 'PROMISC',
                       'ALLMULTI', 'NOARP', 'DYNAMIC', 'MASTER', 'SLAVE'])

    @classmethod
    def _get(cls, *args):
        # We load link in IPR class at runtime.
        # pylint: disable=no-member
        return base.IPR.link.addr.show(*args)

    def __getattr__(self, name):
        if name.upper() in self._validflags:
            return name.upper() in self.flags
        errmsg = "type object {0.__class__!r} has no attribute {1!r}"
        raise AttributeError(errmsg.format(self, name))

    @base.classproperty
    def cmd(cls):
        # We load root in IPR class at runtime.
        # pylint: disable=no-member
        return base.IPR.root.link

    @property
    def add(self):
        """ Add command for link. """
        return getattr(self.cmd.add.link.dev, self.name)

    @property
    def delete(self):
        """ Delete command for link. """
        return self.cmd.delete.bake(self.name)

    @property
    def set(self):
        """ Set command for link. """
        return self.cmd.set.dev.bake(self.name)

    @classmethod
    def construct(cls, result, _):
        _cls = cls
        linktype = result.get('type', None)
        if linktype == 'ether':
            _cls = EtherLink
        elif linktype == 'gre':
            _cls = GRELink
        return _cls(**result)

class EtherLink(Link):
    casts = dict(addr=base.EUI, brd=base.EUI, **Link.casts)

class GRELink(Link):
    casts = dict(addr=base.IPAddress, brd=base.IPAddress, **Link.casts)

