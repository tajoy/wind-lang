#ifndef __WL_CORE_TYPES__
#define __WL_CORE_TYPES__

#include <stdlib.h>
#include <stdio.h>


typedef struct _WLTokenAnalyzer WLTokenAnalyzer;
typedef struct _WLSyntaxAnalyzer WLSyntaxAnalyzer;


typedef struct _WLCompilerContext {
    WLTokenAnalyzer* tokenAnalyzer;
    WLSyntaxAnalyzer* syntaxAnalyzer;
} WLCompilerContext;





#endif // end of __WL_CORE_TYPES__

