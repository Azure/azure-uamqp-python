#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------


cdef extern from "azure_c_shared_utility/strings_types.h":

    ctypedef struct STRING_HANDLE:
        pass


cdef extern from "azure_c_shared_utility/strings.h":

    STRING_HANDLE STRING_new()
    STRING_HANDLE STRING_clone(STRING_HANDLE handle)
    STRING_HANDLE STRING_construct(const char* psz)
    STRING_HANDLE STRING_construct_n(const char* psz, size_t n)
    STRING_HANDLE STRING_new_with_memory(const char* memory)
    STRING_HANDLE STRING_new_quoted(const char* source)
    STRING_HANDLE STRING_new_JSON(const char* source)
    STRING_HANDLE STRING_from_byte_array(const unsigned char* source, size_t size)
    void STRING_delete(STRING_HANDLE handle)
    int STRING_concat(STRING_HANDLE handle, const char* s2)
    int STRING_concat_with_STRING(STRING_HANDLE s1, STRING_HANDLE s2)
    int STRING_quote(STRING_HANDLE handle)
    int STRING_copy(STRING_HANDLE s1, const char* s2)
    int STRING_copy_n(STRING_HANDLE s1, const char* s2, size_t n)
    const char* STRING_c_str(STRING_HANDLE handle)
    int STRING_empty(STRING_HANDLE handle)
    size_t STRING_length(STRING_HANDLE handle)
    int STRING_compare(STRING_HANDLE s1, STRING_HANDLE s2)
    int STRING_replace(STRING_HANDLE handle, char target, char replace)
