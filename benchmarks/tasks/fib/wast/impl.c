__attribute__((import_module("env"), import_name("print_int"))) void print_int(int);

long __attribute__((noinline)) fib(int n) {
    unsigned long first = 0, second = 1, next = 0;
    for (unsigned c = 0; c < n; c++) {
        if (c <= 1) {
            next = c;
        } else {
            next = (first + second) % 100000000;
            first = second;
            second = next;
        }
    }
    return next;
}

int bench() {
    int sum = 0;
#pragma clang loop unroll(disable)
    for (int i = 1000; i < 1050; i++) {
        sum += fib(i);
        sum %= 97;
    }
    print_int(sum);
    return sum;
    // .       ..122583354898000
}
