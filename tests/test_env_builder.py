import pytest
from pathlib import Path
from smartodoo.core.config import AppConfig
from smartodoo.core.env_builder import EnvBuilder

def test_generate_env_content():
    """Weryfikacja formatowania .env na bazie abstrakcji Dataclass, bez tworzenia faktycznego pliku."""
    config = AppConfig(project_name="TestEnvProject", odoo_version="15.0", psql_version="14", enterprise=True)
    builder = EnvBuilder(config, Path("/tmp/fake_dir"))
    
    content = builder.generate_env()
    lines = content.split('\n')
    
    assert "ODOO_VERSION=15.0" in lines
    assert "PSQL_VERSION=14" in lines
    assert "ODOO_PORT=8069" in lines
    assert "ODOO_ENTERPRISE=True" in lines

def test_write_env_file(tmp_path):
    """Izolowany test pisania po dysku do obiektu tymczasowego (z użyciem pytest tmp_path)."""
    config = AppConfig(project_name="FakeProject", odoo_version="16.0")
    # tmp_path to wbudowana funkcja pytest, niszcząca środowisko obok projektu
    fake_project_dir = tmp_path / "FakeProject"
    
    builder = EnvBuilder(config, fake_project_dir)
    builder.write_env()
    
    env_file = fake_project_dir / ".env"
    assert env_file.exists()
    
    text = env_file.read_text("utf-8")
    assert "ODOO_VERSION=16.0" in text

def test_write_docker_compose(tmp_path):
    """Sprawdzenie mechanizmu wklejania szablonów do nowych projektów."""
    config = AppConfig(project_name="DockerFakeProject")
    fake_project_dir = tmp_path / "DockerFakeProject"
    
    builder = EnvBuilder(config, fake_project_dir)
    builder.write_docker_compose("services:\n  web:\n    image: odoo:16.0")
    
    compose = fake_project_dir / "docker-compose.yml"
    assert compose.exists()
    assert "image: odoo:16.0" in compose.read_text("utf-8")
