# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import re, ast

try: # for pip >= 10
	from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
	from pip.req import parse_requirements

# get version from __version__ variable in bench_manager/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('bench_manager/__init__.py', 'rb') as f:
	version = str(ast.literal_eval(_version_re.search(
		f.read().decode('utf-8')).group(1)))

requirements = parse_requirements("requirements.txt", session="")

setup(
	name='bench_manager',
	version=version,
	description='A bench helper for the command line',
	author='Yefri Tavarez',
	author_email='yefritavarez@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=[str(ir.req) for ir in requirements],
	dependency_links=[str(ir._link) for ir in requirements if ir._link]
)
