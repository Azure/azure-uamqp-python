// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#ifndef TEST_DEPENDENCY_H
#define TEST_DEPENDENCY_H

#include "umock_c_prod.h"

#ifdef __cplusplus
extern "C" {
#endif

    MOCKABLE_FUNCTION(, int, the_mocked_one);
    MOCKABLE_FUNCTION(, int, do_not_actually_mock);

#ifdef __cplusplus
}
#endif

#endif /* TEST_DEPENDENCY_H */
