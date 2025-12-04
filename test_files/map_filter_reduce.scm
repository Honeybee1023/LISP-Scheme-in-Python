( begin 
  (define (map fn lst)
    (if (null? lst)
        ()
        (cons (fn (car lst)) (map fn (cdr lst)))))

  (define (filter fn lst)
    (if (null? lst)
        ()
        (if (fn (car lst))
            (cons (car lst) (filter fn (cdr lst)))
            (filter fn (cdr lst)))))

  (define (reduce fn lst val)
    (if (null? lst)
        val
        (reduce fn (cdr lst) (fn val (car lst)))))
)