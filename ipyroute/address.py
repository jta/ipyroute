import functools
import re
from ipyroute import base

class Address(base.Base):
    regex = re.compile(r'(?P<ifnum>\d+): '
                       r'(?P<ifname>\S+?)(@(?P<phy>\S+))?\s+'
                       r'(inet|inet6) '
                       r'(?P<addr>\S+) '
                       r'(brd (?P<brd>\S+))?\s?'
                       r'(peer (?P<peer>\S+))?\s?'
                       r'scope (?P<scope>\S+) '
                       r'(?P=ifname)?((:(?P<label>\S+)))?\\')

    casts = dict(ifnum=int, addr=base.IPNetwork, brd=base.IPAddress, peer=base.IPNetwork)

    _scopes = set(['host', 'link', 'global'])

    @classmethod
    def _get(cls, *args):
        for line in base.IPR.ipv4.addr.show(*args):
            yield line
        for line in base.IPR.ipv6.addr.show(*args):
           yield line

    def __getattr__(self, name):
        """ Map scope types to properties. """
        try:
            scope, end = name.split("_scope")
            if scope in self._scopes and end == "":
                return scope == self.scope
        except ValueError:
            pass

        errmsg = "type object {0.__class__!r} has no attribute {1!r}"
        raise AttributeError(errmsg.format(self, name))

    @base.classproperty
    def cmd(cls):
        # We load root in IPR class at runtime.
        # pylint: disable=no-member
        return base.IPR.root.addr

    @base.classproperty
    def add(cls):
        """ Add command for address. """
        func = cls.cmd.add
        order = ('peer', 'dev', 'scope', 'to', 'label')
        return cls.shwrap(func, order)

    @base.classproperty
    def delete(cls):
        """ Add command for address. """
        func = getattr(cls.cmd, 'del')
        order = ('peer', 'dev', 'label')
        return cls.shwrap(func, order)

