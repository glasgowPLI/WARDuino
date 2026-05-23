
void simple_test() {
    volatile int x = 42;
}

void _start() {
    simple_test();
}
