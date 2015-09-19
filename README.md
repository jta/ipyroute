ipyroute
=========

A very simple wrapper around iproute2 using `sh` and regexing.

### Link

```
>>> import ipyroute
>>> links = ipyroute.Link.get()
>>> [i.name for i in links]
[u'lo', u'bond0', u'dummy0', u'tunl0', u'gre0', u'gretap0', u'p2p1',
```

You can pass a function into `get` to filter out results:

```
>>> lo, = ipyroute.Link.get(filt = lambda x: x.name == 'lo')                                                                                                                      
>>> lo.__dict__
{'qlen': None, 'qdisc': u'noqueue', 'group': u'default', 'name': u'lo', 'phy': None, 'mtu': 65536, 'state': u'UNKNOWN', 'num': 1, 'flags': u'LOOPBACK,UP,LOWER_UP', 'mode': u'DEFAULT', 'brd': u'00:00:00:00:00:00', 'type': u'loopback', 'addr': u'00:00:00:00:00:00'}`
```

From the link object, you should be able to retrieve the relevant set of addresses and neighbors:

```
>>> p2p1, = ipyroute.Link.get(filt = lambda x: x.name == 'p2p1')
>>> p2p1.addresses
set([IPNetwork('fe80::225:90ff:fec0:6140/64'), IPNetwork('172.16.39.24/22')])
>>> p2p1.neighbors
set([IPAddress('172.16.39.23'), IPAddress('172.16.36.7')])
```

### Address

```
>>> addresses = ipyroute.Address.get(filt = lambda x: x.ifname == 'p2p1')
[<ipyroute.address.Address object at 0xedbe50>, <ipyroute.address.Address object at 0xedbe90>]
>>> addresses[0].__dict__
{'addr': IPNetwork('172.16.39.24/22'), 'ifnum': 7, 'label': None, 'phy': None, 'peer': None, 'scope': u'global', 'ifname': u'p2p1', 'brd': IPAddress('172.16.39.255')}
```

### Route

You must specify where you are expecting an IPv4 or IPv6 route sadly.

```
>>> route, = ipyroute.Route4.get(table='default')
>>> route.src
IPAddress('192.168.1.24')
>>> route.nexthops
[<ipyroute.route.Nexthop object at 0x1b935d0>, <ipyroute.route.Nexthop object at 0x1b93810>, <ipyroute.route.Nexthop object at 0x1b93290>, <ipyroute.route.Nexthop object at 0x1b930d0>]
>>> [i.via for i in route.nexthops]
[IPAddress('172.16.57.1'), IPAddress('172.16.59.1'), IPAddress('172.16.56.1'), IPAddress('172.16.58.1')]
```

In IPv6 nexthops are treated as separate route entries, so you have to deal with abstracting over higher up:

```
>>> routes = ipyroute.Route6.get(table='default')
>>> [i.via for i in routes]
[IPAddress('fe80::21c:73ff:fe42:143f'), IPAddress('fe80::21c:73ff:fe42:1e8f'), IPAddress('fe80::21c:73ff:fe1e:a614'), IPAddress('fe80::21c:73ff:fe1e:8970')]
```

Missing documentation for `ipyroute.Neighbor`, `ipyroute.Rule4` and `ipyroute.Rule6`, but if you poke around tests you'll get the picture.
