#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0404,W0622,W0704,W0613
# copyright 2014 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr -- mailto:contact@logilab.fr
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

"""Generic Setup script, takes package info from __pkginfo__.py file.
"""
__docformat__ = "restructuredtext en"

import os
import sys
import shutil
from os.path import isdir, exists, join, dirname

try:
    if os.environ.get('NO_SETUPTOOLS'):
        raise ImportError()
    from setuptools import setup
    from setuptools.command import install_lib
    USE_SETUPTOOLS = 1
except ImportError:
    from distutils.core import setup
    from distutils.command import install_lib
    USE_SETUPTOOLS = 0

try:
    # python3
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    # python2.x
    from distutils.command.build_py import build_py


# load metadata from the __pkginfo__.py file so there is no risk of conflict
# see https://packaging.python.org/en/latest/single_source_version.html
base_dir = dirname(__file__)

pkginfo = {}
with open(join(base_dir, "__pkginfo__.py")) as f:
    exec(f.read(), pkginfo)

# get required metadatas
modname = pkginfo['modname']
version = pkginfo['version']
license = pkginfo['license']
description = pkginfo['description']
web = pkginfo['web']
author = pkginfo['author']
author_email = pkginfo['author_email']
classifiers = pkginfo['classifiers']

with open(join(base_dir, 'README')) as f:
    long_description = f.read()

# get optional metadatas
distname = pkginfo.get('distname', modname)
scripts = pkginfo.get('scripts', ())
include_dirs = pkginfo.get('include_dirs', ())
data_files = pkginfo.get('data_files', None)
ext_modules = pkginfo.get('ext_modules', None)
dependency_links = pkginfo.get('dependency_links', ())

if USE_SETUPTOOLS:
    requires = {}
    for entry in ("__depends__", "__recommends__"):
        requires.update(pkginfo.get(entry, {}))
    install_requires = [("%s %s" % (d, v and v or "")).strip()
                       for d, v in requires.iteritems()]
else:
    install_requires = []

STD_BLACKLIST = ('CVS', '.svn', '.hg', 'debian', 'dist', 'build')
IGNORED_EXTENSIONS = ('.pyc', '.pyo', '.elc', '~')

def ensure_scripts(linux_scripts):
    """Creates the proper script names required for each platform
    (taken from 4Suite)
    """
    from distutils import util
    if util.get_platform()[:3] == 'win':
        scripts_ = [script + '.bat' for script in linux_scripts]
    else:
        scripts_ = linux_scripts
    return scripts_

def get_packages(directory, prefix):
    """return a list of subpackages for the given directory"""
    result = []
    for package in os.listdir(directory):
        absfile = join(directory, package)
        if isdir(absfile):
            if exists(join(absfile, '__init__.py')) or \
                   package in ('test', 'tests'):
                if prefix:
                    result.append('%s.%s' % (prefix, package))
                else:
                    result.append(package)
                result += get_packages(absfile, result[-1])
    return result

EMPTY_FILE = '''"""generated file, don't modify or your data will be lost"""
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    pass
'''

class MyInstallLib(install_lib.install_lib):
    """extend install_lib command to handle  package __init__.py and
    include_dirs variable if necessary
    """
    def run(self):
        """overridden from install_lib class"""
        install_lib.install_lib.run(self)
        # manually install included directories if any
        if include_dirs:
            base = modname
            for directory in include_dirs:
                dest = join(self.install_dir, base, directory)
                shutil.rmtree(dest, ignore_errors=True)
                shutil.copytree(directory, dest)

def install(**kwargs):
    """setup entry point"""
    if USE_SETUPTOOLS:
        if '--force-manifest' in sys.argv:
            sys.argv.remove('--force-manifest')
    # install-layout option was introduced in 2.5.3-1~exp1
    elif sys.version_info < (2, 5, 4) and '--install-layout=deb' in sys.argv:
        sys.argv.remove('--install-layout=deb')
    kwargs['package_dir'] = {modname : '.'}
    packages = [modname] + get_packages(os.getcwd(), modname)
    if USE_SETUPTOOLS and install_requires:
        kwargs['install_requires'] = install_requires
        kwargs['dependency_links'] = dependency_links
    kwargs['packages'] = packages
    return setup(name = distname,
                 version = version,
                 license = license,
                 description = description,
                 long_description = long_description,
                 author = author,
                 author_email = author_email,
                 url = web,
                 scripts = ensure_scripts(scripts),
                 data_files = data_files,
                 ext_modules = ext_modules,
                 cmdclass = {'install_lib': MyInstallLib,
                             'build_py':    build_py},
                 **kwargs
                 )

if __name__ == '__main__' :
    install()
