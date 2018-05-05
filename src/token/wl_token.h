
#ifndef __WL_TOKEN_TOKEN__
#define __WL_TOKEN_TOKEN__

#include <stdlib.h>
#include <stdio.h>

typedef int64_t WLTokenId;

#define WLTokenId_UNKNOWN ((WLTokenId)-1L)

typedef struct _WLToken {
    WLTokenId id;
    char * name;
    
} WLToken;



#endif // end of __WL_TOKEN_TOKEN__
