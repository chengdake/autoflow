#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : qichun tang
# @Contact    : tqichun@gmail.com
import os
import re
import sys

from setuptools import setup, find_packages

from hyperflow.__version__ import __version__


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), encoding='utf-8').read()


if os.name != 'posix':
    raise ValueError(
        'Detected unsupported operating system: %s. '
    )

if sys.version_info < (3, 5):
    raise ValueError(
        'Unsupported Python version %d.%d.%d found. HyperFlow requires Python '
        '3.6 or higher.' % (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    )

with open('README.md') as fh:
    long_description = fh.read()

GIT_PATTERN = re.compile(r"git\+https://github\.com/(.*?)/(.*?)\.git")
HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'requirements.txt')) as fp:
    install_requires = []
    for r in fp.readlines():
        r = r.strip()
        if r.startswith("#"):
            continue
        elif r.startswith("git+"):
            match = GIT_PATTERN.match(r)
            if match:
                package_name = match.group(2)
            install_require = f"{package_name} @ {r}"
            install_requires += [install_require]
        else:
            install_requires += [r]


def get_package_data(name, suffixes):
    g = os.walk(name)
    lst = []
    for path, dir_list, file_list in g:
        for file_name in file_list:
            lst.append(os.path.join(path, file_name))
    ret = []
    for item in lst:
        for suffix in suffixes:
            if item.endswith(suffix):
                ret.append(item)
                break
    M = len(name) + 1
    ret = [s[M:] for s in ret]
    return ret


needed_suffixes = ['.json', '.txt', '.yml', '.yaml']

setup(
    name='HyperFlow',
    version=__version__,
    author='qichun tang',
    author_email='tqichun@gmail.com',
    description='HyperFlow: Automatic machine learning workflow modeling platform.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='BSD',
    url='https://github.com/Hyper-Flow/HyperFlow',
    packages=find_packages("./", exclude=['test', 'examples']),
    package_dir={
        'hyperflow': './hyperflow',
        'dsmac': './dsmac',
        'generic_fs': './generic_fs'
    },
    package_data={'hyperflow': get_package_data('hyperflow', needed_suffixes),
                  'dsmac': get_package_data('dsmac', needed_suffixes)},
    python_requires='>=3.6.*',
    install_requires=install_requires,
    platforms=['Linux'],
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: Linux",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)