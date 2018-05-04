#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from uamqp import utils


class AMQPConnectionError(Exception):
    pass


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
    pass


class RejectMessage(MessageResponse):

    def __init__(self, message, encoding='UTF-8'):
        self.rejection_description = message.encode(encoding) if isinstance(message, str) else message
        super(RejectMessage, self).__init__(message)


class AbandonMessage(MessageResponse):

    def __init__(self, annotations=None, encoding='UTF-8'):
        self.abandoned = True
        self.annotations = utils.data_factory(annotations, encoding=encoding) if annotations else None
        super(AbandonMessage, self).__init__("Releasing message")


class DeferMessage(MessageResponse):

    def __init__(self, annotations=None, encoding='UTF-8'):
        self.deferred = True
        self.annotations = utils.data_factory(annotations, encoding=encoding) if annotations else None
        super(DeferMessage, self).__init__("Deferring message")
