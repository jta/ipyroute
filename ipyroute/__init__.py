""" Interface with ipyroute utility. """
from . import base
from .base import EUI, IPAddress, IPNetwork

from .address import Address
from .link import Link
from .neighbor import Neighbor
from .route import Route4, Route6
from .rule import Rule4, Rule6
