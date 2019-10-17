// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <time.h>
#include <string.h>
#include "azure_uamqp_c/session.h"

#include "azure_c_shared_utility/gballoc.h"
#include "azure_c_shared_utility/platform.h"
#include "azure_c_shared_utility/strings.h"
#include "azure_c_shared_utility/buffer_.h"
#include "azure_c_shared_utility/base64.h"
#include "azure_c_shared_utility/urlencode.h"
#include "azure_c_shared_utility/sastoken.h"
#include "azure_c_shared_utility/tlsio.h"
#include "azure_c_shared_utility/tickcounter.h"
#include "azure_uamqp_c/uamqp.h"

#if _WIN32
#include "windows.h"
#endif

/* This sample connects to an Event Hub, authenticates using SASL MSSBCBS (SAS token given by a put-token) and receives messages from two receivers.
   It demonstrates how to create multiple sessions on a single connection. Eech receiver(link) depends on its own session. */
/* The SAS token is generated based on the policy name/key */
/* Replace the below settings with your own.*/

#define EH_HOST "<<<Replace with your own EH host (like myeventhub.servicebus.windows.net)>>>"
#define EH_KEY_NAME "<<<Replace with your own key name>>>"
#define EH_KEY "<<<Replace with your own key>>>"
#define EH_NAME "<<<Replace with your own EH name (like ingress_eh)>>>"

static bool auth = false;
static bool auth_for_each_partition = false;

static void on_cbs_open_complete(void* context, CBS_OPEN_COMPLETE_RESULT open_complete_result)
{
    (void)context;
    (void)open_complete_result;
    (void)printf("CBS instance open.\r\n");
}

static void on_cbs_error(void* context)
{
    (void)context;
    (void)printf("CBS error.\r\n");
}

static AMQP_VALUE on_message_received(const void* context, MESSAGE_HANDLE message)
{
    int partition_id = *(int*)context;
    (void)message;

    (void)printf("Message received from partition: %d.\r\n", partition_id);

    return NULL;
}

static void on_cbs_put_token_complete(void* context, CBS_OPERATION_RESULT cbs_operation_result, unsigned int status_code, const char* status_description)
{
    (void)context;
    (void)status_code;
    (void)status_description;

    if (cbs_operation_result == CBS_OPERATION_RESULT_OK)
    {
        auth = true;
        printf("cbs token is put\n");
    }
}

SESSION_HANDLE create_session(CONNECTION_HANDLE connection) {
    SESSION_HANDLE session = session_create(connection, NULL, NULL);
    session_set_incoming_window(session, 655565);
    session_set_outgoing_window(session, 65536);
    return session;
}

MESSAGE_RECEIVER_HANDLE create_receiver(SESSION_HANDLE session, int partition_id, int max_link_credit, LINK_HANDLE** created_link) {
    (void*)max_link_credit;
    char partition_str[3];
    sprintf(partition_str, "%d", partition_id);

    STRING_HANDLE source_str = STRING_construct("amqps://" EH_HOST "/" EH_NAME "/ConsumerGroups/$Default/Partitions/");
    STRING_concat(source_str, partition_str);

    STRING_HANDLE target_str = STRING_construct("target-receiver-share-connection-");
    STRING_concat(target_str, partition_str);

    STRING_HANDLE link_name = STRING_construct("link-share-connection-");
    STRING_concat(link_name, partition_str);

    AMQP_VALUE source = messaging_create_source(STRING_c_str(source_str));
    AMQP_VALUE target = messaging_create_target(STRING_c_str(target_str));
    LINK_HANDLE link = link_create(session, STRING_c_str(link_name), role_receiver, source, target);
    link_set_rcv_settle_mode(link, receiver_settle_mode_first);

    MESSAGE_RECEIVER_HANDLE message_receiver = messagereceiver_create(link, NULL, NULL);
    (*created_link) = &link;

    STRING_delete(source_str);
    STRING_delete(target_str);
    STRING_delete(link_name);
    amqpvalue_destroy(source);
    amqpvalue_destroy(target);

    return message_receiver;
}

