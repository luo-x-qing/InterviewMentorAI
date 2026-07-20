import pytest
import tempfile
import os
import uuid
import warnings


@pytest.fixture(autouse=True)
def _suppress_httpx_warning():
    warnings.filterwarnings("ignore", message="The 'app' shortcut is now deprecated")


@pytest.fixture
def vector_db():
    from app.core.vector_db import VectorDB

    db_path = os.path.join(tempfile.gettempdir(), f"test_vector_db_{uuid.uuid4().hex}.db")
    db = VectorDB(db_path=db_path)
    yield db
    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)
