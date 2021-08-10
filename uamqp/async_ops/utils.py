#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import sys
from uamqp.utils import get_running_loop

def get_dict_with_loop_if_needed(loop):
    if sys.version_info >= (3, 10) and loop:
        raise ValueError("Starting Python 3.10, asyncio no longer supports loop as a parameter.")
    return {'loop': loop or get_running_loop()} if sys.version_info < (3, 10) else {}
