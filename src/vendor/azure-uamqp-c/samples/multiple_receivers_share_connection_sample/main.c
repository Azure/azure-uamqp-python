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

/* This sample connects to an Event Hub, authenticates using SASL MSSBCBS (SAS token given by a put-token) and sends 1 message to the EH specifying a publisher ID */
/* The SAS token is generated based on the policy name/key */
/* Replace the below settings with your own.*/

#define EH_HOST ""
#define EH_KEY_NAME ""
#define EH_KEY ""
#define EH_NAME ""

static const size_t msg_count = 1;
static unsigned int sent_messages = 0;
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

static int rec[8] = { 0, 0, 0, 0, 0, 0, 0, 0 };
static AMQP_VALUE on_message_received0(const void* context, MESSAGE_HANDLE message)
{
	(void)context;
	(void)message;
	rec[0]++;
	(void)printf("Message received from 0, total received: %d.\r\n", rec[0]);
	return messaging_delivery_accepted();
}
static AMQP_VALUE on_message_received1(const void* context, MESSAGE_HANDLE message)
{
	(void)context;
	(void)message;
	rec[1]++;
	(void)printf("Message received from 1, total received: %d.\r\n", rec[1]);
	return messaging_delivery_accepted();
}
static AMQP_VALUE on_message_received2(const void* context, MESSAGE_HANDLE message)
{
	(void)context;
	(void)message;
	rec[2]++;
	(void)printf("Message received from 2, total received: %d.\r\n", rec[2]);
	return messaging_delivery_accepted();
}
static AMQP_VALUE on_message_received3(const void* context, MESSAGE_HANDLE message)
{
	(void)context;
	(void)message;
	rec[3]++;
	(void)printf("Message received from 3, total received: %d.\r\n", rec[3]);
	return messaging_delivery_accepted();
}
static AMQP_VALUE on_message_received4(const void* context, MESSAGE_HANDLE message)
{
	(void)context;
	(void)message;
	rec[4]++;
	(void)printf("Message received from 4, total received: %d.\r\n", rec[4]);
	return messaging_delivery_accepted();
}
static AMQP_VALUE on_message_received5(const void* context, MESSAGE_HANDLE message)
{
	(void)context;
	(void)message;
	rec[5]++;
	(void)printf("Message received from 5, total received: %d.\r\n", rec[5]);
	return messaging_delivery_accepted();
}
static AMQP_VALUE on_message_received6(const void* context, MESSAGE_HANDLE message)
{
	(void)context;
	(void)message;
	rec[6]++;
	(void)printf("Message received from 6, total received: %d.\r\n", rec[6]);
	return messaging_delivery_accepted();
}
static AMQP_VALUE on_message_received7(const void* context, MESSAGE_HANDLE message)
{
	(void)context;
	(void)message;
	rec[7]++;
	(void)printf("Message received from 7, total received: %d.\r\n", rec[7]);
	return messaging_delivery_accepted();
}

typedef AMQP_VALUE(*MyFuncType)(const void*, MESSAGE_HANDLE);
MyFuncType receive_funcs[8] = { &on_message_received0, on_message_received1, on_message_received2, on_message_received3,
on_message_received4, on_message_received5, on_message_received6, on_message_received7 };

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

static void on_cbs_for_partition_put_token_complete(void* context, CBS_OPERATION_RESULT cbs_operation_result, unsigned int status_code, const char* status_description)
{
	(void)context;
	(void)status_code;
	(void)status_description;

	if (cbs_operation_result == CBS_OPERATION_RESULT_OK)
	{
		auth_for_each_partition = true;
		printf("token for patition:%d is put\n", *(int*)(context));
	}
}

static bool on_new_session_endpoint(void* context, ENDPOINT_HANDLE new_endpoint)
{
	(void*)context;
	(void*)new_endpoint;
	printf("in the on_new_session_endpoint callback\n");
	return true;
}

SESSION_HANDLE create_session(CONNECTION_HANDLE connection) {
	SESSION_HANDLE session = session_create(connection, NULL, NULL);
	session_set_incoming_window(session, 655565);
	session_set_outgoing_window(session, 65536);
	return session;
}

