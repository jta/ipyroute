#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (2,5):
    raise NotImplementedError("Sorry, you need at least Python 2.5 or Python 3.x to use ipyroute.")

__author__ = 'João Taveira Araújo'
__version__ = '0.0.36'
__license__ = 'MIT'

setup(name='ipyroute',
      version=__version__,
      description="Yet another interface for iproute2",
      author=__author__,
      author_email='joao.taveira@gmail.com',
      url='https://github.com/jta/ipyroute',
      packages=['ipyroute'],
      install_requires=[ "sh", "netaddr", "six" ],
      license='MIT',
      platforms='any',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 2.5',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   ],)
