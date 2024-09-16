#ifdef __CHERI_PURE_CAPABILITY__
__attribute__((import_module("env"), import_name("print_int"))) void print_int(int);
#elif __linux__
#include <stdio.h>
#endif

typedef unsigned long ull;

ull binomial(ull m, ull n) {
    ull r = 1, d = m - n;
    if (d > n) {
        n = d;
        d = m - n;
    }

    while (m > n) {
        r *= m--;
        while (d > 1 && !(r % d)) r /= d--;
    }

    return r;
}

ull __attribute__((noinline)) catalan(int n) {
    return binomial(2 * n, n) / (1 + n);
}

int bench() {
    // printf("%lu!!",catalan(17) );
    int sum = 0;

#pragma clang loop unroll(disable)
    for (int i = 0; i < 10000; ++i) {
        sum += catalan((i + sum) % 18) % 100;
    }

    #ifdef __CHERI_PURE_CAPABILITY__
    print_int(sum % 256);
    #elif __linux__
    printf(sum % 256);
    #endif
    
    return sum % 256;  // 113
}