int main(int argc, char** argv)
{
    int result = 0;

    (void)argc;
    (void)argv;

    if (platform_init() != 0)
        return -1;

    XIO_HANDLE sasl_io;
    CONNECTION_HANDLE connection;
    SESSION_HANDLE session;

    /* create SASL PLAIN handler */
    SASL_MECHANISM_HANDLE sasl_mechanism_handle = saslmechanism_create(saslmssbcbs_get_interface(), NULL);
    XIO_HANDLE tls_io;
    STRING_HANDLE sas_key_name;
    STRING_HANDLE sas_key_value;
    STRING_HANDLE resource_uri;
    STRING_HANDLE encoded_resource_uri;
    STRING_HANDLE sas_token;
    BUFFER_HANDLE buffer;
    TLSIO_CONFIG tls_io_config = { EH_HOST, 5671 };
    const IO_INTERFACE_DESCRIPTION* tlsio_interface;
    SASLCLIENTIO_CONFIG sasl_io_config;
    time_t currentTime;
    size_t expiry_time;
    CBS_HANDLE cbs;

    gballoc_init();

    /* create the TLS IO */
    tlsio_interface = platform_get_default_tlsio();
    tls_io = xio_create(tlsio_interface, &tls_io_config);

    /* create the SASL client IO using the TLS IO */
    sasl_io_config.underlying_io = tls_io;
    sasl_io_config.sasl_mechanism = sasl_mechanism_handle;
    sasl_io = xio_create(saslclientio_get_interface_description(), &sasl_io_config);

    /* create the connection, session and link */
    connection = connection_create(sasl_io, EH_HOST, "aname", NULL, NULL);
    connection_set_trace(connection, true);
    session = session_create(connection, NULL, NULL);
    session_set_incoming_window(session, 655565);
    session_set_outgoing_window(session, 65536);

    /* Construct a SAS token */
    sas_key_name = STRING_construct(EH_KEY_NAME);

    /* unfortunately SASToken wants an encoded key - this should be fixed at a later time */
    buffer = BUFFER_create((unsigned char*)EH_KEY, strlen(EH_KEY));
    sas_key_value = Base64_Encoder(buffer);
    BUFFER_delete(buffer);
    resource_uri = STRING_construct("sb://" EH_HOST "/" EH_NAME);
    encoded_resource_uri = URL_EncodeString(STRING_c_str(resource_uri));

    /* Make a token that expires in one hour */
    currentTime = time(NULL);
    expiry_time = (size_t)(difftime(currentTime, 0) + 3600);
    sas_token = SASToken_Create(sas_key_value, encoded_resource_uri, sas_key_name, expiry_time);

    cbs = cbs_create(session);
    cbs_set_trace(cbs, true);
    if (cbs_open_async(cbs, on_cbs_open_complete, cbs, on_cbs_error, cbs) == 0)
    {
        (void)cbs_put_token_async(cbs, "servicebus.windows.net:sastoken", "sb://" EH_HOST "/" EH_NAME, STRING_c_str(sas_token), on_cbs_put_token_complete, cbs);

        while (!auth)
        {
            connection_dowork(connection);
        }
    }

    STRING_delete(sas_token);
    STRING_delete(sas_key_name);
    STRING_delete(sas_key_value);
    STRING_delete(resource_uri);
    STRING_delete(encoded_resource_uri);

    int max_link_credit = 300;
    int partition_cnt = 2;

    MESSAGE_RECEIVER_HANDLE* receiver_handlers = malloc(sizeof(MESSAGE_RECEIVER_HANDLE) * partition_cnt);
    SESSION_HANDLE* session_handlers = malloc(sizeof(SESSION_HANDLE) * partition_cnt);
    LINK_HANDLE* link_handlers = malloc(sizeof(LINK_HANDLE) * partition_cnt);

    int* running_context = malloc(sizeof(int) * partition_cnt);

    for (int i = 0; i < partition_cnt; i++) {
        /* create a new session */
        session_handlers[i] = create_session(connection);
        LINK_HANDLE* created_link = NULL;
        /* create a receiver depending on the new session */
        receiver_handlers[i] = create_receiver(session_handlers[i], i, max_link_credit, &created_link);
        /* record the underlying link, used for future deallocation */
        link_handlers[i] = *created_link;

        int open_status = -1;

        running_context[i] = i; /* in this simple example, context for the receiver callback is partition id information */
        open_status = messagereceiver_open(receiver_handlers[i], on_message_received, &running_context[i]);

        if (receiver_handlers[i] == NULL || open_status != 0) {
            (void)printf("Cannot open the message receiver: %d.", i);
            result = -1;
        }
    }

    if (result != -1) {
        bool keep_running = true;

        time_t start_time;
        time_t end_time;
        time(&start_time);

        while (keep_running)
        {
            connection_dowork(connection);
            time(&end_time);
            if ((int)(end_time - start_time) >= 3)
            {
                keep_running = false;
            }
        }
    }

    free(running_context);
    cbs_destroy(cbs);

    for (int i = 0; i < partition_cnt; i++) {
        messagereceiver_destroy(receiver_handlers[i]);
        link_destroy(link_handlers[i]);
        session_destroy(session_handlers[i]);
    }

    connection_destroy(connection);
    xio_destroy(sasl_io);
    xio_destroy(tls_io);
    saslmechanism_destroy(sasl_mechanism_handle);
    platform_deinit();

    result = 0;

    return result;
}