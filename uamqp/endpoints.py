#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# The messaging layer deﬁnes two concrete types (source and target) to be used as the source and target of a
# link. These types are supplied in the source and target ﬁelds of the attach frame when establishing or
# resuming link. The source is comprised of an address (which the container of the outgoing Link Endpoint will
# resolve to a Node within that container) coupled with properties which determine:
# 
#   - which messages from the sending Node will be sent on the Link
#   - how sending the message affects the state of that message at the sending Node
#   - the behavior of Messages which have been transferred on the Link, but have not yet reached a
#     terminal state at the receiver, when the source is destroyed.

from enum import Enum

from .types import AMQPTypes, FieldDefinition
from .constants import FIELD


class TerminusDurability(Enum):
    #: No Terminus state is retained durably
    none = 0
    #: Only the existence and conﬁguration of the Terminus is retained durably.
    configuration = 1
    #: In addition to the existence and conﬁguration of the Terminus, the unsettled state for durable
    #: messages is retained durably.
    unsettled_state = 2


class ExpiryPolicy(Enum):
    #: The expiry timer starts when Terminus is detached.
    link_detach = "link-detach"
    #: The expiry timer starts when the most recently associated session is ended.
    session_end = "session-end"
    #: The expiry timer starts when most recently associated connection is closed.
    connection_close = "connection-close"
    #: The Terminus never expires.
    never = "never"


class Source(object):
    """For containers which do not implement address resolution (and do not admit spontaneous link attachment
    from their partners) but are instead only used as producers of messages, it is unnecessary to provide
    spurious detail on the source. For this purpose it is possible to use a "minimal" source in which all the
    ﬁelds are left unset.

    :param str address: The address of the source.
        The address of the source MUST NOT be set when sent on a attach frame sent by the receiving Link Endpoint
        where the dynamic ﬂag is set to true (that is where the receiver is requesting the sender to create an
        addressable node). The address of the source MUST be set when sent on a attach frame sent by the sending
        Link Endpoint where the dynamic ﬂag is set to true (that is where the sender has created an addressable
        node at the request of the receiver and is now communicating the address of that created node).
        The generated name of the address SHOULD include the link name and the container-id of the remote container
        to allow for ease of identiﬁcation.
    :param ~uamqp.endpoints.TerminusDurability durable: Indicates the durability of the terminus.
        Indicates what state of the terminus will be retained durably: the state of durable messages, only
        existence and conﬁguration of the terminus, or no state at all.
    :param ~uamqp.endpoints.ExpiryPolicy expiry_policy: The expiry policy of the Source.
        Determines when the expiry timer of a Terminus starts counting down from the timeout value. If the link
        is subsequently re-attached before the Terminus is expired, then the count down is aborted. If the
        conditions for the terminus-expiry-policy are subsequently re-met, the expiry timer restarts from its
        originally conﬁgured timeout value.
    :param int timeout: Duration that an expiring Source will be retained in seconds.
        The Source starts expiring as indicated by the expiry-policy.
    :param bool dynamic: Request dynamic creation of a remote Node.
        When set to true by the receiving Link endpoint, this ﬁeld constitutes a request for the sending peer
        to dynamically create a Node at the source. In this case the address ﬁeld MUST NOT be set. When set to
        true by the sending Link Endpoint this ﬁeld indicates creation of a dynamically created Node. In this case
        the address ﬁeld will contain the address of the created Node. The generated address SHOULD include the
        Link name and Session-name or client-id in some recognizable form for ease of traceability.
    :param dict dynamic_node_properties: Properties of the dynamically created Node.
        If the dynamic ﬁeld is not set to true this ﬁeld must be left unset. When set by the receiving Link
        endpoint, this ﬁeld contains the desired properties of the Node the receiver wishes to be created. When
        set by the sending Link endpoint this ﬁeld contains the actual properties of the dynamically created node.
    :param bytes distribution_mode: The distribution mode of the Link.
        This ﬁeld MUST be set by the sending end of the Link if the endpoint supports more than one
        distribution-mode. This ﬁeld MAY be set by the receiving end of the Link to indicate a preference when a
        Node supports multiple distribution modes.
    :param dict filter: A set of predicates to ﬁlter the Messages admitted onto the Link.
        The receiving endpoint sets its desired ﬁlter, the sending endpoint sets the ﬁlter actually in place
        (including any ﬁlters defaulted at the node). The receiving endpoint MUST check that the ﬁlter in place
        meets its needs and take responsibility for detaching if it does not.
    :param ~uamqp.outcomes.DeliveryState default_outcome: Default outcome for unsettled transfers.
        Indicates the outcome to be used for transfers that have not reached a terminal state at the receiver
        when the transfer is settled, including when the Source is destroyed. The value MUST be a valid
        outcome (e.g. Released or Rejected).
    :param list(bytes) outcomes: Descriptors for the outcomes that can be chosen on this link.
        The values in this ﬁeld are the symbolic descriptors of the outcomes that can be chosen on this link.
        This ﬁeld MAY be empty, indicating that the default-outcome will be assumed for all message transfers
        (if the default-outcome is not set, and no outcomes are provided, then the accepted outcome must be
        supported by the source). When present, the values MUST be a symbolic descriptor of a valid outcome,
        e.g. "amqp:accepted:list".
    :param list(bytes) capabilities: The extension capabilities the sender supports/desires.
        See http://www.amqp.org/specification/1.0/source-capabilities.
    """
    NAME = "SOURCE"
    CODE = 0x00000028
    DEFINITION = (
        FIELD("address", AMQPTypes.string, False, None, False),
        FIELD("durable", FieldDefinition.terminus_durability, False, "none", False),
        FIELD("expiry_policy", FieldDefinition.expiry_policy, False, "session-end", False),
        FIELD("timeout", FieldDefinition.seconds, False, 0, False),
        FIELD("dynamic", AMQPTypes.boolean, False, False, False),
        FIELD("dynamic_node_properties", FieldDefinition.node_properties, False, None, False),
        FIELD("distribution_mode", AMQPTypes.symbol, False, None, False),
        FIELD("filter", FieldDefinition.filter_set, False, None, False),
        FIELD("default_outcome", FieldDefinition.outcome, False, None, False),
        FIELD("outcomes", AMQPTypes.symbol, False, None, True),
        FIELD("capabilities", AMQPTypes.symbol, False, None, True),
    )