#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from uamqp_encoder import c_uamqp  # pylint: disable=import-self
from ._decode_frame import (
    decode_frame,
    decode_payload,
    decode_pickle_frame,
    decode_empty_frame,
    construct_frame
)

__version__ = "0.1.0"
