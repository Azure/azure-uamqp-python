#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# pylint: disable=no-name-in-module,unused-import

import sys


PY2 = (2, 7) <= sys.version_info < (3, 0)
PY3 = (3, 4) <= sys.version_info < (4, 0)


if PY3:
    from urllib.parse import urlparse, unquote_plus, quote_plus

elif PY2:
    from urllib import urlparse, unquote_plus, quote_plus
