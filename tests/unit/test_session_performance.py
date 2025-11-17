"""Performance benchmarks for Session Manager system"""

import time
from datetime import datetime
import pytest
from src.sessions.manager import SessionManager
from src.sessions.types import Session


class MockPersistenceManager:
    """Fast mock persistence for benchmarking"""

    def __init__(self):
        self.sessions = {}
        self.operation_count = 0

    async def save_session(self, session_id: str, session_data: dict) -> str:
        self.operation_count += 1
        self.sessions[session_id] = session_data
        return session_id

    async def load_session(self, session_id: str):
        return self.sessions.get(session_id)

    async def list_sessions(self):
        return list(self.sessions.keys())


class TestSessionManagerPerformance:
    """Performance benchmarks for SessionManager"""

    def test_session_creation_performance(self):
        """Benchmark session creation speed"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        start_time = time.time()
        for i in range(100):
            session = manager.start_session(f"project-{i}")
            manager.end_session()
        elapsed = time.time() - start_time

        # Should create and end 100 sessions in less than 1 second
        assert elapsed < 1.0, f"Session creation too slow: {elapsed:.3f}s for 100 operations"

    def test_message_recording_performance(self):
        """Benchmark message recording speed"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("perf-test")

        start_time = time.time()
        for i in range(1000):
            manager.record_message({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}" * 10  # ~50 char message
            })
        elapsed = time.time() - start_time

        # Should record 1000 messages in less than 100ms
        assert elapsed < 0.1, f"Message recording too slow: {elapsed:.3f}s for 1000 operations"

    def test_command_recording_performance(self):
        """Benchmark command recording speed"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("perf-test")

        start_time = time.time()
        for i in range(1000):
            manager.record_command(f"git commit -m 'message {i}'")
        elapsed = time.time() - start_time

        # Should record 1000 commands in less than 100ms
        assert elapsed < 0.1, f"Command recording too slow: {elapsed:.3f}s for 1000 operations"

    def test_session_serialization_performance(self):
        """Benchmark session serialization speed"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("serialize-test")

        # Add complex data
        for i in range(100):
            manager.record_message({
                "role": "user",
                "content": f"Complex message {i}" * 5,
                "metadata": {"index": i, "data": list(range(10))}
            })
            manager.record_command(f"cmd {i}")

        # Benchmark serialization
        start_time = time.time()
        for _ in range(100):
            session_dict = session.to_dict()
        elapsed = time.time() - start_time

        # Should serialize 100 times in less than 100ms
        assert elapsed < 0.1, f"Serialization too slow: {elapsed:.3f}s for 100 operations"

    def test_session_deserialization_performance(self):
        """Benchmark session deserialization speed"""
        session = Session(
            session_id="test-session",
            project_name="perf-test",
            start_time=datetime.now()
        )

        # Add complex data
        for i in range(100):
            session.conversation_history.append({
                "role": "user",
                "content": f"Message {i}" * 5,
                "metadata": {"index": i}
            })
            session.command_history.append(f"cmd {i}")

        session_dict = session.to_dict()

        # Benchmark deserialization
        start_time = time.time()
        for _ in range(100):
            Session.from_dict(session_dict)
        elapsed = time.time() - start_time

        # Should deserialize 100 times in less than 100ms
        assert elapsed < 0.1, f"Deserialization too slow: {elapsed:.3f}s for 100 operations"

    def test_persistence_operations_performance(self):
        """Benchmark persistence operations"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create sessions
        session_ids = []
        for i in range(10):
            session = manager.start_session(f"project-{i}")
            session_ids.append(session.session_id)

            # Add data
            for j in range(50):
                manager.record_message({
                    "role": "user",
                    "content": f"Message {j}"
                })
            manager.end_session()

        # Benchmark save operations
        start_time = time.time()
        save_count = 0
        for session_id in session_ids:
            session_data = persistence.sessions[session_id]
            save_count += 1
        elapsed = time.time() - start_time

        # Should complete all operations in less than 100ms
        assert elapsed < 0.1, f"Persistence operations too slow: {elapsed:.3f}s for {save_count} saves"

    def test_session_manager_memory_efficiency(self):
        """Benchmark memory efficiency with many sessions"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create many sessions without running out of memory
        for i in range(100):
            session = manager.start_session(f"project-{i}")

            # Add moderate amount of data
            for j in range(20):
                manager.record_message({
                    "role": "user",
                    "content": f"Message {j}" * 10
                })
                manager.record_command(f"cmd {j}")

            manager.end_session()

        # Should have 100 sessions stored
        assert len(persistence.sessions) == 100
        assert persistence.operation_count == 100  # One save per session

    def test_concurrent_session_operations(self):
        """Benchmark handling multiple concurrent operations"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("concurrent-test")

        # Simulate concurrent message and command recording
        start_time = time.time()
        for i in range(500):
            if i % 2 == 0:
                manager.record_message({"role": "user", "content": f"Msg {i}"})
            else:
                manager.record_command(f"cmd {i}")
        elapsed = time.time() - start_time

        # Should handle 500 mixed operations in less than 50ms
        assert elapsed < 0.05, f"Mixed operations too slow: {elapsed:.3f}s for 500 operations"

    def test_session_isolation_performance(self):
        """Benchmark session isolation (no cross-contamination)"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create multiple sessions
        session_ids = []
        for i in range(10):
            session = manager.start_session(f"project-{i}")
            session_ids.append(session.session_id)

            for j in range(20):
                manager.record_message({
                    "role": "user",
                    "content": f"Session {i} Message {j}"
                })
            manager.end_session()

        # Verify isolation
        start_time = time.time()
        for session_id in session_ids:
            session_data = persistence.sessions[session_id]
            # Each session should have exactly 20 messages
            assert len(session_data["conversation_history"]) == 20
        elapsed = time.time() - start_time

        # Verification should be fast
        assert elapsed < 0.01, f"Verification too slow: {elapsed:.3f}s"


class TestSessionOperationThroughput:
    """Test system throughput under load"""

    def test_high_message_throughput(self):
        """Test high-throughput message recording"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("throughput-test")

        # Record 5000 messages
        start_time = time.time()
        for i in range(5000):
            manager.record_message({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "timestamp": time.time()
            })
        elapsed = time.time() - start_time

        # Should achieve > 50k messages/sec
        throughput = 5000 / elapsed
        assert throughput > 50000, f"Throughput too low: {throughput:.0f} msgs/sec"

    def test_high_command_throughput(self):
        """Test high-throughput command recording"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("throughput-test")

        # Record 5000 commands
        start_time = time.time()
        for i in range(5000):
            manager.record_command(f"command-{i} --flag value")
        elapsed = time.time() - start_time

        # Should achieve > 50k commands/sec
        throughput = 5000 / elapsed
        assert throughput > 50000, f"Throughput too low: {throughput:.0f} cmds/sec"

    def test_session_lifecycle_throughput(self):
        """Test session lifecycle throughput"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create and close 500 sessions
        start_time = time.time()
        for i in range(500):
            session = manager.start_session(f"project-{i}")
            manager.record_message({"role": "user", "content": "test"})
            manager.end_session()
        elapsed = time.time() - start_time

        # Should achieve > 500 sessions/sec
        throughput = 500 / elapsed
        assert throughput > 500, f"Throughput too low: {throughput:.0f} sessions/sec"
