import os
import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import TypeVar

# 类型变量（保持泛型返回值）
T = TypeVar("T")


# I/O 密集型任务线程池（文件读写/网络调用）
IO_POOL = ThreadPoolExecutor(
    max_workers=min(32, (os.cpu_count() or 1) * 4), thread_name_prefix="mineru-io"
)

# CPU 密集型任务进程池（Excel/PDF 解析）
CPU_POOL = ProcessPoolExecutor(
    max_workers=min(4, os.cpu_count() or 1),  # 避免耗尽 CPU
    initializer=lambda: os.nice(10),  # 降低优先级，保 API 响应
)


async def run_io(func, *args, **kwargs):
    """IO密集型异步调用"""
    loop = asyncio.get_running_loop()
    bound_func = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(IO_POOL, bound_func)


async def run_cpu(func, *args, **kwargs):
    """CPU密集型异步调用"""
    loop = asyncio.get_running_loop()
    bound_func = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(CPU_POOL, bound_func)
