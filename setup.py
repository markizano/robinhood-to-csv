#!/usr/bin/env python3

import os
import sys
from glob import glob
from pprint import pprint
from setuptools import setup

sys.path.insert(0, os.path.abspath('lib'))

setup_opts = {
    'name'                : 'robinhood',
    # We change this default each time we tag a release.
    'version'             : '1.0.3',
    'description'         : 'Robinhood to CSV script. Enables you to create a CSV from your transactions.',
    'author'              : 'Josh Fraser (2015), Rohan Pai (2015), Markizano Draconus (2021) <markizano@markizano.net>',
    'author_email'        : 'null, null, markizano@markizano.net',
    'license'             : 'MIT',
    'url'                 : 'https://www.robinhood.com/',

    'tests_require'       : ['nose', 'mock', 'coverage'],
    'install_requires'    : [
      'requests',
      'pandas>=0.17.0',
      'uuid',
      'kizano',
    ],
    'package_dir'         : { 'Robinhood': 'lib/Robinhood' },
    'packages'            : [
        'Robinhood',
    ],
    'scripts'             : glob('bin/*'),
    'test_suite'          : 'tests',
}

try:
    import argparse
    HAS_ARGPARSE = True
except:
    HAS_ARGPARSE = False

if not HAS_ARGPARSE: setup_opts['install_requires'].append('argparse')

# I botch this too many times.
if sys.argv[1] == 'test':
    sys.argv[1] = 'nosetests'

if 'DEBUG' in os.environ: pprint(setup_opts)

setup(**setup_opts)

