from sonyflake import Sonyflake
from datetime import datetime

sf = Sonyflake(start_time=datetime(2025, 12, 12))


def next_id():
    """获取下一个自增ID(单例中使用)"""
    return sf.next_id()


async def next_id_async():
    """获取下一个自增ID(单例中使用)"""
    return await sf.next_id_async()
