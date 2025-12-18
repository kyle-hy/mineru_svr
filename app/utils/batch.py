import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, TypeVar
from collections.abc import Awaitable

T = TypeVar("T")  # 入参
U = TypeVar("U")  # 出参


def batch(func: Callable[[T], U], items: list[T], workers: int = 5) -> list[U]:
    """
    并发执行同步函数，处理列表中的每个元素，无容错处理
    :param func: 调用的同步函数，接受一个参数
    :param items: 多任务的参数列表
    :param workers: 并发线程数
    :return: 按items顺序返回结果列表
    """
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # map按顺序等待并获取结果（as_completed会乱序返回）
        results = list(executor.map(func, items))
        return results


def batch_safe(
    func: Callable[[T], U],
    items: list[T],
    workers: int = 5,
    timeout: float | None = None,
    return_exceptions: bool = True,
) -> list[tuple[bool, int, T, U | str]]:
    """
    并发执行同步函数，处理列表中的每个元素,容错处理
    :param func: 调用的同步函数，f(T)->U
    :param items: 多任务的参数列表,list[T]
    :param workers: 并发线程数
    :param timeout: 获取结果超时
    :param return_exceptions: 容忍异常，返回异常信息
    :return: 列表(状态, 编号，入参T，出参U | 错误信息)
    """
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_idx = {executor.submit(func, item): i for i, item in enumerate(items)}
        for future in as_completed(future_idx):
            idx = future_idx[future]
            item = items[idx]
            try:
                result = future.result(timeout=timeout)
                results.append((True, idx, item, result))
            except asyncio.TimeoutError:
                err_msg = f"timeout: {timeout}"
                results.append((False, idx, item, err_msg))
            except Exception as e:
                if return_exceptions:
                    err_msg = f"{type(e).__name__}: {e}: {traceback.format_exc()}"
                    results.append((False, idx, item, err_msg))
                else:
                    raise
    return results


async def batch_async(
    async_func: Callable[[T], Awaitable[U]],
    items: list[T],
    workers: int = 10,
    timeout: float | None = 30.0,
    return_exceptions: bool = True,
) -> list[tuple[bool, int, T, U | str]]:
    """
    并发执行异步函数，处理列表每个参数
    :param async_func: 调用的异步函数，f(T)->U
    :param items: 多任务的参数列表,list[T]
    :param workers: 并发线程数
    :param timeout: 任务超时时间
    :param return_exceptions: 容忍异常，返回异常信息
    :return: 列表(状态, 编号，入参T，出参U | 错误信息)
    """
    if not items:
        return [], []

    # 异步信号量控制并发
    semaphore = asyncio.Semaphore(workers)

    async def _wrapped(idx: int, item: T) -> tuple[bool, int, T, U | str]:
        async with semaphore:
            try:
                # timeout=None 表示无超时
                if timeout is not None:
                    result = await asyncio.wait_for(async_func(item), timeout=timeout)
                else:
                    result = await async_func(item)
                return (True, idx, item, result)
            except asyncio.TimeoutError:
                err_msg = f"timeout: {timeout}"
            except Exception as e:
                if return_exceptions:
                    err_msg = f"{type(e).__name__}: {e}: {traceback.format_exc()}"
                else:
                    raise
            return (False, idx, item, err_msg)

    # 创建任务（携带索引）
    tasks = [asyncio.create_task(_wrapped(i, item)) for i, item in enumerate(items)]

    # 并发执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=False)

    return results
