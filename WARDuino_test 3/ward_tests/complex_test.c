void _start() {
    int array[5][5];
    int i, j;
    
    // 正常访问
    for (i = 0; i < 5; i++) {
        for (j = 0; j < 5; j++) {
            array[i][j] = i * j;
        }
    }
    
    // 越界访问
    array[5][0] = 99;  // 第一维越界
    array[0][5] = 88;  // 第二维越界
}
