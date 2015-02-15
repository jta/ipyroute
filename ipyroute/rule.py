""" Lookup rules """
import re
import six
from ipyroute import base

class Rule(base.Base):
    regex = re.compile(r'(?P<pref>\d+):\s+'
                       r'(from (?P<fromprefix>\w+)\s+)?'
                       r'(to (?P<toprefix>\w+)\s+)?'
                       r'(fwmark (?P<fwmark>\w+)\s+)?'
                       r'(lookup (?P<lookup>\w+))?')

    casts = dict(pref=int,
                 fwmark=lambda x: int(x, 16) if isinstance(x, six.string_types) and 'x' in x else int(x),
                 lookup=unicode if not six.PY3 else lambda x: x,
                 fromprefix=base.IPNetwork,
                 toprefix=base.IPNetwork)
    _order = ('from', 'fwmark', 'lookup', 'pref')

    @classmethod
    def _get(cls, *args):
        for line in cls.cmd.show(*args):
            yield line

    def add(self):
        """ Add command for address. """
        Rule.cache.clear()
        kwargs = dict([(k.replace('prefix', ''), str(v))
                      for (k, v) in self.__dict__.items() if v is not None])
        return self.shwrap(self.cmd.add, self._order)(**kwargs)

    def delete(self):
        """ Delete command for rule. """
        Rule.cache.clear()
        kwargs = dict([(k.replace('prefix', ''), str(v))
                      for (k, v) in self.__dict__.items() if v is not None])
        return self.shwrap(getattr(self.cmd, 'del'), self._order)(**kwargs)

    @classmethod
    def construct(cls, result, _, *args):
        fromprefix = result.get('fromprefix')
        if fromprefix == 'all':
            result['fromprefix'] = cls.anyaddr
        return cls(**result)

    def __hash__(self):
        """ Needed for constructing rule sets. """
        return self.pref

class Rule4(Rule):
    anyaddr = "0.0.0.0/0"

    @base.classproperty
    def cmd(cls, *args):
        """ Rules are a pain because we have to manage both v4 and v6 transparently. """
        return base.IPR.ipv4.rule

class Rule6(Rule):
    anyaddr = "::/0"

    @base.classproperty
    def cmd(cls, *args):
        """ Rules are a pain because we have to manage both v4 and v6 transparently. """
        return base.IPR.ipv6.rule


