#include "../WARDuino/internals.h"
#include "primitives.h"

// Basic function types

Type NoneToNoneU32 = {
    .form = FUNC,
    .params = {},
    .param_count = 0,
    .returns = {},
    .return_count = 0
};

Type NoneToOneU32 = {
    .form = FUNC,
    .params = {},
    .param_count = 0,
    .returns = { I32 },
    .return_count = 1
};

Type NoneToOneU64 = {
    .form = FUNC,
    .params = {},
    .param_count = 0,
    .returns = { I64 },
    .return_count = 1
};

Type oneToNoneU32 = {
    .form = FUNC,
    .params = { I32 },
    .param_count = 1,
    .returns = {},
    .return_count = 0
};

Type oneToOneU32 = {
    .form = FUNC,
    .params = { I32 },
    .param_count = 1,
    .returns = { I32 },
    .return_count = 1
};

Type oneToOneI32 = {
    .form = FUNC,
    .params = { I32 },
    .param_count = 1,
    .returns = { I32 },
    .return_count = 1
};

Type twoToNoneU32 = {
    .form = FUNC,
    .params = { I32, I32 },
    .param_count = 2,
    .returns = {},
    .return_count = 0
};

Type twoToOneU32 = {
    .form = FUNC,
    .params = { I32, I32 },
    .param_count = 2,
    .returns = { I32 },
    .return_count = 1
};

Type threeToNoneU32 = {
    .form = FUNC,
    .params = { I32, I32, I32 },
    .param_count = 3,
    .returns = {},
    .return_count = 0
};

Type fourToNoneU32 = {
    .form = FUNC,
    .params = { I32, I32, I32, I32 },
    .param_count = 4,
    .returns = {},
    .return_count = 0
};

Type fourToOneU32 = {
    .form = FUNC,
    .params = { I32, I32, I32, I32 },
    .param_count = 4,
    .returns = { I32 },
    .return_count = 1
};

Type tenToOneU32 = {
    .form = FUNC,
    .params = { I32, I32, I32, I32, I32, I32, I32, I32, I32, I32 },
    .param_count = 10,
    .returns = { I32 },
    .return_count = 1
};
