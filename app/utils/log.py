import os
import logging


class parent_file_path(logging.Filter):
    def filter(self, record):
        # 获取文件名（如 upload.py）
        filename = os.path.basename(record.pathname)
        # 获取父目录名（如 api）
        parent_dir = os.path.basename(os.path.dirname(record.pathname))
        # 组合成：api/upload.py
        record.one_level_path = os.path.join(parent_dir, filename)
        return True


# 创建 logger
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# 创建控制台处理器
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(one_level_path)s:%(lineno)d:%(funcName)s  %(message)s"
)
handler.setFormatter(formatter)

# 添加处理器到 logger
handler.addFilter(parent_file_path())
log.addHandler(handler)
