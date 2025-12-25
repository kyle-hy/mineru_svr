from pathlib import Path
import aiofiles
import asyncio
import os
from .aiorun import run_io


async def unlink(fpath: str | Path) -> None:
    """
    异步删除文件（安全、非阻塞）

    :raises FileNotFoundError: 文件不存在
    :raises PermissionError: 权限不足
    :raises OSError: 其他系统错误（如目录非空）
    """
    await run_io(os.unlink, fpath)


async def read_file(fpath: str) -> str:
    async with aiofiles.open(fpath, "r", encoding="utf-8") as f:
        return await f.read()


async def write_file(
    fpath: str | Path,
    content: str,
    check_folder: bool = True,
    encoding: str = "utf-8",
    mkdir_mode: int = 0o755,  # 权限：rwxr-xr-x
) -> Path:
    """
    异步安全写入文本文件（生产级推荐）

    :param fpath: 文件路径（支持 str / Path）
    :param content: 要写入的文本内容
    :param check_folder: 是否自动创建父目录
    :param encoding: 文件编码（默认 utf-8）
    :param mkdir_mode: 创建目录的权限模式
    :return: 实际写入的绝对路径（Path 对象）
    :raises OSError: 磁盘满/权限不足等
    :raises UnicodeEncodeError: 编码失败（如 content 含 surrogate）
    """

    # 创建目录（异步！避免阻塞）
    path = Path(fpath)
    if check_folder:
        await run_io(path.parent.mkdir, parents=True, exist_ok=True, mode=mkdir_mode)

    # 异步写入（核心）
    async with aiofiles.open(path, "w", encoding=encoding) as f:
        await f.write(content)

    return path


async def write_bin(
    fpath: str | Path,
    content: str,
    check_folder: bool = True,
    mkdir_mode: int = 0o755,  # 权限：rwxr-xr-x
) -> Path:
    """
    异步安全写入文本文件（生产级推荐）

    :param fpath: 文件路径（支持 str / Path）
    :param content: 要写入的文本内容
    :param check_folder: 是否自动创建父目录
    :param mkdir_mode: 创建目录的权限模式
    :return: 实际写入的绝对路径（Path 对象）
    :raises OSError: 磁盘满/权限不足等
    :raises UnicodeEncodeError: 编码失败（如 content 含 surrogate）
    """

    # 创建目录（异步！避免阻塞）
    path = Path(fpath)
    if check_folder:
        await run_io(path.parent.mkdir, parents=True, exist_ok=True, mode=mkdir_mode)

    # 异步写入（核心）
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)

    return path


async def file_exists(
    fpath: str | Path,
    base_dir: Path | None = None,
    resolve_symlinks: bool = True,
) -> bool:
    """
    异步检查文件是否存在（带安全防护）

    :param fpath: 待检查路径（支持 str / Path）
    :param base_dir: 可选基目录（用于限制路径范围，防 ../ 遍历）
    :param resolve_symlinks: 是否解析符号链接（True=检查真实文件，False=检查链接本身）
    :return: True if file exists and is a regular file
    """
    try:
        path = Path(fpath)

        # 路径安全校验（关键！）
        if base_dir is not None:
            resolved = path.resolve()  # 消解所有 ../ 和软链接
            if not resolved.is_relative_to(base_dir.resolve()):
                return False  # 拒绝越权访问

        # ️ 异步执行存在性检查（避免阻塞事件循环）
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: (
                path.is_file()
                if resolve_symlinks
                else path.exists() and not path.is_dir()
            ),
        )

    except (OSError, ValueError):
        # 路径含非法字符（如 \0）或权限不足 → 视为不存在
        return False
