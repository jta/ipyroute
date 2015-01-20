""" Test Configuration
"""
import functools
import mock
import socket
import time
import unittest

from nose.tools import raises

import ipyroute

def mocked(method, output):
    def wrap(func):
        @functools.wraps(func)
        def wrapped(self, *args):
            kwargs = { method + '.return_value': output.splitlines() }
            ipyroute.base.IPR.configure_mock(**kwargs)
            return func(self, *args)
        return wrapped
    return wrap

class TestLink(unittest.TestCase):
    """ Test Link lib. """
    def setUp(self):
        ipyroute.base.IPR = mock.Mock()

    def tearDown(self):
        pass

    @mocked("link.addr.show",
            "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN \   link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00")
    def test_loopback_link(self):
        """ Parse loopback link. """
        link = ipyroute.Link.get().pop()
        assert link.name == "lo"
        assert link.loopback
        assert link.up
        assert link.lower_up
        assert link.mtu == 65536
        assert not link.broadcast

    @mocked("link.addr.show",
            "2: bond0: <BROADCAST,MULTICAST,MASTER> mtu 1500 qdisc noop state DOWN \    link/ether 82:e1:10:2e:d2:bf brd ff:ff:ff:ff:ff:ff")
    def test_bond_link(self):
        """ Parse bond link. """
        link = ipyroute.Link.get().pop()
        assert link.name == "bond0"
        assert link.broadcast
        assert link.multicast
        assert link.master
        assert link.mtu == 1500
        assert link.qdisc == 'noop'
        assert link.type == 'ether'
        assert link.addr == ipyroute.EUI('82:e1:10:2e:d2:bf')

    @mocked("link.addr.show",
            "3: dummy0: <BROADCAST,NOARP> mtu 1500 qdisc noop state DOWN \    link/ether c2:9a:cc:30:2c:67 brd ff:ff:ff:ff:ff:ff")
    def test_dummy_link(self):
        """ Parse dummy link. """
        link = ipyroute.Link.get().pop()
        assert link.name == "dummy0"
        assert link.broadcast
        assert link.noarp
        assert not link.master
        assert link.mtu == 1500
        assert link.addr == ipyroute.EUI('c2:9a:cc:30:2c:67')
        assert link.brd == ipyroute.EUI('ff:ff:ff:ff:ff:ff')

    @mocked("link.addr.show",
            "5: gre0@NONE: <NOARP> mtu 1476 qdisc noop state DOWN \    link/gre 0.0.0.0 brd 0.0.0.0")
    def test_gre_link(self):
        """ Parse GRE link. """
        link = ipyroute.Link.get().pop()
        assert link.name == "gre0"
        assert link.phy == "NONE"
        assert not link.broadcast
        assert link.noarp
        assert link.mtu == 1476
        assert link.addr == ipyroute.IPAddress('0.0.0.0')
        assert link.brd == ipyroute.IPAddress('0.0.0.0')

    # XXX: generic?
    @raises(ValueError)
    @mocked("link.addr.show", "\n")
    def test_unmatched_line(self):
        """ If no regex match is found, value error should be raised. """
        ipyroute.Link.get()

    # XXX: generic? ValueError or TypeError?
    @raises(ValueError)
    @mocked("link.addr.show",
            "5: gre0@NONE: <NOARP> mtu WRONG qdisc noop state DOWN \    link/gre 0.0.0.0 brd 0.0.0.0")
    def test_wrong_type_int(self):
        """ ValueError should be raised when field has wrong type (mtu must be int). """
        ipyroute.Link.get()

    @mocked("link.addr.show",
            "8: p3p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000\    link/ether 02:40:00:20:03:01 brd ff:ff:ff:ff:ff:ff")
    def test_add_veth(self):
        """ Confirm correct args get passed when adding a virtual link. """
        link = ipyroute.Link.get().pop()
        link.add('vethp3p1', type='macvlan', mode='private')

        expected = ipyroute.base.IPR.root.link.add.link.dev.p3p1
        assert expected.called
        assert " ".join(expected.call_args[0]) == 'vethp3p1 type macvlan mode private'


class TestAddress(unittest.TestCase):
    """ Test Address lib. """
    def setUp(self):
        ipyroute.base.IPR = mock.Mock()

    def tearDown(self):
        pass

    @mocked("ipv4.addr.show", "1: lo    inet 127.2.0.1/32 scope host lo:label\       valid_lft forever preferred_lft forever")
    @mocked("ipv6.addr.show", "1: lo    inet6 ::1/128 scope host \       valid_lft forever preferred_lft forever")
    def test_loopback_address(self):
        """ Parse loopback link IPv4 address. """
        v4addr, v6addr = ipyroute.Address.get()

        assert v4addr.addr == ipyroute.IPNetwork("127.2.0.1/32")
        assert v4addr.label == "label"
        assert v4addr.ifname == "lo"
        assert v4addr.ifnum == 1
        assert v4addr.peer is None
        assert v4addr.brd is None
        assert v4addr.host_scope

        assert v6addr.addr == ipyroute.IPNetwork("::1/128")
        assert v6addr.label is None
        assert v6addr.ifname == "lo"
        assert v6addr.ifnum == 1
        assert v6addr.peer is None
        assert v6addr.brd is None
        assert v6addr.host_scope

    @mocked("ipv4.addr.show", "11: p6p1    inet 172.235.34.20 peer 172.242.148.197/32 scope global p6p1:label\       valid_lft forever preferred_lft forever")
    @mocked("ipv6.addr.show", "11: p6p1    inet6 fe80::40:ff:fe20:601/64 scope link \       valid_lft forever preferred_lft forever")
    def test_peer_address(self):
        """ Parse peer IP address. """
        v4addr, v6addr = ipyroute.Address.get()

        assert v4addr.addr == ipyroute.IPNetwork("172.235.34.20/32")
        assert v4addr.label == "label"
        assert v4addr.ifname == "p6p1"
        assert v4addr.ifnum == 11
        assert v4addr.peer == ipyroute.IPNetwork("172.242.148.197/32")
        assert v4addr.brd is None
        assert v4addr.global_scope

        assert v6addr.addr == ipyroute.IPNetwork("fe80::40:ff:fe20:601/64")
        assert v6addr.label is None
        assert v6addr.ifname == "p6p1"
        assert v6addr.ifnum == 11
        assert v6addr.peer is None
        assert v6addr.brd is None
        assert v6addr.link_scope

    def test_add_address(self):
        """ Confirm correct args get passed when adding a virtual link. """
        ipyroute.Address.add("172.16.0.0/12", label="lo:test", dev="lo")
        expected = ipyroute.base.IPR.root.addr.add
        assert expected.called
        assert " ".join(expected.call_args[0]) == '172.16.0.0/12 dev lo label lo:test'

    def test_del_address(self):
        """ Delete peer. """
        ipyroute.Address.delete("172.16.0.1/32", peer="172.17.0.1/32", dev="p3p1")
        expected = getattr(ipyroute.base.IPR.root.addr, 'del')
        assert expected.called
        assert " ".join(expected.call_args[0]) == '172.16.0.1/32 peer 172.17.0.1/32 dev p3p1'

