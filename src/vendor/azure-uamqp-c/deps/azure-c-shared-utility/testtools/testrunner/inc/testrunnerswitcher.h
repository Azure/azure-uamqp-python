// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#ifndef TESTRUNNERSWITCHER_H
#define TESTRUNNERSWITCHER_H

#include "macro_utils.h"

#ifdef __cplusplus
#include <cstring>
#else
#include <stdbool.h>
#include <string.h>
#endif

#ifdef MBED_BUILD_TIMESTAMP
#define USE_CTEST
#endif

typedef void* TEST_MUTEX_HANDLE;

#define TEST_DEFINE_ENUM_TYPE(type, ...) TEST_ENUM_TYPE_HANDLER(type, FOR_EACH_1(DEFINE_ENUMERATION_CONSTANT_AS_WIDESTRING, __VA_ARGS__));

#ifdef USE_CTEST

#include "ctest.h"

#define BEGIN_TEST_SUITE(name)          CTEST_BEGIN_TEST_SUITE(name)
#define END_TEST_SUITE(name)            CTEST_END_TEST_SUITE(name)

#define TEST_SUITE_INITIALIZE(name)     CTEST_SUITE_INITIALIZE()
#define TEST_SUITE_CLEANUP(name)        CTEST_SUITE_CLEANUP()
#define TEST_FUNCTION_INITIALIZE(name)  CTEST_FUNCTION_INITIALIZE()
#define TEST_FUNCTION_CLEANUP(name)     CTEST_FUNCTION_CLEANUP()

#define TEST_FUNCTION(name)             CTEST_FUNCTION(name)

#define ASSERT_ARE_EQUAL                CTEST_ASSERT_ARE_EQUAL
#define ASSERT_ARE_EQUAL_WITH_MSG       CTEST_ASSERT_ARE_EQUAL_WITH_MSG
#define ASSERT_ARE_NOT_EQUAL            CTEST_ASSERT_ARE_NOT_EQUAL
#define ASSERT_ARE_NOT_EQUAL_WITH_MSG   CTEST_ASSERT_ARE_NOT_EQUAL_WITH_MSG
#define ASSERT_FAIL                     CTEST_ASSERT_FAIL
#define ASSERT_IS_NULL                  CTEST_ASSERT_IS_NULL
#define ASSERT_IS_NULL_WITH_MSG         CTEST_ASSERT_IS_NULL_WITH_MSG
#define ASSERT_IS_NOT_NULL              CTEST_ASSERT_IS_NOT_NULL
#define ASSERT_IS_NOT_NULL_WITH_MSG     CTEST_ASSERT_IS_NOT_NULL_WITH_MSG
#define ASSERT_IS_TRUE                  CTEST_ASSERT_IS_TRUE
#define ASSERT_IS_TRUE_WITH_MSG         CTEST_ASSERT_IS_TRUE_WITH_MSG
#define ASSERT_IS_FALSE                 CTEST_ASSERT_IS_FALSE
#define ASSERT_IS_FALSE_WITH_MSG        CTEST_ASSERT_IS_FALSE_WITH_MSG

#define RUN_TEST_SUITE(...)             CTEST_RUN_TEST_SUITE(__VA_ARGS__)

#define TEST_MUTEX_CREATE()             (TEST_MUTEX_HANDLE)1
// the strlen check is simply to shut the compiler up and not create a hell of #pragma warning suppress
#define TEST_MUTEX_ACQUIRE(mutex)       (strlen("a") == 0)
#define TEST_MUTEX_RELEASE(mutex)
#define TEST_MUTEX_DESTROY(mutex)

#define TEST_INITIALIZE_MEMORY_DEBUG(semaphore)     (void)(semaphore)
#define TEST_DEINITIALIZE_MEMORY_DEBUG(semaphore)   (void)(semaphore)

