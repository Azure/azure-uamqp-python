
# pylint: skip-file

import struct
import time
from enum import Enum

from .performatives import _decode_frame

# The protocol header consists of the upper case ASCII letters "AMQP" followed by a protocol id of zero, followed by three unsigned bytes representing the major, minor, and revision of the protocol version (currently 1 (MAJOR), 0 (MINOR), 0 (REVISION)). In total this is an 8-octet sequence] */
AMQP_HEADER = b'AMQP0100'


def unpack(data):
    if len(data) != 8:
        raise ValueError("Invalid frame header")
    if data[0:4] == AMQP_HEADER[0:4]:
        return None, None, None, None  # TODO: Validate AMQP version
    size = struct.unpack('>I', data[0:4])[0]
    offset = struct.unpack('>B', data[4:5])[0]
    frame_type = struct.unpack('>B', data[5:6])[0]
    channel = struct.unpack('>H', data[6:])[0]
    return (size, offset, frame_type, channel)


class ReceiveFrameState(Enum):
    FRAME_SIZE = 0
    FRAME_DATA = 1

class ConnectionState(Enum):
    START = 0
    HDR_RCVD = 1
    HDR_SENT = 2
    HDR_EXCH = 3
    OPEN_PIPE = 4
    OC_PIPE = 5
    OPEN_RCVD = 6
    OPEN_SENT = 7
    CLOSE_PIPE = 8
    OPENED = 9
    CLOSE_RCVD = 10
    CLOSE_SENT = 11
    DISCARDING = 12
    END = 13
    ERROR = 14


class OnConnectionClosedEvent(object):

    def __init__(self):
        self.on_connection_close_received = None
        self.context = None


class Endpoint(object):

    def __init__(self):
        self.incoming_channel = None
        self.outgoing_channel = None
        self.on_endpoint_frame_received = None
        self.on_connection_state_changed = None
        self.callback_context = None
        self.connection = None


class Connection(object):

    def __init__(self):
        self.io = None
        self.state = None
        self.header_bytes_received = None
        self.connection_state = None
        self.frame_codec = None
        self.amqp_frame_codec = None
        self.endpoints = []
        self.endpoint_count = None
        self.host_name = None
        self.container_id = None
        self.tick_counter = None
        self.remote_max_frame_size = None

        self.on_send_complete = None
        self.on_new_endpoint = None
        self.on_state_changed = None
        self.on_io_error = None
        self.on_close_received_event = None

        # options
        self.max_frame_size = None
        self.channel_max = None
        self.idle_timeout = None
        self.remote_idle_timeout = None
        self.remote_idle_timeout_send_frame_millisecond = None
        self.idle_timeout_empty_frame_send_ratio = None
        self.last_frame_received_time = None
        self.last_frame_sent_time = None
        self.properties = None

        self.is_underlying_io_open = False
        self.idle_timeout_specified = False
        self.is_remote_frame_received = False
        self.is_trace_on = True

    def set_state(self, connection_state):
        previous_state = self.state
        self.state = connection_state

        if self.on_state_changed:
            self.on_state_changed(
                self,
                connection_state,
                previous_state
            )
        for endpoint in self.endpoints:
            if endpoint.on_connection_state_changed:
                endpoint.on_connection_state_changed(
                    endpoint,
                    connection_state,
                    previous_state
                )
        print("Connection state changed {} -> {}".format(previous_state, connection_state))

    def read_frame(self):
        frame = self.io.read_frame(unpack=unpack)
        if frame[0] is not None:  # TODO: What to do with frame type?
            return _decode_frame(frame[2], frame[3] - 2)

    def open(self):
        if not self.is_underlying_io_open:
            try:
                self.io.connect()
            except:
                raise
            else:
                self.is_underlying_io_open = True
                self.set_state(ConnectionState.START)
                return 0
        return 0

    def send_header(self):
        try:
            self.io.write(AMQP_HEADER)
        except Exception as e:
            print("Write failed", e)
            try:
                self.io.close()
            except Exception as e:
                print("xio_close failed.", e)
            self.set_state(ConnectionState.END)
            return 1
        
        if self.is_trace_on:
            print("-> Header (AMQP 0.1.0.0)")
        self.set_state(ConnectionState.HDR_SENT)
        return 0

    def send_frame(self, frame, channel):
        try:
            frame_data, header = frame.encode()
            payload = header + channel + frame_data
            print(payload)
            self.io.write(payload)
        except Exception as e:
            print("Write failed", e)
            try:
                self.io.close()
            except Exception as e:
                print("xio_close failed.", e)
            self.set_state(ConnectionState.END)
            return 1
        
        if self.is_trace_on:
            print(frame.log())
        self.set_state(ConnectionState.HDR_SENT)
        return 0




