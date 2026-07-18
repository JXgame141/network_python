from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def heavy_compute(x: int) -> int:
    total = 0
    for n in range(2, x + 1):
        if is_prime(n):
            total += n
    return total


def compute_sequential(numbers: list[int]) -> list[int]:
    return [heavy_compute(number) for number in numbers]


def compute_parallel_pool(
    numbers: list[int], processes: int = 4
) -> list[int]:
    if not numbers:
        return []
    with Pool(processes=processes) as pool:
        return pool.map(heavy_compute, numbers)


def compute_with_threads(
    numbers: list[int], workers: int = 4
) -> list[int]:
    if not numbers:
        return []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(heavy_compute, numbers))
