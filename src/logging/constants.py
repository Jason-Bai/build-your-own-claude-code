"""
日志系统常量定义
"""

# 默认配置
DEFAULT_LOG_DIR = "~/.tiny-claude-code/logs"
DEFAULT_QUEUE_SIZE = 1000
DEFAULT_BATCH_SIZE = 100
DEFAULT_BATCH_TIMEOUT = 1.0  # 秒
DEFAULT_RETENTION_DAYS = 30
DEFAULT_MAX_TOTAL_SIZE_MB = 1024
DEFAULT_COMPRESS_AFTER_DAYS = 7

# 性能参数
WORKER_HEARTBEAT_TIMEOUT = 10  # 秒，心跳超时阈值
WORKER_RESTART_MAX_ATTEMPTS = 3  # 最大重启尝试次数
LOG_OUTPUT_MAX_CHARS = 1000  # 输出字段最大字符数（用于截断）

# 文件命名
LOG_FILE_DATE_FORMAT = "%Y-%m-%d"
LOG_FILE_EXTENSION = ".jsonl"
LOG_FILE_COMPRESSED_EXTENSION = ".jsonl.gz"
ROTATION_LOCK_FILE = ".rotation.lock"
METADATA_FILE = "metadata.json"

# 数据脱敏
SENSITIVE_FIELD_NAMES = [
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "private_key",
    "privatekey",
]

# 敏感数据匹配模式（正则）
SENSITIVE_PATTERNS = [
    # API密钥：sk-ant-api03-xxx（Anthropic）
    (r"sk-ant-api03-[a-zA-Z0-9\-_]+", r"sk-***[MASKED]***"),
    # API密钥：sk-xxx（OpenAI/通用）
    (r"sk-[a-zA-Z0-9]{48,}", r"sk-***[MASKED]***"),
    # Bearer token
    (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", r"Bearer [MASKED]"),
    # 用户目录路径
    (r"/Users/[^/\s]+/", r"/Users/[USER]/"),
    (r"/home/[^/\s]+/", r"/home/[USER]/"),
    (r"C:\\Users\\[^\\s]+\\", r"C:\\Users\\[USER]\\"),
    # 邮箱地址
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", r"[EMAIL_MASKED]"),
    # 中国手机号（1开头，11位数字）
    (r"1[3-9]\d{9}", r"[PHONE_MASKED]"),
    # 国际手机号（+号开头，1-3位国家码，后跟号码）
    (r"\+\d{1,3}[-\s]?\d{1,14}", r"[PHONE_MASKED]"),
]
