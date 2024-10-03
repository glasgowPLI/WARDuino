#ifdef __CHERI_PURE_CAPABILITY__
__attribute__((import_module("env"), import_name("print_int"))) void print_int(int);
#endif

int __attribute__((noinline)) tak(int x, int y, int z) {
    if (!(y < x)) {
        return z;
    } else {
        return tak(tak(x - 1, y, z), tak(y - 1, z, x), tak(z - 1, x, y));
    }
}

int bench() { 

    #ifdef __CHERI_PURE_CAPABILITY__
    print_int(tak(18, 12, 6)); 
    #endif

    return tak(18, 12, 6); 
    }
