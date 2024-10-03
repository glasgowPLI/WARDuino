#ifdef __CHERI_PURE_CAPABILITY__
__attribute__((import_module("env"), import_name("print_int"))) void print_int(int);
#endif

int __attribute__((noinline)) is_prime(unsigned n) {
    if (n < 3) {
        return n > 1;
    } else {
        if ((n % 2 == 0) || (n % 3 == 0)) {
            return 0;
        } else {
            unsigned i = 5;
            while (i * i <= n) {
                if ((n % i == 0) || (n % (i + 2) == 0)) {
                    return 0;
                }
                i += 6;
            }
            return 1;
        }
    }
}

/*
 *
 * function is_prime(n)
    if n ≤ 3
       return n > 1
    else if n mod 2 = 0 or n mod 3 = 0
       return false
    let i ← 5
    while i * i ≤ n
       if n mod i = 0 or n mod (i + 2) = 0
           return false
       i ← i + 6
    return true
 * */
int bench() {
    unsigned sum = 0;
    int count = 0;
    for (unsigned i = 1; sum < 13374242; i++) {
        if (is_prime(i)) {
            sum += i;
            count++;
        }
    }

    #ifdef __CHERI_PURE_CAPABILITY__
    print_int(count);
    #endif    

    return count;
}
