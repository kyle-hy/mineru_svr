from pathlib import Path
import aiofiles
import aiofiles.os as aos


async def read_file(fpath: str) -> str:
    """异步读取文本文件"""
    async with aiofiles.open(fpath, "r", encoding="utf-8") as f:
        return await f.read()


async def write_file(
    fpath: str | Path,
    content: str,
    check_folder: bool = True,
) -> Path:
    """
    异步安全写入文本文件
    :param fpath: 文件路径（支持 str / Path）
    :param content: 要写入的文本内容
    :param check_folder: 是否自动创建父目录
    :return: 实际写入的绝对路径（Path 对象）
    """

    # 创建目录（异步！避免阻塞）
    fpath = Path(fpath)
    if check_folder:
        await aos.makedirs(fpath.parent, exist_ok=True, mode=0o755)

    # 异步写入（核心）
    async with aiofiles.open(fpath, "w", encoding="utf-8") as f:
        await f.write(content)

    return fpath


async def write_bin(
    fpath: str | Path,
    content: str,
    check_folder: bool = True,
) -> Path:
    """
    异步安全写入二进制文件
    :param fpath: 文件路径（支持 str / Path）
    :param content: 要写入的文本内容
    :param check_folder: 是否自动创建父目录
    :return: 实际写入的绝对路径（Path 对象）
    """

    # 创建目录（异步！避免阻塞）
    fpath = Path(fpath)
    if check_folder:
        await aos.makedirs(fpath.parent, exist_ok=True, mode=0o755)

    # 异步写入（核心）
    async with aiofiles.open(fpath, "wb") as f:
        await f.write(content)

    return fpath
