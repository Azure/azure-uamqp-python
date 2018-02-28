#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from uamqp import utils


class MessageResponse(Exception):
    pass


class RejectMessage(MessageResponse):

    def __init__(self, message):
        self.rejection_description = message.encode('utf-8')
        super(RejectMessage, self).__init__(message)


class AbandonMessage(MessageResponse):

    def __init__(self, annotations=None):
        self.abandoned = True
        self.annotations = utils.data_factory(annotations) if annotations else None
        super(AbandonMessage, self).__init__("Releasing message")


class DeferMessage(MessageResponse):

    def __init__(self, annotations=None):
        self.deferred = True
        self.annotations = utils.data_factory(annotations) if annotations else None
        super(DeferMessage, self).__init__("Deferring message")