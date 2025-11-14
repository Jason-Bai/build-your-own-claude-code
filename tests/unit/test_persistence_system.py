import pytest
import asyncio
from pathlib import Path
import os
import shutil
from datetime import datetime

from src.persistence.storage import JSONStorage, SQLiteStorage
from src.persistence.manager import PersistenceManager
from src.checkpoint.types import Checkpoint
from src.checkpoint.manager import CheckpointManager

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

PROJECT_NAME = "test_project"
BASE_DIR = "~/.cache/tiny-claude-code-tests"

@pytest.fixture(scope="module")
def event_loop():
    """Overrides pytest-asyncio default event_loop fixture."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", params=["json", "sqlite"])
async def persistence_manager(request):
    """Fixture to provide a PersistenceManager with both storage backends."""
    if request.param == "json":
        storage = JSONStorage(project_name=PROJECT_NAME, base_dir=BASE_DIR)
    else:
        storage = SQLiteStorage(project_name=PROJECT_NAME, base_dir=BASE_DIR)
    
    manager = PersistenceManager(storage)
    yield manager
    
    # Teardown: clean up the test cache directory
    test_cache_dir = Path(BASE_DIR).expanduser()
    if test_cache_dir.exists():
        shutil.rmtree(test_cache_dir)

class TestPersistenceManager:
    async def test_save_and_load(self, persistence_manager: PersistenceManager):
        category, key, data = "test_cat", "test_key", {"hello": "world"}
        await persistence_manager.storage.save(category, key, data)
        loaded_data = await persistence_manager.storage.load(category, key)
        assert loaded_data == data

    async def test_load_nonexistent(self, persistence_manager: PersistenceManager):
        loaded_data = await persistence_manager.storage.load("test_cat", "nonexistent")
        assert loaded_data is None

    async def test_delete(self, persistence_manager: PersistenceManager):
        category, key, data = "test_cat", "test_key_del", {"hello": "world"}
        await persistence_manager.storage.save(category, key, data)
        
        existed = await persistence_manager.storage.load(category, key)
        assert existed is not None

        deleted = await persistence_manager.storage.delete(category, key)
        assert deleted is True

        not_existed = await persistence_manager.storage.load(category, key)
        assert not_existed is None

    async def test_delete_nonexistent(self, persistence_manager: PersistenceManager):
        deleted = await persistence_manager.storage.delete("test_cat", "nonexistent_del")
        assert deleted is False

    async def test_list(self, persistence_manager: PersistenceManager):
        category = "list_test"
        await persistence_manager.storage.save(category, "key1", {"data": 1})
        await persistence_manager.storage.save(category, "key2", {"data": 2})
        
        keys = await persistence_manager.storage.list(category)
        assert sorted(keys) == ["key1", "key2"]

class TestCheckpointManager:
    @pytest.fixture
    def checkpoint_manager(self, persistence_manager):
        return CheckpointManager(persistence_manager)

    async def test_create_and_load_checkpoint(self, checkpoint_manager: CheckpointManager):
        exec_id = "exec-123"
        cp = await checkpoint_manager.create_checkpoint(
            execution_id=exec_id,
            step_name="test_step",
            step_index=1,
            state={"agent_state": "thinking"},
            context={"messages": []},
            variables={"var1": "value1"}
        )
        
        loaded_cp = await checkpoint_manager.load_checkpoint(cp.id)
        assert loaded_cp is not None
        assert loaded_cp.id == cp.id
        assert loaded_cp.execution_id == exec_id
        assert loaded_cp.step_index == 1
        assert loaded_cp.state == {"agent_state": "thinking"}
        assert isinstance(loaded_cp.timestamp, datetime)

    async def test_list_checkpoints(self, checkpoint_manager: CheckpointManager):
        exec_id_1 = "exec-list-1"
        exec_id_2 = "exec-list-2"

        await checkpoint_manager.create_checkpoint(exec_id_1, "step1", 1, {}, {}, {})
        await checkpoint_manager.create_checkpoint(exec_id_1, "step2", 2, {}, {}, {})
        await checkpoint_manager.create_checkpoint(exec_id_2, "stepA", 1, {}, {}, {})

        exec1_cps = await checkpoint_manager.list_checkpoints(exec_id_1)
        assert len(exec1_cps) == 2
        assert exec1_cps[0].step_index == 1
        assert exec1_cps[1].step_index == 2

        exec2_cps = await checkpoint_manager.list_checkpoints(exec_id_2)
        assert len(exec2_cps) == 1
        assert exec2_cps[0].step_name == "stepA"

    async def test_get_last_successful_checkpoint(self, checkpoint_manager: CheckpointManager):
        exec_id = "exec-last-succ"
        await checkpoint_manager.create_checkpoint(exec_id, "step1", 1, {}, {}, {}, status="success")
        await checkpoint_manager.create_checkpoint(exec_id, "step2", 2, {}, {}, {}, status="success")
        await checkpoint_manager.create_checkpoint(exec_id, "step3", 3, {}, {}, {}, status="failed")
        await checkpoint_manager.create_checkpoint(exec_id, "step4", 4, {}, {}, {}, status="success")

        last_cp = await checkpoint_manager.get_last_successful_checkpoint(exec_id)
        assert last_cp is not None
        assert last_cp.step_index == 4

        last_cp_before_3 = await checkpoint_manager.get_last_successful_checkpoint(exec_id, before_step=3)
        assert last_cp_before_3 is not None
        assert last_cp_before_3.step_index == 2
