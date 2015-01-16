""" Test Configuration
"""
import functools
import mock
import socket
import time
import unittest

from nose.tools import raises

from ipyroute import base, Link

def mocked(method, output):
    def wrap(func):
        @functools.wraps(func)
        def wrapped(self, *args):
            kwargs = { method + '.return_value': output.splitlines() }
            base.IPR.configure_mock(**kwargs)
            return func(self, *args)
        return wrapped
    return wrap

class TestLink(unittest.TestCase):
    output = """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN \    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: bond0: <BROADCAST,MULTICAST,MASTER> mtu 1500 qdisc noop state DOWN \    link/ether 82:e1:10:2e:d2:bf brd ff:ff:ff:ff:ff:ff
3: dummy0: <BROADCAST,NOARP> mtu 1500 qdisc noop state DOWN \    link/ether c2:9a:cc:30:2c:67 brd ff:ff:ff:ff:ff:ff
4: tunl0@NONE: <NOARP> mtu 1480 qdisc noop state DOWN \    link/ipip 0.0.0.0 brd 0.0.0.0
5: gre0@NONE: <NOARP> mtu 1476 qdisc noop state DOWN \    link/gre 0.0.0.0 brd 0.0.0.0
6: gretap0@NONE: <BROADCAST,MULTICAST> mtu 1462 qdisc noop state DOWN qlen 1000\    link/ether 00:00:00:00:00:00 brd ff:ff:ff:ff:ff:ff
7: em1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000\    link/ether 00:25:90:c2:ff:84 brd ff:ff:ff:ff:ff:ff
8: p3p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000\    link/ether 02:40:00:20:03:01 brd ff:ff:ff:ff:ff:ff
9: em2: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN qlen 1000\    link/ether 00:25:90:c2:ff:85 brd ff:ff:ff:ff:ff:ff
10: p3p2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000\    link/ether 02:40:00:20:03:02 brd ff:ff:ff:ff:ff:ff
11: p6p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000\    link/ether 02:40:00:20:06:01 brd ff:ff:ff:ff:ff:ff
12: p6p2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000\    link/ether 02:40:00:20:06:02 brd ff:ff:ff:ff:ff:ff
13: vp3p1-primary@p3p1: <BROADCAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN \    link/ether 02:01:02:00:01:01 brd 00:00:00:00:00:00
14: vp3p1-from-2@p3p1: <BROADCAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN \    link/ether 02:01:02:00:01:02 brd 00:00:00:00:00:00
15: vp3p1-from-3@p3p1: <BROADCAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN \    link/ether 02:01:02:00:01:03 brd 00:00:00:00:00:00
16: vp3p1-from-4@p3p1: <BROADCAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN \    link/ether 02:01:02:00:01:04 brd 00:00:00:00:00:00"""

    def setUp(self):
        base.IPR = mock.Mock()

    def tearDown(self):
        pass

    @mocked("link.addr.show",
            "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN "
            "\   link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00")
    def test_loopback_link(self):
        """ Get links. """
        link = Link.get().pop()
        assert link.name == "lo"
        assert link.loopback
        assert link.up
        assert link.lower_up
        assert link.mtu == 65536
        assert not link.broadcast

    @mocked("link.addr.show",
            "2: bond0: <BROADCAST,MULTICAST,MASTER> mtu 1500 qdisc noop "
            "state DOWN \    link/ether 82:e1:10:2e:d2:bf brd ff:ff:ff:ff:ff:ff")
    def test_bond_link(self):
        """ Get links. """
        link = Link.get().pop()
        assert link.name == "bond0"
        assert link.broadcast
        assert link.multicast
        assert link.master
        assert link.mtu == 1500
        assert link.qdisc == 'noop'
        assert link.type == 'ether'
        assert link.addr == '82:e1:10:2e:d2:bf'

    @mocked("link.addr.show",
            "3: dummy0: <BROADCAST,NOARP> mtu 1500 qdisc noop state DOWN "
            "\    link/ether c2:9a:cc:30:2c:67 brd ff:ff:ff:ff:ff:ff")
    def test_dummy_link(self):
        """ Get links. """
        link = Link.get().pop()
        assert link.name == "dummy0"
        assert link.broadcast
        assert link.noarp
        assert not link.master
        assert link.mtu == 1500
        assert link.addr == 'c2:9a:cc:30:2c:67'
        assert link.brd == 'ff:ff:ff:ff:ff:ff'

    @mocked("link.addr.show",
            "5: gre0@NONE: <NOARP> mtu 1476 qdisc noop state DOWN "
            "\    link/gre 0.0.0.0 brd 0.0.0.0")
    def test_gre_link(self):
        """ Get links. """
        link = Link.get().pop()
        assert link.name == "gre0"
        assert link.phy == "NONE"
        assert not link.broadcast
        assert link.noarp
        assert link.mtu == 1476
        assert link.addr == '0.0.0.0'
        assert link.brd == '0.0.0.0'

    # XXX: generic?
    @raises(ValueError)
    @mocked("link.addr.show", "\n")
    def test_unmatched_line(self):
        """ If no regex match is found, value error should be raised. """
        Link.get()

    # XXX: generic? ValueError or TypeError?
    @raises(ValueError)
    @mocked("link.addr.show",
            "5: gre0@NONE: <NOARP> mtu bogus qdisc noop state "
            "DOWN \    link/gre 0.0.0.0 brd 0.0.0.0")
    def test_wrong_type_int(self):
        """ ValueError should be raised when field has wrong type. """
        Link.get()

    @mocked("link.addr.show",
            "8: p3p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 "
            "qdisc mq state UP qlen 1000\    link/ether "
            "02:40:00:20:03:01 brd ff:ff:ff:ff:ff:ff")
    def test_set_link(self):
        """ Confirm correct args get passed when adding a virtual link. """
        link = Link.get().pop()
        callargs = 'vethp3p1 type macvlan mode private'
        link.add(callargs)

        expected = base.IPR.root.link.add.link.dev.p3p1
        assert expected.called
        assert callargs == " ".join(expected.call_args[0])


