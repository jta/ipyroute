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

    @mocked("link.link.show",
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

    @mocked("link.link.show",
            "3: pimreg@NONE: <NOARP,UP,LOWER_UP> mtu 1472 qdisc noqueue state UNKNOWN \    link/pimreg ")
    def test_no_broadcast(self):
        """ Parse link with no broadcast address. """
        link = ipyroute.Link.get().pop()
        assert link.name == "pimreg"
        assert not link.loopback
        assert link.up
        assert link.lower_up
        assert link.mtu == 1472
        assert not link.broadcast


    @mocked("link.link.show",
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

    @mocked("link.link.show",
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

    @mocked("link.link.show",
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
    @mocked("link.link.show", "\n")
    def test_unmatched_line(self):
        """ If no regex match is found, value error should be raised. """
        ipyroute.Link.get()

    # XXX: generic? ValueError or TypeError?
    @raises(ValueError)
    @mocked("link.link.show",
            "5: gre0@NONE: <NOARP> mtu WRONG qdisc noop state DOWN \    link/gre 0.0.0.0 brd 0.0.0.0")
    def test_wrong_type_int(self):
        """ ValueError should be raised when field has wrong type (mtu must be int). """
        ipyroute.Link.get()

    @mocked("link.link.show",
            "8: p3p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000\    link/ether 02:40:00:20:03:01 brd ff:ff:ff:ff:ff:ff")
    def test_add_veth(self):
        """ Confirm correct args get passed when adding a virtual link. """
        link = ipyroute.Link.get().pop()
        link.add('vethp3p1', type='macvlan', mode='private')

        expected = ipyroute.base.IPR.root.link.add.link.p3p1.dev
        assert expected.called
        assert " ".join(expected.call_args[0]) == 'vethp3p1 type macvlan mode private'

    @mocked("link.link.show",
            "8: vp6p1-primary@p6p1: <BROADCAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group 8 \    link/ether 03:03:03:00:03:03 brd 00:00:00:00:00:00")
    def test_ss150210(self):
        """ Parse more recent representation. """
        link = ipyroute.Link.get().pop()
        assert link.group == '8'
        assert link.mode == 'DEFAULT'

    @mocked("link.link.show",
            "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN \   link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00")
    def test_link_group(self):
        """ Parse link for specific link group. """
        link = ipyroute.Link.get(group='test').pop()
        assert link.group == 'test'



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
    @mocked("ipv6.addr.show", "9: p1p3    inet6 2620:11a:c000:2:40:ff:fe27:301/64 scope global dynamic \       valid_lft 2534671sec preferred_lft 547471sec")
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

        assert v6addr.addr == ipyroute.IPNetwork("2620:11a:c000:2:40:ff:fe27:301/64")
        assert v6addr.label is None
        assert v6addr.ifname == "p1p3"
        assert v6addr.ifnum == 9
        assert v6addr.peer is None
        assert v6addr.brd is None
        assert v6addr.global_scope

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

    @raises(AttributeError)
    @mocked("ipv4.addr.show", "11: p6p1    inet 172.235.34.20 peer 172.242.148.197/32 scope global p6p1:label\       valid_lft forever preferred_lft forever")
    @mocked("ipv6.addr.show", "11: p6p1    inet6 fe80::40:ff:fe20:601/64 scope link \       valid_lft forever preferred_lft forever")
    def test_bogus_scope(self):
        """ Parse peer IP address. """
        v4addr, v6addr = ipyroute.Address.get()
        assert v4addr.no_scope

class TestNeighbor(unittest.TestCase):
    """ Test Neighbor lib. """
    def setUp(self):
        ipyroute.base.IPR = mock.Mock()

    def tearDown(self):
        pass

    @mocked("ipv4.neigh.show", "10.11.12.3 dev p6p2 lladdr ff:ff:ff:ff:ff:ff PERMANENT")
    @mocked("ipv6.neigh.show", "fe80::12f3:11ff:fe2b:7a76 dev vp3p1-from-5 lladdr 10:f3:11:2b:7a:76 router STALE")
    def test_neighbors(self):
        """ Parse neighbors. """
        v4neigh, v6neigh = ipyroute.Neighbor.get()

        assert v4neigh.ipaddr == ipyroute.IPAddress('10.11.12.3')
        assert v4neigh.ifaddr == ipyroute.EUI('ff:ff:ff:ff:ff:ff')
        assert v4neigh.ifname == 'p6p2'
        assert v4neigh.permanent
        assert v6neigh.ipaddr == ipyroute.IPAddress('fe80::12f3:11ff:fe2b:7a76')
        assert v6neigh.ifaddr == ipyroute.EUI('10:f3:11:2b:7a:76')
        assert v6neigh.ifname == 'vp3p1-from-5'
        assert v6neigh.stale
        assert not v6neigh.permanent


    @mocked("ipv4.neigh.show", "10.11.12.3 lladdr ff:ff:ff:ff:ff:ff PERMANENT")
    @mocked("ipv6.neigh.show", "fe80::12f3:11ff:fe2b:7a77 lladdr 10:f3:11:2b:7a:77 router STALE")
    def test_neighbors_missing_dev(self):
        """ ip neigh show dev <ifname> ends up not outputting any device name. """
        v4neigh, v6neigh = ipyroute.Neighbor.get()
        assert v4neigh.ipaddr == ipyroute.IPAddress('10.11.12.3')
        assert v4neigh.ifaddr == ipyroute.EUI('ff:ff:ff:ff:ff:ff')
        assert v4neigh.ifname == None
        assert v4neigh.permanent
        assert v6neigh.ipaddr == ipyroute.IPAddress('fe80::12f3:11ff:fe2b:7a77')
        assert v6neigh.ifaddr == ipyroute.EUI('10:f3:11:2b:7a:77')
        assert v6neigh.ifname == None
        assert v6neigh.stale
        assert not v6neigh.permanent



    def test_replace_neigh(self):
        """ Replace peer. """
        ipyroute.Neighbor.replace("172.16.0.1", lladdr='ff:ff:ff:ff:ff:ff', nud='permanent', dev='p3p1')
        expected = ipyroute.base.IPR.root.neigh.replace
        assert expected.called
        assert " ".join(expected.call_args[0]) == '172.16.0.1 lladdr ff:ff:ff:ff:ff:ff nud permanent dev p3p1'


class TestRoute(unittest.TestCase):
    """ Test Route lib. """
    def setUp(self):
        ipyroute.base.IPR = mock.Mock()

    def tearDown(self):
        pass

    @mocked("ipv4.route.show", "default  proto bird  src 23.235.34.27 \ nexthop via 172.16.56.4  dev p6p1 weight 1\     nexthop via 172.16.57.4  dev p1p3 weight 1")
    @mocked("ipv6.route.show", "fe80::/64 dev p1p4  proto kernel  metric 256")
    def test_default(self):
        """ Parse neighbors. """
        v4route, = ipyroute.Route4.get()
        assert v4route.network == ipyroute.IPNetwork('0.0.0.0/0')
        assert v4route.proto == "bird"
        assert v4route.src == ipyroute.IPAddress('23.235.34.27')
        nexthops = [(n.via, n.dev) for n in v4route.nexthops]
        assert nexthops == [(ipyroute.IPAddress('172.16.56.4'), 'p6p1'), (ipyroute.IPAddress('172.16.57.4'), 'p1p3')]

        v6route, = ipyroute.Route6.get()
        assert v6route.network == ipyroute.IPNetwork('fe80::/64')
        assert v6route.dev == 'p1p4'
        assert v6route.metric == 256

    @mocked("ipv4.route.show", "local 8.8.8.8 dev lo  scope host")
    @mocked("ipv6.route.show", "unreachable fe80::/64 dev p1p4  proto kernel  metric 256 error -101")
    def test_route_types(self):
        """ Parse route types. """
        v4route, = ipyroute.Route4.get()
        assert v4route.is_local
        assert v4route.network == ipyroute.IPNetwork('8.8.8.8/32')
        assert v4route.dev == "lo"

        v6route, = ipyroute.Route6.get()
        assert v6route.is_unreachable
        assert v6route.network == ipyroute.IPNetwork('fe80::/64')
        assert v6route.dev == "p1p4"
        assert v6route.proto == "kernel"
        assert v6route.metric == 256
        assert v6route.error == -101


class TestRule(unittest.TestCase):
    """ Test rule lib. """
    def setUp(self):
        ipyroute.base.IPR = mock.Mock()

    def tearDown(self):
        pass

    @mocked("ipv4.rule.show", "0:      from all lookup local")
    @mocked("ipv6.rule.show", "32766:  from all lookup main")
    def test_rule_list(self):
        """ Parse neighbors. """
        v4rule, = ipyroute.Rule4.get()
        assert v4rule.pref == 0
        assert v4rule.lookup == 'local'
        assert v4rule.fromprefix == ipyroute.IPNetwork('0.0.0.0/0')

        v6rule, = ipyroute.Rule6.get()
        assert v6rule.pref == 32766
        assert v6rule.lookup == 'main'
        assert v6rule.fromprefix == ipyroute.IPNetwork('::/0')

    @mocked("ipv4.rule.show", "0:      from all lookup local")
    def test_del_rule(self):
        """ Confirm rule deletion syntax. """
        rule = ipyroute.Rule4.get().pop()
        rule.delete()

        expected = getattr(ipyroute.base.IPR.ipv4.rule, 'del')
        assert expected.called
        assert " ".join(expected.call_args[0]) == 'from 0.0.0.0/0 lookup local pref 0'

    def test_add_rule(self):
        """ Confirm rule addition syntax. """
        rule = ipyroute.Rule6(fromprefix=ipyroute.Rule6.anyaddr, fwmark=5, lookup='local', pref=10)
        rule.add()
        expected = ipyroute.base.IPR.ipv6.rule.add
        assert expected.called
        assert " ".join(str(i) for i in expected.call_args[0]) == 'from ::/0 fwmark 5 lookup local pref 10'

    @mocked("ipv4.rule.show", "107:    from all fwmark 0x7 lookup 107")
    def test_fwmark(self):
        """ Assert fwmarks get translated to integers. """
        rule = ipyroute.Rule4.get().pop()
        assert rule.fwmark == 7

class TestLinkAux(unittest.TestCase):
    """ Test auxiliary functions on Link object to add addresses and ARP/ND neighbors. """
    def setUp(self):
        ipyroute.base.IPR = mock.Mock()

    def tearDown(self):
        pass

    @mocked("link.link.show",
            "8: p3p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000\    link/ether 02:40:00:20:03:01 brd ff:ff:ff:ff:ff:ff")
    @mocked("ipv4.addr.show", "8: p1p3    inet 172.16.1.1/24 brd 172.16.1.255 scope global p1p3\       valid_lft forever preferred_lft forever\n\
8: p1p3    inet 172.16.1.1 peer 192.168.1.1/32 scope global p1p3:egress\       valid_lft forever preferred_lft forever")
    @mocked("ipv6.addr.show", "8: p3p1    inet6 ::1/128 scope host \       valid_lft forever preferred_lft forever")
    def test_cache_expiry(self):
        """ Cached results should expire after fixed period. """
        link = ipyroute.Link.get().pop()

        ipyroute.Address.set_cache(0.1)
        assert not ipyroute.base.IPR.ipv4.addr.show.call_count
        assert ipyroute.IPNetwork('172.16.1.1/32') in link.addresses
        assert ipyroute.base.IPR.ipv4.addr.show.call_count == 1
        assert ipyroute.IPNetwork('192.168.1.1/32') in link.peers
        assert ipyroute.base.IPR.ipv4.addr.show.call_count == 1
        import time
        time.sleep(0.1)
        assert ipyroute.IPNetwork('192.168.1.1/32') in link.peers
        assert ipyroute.base.IPR.ipv4.addr.show.call_count == 2

    @mocked("link.link.show",
            "8: p3p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000\    link/ether 02:40:00:20:03:01 brd ff:ff:ff:ff:ff:ff")
    @mocked("ipv4.addr.show", "8: p1p3    inet 172.16.1.1/24 brd 172.16.1.255 scope global p1p3\       valid_lft forever preferred_lft forever\n\
8: p1p3    inet 172.16.1.1 peer 192.168.1.1/32 scope global p1p3:egress\       valid_lft forever preferred_lft forever")
    @mocked("ipv6.addr.show", "8: p3p1    inet6 ::1/128 scope host \       valid_lft forever preferred_lft forever")
    def test_cache_bust(self):
        """ Cached results should be purged on applying changes. """
        link = ipyroute.Link.get().pop()

        ipyroute.Address.set_cache(1)
        assert not ipyroute.base.IPR.ipv4.addr.show.call_count
        assert ipyroute.IPNetwork('172.16.1.1/32') in link.addresses
        assert ipyroute.base.IPR.ipv4.addr.show.call_count == 1
        assert ipyroute.IPNetwork('192.168.1.1/32') in link.peers
        assert ipyroute.base.IPR.ipv4.addr.show.call_count == 1

        link.add_peer(ipyroute.IPNetwork('172.16.1.1/32'), ipyroute.IPNetwork('192.16.1.2/32'))
        assert ipyroute.IPNetwork('192.168.1.1/32') in link.peers
        assert ipyroute.base.IPR.ipv4.addr.show.call_count == 2