#define TEST_ENUM_TYPE_HANDLER(EnumName, ...) \
const wchar_t *EnumName##_Strings[]= \
{ \
__VA_ARGS__ \
}; \
static void EnumName##_ToString(char* dest, size_t bufferSize, EnumName enumValue) \
{ \
    (void)snprintf(dest, bufferSize, "%S", EnumName##_Strings[enumValue]); \
} \
static bool EnumName##_Compare(EnumName left, EnumName right) \
{ \
    return left != right; \
}

#define TEST_USE_CTEST_FUNCTIONS_FOR_TYPE(my_type)

#elif defined CPP_UNITTEST

#ifdef _MSC_VER
#pragma warning(disable:4505)
#endif

#include "CppUnitTest.h"
#include "testmutex.h"

using namespace Microsoft::VisualStudio::CppUnitTestFramework;

typedef const char* char_ptr;
typedef void* void_ptr;

#ifdef CPPUNITTEST_SYMBOL
extern "C" void CPPUNITTEST_SYMBOL(void) {}
#endif

#define BEGIN_TEST_SUITE(name)          TEST_CLASS(name) {

#define END_TEST_SUITE(name)            };

#define TEST_SUITE_INITIALIZE(name)     TEST_CLASS_INITIALIZE(name)
#define TEST_SUITE_CLEANUP(name)        TEST_CLASS_CLEANUP(name)
#define TEST_FUNCTION_INITIALIZE(name)  TEST_METHOD_INITIALIZE(name)
#define TEST_FUNCTION_CLEANUP(name)     TEST_METHOD_CLEANUP(name)

#define TEST_FUNCTION(name)             TEST_METHOD(name)

#define ASSERT_ARE_EQUAL(type, A, B)                        Assert::AreEqual((type)(A), (type)(B))
#define ASSERT_ARE_EQUAL_WITH_MSG(type, A, B, message)      Assert::AreEqual((type)(A), (type)(B), ToString(message).c_str())
#define ASSERT_ARE_NOT_EQUAL(type, A, B)                    Assert::AreNotEqual((type)(A), (type)(B))
#define ASSERT_ARE_NOT_EQUAL_WITH_MSG(type, A, B, message)  Assert::AreNotEqual((type)(A), (type)(B), ToString(message).c_str())
#define ASSERT_FAIL(message)                                Assert::Fail(ToString(message).c_str())
#define ASSERT_IS_TRUE(expression)                          Assert::IsTrue(expression)
#define ASSERT_IS_TRUE_WITH_MSG(expression, message)        Assert::IsTrue(expression, ToString(message).c_str())
#define ASSERT_IS_FALSE(expression)                         Assert::IsFalse(expression)
#define ASSERT_IS_FALSE_WITH_MSG(expression, message)       Assert::IsFalse(expression, ToString(message).c_str())
#define ASSERT_IS_NOT_NULL(value)                           Assert::IsNotNull(value)
#define ASSERT_IS_NOT_NULL_WITH_MSG(value, message)         Assert::IsNotNull(value, ToString(message).c_str())
#define ASSERT_IS_NULL(value)                               Assert::IsNull(value)
#define ASSERT_IS_NULL_WITH_MSG(value, message)             Assert::IsNull(value, ToString(message).c_str())

#define RUN_TEST_SUITE(...)

#define TEST_MUTEX_CREATE()                                 testmutex_create()
#define TEST_MUTEX_ACQUIRE(mutex)                           testmutex_acquire(mutex)
#define TEST_MUTEX_RELEASE(mutex)                           testmutex_release(mutex)
#define TEST_MUTEX_DESTROY(mutex)                           testmutex_destroy(mutex)

#define TEST_INITIALIZE_MEMORY_DEBUG(semaphore) \
    semaphore = testmutex_acquire_global_semaphore(); \
    ASSERT_IS_NOT_NULL_WITH_MSG(semaphore, "Unable to acquire global semaphore");

#define TEST_DEINITIALIZE_MEMORY_DEBUG(semaphore) \
(void)testmutex_release_global_semaphore(semaphore);\

#define TEST_ENUM_TYPE_HANDLER(EnumName, ...) \
namespace Microsoft \
{ \
    namespace VisualStudio \
    { \
        namespace CppUnitTestFramework \
        { \
            static const wchar_t *EnumName##_Strings[]= \
            { \
                __VA_ARGS__ \
            }; \
            template <> std::wstring ToString < EnumName > (const EnumName & q)  \
            {  \
                if((size_t)q>=sizeof(EnumName##_Strings)/sizeof(EnumName##_Strings[0])) \
                { \
                    return(L"out of range value for " L#EnumName); \
                } \
                else \
                { \
                    return EnumName##_Strings[q]; \
                } \
            } \
        } \
    } \
};

#define TEST_USE_CTEST_FUNCTIONS_FOR_TYPE(my_type) \
namespace Microsoft \
{ \
    namespace VisualStudio \
    { \
        namespace CppUnitTestFramework \
        { \
            template<> \
            inline std::wstring ToString<my_type>(const my_type& value) \
            { \
                char temp_str[1024]; \
                std::wstring result; \
                if (C2(my_type,_ToString)(temp_str, sizeof(temp_str), value) != 0) \
                { \
                    return L""; \
                } \
                else \
                { \
                    int size_needed_in_chars = MultiByteToWideChar(CP_UTF8, 0, &temp_str[0], -1, NULL, 0); \
                    if (size_needed_in_chars == 0) \
                    { \
                        result = L""; \
                    } \
                    else \
                    { \
                        WCHAR* widechar_string = (WCHAR*)malloc(size_needed_in_chars * sizeof(WCHAR)); \
                        if (widechar_string == NULL) \
                        { \
                            result = L""; \
                        } \
                        else \
                        { \
                            if (MultiByteToWideChar(CP_UTF8, 0, temp_str, -1, widechar_string, size_needed_in_chars) == 0) \
                            { \
                                result = L""; \
                            } \
                            else \
                            { \
                                result = std::wstring(widechar_string); \
                            } \
                            free(widechar_string); \
                        } \
                    } \
                } \
                return result; \
            } \
            template<> \
            static void Assert::AreEqual<my_type>(const my_type& expected, const my_type& actual, const wchar_t* message, const __LineInfo* pLineInfo) \
            { \
                FailOnCondition((C2(my_type,_Compare)(expected, actual) == 0), EQUALS_MESSAGE(expected, actual, message), pLineInfo); \
            } \
        } \
    } \
} \

/*because for some reason this is not defined by Visual Studio, it is defined here, so it is not multiplied in every single other unittest*/
namespace Microsoft
{
    namespace VisualStudio
    {
        namespace CppUnitTestFramework
        {
            template<> inline std::wstring ToString<int64_t>(const int64_t& t)
            {
                RETURN_WIDE_STRING(t);
            }
            template<> inline std::wstring ToString<uint16_t>(const uint16_t& t)
            {
                RETURN_WIDE_STRING(t);
            }
        }
    }
}

#else
#error No test runner defined
#endif

#endif
