#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
from enum import Enum
import time
import logging

# C imports
from libc cimport stdint
from libc.stdlib cimport malloc, free
from libc.string cimport memset

cimport c_cbs
cimport c_utils
cimport c_strings
cimport c_session


_logger = logging.getLogger(__name__)


cpdef create_sas_token(const char* key, const char* scope, const char* keyname, size_t expiry):
    cdef c_strings.STRING_HANDLE str_value
    str_value = c_utils.SASToken_CreateString(key, scope, keyname, expiry)

    if <void*>str_value == NULL:
        raise ValueError("Failed to create SAS token.")
    if c_utils.SASToken_Validate(str_value) != True:
        raise ValueError("Generated invalid SAS token")
    cdef bytes py_str = c_strings.STRING_c_str(str_value)
    c_strings.STRING_delete(str_value)
    return py_str


cdef class CBSTokenAuth(object):

    cdef const char* audience
    cdef const char* token_type
    cdef const char* token
    cdef stdint.uint64_t expires_at
    cdef stdint.uint64_t _refresh_window
    cdef c_cbs.CBS_HANDLE _cbs_handle
    cdef c_cbs.AUTH_STATUS state
    cdef stdint.uint64_t auth_timeout
    cdef stdint.uint64_t _token_put_time
    cdef unsigned int token_status_code
    cdef const char* token_status_description
    cdef const char* connection_id
    cdef cSession _session

    def __cinit__(self, const char* audience, const char* token_type, const char* token, stdint.uint64_t expires_at, cSession session, stdint.uint64_t timeout, const char* connection_id, stdint.uint64_t refresh_window):
        self.state = AUTH_STATUS_IDLE
        self.audience = audience
        self.token_type = token_type
        self.token = token
        self.expires_at = expires_at
        self.auth_timeout = timeout
        self.connection_id = connection_id
        self._token_put_time = 0
        if refresh_window > 0:
            self._refresh_window = refresh_window
        else:
            current_time = int(time.time())
            remaining_time = expires_at - current_time
            self._refresh_window = int(float(remaining_time) * 0.1)
        self._cbs_handle = c_cbs.cbs_create(<c_session.SESSION_HANDLE>session._c_value)
        self._session = session
        if <void*>self._cbs_handle == NULL:
            raise MemoryError("Unable to create CBS Handle.")
        if c_cbs.cbs_open_async(self._cbs_handle, <c_cbs.ON_CBS_OPEN_COMPLETE>on_cbs_open_complete, <void*>self, <c_cbs.ON_CBS_ERROR>on_cbs_error, <void*>self) != 0:
            raise ValueError("Unable to open CBS link.")

    def __dealloc__(self):
        _logger.debug("Deallocating CBSTokenAuth")
        self.destroy()

    cpdef destroy(self):
        if <void*>self._cbs_handle is not NULL:
            _logger.debug("Destroying CBSTokenAuth for connection %r", self.connection_id)
            c_cbs.cbs_destroy(self._cbs_handle)
            self._cbs_handle = <c_cbs.CBS_HANDLE>NULL
            self._session = None

    cpdef close(self):
        if c_cbs.cbs_close(self._cbs_handle) != 0:
            self._value_error("Unable to close CBS link.")

    cpdef set_trace(self, bint trace_on):
        if c_cbs.cbs_set_trace(self._cbs_handle, trace_on) != 0:
            raise ValueError("Unable to set debug trace.")

    cpdef authenticate(self):
        if self.state == AUTH_STATUS_IN_PROGRESS:
            return
        current_time = int(time.time())
        if current_time >= self.expires_at:
            raise ValueError("Token has expired")
        self._token_put_time = current_time
        if <void*>c_cbs.cbs_put_token_async(
                self._cbs_handle,
                self.token_type,
                self.audience,
                self.token,
                <c_cbs.ON_CBS_OPERATION_COMPLETE>on_cbs_put_token_complete,
                <void*>self) == NULL:
            raise ValueError("Put-Token request failed.")
        else:
            self.state = AUTH_STATUS_IN_PROGRESS

    cpdef get_status(self):
        self._update_status()
        return self.state

    cpdef get_failure_info(self):
        return self.token_status_code, self.token_status_description

    cpdef refresh(self, const char* refresh_token, stdint.uint64_t expires_at):
        self._update_status()
        if self.state == AUTH_STATUS_REFRESH_REQUIRED:
            self.token = refresh_token
            self.authenticate()
            self.expires_at = expires_at

    cpdef _update_status(self):
        error_code = 0
        is_refresh_required = False
        if self.state == AUTH_STATUS_OK or self.state == AUTH_STATUS_REFRESH_REQUIRED:
            is_expired, is_refresh_required = self._check_expiration_and_refresh_status()
            if is_expired:
                self.state = AUTH_STATUS_EXPIRED
            elif is_refresh_required:
                self.state = AUTH_STATUS_REFRESH_REQUIRED
        elif self.state == AUTH_STATUS_IN_PROGRESS:
            put_timeout = self._check_put_timeout_status()
            if put_timeout:
                self.state = AUTH_STATUS_TIMEOUT

    cpdef _check_put_timeout_status(self):
        seconds_since_epoc = int(time.time())
        if self.auth_timeout > 0:
            return (seconds_since_epoc - self._token_put_time) >= self.auth_timeout
        else:
            return False

    cpdef _check_expiration_and_refresh_status(self):
        seconds_since_epoc = int(time.time())
        is_expired = seconds_since_epoc >= self.expires_at
        is_refresh_required = (self.expires_at - seconds_since_epoc) <= self._refresh_window
        return is_expired, is_refresh_required

    cpdef _cbs_open_complete(self, result):
        self.on_cbs_open_complete(result)

    cpdef on_cbs_open_complete(self, result):
        _logger.info("CBS for connection %r completed opening with status: %r", self.connection_id, result)
        if result == c_cbs.CBS_OPEN_COMPLETE_RESULT_TAG.CBS_OPEN_ERROR:
            self.state = AUTH_STATUS_FAILURE

    cpdef _cbs_error(self):
        self.on_cbs_error()

    cpdef on_cbs_error(self):
        _logger.info("CBS error occurred on connection %r.", self.connection_id)

    cpdef _cbs_put_token_compelete(self, c_cbs.CBS_OPERATION_RESULT_TAG result, unsigned int status_code, const char* status_description):
        if result == CBS_OPERATION_RESULT_OK:
            self.state = AUTH_STATUS_OK
        else:
            self.state = AUTH_STATUS_ERROR
        self.token_status_code = status_code
        self.token_status_description = status_description
        self.on_cbs_put_token_complete(result, status_code, status_description)

    cpdef on_cbs_put_token_complete(self, c_cbs.CBS_OPERATION_RESULT_TAG result, unsigned int status_code, const char* status_description):
        _logger.info("Token put complete with result: %r, status: %r, description: %r, connection: %r", result, status_code, status_description, self.connection_id)


