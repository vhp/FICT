#!/usr/bin/env python3
from setuptools import setup

setup(
    name = 'Fict',
    version = "0.1",
    description = 'File integrity checking tool',
    author = 'Vincent Perricone',
    author_email = 'vhp@fastmail.fm',
    url = 'https://github.com/vhp/fict',
    download_url = 'none',
    platforms = ['linux'],
    license = 'Simplified FreeBSD License',
    scripts = ['fict'],
    packages = ['lib'],
    install_requires=["docopt"],
    )
