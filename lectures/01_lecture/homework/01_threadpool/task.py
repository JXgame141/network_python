from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable


def fetch_one(url: str) -> str:
    import time

    time.sleep(0.05)
    return f"data:{url}"


def fetch_one_with_delay(url_delay: tuple[str, float]) -> str:
    url, delay = url_delay
    import time

    time.sleep(delay)
    return f"data:{url}"


def fetch_all(urls: list[str], max_workers: int = 4) -> list[str]:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(fetch_one, urls))


def fetch_all_with_errors(
    urls: list[str], max_workers: int = 4
) -> list[str | None]:
    def fetch(url: str) -> str | None:
        try:
            if "bad" in url:
                raise ConnectionError(f"Failed to fetch {url}")
            return fetch_one(url)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(fetch, urls))


def fetch_all_with_progress(
    urls: list[str],
    max_workers: int = 4,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[str]:
    results = []
    total = len(urls)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_one, url) for url in urls]
        for completed, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if progress_callback is not None:
                progress_callback(completed, total)

    return results
