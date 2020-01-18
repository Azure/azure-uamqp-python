#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
from enum import Enum

from ._encode import encode_value, describe_performative
from .message import BareMessage, MessageBodyType
from .link import LinkDeliverySettleReason


LOGGER = logging.getLogger(__name__)


class SenderState(Enum):

    IDLE = 0
    OPENING = 1
    OPEN = 2
    CLOSING = 3
    ERROR = 4


class MessageSendResult(Enum):

    OK = 0
    ERROR = 1
    TIMEOUT = 2
    CANCELLED = 3


class _MessageSendState(Enum):

    NOT_SENT = 0
    PENDING = 1


class _SingleMessageSendResult(Enum):

    OK = 0
    ERROR = 1
    BUSY = 2


class _MessageWithCallback(object):

    message = None
    on_message_send_complete = None
    context = None
    sender = None
    send_state = None
    timeout = None


class Sender(object):

    _link = None
    _on_state_changed = None
    _on_state_changed_context = None
    message_count = 0
    state = None
    tracing = False

    def __init__(self, link, on_state_changed, context=None, tracing=False):
        # type: (Link, Callable[], Any, bool) -> None
        self._link = link
        self._on_state_changed = on_state_changed
        self._on_state_changed_context = context
        self._pending_messages = []  # type: List[_MessageWithCallback]
        self.state = SenderState.IDLE
        self.tracing = tracing

    def _remove_pending_message(self, message):
        # type: (_MessageWithCallback) -> None
        self._pending_messages = [m for m in self._pending_messages if m != message]
        self.message_count -= 1

    def _on_delivery_settled(self, pending_send, delivery_no, reason, delivery_state):
        # type: (_MessageWithCallback, int, LinkDeliverySettleReason, Tuple(Any, Any)) -> None
        if pending_send.on_message_send_complete:
            if reason == LinkDeliverySettleReason.DispositionReceived:
                if delivery_state:
                    pending_send.on_message_send_complete(
                        pending_send.context,
                        MessageSendResult.OK if delivery_state[0] == 'ACCEPTED' else MessageSendResult.ERROR,
                        delivery_state[1]
                    )
                else:
                    LOGGER.error("Delivery state not provided.")
            elif reason == LinkDeliverySettleReason.Settled:
                pending_send.on_message_send_complete(
                    pending_send.context,
                    MessageSendResult.OK,
                    None
                )
            elif reason == LinkDeliverySettleReason.Timeout:
                pending_send.on_message_send_complete(
                    pending_send.context,
                    MessageSendResult.TIMEOUT,
                    None
                )
            else:
                pending_send.on_message_send_complete(
                    pending_send.context,
                    MessageSendResult.ERROR,
                    None
                )
        self._remove_pending_message(pending_send)

    def _encode_bytes(self):
        pass

    def _log_message_chunk(self, name, value):
        # type: (str, str) -> None
        """Log outgoing message segment at INFO level.

        This function will only log data if tracing is enabled for this sender.

        :param str name: The name of the message segment, e.g. 'Header', 'Properties', etc.
        :param str value: The data in the message segment.
        """
        if self.tracing:
            LOGGER.info('%s: %s', name, value)

    def _send_single_message(self, pending_send, message):
        # type: (_MessageWithCallback, BareMessage) -> None
        message_body_type = message.get_body_type()
        message_bytes = b""

        for message_section in message.SECTIONS:
            section_obj = getattr(message, message_section.name)
            if section_obj is not None:
                if not message_section.name.startwith('_'):
                    self._log_message_chunk(message_section.name, section_obj)
                    section_description = describe_performative(section_obj)
                    message_bytes = encode_value(message_bytes, section_description)
                else:
                    self._log_message_chunk('body', "<data>")
                    if message_body_type == MessageBodyType.DATA:
                        pass
                    elif message_body_type == MessageBodyType.VALUE:
                        pass
                    elif message_body_type == MessageBodyType.SEQUENCE:
                        raise NotImplementedError("Messages with a 'sequence' body type are not yet supported.")
                    else:
                        raise ValueError("Unsupported message body type: {}".format(message_body_type))


            
        



