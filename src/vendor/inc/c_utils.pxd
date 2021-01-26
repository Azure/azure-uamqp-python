#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import sys
from libc cimport stdint

cimport c_strings


cdef extern from "Python.h":

    ctypedef int Py_intptr_t
    ctypedef size_t Py_ssize_t


cdef extern from "azure_c_shared_utility/sastoken.h":
    bint SASToken_Validate(c_strings.STRING_HANDLE sasToken)
    c_strings.STRING_HANDLE SASToken_Create(c_strings.STRING_HANDLE key, c_strings.STRING_HANDLE scope, c_strings.STRING_HANDLE keyName, size_t expiry)
    c_strings.STRING_HANDLE SASToken_CreateString(const char* key, const char* scope, const char* keyName, size_t expiry)


cdef extern from "azure_c_shared_utility/buffer_.h":

    ctypedef struct BUFFER_HANDLE:
        pass

    BUFFER_HANDLE BUFFER_create(const unsigned char* source, size_t size);
    void BUFFER_delete(BUFFER_HANDLE handle)


cdef extern from "azure_c_shared_utility/map.h":

    cdef enum MAP_RESULT_TAG:
        MAP_OK,
        MAP_ERROR,
        MAP_INVALIDARG,
        MAP_KEYEXISTS,
        MAP_KEYNOTFOUND,
        MAP_FILTER_REJECT

    ctypedef struct MAP_HANDLE:
        pass

    ctypedef int (*MAP_FILTER_CALLBACK)(const char* mapProperty, const char* mapValue)

    MAP_RESULT_TAG Map_GetInternals(MAP_HANDLE handle, const char*const** keys, const char*const** values, size_t* count)
    MAP_HANDLE Map_Create(MAP_FILTER_CALLBACK mapFilterFunc)
    MAP_RESULT_TAG Map_Add(MAP_HANDLE handle, const char* key, const char* value)
    MAP_RESULT_TAG Map_AddOrUpdate(MAP_HANDLE handle, const char* key, const char* value)
    void Map_Destroy(MAP_HANDLE handle)


cdef extern from "azure_c_shared_utility/urlencode.h":

    c_strings.STRING_HANDLE URL_EncodeString(const char* textEncode)
    c_strings.STRING_HANDLE URL_Encode(c_strings.STRING_HANDLE input)


cdef extern from "azure_c_shared_utility/azure_base64.h":

    c_strings.STRING_HANDLE Azure_Base64_Encode(BUFFER_HANDLE input)
    c_strings.STRING_HANDLE Azure_Base64_Encode_Bytes(const unsigned char* source, size_t size)
    BUFFER_HANDLE Base64_Decoder(const char* source)


cdef extern from "azure_c_shared_utility/tickcounter.h":

    ctypedef struct TICK_COUNTER_HANDLE:
        pass

    # TODO: This is only for windows
    ctypedef stdint.uint_fast64_t tickcounter_ms_t  # Use 64-bit because of QueryPerformanceCounter call
    void tickcounter_destroy(TICK_COUNTER_HANDLE tick_counter)
    TICK_COUNTER_HANDLE tickcounter_create()
    int tickcounter_get_current_ms(TICK_COUNTER_HANDLE tick_counter, tickcounter_ms_t* current_ms)


cdef extern from "azure_c_shared_utility/doublylinkedlist.h":

    ctypedef struct DLIST_ENTRY_TAG:
        DLIST_ENTRY_TAG *Flink
        DLIST_ENTRY_TAG *Blink

    ctypedef DLIST_ENTRY_TAG DLIST_ENTRY
    ctypedef DLIST_ENTRY_TAG *PDLIST_ENTRY

    void DList_InitializeListHead(PDLIST_ENTRY listHead)
    int DList_IsListEmpty(const PDLIST_ENTRY listHead)
    void DList_InsertTailList(PDLIST_ENTRY listHead, PDLIST_ENTRY listEntry)
    void DList_InsertHeadList(PDLIST_ENTRY listHead, PDLIST_ENTRY listEntry)
    void DList_AppendTailList(PDLIST_ENTRY listHead, PDLIST_ENTRY ListToAppend)
    int DList_RemoveEntryList(PDLIST_ENTRY listEntry)
    PDLIST_ENTRY DList_RemoveHeadList(PDLIST_ENTRY listHead)


cdef extern from "azure_c_shared_utility/optionhandler.h":

    cdef enum OPTIONHANDLER_RESULT_TAG:
        OPTIONHANDLER_OK,
        OPTIONHANDLER_ERROR,
        OPTIONHANDLER_INVALIDARG

    ctypedef struct OPTIONHANDLER_HANDLE:
        pass

    ctypedef void* (*pfCloneOption)(const char* name, const void* value)
    ctypedef void (*pfDestroyOption)(const char* name, const void* value)
    ctypedef int (*pfSetOption)(void* handle, const char* name, const void* value)

    OPTIONHANDLER_HANDLE OptionHandler_Create(pfCloneOption cloneOption, pfDestroyOption destroyOption, pfSetOption setOption)
    OPTIONHANDLER_HANDLE OptionHandler_Clone(OPTIONHANDLER_HANDLE handler)
    OPTIONHANDLER_RESULT_TAG OptionHandler_AddOption(OPTIONHANDLER_HANDLE handle, const char* name, const void* value)
    OPTIONHANDLER_RESULT_TAG OptionHandler_FeedOptions(OPTIONHANDLER_HANDLE handle, void* destinationHandle)
    void OptionHandler_Destroy(OPTIONHANDLER_HANDLE handle)
