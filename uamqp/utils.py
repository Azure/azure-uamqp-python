#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import six
import datetime
from base64 import b64encode
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlencode, quote_plus
import time

from ._encode import encode_payload


class UTC(datetime.tzinfo):
    """Time Zone info for handling UTC"""

    def utcoffset(self, dt):
        """UTF offset for UTC is 0."""
        return datetime.timedelta(0)

    def tzname(self, dt):
        """Timestamp representation."""
        return "Z"

    def dst(self, dt):
        """No daylight saving for UTC."""
        return datetime.timedelta(hours=1)


try:
    from datetime import timezone  # pylint: disable=ungrouped-imports

    TZ_UTC = timezone.utc  # type: ignore
except ImportError:
    TZ_UTC = UTC()  # type: ignore


def utc_from_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, tz=TZ_UTC)


def utc_now():
    return datetime.datetime.now(tz=TZ_UTC)


def encode(value, encoding='UTF-8'):
    return value.encode(encoding) if isinstance(value, six.text_type) else value


def generate_sas_token(audience, policy, key, expiry=None):
    """
    Generate a sas token according to the given audience, policy, key and expiry

    :param str audience:
    :param str policy:
    :param str key:
    :param int expiry: abs expiry time
    :rtype: str
    """
    if not expiry:
        expiry = int(time.time()) + 3600  # Default to 1 hour.

    encoded_uri = quote_plus(audience)
    encoded_policy = quote_plus(policy).encode("utf-8")
    encoded_key = key.encode("utf-8")

    ttl = int(expiry)
    sign_key = '%s\n%d' % (encoded_uri, ttl)
    signature = b64encode(HMAC(encoded_key, sign_key.encode('utf-8'), sha256).digest())
    result = {
        'sr': audience,
        'sig': signature,
        'se': str(ttl)}
    if policy:
        result['skn'] = encoded_policy
    return 'SharedAccessSignature ' + urlencode(result)


def add_batch(batch, message):
    # Add a message to a batch
    output = bytearray()
    encode_payload(output, message)
    batch.data.append(output)


def get_message_encoded_size(message):
    output = bytearray()
    encode_payload(output, message)
    return len(output)
