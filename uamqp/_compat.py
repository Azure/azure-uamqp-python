#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# pylint: disable=no-name-in-module,unused-import,redefined-builtin,import-error,undefined-variable,ungrouped-imports

import sys

PY2 = (2, 7) <= sys.version_info < (3, 0)
PY3 = (3, 4) <= sys.version_info < (4, 0)


if PY3:
    builtin_str = str
    str = str
    bytes = bytes
    basestring = (str, bytes,)
    numeric_types = (int, float,)
    integer_types = (int,)

    long = int

elif PY2:
    builtin_str = str
    bytes = str
    str = unicode
    basestring = basestring
    numeric_types = (int, long, float,)
    integer_types = (int, long,)

    long = long
