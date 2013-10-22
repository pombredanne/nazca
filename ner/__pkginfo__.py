# -*- coding:utf-8 -*-
# copyright 2013 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
"""Nerdy packaging information."""
__docformat__ = "restructuredtext en"
import sys

distname = 'nerdy'
modname = 'nerdy'

numversion = (0, 1, 0)
version = '.'.join([str(num) for num in numversion])

license = 'LGPL' # 2.1 or later
description = "Python library for data alignment"
web = "https://www.logilab.org/project/nerdy"
author = "Logilab"
author_email = "contact@logilab.fr"


from os.path import join
scripts = []
include_dirs = []

if sys.version_info < (2, 7):
    install_requires = ['unittest2 >= 0.5.1']
