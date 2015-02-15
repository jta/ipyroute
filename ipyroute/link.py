""" Manage links. """
# -*- coding: utf-8 -*-
from __future__ import print_function

import re

from ipyroute import base
from .address import Address
from .neighbor import Neighbor

class Link(base.Base):
    """ Interact with `ip link`. """
    regex = re.compile(r'(?P<num>\d+): '
                       r'(?P<name>\S+?)(@(?P<phy>\S+))?: '
                       r'<(?P<flags>\S+)> '
                       r'(mtu (?P<mtu>\d+)\s*)?'
                       r'(qdisc (?P<qdisc>\S+)\s*)?'
                       r'(state (?P<state>\S+)\s*)?'
                       r'(mode (?P<mode>\S+)\s*)?'
                       r'(group (?P<group>\S+)\s*)?'
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
        try:
            return base.IPR.link.link.show(*args)
        except base.ErrorReturnCode:
            return []

    def __getattr__(self, name):
        if name == 'group':
            return None

        if name.upper() in self._validflags:
            return name.upper() in self.flags
        super(Link, self).__getattr__(name)

    @base.classproperty
    def cmd(cls):
        # We load root in IPR class at runtime.
        # pylint: disable=no-member
        return base.IPR.root.link

    @property
    def add(self):
        """ Add command for link. """
        Link.cache.clear()
        func = getattr(self.cmd.add.link, self.name)
        order = ('type',  'mode')
        return self.shwrap(func.dev, order)

    @property
    def delete(self):
        """ Delete command for link. """
        Link.cache.clear()
        func = getattr(self.cmd.delete, self.name)
        order = ()
        return self.shwrap(func, order)

    @property
    def set(self):
        """ Set command for link. """
        Link.cache.clear()
        func = getattr(self.cmd.set.dev, self.name)
        order = ()
        return self.shwrap(func, order)

    @classmethod
    def construct(cls, result, _, *args):
        _cls = cls
        if 'group' in args:
            idx = args.index('group')
            result['group'] = args[idx+1]
        linktype = result.get('type', None)
        if linktype == 'ether':
            _cls = EtherLink
        elif linktype == 'gre':
            _cls = GRELink
        return _cls(**result)

    @property
    def addresses(self):
        return set(i.addr for i in Address.get(self.name))

    @property
    def peers(self):
        """ Return set of peeers associated to this link. """
        return set(i.peer for i in Address.get(self.name) if i.peer)

    def add_peer(self, srcip, dstip):
        """ Add peer to interface. """
        Address.add(srcip, peer=dstip, dev=self.name)

    def del_peer(self, srcip, dstip):
        """ Delete peer from interface. """
        Address.delete(srcip, peer=dstip, dev=self.name)

    @property
    def neighbors(self):
        """ Delete peer from interface. """
        return set(i.ipaddr for i in Neighbor.get(self.name))

    def add_neighbor(self, ipaddr, lladdr):
        """ Add peer to interface. """
        Neighbor.add(ipaddr, lladdr=lladdr, nud='permanent', dev=self.name)

    def del_peer(self, srcip, dstip):
        """ Delete peer from interface. """
        Neighbor.delete(ipaddr, lladdr=lladdr, nud='permanent', dev=self.name)

class EtherLink(Link):
    casts = dict(addr=base.EUI, brd=base.EUI, **Link.casts)

class GRELink(Link):
    casts = dict(addr=base.IPAddress, brd=base.IPAddress, **Link.casts)

