def fib(n):
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError("n must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
