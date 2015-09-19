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
                       r'(master (?P<master>\S+)\s*)?'
                       r'(state (?P<state>\S+)\s*)?'
                       r'(mode (?P<mode>\S+)\s*)?'
                       r'(group (?P<group>\S+)\s*)?'
                       r'(qlen (?P<qlen>\S+)\s*)?'
                       r'\\\s+link/(?P<type>\S+)\s*'
                       r'((?P<addr>[a-f\d.:]+)\s*)?'
                       r'(brd (?P<brd>[a-f\d.:]+))?')

    casts = dict(num=int, mtu=int)

    _validflags = set(['UP', 'LOWER_UP', 'LOOPBACK', 'BROADCAST',
                       'POINTTOPOINT', 'MULTICAST', 'PROMISC',
                       'ALLMULTI', 'NOARP', 'DYNAMIC'])
    _validassoc = set(['MASTER', 'SLAVE'])

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
        elif name.startswith('is_') and name[3:].upper() in self._validassoc:
            return name[3:].upper() in self.flags
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

    def _mod_peer(self, method, srcip, dstip, **kwargs):
        method(srcip, peer=dstip, dev=self.name, **kwargs)

    def add_peer(self, *args, **kwargs):
        """ Add peer to interface. """
        self._mod_peer(Address.add, *args, **kwargs)

    def replace_peer(self, *args, **kwargs):
        """ Replace peer on interface. """
        self._mod_peer(Address.replace, *args, **kwargs)

    def del_peer(self, *args, **kwargs):
        """ Delete peer from interface. """
        self._mod_peer(Address.delete, *args, **kwargs)

    def change_peer(self, *args, **kwargs):
        """ Change peer on interface. """
        self._mod_peer(Address.change, *args, **kwargs)

    @property
    def neighbors(self):
        """ Return list of neighbor IPs for interface. """
        return set(i.ipaddr for i in Neighbor.get(dev=self.name) if not i.failed)

    def _mod_neighbor(self, method, ipaddr, lladdr, **kwargs):
        """ Add peer to interface. """
        method(ipaddr, lladdr=lladdr, nud='permanent', dev=self.name, **kwargs)

    def add_neighbor(self, *args, **kwargs):
        """ Add neighbor to interface. """
        self._mod_neighbor(Neighbor.add, *args)

    def del_neighbor(self, *args, **kwargs):
        """ Delete neighbor from interface. """
        self._mod_neighbor(Neighbor.delete, *args)

    def replace_neighbor(self, *args, **kwargs):
        """ Replace neighbor for interface. """
        self._mod_neighbor(Neighbor.replace, *args)

    def change_neighbor(self, *args, **kwargs):
        """ Change neighbor on interface. """
        self._mod_neighbor(Neighbor.change, *args)

class EtherLink(Link):
    casts = dict(addr=base.EUI, brd=base.EUI, **Link.casts)

class GRELink(Link):
    casts = dict(addr=base.IPAddress, brd=base.IPAddress, **Link.casts)

