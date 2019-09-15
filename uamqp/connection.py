#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from enum import Enum


class ConnectionState(Enum):
    #: In this state a Connection exists, but nothing has been sent or received. This is the state an
    #: implementation would be in immediately after performing a socket connect or socket accept.
    START = 0
    #: In this state the Connection header has been received from our peer, but we have not yet sent anything.
    HDR_RCVD = 1
    #: In this state the Connection header has been sent to our peer, but we have not yet received anything.
    HDR_SENT = 2
    #: In this state we have sent and received the Connection header, but we have not yet sent or
    #: received an open frame.
    HDR_EXCH = 3
    #: In this state we have sent both the Connection header and the open frame, but
    #: we have not yet received anything.
    OPEN_PIPE = 4
    #: In this state we have sent the Connection header, the open frame, any pipelined Connection traffic,
    #: and the close frame, but we have not yet received anything.
    OC_PIPE = 5
    #: In this state we have sent and received the Connection header, and received an open frame from
    #: our peer, but have not yet sent an open frame.
    OPEN_RCVD = 6
    #: In this state we have sent and received the Connection header, and sent an open frame to our peer,
    #: but have not yet received an open frame.
    OPEN_SENT = 7
    #: In this state we have send and received the Connection header, sent an open frame, any pipelined
    #: Connection traffic, and the close frame, but we have not yet received an open frame.
    CLOSE_PIPE = 8
    #: In this state the Connection header and the open frame have both been sent and received.
    OPENED = 9
    #: In this state we have received a close frame indicating that our partner has initiated a close.
    #: This means we will never have to read anything more from this Connection, however we can
    #: continue to write frames onto the Connection. If desired, an implementation could do a TCP half-close
    #: at this point to shutdown the read side of the Connection.
    CLOSE_RCVD = 10
    #: In this state we have sent a close frame to our partner. It is illegal to write anything more onto
    #: the Connection, however there may still be incoming frames. If desired, an implementation could do
    #: a TCP half-close at this point to shutdown the write side of the Connection.
    CLOSE_SENT = 11
    #: The DISCARDING state is a variant of the CLOSE_SENT state where the close is triggered by an error.
    #: In this case any incoming frames on the connection MUST be silently discarded until the peer's close
    #: frame is received.
    DISCARDING = 12
    #: In this state it is illegal for either endpoint to write anything more onto the Connection. The
    #: Connection may be safely closed and discarded.
    END = 13


class Connection(object):
    """
    :param str container_id: The ID of the source container.
    :param str hostname: The name of the target host.
    :param int max_frame_size: Proposed maximum frame size in bytes.
    :param int channel_max: The maximum channel number that may be used on the Connection.
    :param timedelta idle_time_out: Idle time-out in milliseconds.
    :param list(str) outgoing_locales: Locales available for outgoing text.
    :param list(str) incoming_locales: Desired locales for incoming text in decreasing level of preference.
    :param list(str) offered_capabilities: The extension capabilities the sender supports.
    :param list(str) required_capabilities: The extension capabilities the sender may use if the receiver supports
    :param dict properties: Connection properties.
    """
