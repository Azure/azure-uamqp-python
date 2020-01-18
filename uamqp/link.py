

from enum import Enum


class LinkDeliverySettleReason(Enum):

    DispositionReceived = 0
    Settled = 1
    NotDelivered = 2
    Timeout = 3
    Cancelled = 4
