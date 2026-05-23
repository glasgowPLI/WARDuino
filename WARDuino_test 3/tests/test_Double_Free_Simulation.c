// 双重释放模拟测试
static int resource_acquired = 0;

void test_Double_Free_Simulation() {{
    // "分配"资源
    if (!resource_acquired) {{
        resource_acquired = 1;
    }}
    
    // "释放"资源
    resource_acquired = 0;
    
    // 再次"释放" - 模拟双重释放
    resource_acquired = 0; // 重复操作，可能造成状态不一致
}}

void _start() {{
    test_Double_Free_Simulation();
}}
