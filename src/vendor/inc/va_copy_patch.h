#include <stdarg.h>
// define va_copy for visual c++ 9.0
#ifndef va_copy
    #define va_copy(dest, src) (dest = src)
#endif