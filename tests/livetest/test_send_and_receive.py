#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import time
import pytest

from uamqp.message import Message, BatchMessage, Header, Properties
from uamqp.utils import add_batch

@pytest.mark.liveTest
def test_send_to_and_receive_from_partition_single_message(live_eventhub_send_client, live_eventhub_receive_client):

    live_eventhub_send_client.send_message(Message(data=[b'E2E Single Message Test']))

    messages = live_eventhub_receive_client.receive_message_batch(max_batch_size=1)
    assert messages[0]['data'] == [b'E2E Single Message Test']
