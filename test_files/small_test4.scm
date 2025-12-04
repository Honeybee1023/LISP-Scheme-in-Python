(begin
  (define (foo x) (if (>= x 0) x (- 0 x)))
  (filter (lambda (x) (> (foo x) 20)) (list -100 -40 -19 -5 0 5 19 40 100))
)