#### Callbacks

cdef void on_cbs_open_complete(void *context, c_cbs.CBS_OPEN_COMPLETE_RESULT_TAG open_complete_result):
    if <void*>context != NULL:
        context_pyobj = <PyObject*>context
        if context_pyobj.ob_refcnt == 0: # context is being garbage collected, skip the callback
            _logger.warning("Can't call on_cbs_open_complete during garbage collection.")
            return
        context_obj = <object>context
        context_obj._cbs_open_complete(open_complete_result)


cdef void on_cbs_error(void* context):
    if <void*>context != NULL:
        context_pyobj = <PyObject*>context
        if context_pyobj.ob_refcnt == 0: # context is being garbage collected, skip the callback
            _logger.warning("Can't call on_cbs_error during garbage collection.")
            return
        context_obj = <object>context
        context_obj._cbs_error()


cdef void on_cbs_put_token_complete(void* context, c_cbs.CBS_OPERATION_RESULT_TAG complete_result, unsigned int status_code, const char* status_description):
    cdef unsigned int verified_status_code
    cdef const char* verified_description
    if <void*>context != NULL:
        context_pyobj = <PyObject*>context
        if context_pyobj.ob_refcnt == 0: # context is being garbage collected, skip the callback
            _logger.warning("Can't call on_cbs_put_token_complete during garbage collection.")
            return
        context_obj = <object>context
        try:
            if <void*>status_code != NULL:
                verified_status_code = status_code
            else:
                verified_status_code = 0
            if <void*>status_description != NULL:
                verified_description = status_description
            else:
                verified_description = b"CBS Session closed."
            context_obj._cbs_put_token_compelete(complete_result, verified_status_code, verified_description)
        except KeyboardInterrupt:
            context_obj._cbs_put_token_compelete(
                CBS_OPERATION_RESULT_INSTANCE_CLOSED, 1, b"Client shutdown with keyboard interrupt.")
