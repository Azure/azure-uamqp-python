#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

try:
    from urllib import urlparse
except Exception:
    from urllib.parse import urlparse
import logging

from uamqp import constants
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class Address:

    def __init__(self, address):
        self.parsed_address = self._validate_address(address)
        self._c_address = c_uamqp.string_value(
            address.encode('utf-8') if isinstance(address, str) else address)

    @property
    def address(self):
        return self._address.address.decode('utf-8')

    @property
    def durable(self):
        return self._address.durable

    @durable.setter
    def durable(self, value):
        self._address.durable = value

    @property
    def expiry_policy(self):
        return self._address.expiry_policy

    @expiry_policy.setter
    def expiry_policy(self, value):
        self._address.expiry_policy = value

    @property
    def timeout(self):
        return self._address.timeout

    @timeout.setter
    def timeout(self, value):
        self._address.timeout = value

    @property
    def dynamic(self):
        return self._address.dynamic

    @dynamic.setter
    def dynamic(self, value):
        self._address.dynamic = value

    @property
    def distribution_mode(self):
        return self._address.distribution_mode.decode('utf-8')

    @distribution_mode.setter
    def distribution_mode(self, value):
        mode = value.encode('utf-8') if isinstance(value, str) else value
        self._address.distribution_mode = mode

    def _validate_address(self, address):
        parsed = urlparse(address)
        if not parsed.scheme.startswith('amqp'):
            raise ValueError("Source scheme must be amqp or amqps.")
        if not parsed.netloc or not parsed.path:
            raise ValueError("Invalid {} address: {}".format(
                self.__class__.__name__, parsed))
        return parsed


class Source(Address):

    def __init__(self, address):
        super(Source, self).__init__(address)
        self._filters = []
        self._address = c_uamqp.create_source()
        self._address.address = self._c_address

    def set_filter(self, filter):
        value = filter.encode('utf-8') if isinstance(filter, str) else filter
        filter_set = c_uamqp.dict_value()
        filter_key = c_uamqp.symbol_value(constants.STRING_FILTER)
        descriptor = c_uamqp.symbol_value(constants.STRING_FILTER)
        filter_value = c_uamqp.string_value(value)
        described_filter_value = c_uamqp.described_value(descriptor, filter_value)
        self._filters.append((descriptor, filter_value))
        filter_set[filter_key] = described_filter_value
        self._address.filter_set = filter_set


class Target(Address):

    def __init__(self, address):
        super(Target, self).__init__(address)
        self._address = c_uamqp.create_target()
        self._address.address = self._c_address