"""
static SEND_ONE_MESSAGE_RESULT send_one_message(MESSAGE_SENDER_INSTANCE* message_sender, ASYNC_OPERATION_HANDLE pending_send, MESSAGE_HANDLE message)
{
    SEND_ONE_MESSAGE_RESULT result;

    size_t encoded_size;
    size_t total_encoded_size = 0;
    MESSAGE_BODY_TYPE message_body_type;
    message_format message_format;

    if ((message_get_body_type(message, &message_body_type) != 0) ||
        (message_get_message_format(message, &message_format) != 0))
    {
        LogError("Failure getting message body type and/or message format");
        result = SEND_ONE_MESSAGE_ERROR;
    }
    else
    {
        // header
        HEADER_HANDLE header = NULL;
        AMQP_VALUE header_amqp_value = NULL;
        PROPERTIES_HANDLE properties = NULL;
        AMQP_VALUE properties_amqp_value = NULL;
        AMQP_VALUE application_properties = NULL;
        AMQP_VALUE application_properties_value = NULL;
        AMQP_VALUE body_amqp_value = NULL;
        size_t body_data_count = 0;
        AMQP_VALUE msg_annotations = NULL;
        bool is_error = false;



  

        if (is_error)
        {
            result = SEND_ONE_MESSAGE_ERROR;
        }
        else
        {
            result = SEND_ONE_MESSAGE_OK;

            // body - amqp data
            switch (message_body_type)
            {
            default:
                LogError("Unknown body type");
                result = SEND_ONE_MESSAGE_ERROR;
                break;

            case MESSAGE_BODY_TYPE_VALUE:
            {
                AMQP_VALUE message_body_amqp_value;
                if (message_get_body_amqp_value_in_place(message, &message_body_amqp_value) != 0)
                {
                    LogError("Cannot obtain AMQP value from body");
                    result = SEND_ONE_MESSAGE_ERROR;
                }
                else
                {
                    body_amqp_value = amqpvalue_create_amqp_value(message_body_amqp_value);
                    if (body_amqp_value == NULL)
                    {
                        LogError("Cannot create body AMQP value");
                        result = SEND_ONE_MESSAGE_ERROR;
                    }
                    else
                    {
                        if (amqpvalue_get_encoded_size(body_amqp_value, &encoded_size) != 0)
                        {
                            LogError("Cannot get body AMQP value encoded size");
                            result = SEND_ONE_MESSAGE_ERROR;
                        }
                        else
                        {
                            total_encoded_size += encoded_size;
                        }
                    }
                }

                break;
            }

            case MESSAGE_BODY_TYPE_DATA:
            {
                BINARY_DATA binary_data;
                size_t i;

                if (message_get_body_amqp_data_count(message, &body_data_count) != 0)
                {
                    LogError("Cannot get body AMQP data count");
                    result = SEND_ONE_MESSAGE_ERROR;
                }
                else
                {
                    if (body_data_count == 0)
                    {
                        LogError("Body data count is zero");
                        result = SEND_ONE_MESSAGE_ERROR;
                    }
                    else
                    {
                        for (i = 0; i < body_data_count; i++)
                        {
                            if (message_get_body_amqp_data_in_place(message, i, &binary_data) != 0)
                            {
                                LogError("Cannot get body AMQP data %u", (unsigned int)i);
                                result = SEND_ONE_MESSAGE_ERROR;
                            }
                            else
                            {
                                AMQP_VALUE body_amqp_data;
                                amqp_binary binary_value;
                                binary_value.bytes = binary_data.bytes;
                                binary_value.length = (uint32_t)binary_data.length;
                                body_amqp_data = amqpvalue_create_data(binary_value);
                                if (body_amqp_data == NULL)
                                {
                                    LogError("Cannot create body AMQP data");
                                    result = SEND_ONE_MESSAGE_ERROR;
                                }
                                else
                                {
                                    if (amqpvalue_get_encoded_size(body_amqp_data, &encoded_size) != 0)
                                    {
                                        LogError("Cannot get body AMQP data encoded size");
                                        result = SEND_ONE_MESSAGE_ERROR;
                                    }
                                    else
                                    {
                                        total_encoded_size += encoded_size;
                                    }

                                    amqpvalue_destroy(body_amqp_data);
                                }
                            }
                        }
                    }
                }
                break;
            }
            }

            if (result == 0)
            {
                void* data_bytes = malloc(total_encoded_size);
                PAYLOAD payload;
                payload.bytes = (const unsigned char*)data_bytes;
                payload.length = 0;
                result = SEND_ONE_MESSAGE_OK;

                if (header != NULL)
                {
                    if (amqpvalue_encode(header_amqp_value, encode_bytes, &payload) != 0)
                    {
                        LogError("Cannot encode header value");
                        result = SEND_ONE_MESSAGE_ERROR;
                    }

                    log_message_chunk(message_sender, "Header:", header_amqp_value);
                }

                if ((result == SEND_ONE_MESSAGE_OK) && (msg_annotations != NULL))
                {
                    if (amqpvalue_encode(msg_annotations, encode_bytes, &payload) != 0)
                    {
                        LogError("Cannot encode message annotations value");
                        result = SEND_ONE_MESSAGE_ERROR;
                    }

                    log_message_chunk(message_sender, "Message Annotations:", msg_annotations);
                }

                if ((result == SEND_ONE_MESSAGE_OK) && (properties != NULL))
                {
                    if (amqpvalue_encode(properties_amqp_value, encode_bytes, &payload) != 0)
                    {
                        LogError("Cannot encode message properties value");
                        result = SEND_ONE_MESSAGE_ERROR;
                    }

                    log_message_chunk(message_sender, "Properties:", properties_amqp_value);
                }

                if ((result == SEND_ONE_MESSAGE_OK) && (application_properties != NULL))
                {
                    if (amqpvalue_encode(application_properties_value, encode_bytes, &payload) != 0)
                    {
                        LogError("Cannot encode application properties value");
                        result = SEND_ONE_MESSAGE_ERROR;
                    }

                    log_message_chunk(message_sender, "Application properties:", application_properties_value);
                }

                if (result == SEND_ONE_MESSAGE_OK)
                {
                    switch (message_body_type)
                    {
                    default:
                        LogError("Unknown message type");
                        result = SEND_ONE_MESSAGE_ERROR;
                        break;

                    case MESSAGE_BODY_TYPE_VALUE:
                    {
                        if (amqpvalue_encode(body_amqp_value, encode_bytes, &payload) != 0)
                        {
                            LogError("Cannot encode body AMQP value");
                            result = SEND_ONE_MESSAGE_ERROR;
                        }

                        log_message_chunk(message_sender, "Body - amqp value:", body_amqp_value);
                        break;
                    }
                    case MESSAGE_BODY_TYPE_DATA:
                    {
                        BINARY_DATA binary_data;
                        size_t i;

                        for (i = 0; i < body_data_count; i++)
                        {
                            if (message_get_body_amqp_data_in_place(message, i, &binary_data) != 0)
                            {
                                LogError("Cannot get AMQP data %u", (unsigned int)i);
                                result = SEND_ONE_MESSAGE_ERROR;
                            }
                            else
                            {
                                AMQP_VALUE body_amqp_data;
                                amqp_binary binary_value;
                                binary_value.bytes = binary_data.bytes;
                                binary_value.length = (uint32_t)binary_data.length;
                                body_amqp_data = amqpvalue_create_data(binary_value);
                                if (body_amqp_data == NULL)
                                {
                                    LogError("Cannot create body AMQP data %u", (unsigned int)i);
                                    result = SEND_ONE_MESSAGE_ERROR;
                                }
                                else
                                {
                                    if (amqpvalue_encode(body_amqp_data, encode_bytes, &payload) != 0)
                                    {
                                        LogError("Cannot encode body AMQP data %u", (unsigned int)i);
                                        result = SEND_ONE_MESSAGE_ERROR;
                                        break;
                                    }

                                    amqpvalue_destroy(body_amqp_data);
                                }
                            }
                        }
                        break;
                    }
                    }
                }

                if (result == SEND_ONE_MESSAGE_OK)
                {
                    ASYNC_OPERATION_HANDLE transfer_async_operation;
                    LINK_TRANSFER_RESULT link_transfer_error;
                    MESSAGE_WITH_CALLBACK* message_with_callback = GET_ASYNC_OPERATION_CONTEXT(MESSAGE_WITH_CALLBACK, pending_send);
                    message_with_callback->message_send_state = MESSAGE_SEND_STATE_PENDING;

                    transfer_async_operation = link_transfer_async(message_sender->link, message_format, &payload, 1, on_delivery_settled, pending_send, &link_transfer_error, message_with_callback->timeout);
                    if (transfer_async_operation == NULL)
                    {
                        if (link_transfer_error == LINK_TRANSFER_BUSY)
                        {
                            message_with_callback->message_send_state = MESSAGE_SEND_STATE_NOT_SENT;
                            result = SEND_ONE_MESSAGE_BUSY;
                        }
                        else
                        {
                            LogError("Error in link transfer");
                            result = SEND_ONE_MESSAGE_ERROR;
                        }
                    }
                    else
                    {
                        result = SEND_ONE_MESSAGE_OK;
                    }
                }

                free(data_bytes);

                if (body_amqp_value != NULL)
                {
                    amqpvalue_destroy(body_amqp_value);
                }
            }
        }

        if (header != NULL)
        {
            header_destroy(header);
        }

        if (header_amqp_value != NULL)
        {
            amqpvalue_destroy(header_amqp_value);
        }

        if (msg_annotations != NULL)
        {
            annotations_destroy(msg_annotations);
        }

        if (application_properties != NULL)
        {
            amqpvalue_destroy(application_properties);
        }

        if (application_properties_value != NULL)
        {
            amqpvalue_destroy(application_properties_value);
        }

        if (properties_amqp_value != NULL)
        {
            amqpvalue_destroy(properties_amqp_value);
        }

        if (properties != NULL)
        {
            properties_destroy(properties);
        }
    }

    return result;
}
"""

            

