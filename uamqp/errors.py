#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from uamqp import utils


class AMQPConnectionError(Exception):
    pass


class ConnectionClose(AMQPConnectionError):

    def __init__(self, condition, description=None, info=None, encoding="UTF-8"):
        self._encoding = encoding
        self.condition = condition
        self.description = description
        self.info = info
        message = self.condition.decode(self._encoding)
        if self.description:
            message += ": {}".format(self.description.decode(self._encoding))
        super(ConnectionClose, self).__init__(message)


class LinkDetach(AMQPConnectionError):

    def __init__(self, condition, description=None, info=None, encoding="UTF-8"):
        self._encoding = encoding
        self.condition = condition
        self.description = description
        self.info = info
        message = self.condition.decode(self._encoding)
        if self.description:
            message += ": {}".format(self.description.decode(self._encoding))
        super(LinkDetach, self).__init__(message)


class LinkRedirect(LinkDetach):

    def __init__(self, condition, description=None, info=None, encoding="UTF-8"):
        self.hostname = info.get(b'hostname')
        self.network_host = info.get(b'network-host')
        self.port = info.get(b'port')
        self.address = info.get(b'address')
        self.scheme = info.get(b'scheme')
        self.path = info.get(b'path')
        super(LinkRedirect, self).__init__(condition, description, info, encoding)


class MessageException(Exception):
    pass


class MessageSendFailed(MessageException):
    pass


class AuthenticationException(Exception):
    pass


class TokenExpired(AuthenticationException):
    pass


class TokenAuthFailure(AuthenticationException):

    def __init__(self, status_code, description):
        self.status_code = status_code
        self.description = str(description)
        message = ("CBS Token authentication failed."
                   "\nStatus code: {}"
                   "\nDescription: {}").format(self.status_code, self.description)
        super(TokenAuthFailure, self).__init__(message)


class MessageResponse(Exception):

    def __init__(self, message=None):
        response = message or "Sending {} disposition.".format(self.__class__.__name__)
        super(MessageResponse, self).__init__(response)


class MessageAlreadySettled(MessageResponse):

    def __init__(self):
        response = "Invalid operation: this message is already settled."
        super(MessageAlreadySettled, self).__init__(response)


class MessageAccepted(MessageResponse):
    pass


class MessageRejected(MessageResponse):

    def __init__(self, condition=None, description=None, encoding='UTF-8'):
        if condition:
            self.error_condition = condition.encode(encoding) if isinstance(condition, str) else condition
        else:
            self.error_condition = b"amqp:internal-error"
        self.error_description = None
        if description:
            self.error_description = description.encode(encoding) if isinstance(description, str) else description
        else:
            self.error_description = b""
        super(MessageRejected, self).__init__()


class MessageReleased(MessageResponse):
    pass


class MessageModified(MessageResponse):

    def __init__(self, failed, undeliverable, annotations=None, encoding='UTF-8'):
        self.failed = failed
        self.undeliverable = undeliverable
        if annotations and not isinstance(annotations, dict):
            raise TypeError("Disposition annotations must be a dictionary.")
        self.annotations = utils.data_factory(annotations, encoding=encoding) if annotations else None
        super(MessageModified, self).__init__()


class ErrorResponse:

    def __init__(self, error_info):
        self._error = error_info

    @property
    def condition(self):
        return self._error.condition

    @property
    def description(self):
        return self._error.description

    @property
    def information(self):
        info = self._error.info
        if info:
            return info.value
        return None
