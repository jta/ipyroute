""" Lookup rules """
import re
from ipyroute import base

class Rule(base.Base):
    regex = re.compile(r'(?P<pref>\d+):\s+'
                       r'(from (?P<fromprefix>\w+)\s+)?'
                       r'(to (?P<toprefix>\w+)\s+)?'
                       r'(fwmark (?P<fwmark>\w+)\s+)?'
                       r'(lookup (?P<lookup>\w+))?')

    casts = dict(pref=int, fromprefix=base.IPNetwork, toprefix=base.IPNetwork)
    _order = ('from', 'fwmark', 'lookup', 'pref')

    @classmethod
    def _get(cls, *args):
        for line in cls.cmd.show(*args):
            yield line

    @classmethod
    def add(cls, fromprefix, **kwargs):
        """ Add command for address. """
        kwargs['from'] = cls._allprefix if fromprefix == 'any' else str(fromprefix)
        return cls.shwrap(cls.cmd.add, cls._order)(**kwargs)

    def delete(self):
        """ Delete command for rule. """
        kwargs = dict([(k.replace('prefix', ''), str(v))
                      for (k, v) in self.__dict__.items() if v is not None])
        return self.shwrap(getattr(self.cmd, 'del'), self._order)(**kwargs)

    @classmethod
    def construct(cls, result, _, *args):
        fromprefix = result.get('fromprefix')
        if fromprefix == 'all':
            result['fromprefix'] = cls._allprefix
        return cls(**result)

class Rule4(Rule):
    _allprefix = "0.0.0.0/0"

    @base.classproperty
    def cmd(cls, *args):
        """ Rules are a pain because we have to manage both v4 and v6 transparently. """
        return base.IPR.ipv4.rule

class Rule6(Rule):
    _allprefix = "::/0"

    @base.classproperty
    def cmd(cls, *args):
        """ Rules are a pain because we have to manage both v4 and v6 transparently. """
        return base.IPR.ipv6.rule


