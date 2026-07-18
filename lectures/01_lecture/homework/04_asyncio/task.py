"""
Домашнее задание 4: Asyncio 🔄
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress


async def fetch_one_async(url: str) -> str:
    """Асинхронно «скачать» URL."""
    await asyncio.sleep(0.05)
    return f"data:{url}"


async def fetch_all_async(urls: list[str]) -> list[str]:
    """Скачать все URL конкурентно, сохранив исходный порядок."""
    return list(await asyncio.gather(*(fetch_one_async(url) for url in urls)))


async def fetch_with_delay(name: str, delay: float, fail: bool = False) -> str:
    """Имитация асинхронной загрузки. НЕ МЕНЯТЬ."""
    await asyncio.sleep(delay)
    if fail:
        raise ValueError(f"Ошибка загрузки {name}")
    return f"data:{name}"


async def run_task_group(names: list[str]) -> dict[str, str | None]:
    """Запустить загрузки через TaskGroup и обработать ExceptionGroup."""
    if not names:
        return {}

    tasks: dict[str, asyncio.Task[str]] = {}

    try:
        async with asyncio.TaskGroup() as group:
            for name in names:
                tasks[name] = group.create_task(
                    fetch_with_delay(
                        name,
                        delay=0.1,
                        fail=("bad" in name),
                    )
                )
    except* ValueError:
        # TaskGroup объединяет ошибки дочерних задач в ExceptionGroup.
        pass

    results: dict[str, str | None] = {}
    successful = False

    for name, task in tasks.items():
        if task.cancelled():
            results[name] = None
        elif task.exception() is not None:
            results[name] = None
        else:
            results[name] = task.result()
            successful = True

    return results if successful else {}



async def fetch_with_timeout(url: str, delay: float, timeout: float) -> str:
    """Выполнить асинхронную загрузку с ограничением времени."""
    return await asyncio.wait_for(
        fetch_with_delay(url, delay=delay),
        timeout=timeout,
    )


async def cancellable_worker(name: str, steps: int) -> str:
    """Выполнить работу по шагам с корректной обработкой отмены."""
    try:
        for step in range(1, steps + 1):
            await asyncio.sleep(0.1)
            print(f"  {name}: шаг {step}/{steps}")
    except asyncio.CancelledError:
        print(f"  {name}: очищаю ресурсы...")
        raise

    return f"{name}: готов после {steps} шагов"


async def run_with_cancel(name: str, steps: int, cancel_after: float) -> str | None:
    """Вернуть результат, если задача успела, иначе отменить её."""
    task = asyncio.create_task(cancellable_worker(name, steps))
    timer = asyncio.create_task(asyncio.sleep(cancel_after))

    done, _ = await asyncio.wait(
        {task, timer},
        return_when=asyncio.FIRST_COMPLETED,
    )

    if task in done:
        timer.cancel()
        with suppress(asyncio.CancelledError):
            await timer
        return await task

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        return None
    finally:
        if not timer.done():
            timer.cancel()
            with suppress(asyncio.CancelledError):
                await timer

    return None


async def fast_or_slow(name: str, delay: float) -> str:
    """Имитация быстрой или медленной загрузки. НЕ МЕНЯТЬ."""
    await asyncio.sleep(delay)
    return f"{name}: готов за {delay}с"


async def fetch_as_completed(tasks: list[tuple[str, float]]) -> list[str]:
    """Вернуть результаты в порядке завершения корутин."""
    coroutines = [fast_or_slow(name, delay) for name, delay in tasks]
    results: list[str] = []

    for completed in asyncio.as_completed(coroutines):
        results.append(await completed)

    return results


def blocking_compute(x: int) -> int:
    """CPU-bound функция: проверка на простоту. НЕ МЕНЯТЬ."""
    import math
    import time

    time.sleep(0.01)
    for i in range(2, int(math.sqrt(x)) + 1):
        if x % i == 0:
            return 0
    return x


async def async_process_numbers(numbers: list[int], max_workers: int = 4) -> list[int]:
    """Выполнить blocking_compute в ограниченном пуле потоков."""
    if not numbers:
        return []

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            loop.run_in_executor(executor, blocking_compute, number)
            for number in numbers
        ]
        return list(await asyncio.gather(*futures))
