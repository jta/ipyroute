import re
from ipyroute import base
import six

class Address(base.Base):
    regex = re.compile(r'(?P<ifnum>\d+): '
                       r'(?P<ifname>\S+?)(@(?P<phy>\S+))?\s+'
                       r'(inet|inet6) '
                       r'(?P<addr>\S+) '
                       r'(brd (?P<brd>\S+))?\s?'
                       r'(peer (?P<peer>\S+))?\s?'
                       r'scope (?P<scope>\S+) '
                       r'(?P<deprecated>deprecated)?\s?'
                       r'(mngtmpaddr (?P<mngtmpaddr>\S+))?\s?'
                       r'(?P=ifname)?((:(?P<label>[^\\]+)))?')


    casts = dict(ifnum=int,
                 ifname=unicode if not six.PY3 else lambda x: x,
                 label=unicode if not six.PY3 else lambda x: x,
                 addr=base.IPNetwork, brd=base.IPAddress, peer=base.IPNetwork)

    _scopes = set(['host', 'link', 'global'])
    _order = ('peer', 'dev', 'scope', 'to', 'label')

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
        super(Address, self).__getattr__(name)

    @base.classproperty
    def cmd(cls):
        # We load root in IPR class at runtime.
        # pylint: disable=no-member
        return base.IPR.root.addr

    @base.classproperty
    def add(cls):
        """ Add command for address. """
        cls.cache.clear()
        return cls.shwrap(cls.cmd.add, cls._order)

    @base.classproperty
    def change(cls):
        """ Change command for address. """
        cls.cache.clear()
        return cls.shwrap(cls.cmd.change, cls._order)

    @base.classproperty
    def replace(cls):
        """ Replace command for address. """
        cls.cache.clear()
        return cls.shwrap(cls.cmd.replace, cls._order)

    @base.classproperty
    def delete(cls):
        """ Delete command for address. """
        cls.cache.clear()
        return cls.shwrap(getattr(cls.cmd, 'del'), cls._order)

