#!/usr/bin/env python3
from setuptools import setup
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name = 'Fict',
    version = "1.0.0",
    description = 'File integrity checking tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author = 'Vincent Perricone',
    author_email = 'vhp@fastmail.fm',
    url = 'https://github.com/vhp/fict',
    download_url = 'https://github.com/vhp/fict',
    platforms = ['linux'],
    license = 'Simplified FreeBSD License',
    scripts = ['fict'],
    packages = ['lib'],
    install_requires=["docopt", "joblib", "alive_progress<2.2"],
    )
