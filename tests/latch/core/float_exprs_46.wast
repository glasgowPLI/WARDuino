(module
  (func (export "f32.no_fold_lt_if_to_abs") (param $x f32) (result f32)
    (if (result f32) (f32.lt (local.get $x) (f32.const 0.0))
      (then (f32.neg (local.get $x))) (else (local.get $x))
    )
  )
  (func (export "f32.no_fold_le_if_to_abs") (param $x f32) (result f32)
    (if (result f32) (f32.le (local.get $x) (f32.const -0.0))
      (then (f32.neg (local.get $x))) (else (local.get $x))
    )
  )
  (func (export "f32.no_fold_gt_if_to_abs") (param $x f32) (result f32)
    (if (result f32) (f32.gt (local.get $x) (f32.const -0.0))
      (then (local.get $x)) (else (f32.neg (local.get $x)))
    )
  )
  (func (export "f32.no_fold_ge_if_to_abs") (param $x f32) (result f32)
    (if (result f32) (f32.ge (local.get $x) (f32.const 0.0))
      (then (local.get $x)) (else (f32.neg (local.get $x)))
    )
  )

  (func (export "f64.no_fold_lt_if_to_abs") (param $x f64) (result f64)
    (if (result f64) (f64.lt (local.get $x) (f64.const 0.0))
      (then (f64.neg (local.get $x))) (else (local.get $x))
    )
  )
  (func (export "f64.no_fold_le_if_to_abs") (param $x f64) (result f64)
    (if (result f64) (f64.le (local.get $x) (f64.const -0.0))
      (then (f64.neg (local.get $x))) (else (local.get $x))
    )
  )
  (func (export "f64.no_fold_gt_if_to_abs") (param $x f64) (result f64)
    (if (result f64) (f64.gt (local.get $x) (f64.const -0.0))
      (then (local.get $x)) (else (f64.neg (local.get $x)))
    )
  )
  (func (export "f64.no_fold_ge_if_to_abs") (param $x f64) (result f64)
    (if (result f64) (f64.ge (local.get $x) (f64.const 0.0))
      (then (local.get $x)) (else (f64.neg (local.get $x)))
    )
  )
)

