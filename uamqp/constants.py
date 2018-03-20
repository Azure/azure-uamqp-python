#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from enum import Enum

from uamqp import utils
from uamqp import c_uamqp


DEFAULT_AMQPS_PORT = c_uamqp.AMQPS_PORT
AUTH_EXPIRATION_SECS = c_uamqp.AUTH_EXPIRATION_SECS
AUTH_REFRESH_SECS = c_uamqp.AUTH_REFRESH_SECS

STRING_FILTER = b"apache.org:selector-filter:string"
OPERATION = b"operation"
READ_OPERATION = b"READ"
MGMT_TARGET = b"$management"


BATCH_MESSAGE_FORMAT = c_uamqp.AMQP_BATCH_MESSAGE_FORMAT
MAX_FRAME_SIZE_BYTES = c_uamqp.MAX_FRAME_SIZE_BYTES
MAX_MESSAGE_LENGTH_BYTES = c_uamqp.MAX_MESSAGE_LENGTH_BYTES


class MessageState(Enum):
    WaitingToBeSent = 0
    WaitingForAck = 1
    Complete = 2
    PartiallySent = 3


class MessageReceiverState(Enum):
    Idle = c_uamqp.MESSAGE_RECEIVER_STATE_IDLE
    Opening = c_uamqp.MESSAGE_RECEIVER_STATE_OPENING
    Open = c_uamqp.MESSAGE_RECEIVER_STATE_OPEN
    Closing = c_uamqp.MESSAGE_RECEIVER_STATE_CLOSING
    Error = c_uamqp.MESSAGE_RECEIVER_STATE_ERROR


class MessageSendResult(Enum):
    Ok = c_uamqp.MESSAGE_SEND_OK
    Error = c_uamqp.MESSAGE_SEND_ERROR
    Timeout = c_uamqp.MESSAGE_SEND_TIMEOUT
    Cancelled = c_uamqp.MESSAGE_SEND_CANCELLED


class MessageSenderState(Enum):
    Idle = c_uamqp.MESSAGE_SENDER_STATE_IDLE
    Opening = c_uamqp.MESSAGE_SENDER_STATE_OPENING
    Open = c_uamqp.MESSAGE_SENDER_STATE_OPEN
    Closing = c_uamqp.MESSAGE_SENDER_STATE_CLOSING
    Error = c_uamqp.MESSAGE_SENDER_STATE_ERROR


class MessageReceiverState(Enum):
    Idle = c_uamqp.MESSAGE_RECEIVER_STATE_IDLE
    Opening = c_uamqp.MESSAGE_RECEIVER_STATE_OPENING
    Open = c_uamqp.MESSAGE_RECEIVER_STATE_OPEN
    Closing = c_uamqp.MESSAGE_RECEIVER_STATE_CLOSING
    Error = c_uamqp.MESSAGE_RECEIVER_STATE_ERROR


class ManagementLinkState(Enum):
    Ok = c_uamqp.AMQP_MANAGEMENT_OPEN_OK
    Error = c_uamqp.AMQP_MANAGEMENT_OPEN_ERROR
    Cancelled = c_uamqp.AMQP_MANAGEMENT_OPEN_CANCELLED


class ManagementOperationResult(Enum):
    Ok = c_uamqp.AMQP_MANAGEMENT_EXECUTE_OPERATION_OK
    Error = c_uamqp.AMQP_MANAGEMENT_EXECUTE_OPERATION_ERROR
    BadStatus = c_uamqp.AMQP_MANAGEMENT_EXECUTE_OPERATION_FAILED_BAD_STATUS
    Closed = c_uamqp.AMQP_MANAGEMENT_EXECUTE_OPERATION_INSTANCE_CLOSED


class Role(Enum):
    Sender = c_uamqp.ROLE_SENDER
    Receiver = c_uamqp.ROLE_RECEIVER


class SenderSettleMode(Enum):
    Unsettled = c_uamqp.SENDER_SETTLE_MODE_UNSETTLED
    Settled = c_uamqp.SENDER_SETTLE_MODE_SETTLED
    Mixed = c_uamqp.SENDER_SETTLE_MODE_MIXED


class ReceiverSettleMode(Enum):
    PeekLock = c_uamqp.RECEIVER_SETTLE_MODE_PEEKLOCK
    ReceiveAndDelete = c_uamqp.RECEIVER_SETTLE_MODE_RECEIVEANDDELETE


class CBSOperationResult(Enum):
    Ok = c_uamqp.CBS_OPERATION_RESULT_OK
    Error = c_uamqp.CBS_OPERATION_RESULT_CBS_ERROR
    Failed = c_uamqp.CBS_OPERATION_RESULT_OPERATION_FAILED
    Closed = c_uamqp.CBS_OPERATION_RESULT_INSTANCE_CLOSED


class CBSOpenState(Enum):
    Ok = c_uamqp.CBS_OPEN_COMPLETE_OK
    Error = c_uamqp.CBS_OPEN_COMPLETE_ERROR
    Cancelled = c_uamqp.CBS_OPEN_COMPLETE_CANCELLED


class CBSAuthStatus(Enum):
    Ok = c_uamqp.AUTH_STATUS_OK
    Idle = c_uamqp.AUTH_STATUS_IDLE
    InProgress = c_uamqp.AUTH_STATUS_IN_PROGRESS
    Timeout = c_uamqp.AUTH_STATUS_TIMEOUT
    RefreshRequired = c_uamqp.AUTH_STATUS_REFRESH_REQUIRED
    Expired = c_uamqp.AUTH_STATUS_EXPIRED
    Failure = c_uamqp.AUTH_STATUS_FAILURE


class MgmtExecuteResult(Enum):
    Ok = c_uamqp.AMQP_MANAGEMENT_EXECUTE_OPERATION_OK
    Error = c_uamqp.AMQP_MANAGEMENT_EXECUTE_OPERATION_ERROR
    Failed = c_uamqp.AMQP_MANAGEMENT_EXECUTE_OPERATION_FAILED_BAD_STATUS
    Closed = c_uamqp.AMQP_MANAGEMENT_EXECUTE_OPERATION_INSTANCE_CLOSED


class MgmtOpenStatus(Enum):
    Ok = c_uamqp.AMQP_MANAGEMENT_OPEN_OK
    Error = c_uamqp.AMQP_MANAGEMENT_OPEN_ERROR
    Cancelled = c_uamqp.AMQP_MANAGEMENT_OPEN_CANCELLED

