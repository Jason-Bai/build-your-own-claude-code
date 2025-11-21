"""
集成测试：日志系统与核心系统集成

测试内容：
1. SessionManager 集成
2. EnhancedAgent 集成（状态变化）
3. 数据脱敏在真实场景中的工作
"""
import tempfile
import time
from pathlib import Path
from datetime import datetime
import json
import pytest

from src.sessions.manager import SessionManager
from src.persistence.manager import PersistenceManager
from src.persistence.storage import JSONStorage
from src.logging import init_logger, shutdown_logger
from src.logging.types import ActionType


@pytest.fixture
def temp_log_dir():
    """临时日志目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def logger_instance(temp_log_dir):
    """初始化日志器实例"""
    # 强制重新初始化以使用临时目录
    logger = init_logger(log_dir=temp_log_dir, enabled=True, force_reinit=True)
    yield logger
    shutdown_logger()


@pytest.fixture
def session_manager(temp_log_dir, logger_instance):
    """创建SessionManager实例"""
    persistence = PersistenceManager(JSONStorage("test_project"))
    manager = SessionManager(persistence, action_logger=logger_instance)
    yield manager


class TestSessionManagerIntegration:
    """SessionManager 集成测试"""

    def test_session_start_logs(self, session_manager, logger_instance, temp_log_dir):
        """测试会话开始时记录日志"""
        # 启动会话
        session = session_manager.start_session("test-project")

        # 等待日志写入（增加等待时间以确保批量写入完成）
        time.sleep(1.5)
        logger_instance.flush()

        # 验证日志文件存在
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"{today}.jsonl"
        assert log_file.exists()

        # 读取日志
        with open(log_file, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0, "No logs written to file"

            # 解析第一条日志
            first_log = json.loads(lines[0])
            assert first_log["action_type"] == ActionType.SESSION_START
            assert first_log["session_id"] == session.session_id
            assert first_log["project_name"] == "test-project"

    def test_session_end_logs(self, session_manager, logger_instance, temp_log_dir):
        """测试会话结束时记录日志"""
        # 启动和结束会话
        session = session_manager.start_session("test-project")
        time.sleep(0.5)
        session_manager.end_session()

        # 等待日志写入
        time.sleep(1)
        logger_instance.flush()

        # 读取日志
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"{today}.jsonl"

        with open(log_file, "r") as f:
            lines = f.readlines()
            assert len(lines) >= 2  # start + end

            # 验证 SESSION_END 日志
            end_log = json.loads(lines[-1])
            assert end_log["action_type"] == ActionType.SESSION_END
            assert end_log["session_id"] == session.session_id
            assert "duration_seconds" in end_log


class TestDataMaskingIntegration:
    """数据脱敏集成测试"""

    def test_sensitive_data_masked_in_logs(self, temp_log_dir, logger_instance):
        """测试敏感数据在日志中被脱敏"""
        # 记录包含敏感数据的日志
        logger_instance.log(
            action_type=ActionType.USER_INPUT,
            session_id="test-session",
            content="My API key is sk-ant-api03-" + "x" * 48,
            password="secret123"
        )

        # 刷新并读取 (增加等待时间确保批量写入完成)
        time.sleep(1.5)
        logger_instance.flush()

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"{today}.jsonl"

        with open(log_file, "r") as f:
            log_record = json.loads(f.readline())

            # 验证敏感数据被脱敏
            assert "sk-***[MASKED]***" in log_record["content"]
            assert "sk-ant-api03" not in log_record["content"]
            assert log_record["password"] == "[MASKED]"
            assert "secret123" not in str(log_record)


class TestFullWorkflow:
    """完整工作流测试"""

    def test_complete_session_workflow(self, session_manager, logger_instance, temp_log_dir):
        """测试完整会话工作流的日志记录"""
        # 1. 启动会话
        session = session_manager.start_session("my-app")

        # 2. 模拟一些行动
        logger_instance.log(
            ActionType.USER_INPUT,
            session.session_id,
            content="Hello, help me write code"
        )

        logger_instance.log(
            ActionType.AGENT_STATE_CHANGE,
            session.session_id,
            from_state="IDLE",
            to_state="THINKING"
        )

        logger_instance.log(
            ActionType.LLM_REQUEST,
            session.session_id,
            provider="anthropic",
            model="claude-3",
            messages_count=5
        )

        # 3. 结束会话
        session_manager.end_session()

        # 4. 刷新并验证
        time.sleep(1.5)
        logger_instance.flush()

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"{today}.jsonl"

        with open(log_file, "r") as f:
            lines = f.readlines()
            assert len(lines) >= 5  # start + 3 actions + end

            # 验证行动序号递增
            action_numbers = [json.loads(line)["action_number"] for line in lines]
            assert action_numbers == sorted(action_numbers)
            assert action_numbers[0] == 1


class TestPerformanceImpact:
    """性能影响测试"""

    def test_logging_overhead(self, logger_instance):
        """测试日志记录的性能开销"""
        import time

        # 记录100条日志的时间
        start = time.time()
        for i in range(100):
            logger_instance.log(
                ActionType.USER_INPUT,
                "session-test",
                content=f"Message {i}"
            )
        elapsed = time.time() - start

        # 平均每条日志应该 < 1ms (异步队列)
        avg_time_ms = (elapsed / 100) * 1000
        assert avg_time_ms < 1, f"Logging overhead too high: {avg_time_ms:.2f}ms per action"
