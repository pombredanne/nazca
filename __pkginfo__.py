# pylint: disable-msg=W0622
# copyright 2004-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of rql.
#
# rql is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# rql is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with rql. If not, see <http://www.gnu.org/licenses/>.
"""Nazca packaging information."""
__docformat__ = "restructuredtext en"
import sys

distname = 'nazca'
modname = 'nazca'

numversion = (0, 4, 1)
version = '.'.join([str(num) for num in numversion])

license = 'LGPL' # 2.1 or later
description = "Python library for data alignment"
web = "https://www.logilab.org/project/nazca"
author = "Logilab"
author_email = "contact@logilab.fr"


from os.path import join
include_dirs = [join('test', 'data'), 'data', 'examples', 'ner', 'rl', 'utils']

if sys.version_info < (2, 7):
    install_requires = ['unittest2 >= 0.5.1']
