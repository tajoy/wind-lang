
#ifndef __WL_TOKEN_TOKENIZER__
#define __WL_TOKEN_TOKENIZER__



#include <stdlib.h>
#include <stdio.h>

typedef struct _WLTokenizer WLTokenizer;

typedef void (*WLTokenizerProcessFunc)(WLTokenizer* tokenizer);


struct _WLTokenizer {
    int _;
};







#endif // end of __WL_TOKEN_TOKENIZER__