MESSAGE_RECEIVER_HANDLE create_receiver(SESSION_HANDLE session, int partition_id, int max_link_credit) {
	(void*)max_link_credit;
	char partition_str[3];
	sprintf(partition_str, "%d", partition_id);

	STRING_HANDLE source_str = STRING_construct("amqps://" EH_HOST "/" EH_NAME "/ConsumerGroups/$Default/Partitions/");
	//STRING_HANDLE source_str = STRING_construct(EH_NAME "/ConsumerGroups/$default/Partitions/");
	STRING_concat(source_str, partition_str);

	STRING_HANDLE target_str = STRING_construct("test_receiver_share_connection-");
	STRING_concat(target_str, partition_str);

	STRING_HANDLE link_name = STRING_construct("receiver-link-share-connection-");
	STRING_concat(link_name, partition_str);

	AMQP_VALUE source = messaging_create_source(STRING_c_str(source_str));
	AMQP_VALUE target = messaging_create_target(STRING_c_str(target_str));
	LINK_HANDLE link = link_create(session, STRING_c_str(link_name), role_receiver, source, target);
	link_set_rcv_settle_mode(link, receiver_settle_mode_first);

	//(void)link_set_max_link_credit(link, max_link_credit);

	//(void)link_set_max_message_size(link, 65536);

	MESSAGE_RECEIVER_HANDLE message_receiver = messagereceiver_create(link, NULL, NULL);
	return message_receiver;
}

int main(int argc, char** argv)
{
    int result;

    (void)argc;
    (void)argv;

    if (platform_init() != 0)
    {
        result = -1;
    }
    else
    {
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
        connection = connection_create(sasl_io, EH_HOST, "aname", on_new_session_endpoint, NULL);
		connection_set_trace(connection, true);
        session = session_create(connection, NULL, NULL);
        session_set_incoming_window(session, 655565);
        session_set_outgoing_window(session, 65536);
		//printf("cbs session state: %s\n", get_session_state(session));

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
		//printf("cbs session state: %s\n", get_session_state(session));

		int max_link_credit = 300;
		int partition_cnt = 3;

		//for(int i = 0; i < partition_cnt; i++) {
		//	char partition_str[3];
		//	sprintf(partition_str, "%d", i);

		//	auth_for_each_partition = false;
		//	sas_key_name = STRING_construct(EH_KEY_NAME);
		//	buffer = BUFFER_create((unsigned char*)EH_KEY, strlen(EH_KEY));
		//	sas_key_value = Base64_Encoder(buffer);
		//	BUFFER_delete(buffer);
		//	resource_uri = STRING_construct("sb://" EH_HOST "/" EH_NAME "/ConsumerGroups/$Default/Partitions/");
		//	STRING_concat(resource_uri, partition_str);
		//	encoded_resource_uri = URL_EncodeString(STRING_c_str(resource_uri));

		//	sas_token = SASToken_Create(sas_key_value, encoded_resource_uri, sas_key_name, expiry_time);
		//	int* p_id = malloc(sizeof(int));
		//	*p_id = i;
		//	(void)cbs_put_token_async(cbs, "servicebus.windows.net:sastoken", STRING_c_str(resource_uri), STRING_c_str(sas_token), on_cbs_for_partition_put_token_complete, p_id);
		//	while (!auth_for_each_partition)
		//	{
		//		connection_dowork(connection);
		//	}
		//	printf("auth for partition:%d is done.\n", i);
		//}

		MESSAGE_RECEIVER_HANDLE* receiver_handlers = malloc(sizeof(MESSAGE_RECEIVER_HANDLE) * partition_cnt);
		SESSION_HANDLE* session_handlers = malloc(sizeof(SESSION_HANDLE) * partition_cnt);
		for (int i = 0; i < partition_cnt; i++) {
			session_handlers[i] = create_session(connection);
			receiver_handlers[i] = create_receiver(session_handlers[i], i, max_link_credit);

			int open_status = -1;
			open_status = messagereceiver_open(receiver_handlers[i], receive_funcs[i], receiver_handlers[i]);

			if (receiver_handlers[i] == NULL || open_status != 0) {
				(void)printf("Cannot open the message receiver: %d.", i);
				return -1;
			}
		}

		bool keep_running = true;
		while (keep_running)
		{
			connection_dowork(connection);
			for (int i = 0; i < partition_cnt; i++) {
				printf("| partition: %d, cnt: %d |", i, rec[i]);
			}
		    printf("\n");
		}

        result = 0;
    }

    return result;
}