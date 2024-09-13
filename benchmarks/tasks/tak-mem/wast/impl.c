__attribute__((import_module("env"), import_name("print_int"))) void print_int(int);

int tak(int x, int y, int z) {
    if (!(y < x)) {
        return z;
    } else {
        return tak(tak(x - 1, y, z), tak(y - 1, z, x), tak(z - 1, x, y));
    }
}

int bench() { print_int(tak(18, 12, 6)); return tak(18, 12, 6); }
