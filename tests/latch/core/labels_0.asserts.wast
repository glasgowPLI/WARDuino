       (assert_return (invoke "block") (i32.const 1))
       (assert_return (invoke "loop1") (i32.const 5))
       (assert_return (invoke "loop2") (i32.const 8))
       (assert_return (invoke "loop3") (i32.const 1))
       (assert_return (invoke "loop4" (i32.const 8)) (i32.const 16))
       (assert_return (invoke "loop5") (i32.const 2))
       (assert_return (invoke "loop6") (i32.const 3))
       (assert_return (invoke "if") (i32.const 5))
       (assert_return (invoke "if2") (i32.const 5))
       (assert_return (invoke "switch" (i32.const 0)) (i32.const 50))
       (assert_return (invoke "switch" (i32.const 1)) (i32.const 20))
       (assert_return (invoke "switch" (i32.const 2)) (i32.const 20))
       (assert_return (invoke "switch" (i32.const 3)) (i32.const 3))
       (assert_return (invoke "switch" (i32.const 4)) (i32.const 50))
       (assert_return (invoke "switch" (i32.const 5)) (i32.const 50))
       (assert_return (invoke "return" (i32.const 0)) (i32.const 0))
       (assert_return (invoke "return" (i32.const 1)) (i32.const 2))
       (assert_return (invoke "return" (i32.const 2)) (i32.const 2))
       (assert_return (invoke "br_if0") (i32.const 0x1d))
       (assert_return (invoke "br_if1") (i32.const 1))
       (assert_return (invoke "br_if2") (i32.const 1))
       (assert_return (invoke "br_if3") (i32.const 2))
       (assert_return (invoke "br") (i32.const 1))
       (assert_return (invoke "shadowing") (i32.const 1))
       (assert_return (invoke "redefinition") (i32.const 5))
