import pytest
from pathlib import Path
from smartodoo.core.config import Settings
from smartodoo.core.env_builder import EnvBuilder

def test_env_builder_renders_jinja2(tmp_path, monkeypatch):
    """
    Testuje czy EnvBuilder poprawnie renderuje pliki odoo.conf, docker-compose.yml
    i entrypoint.sh i używa załadowanego Settings via Jinja2 zamiast starego replace().
    """
    env_vars = {
        "PROJECT_LOCATION": str(tmp_path),
        "ENTERPRISE_LOCATION": str(tmp_path / "ent"),
        "UPGRADE_UTIL_LOCATION": str(tmp_path / "util"),
        "PROJECT_NAME": "test_proj",
        "ODOO_VER": "16.0",
        "ODOO_REVISION": "",
        "PSQL_VER": "15",
        "ODOO_CONT_NAME": "cont_odoo",
        "PSQL_CONT_NAME": "cont_psql",
        "SMTP_CONT_NAME": "cont_smtp",
        "ODOO_VOLUME": "vol_odoo",
        "PSQL_VOLUME": "vol_psql",
        "SMTP_VOLUME": "vol_smtp",
        "PSQL_DB_NAME": "dbpostgres",
        "PSQL_DB_PASSWORD": "dbpassword",
        "PSQL_DB_USERNAME": "db_user"
    }
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
        
    settings = Settings(_env_file=None)
    builder = EnvBuilder(config=settings, project_dir=tmp_path)
    
    # Symulacja akcji generate (buduje wszystkie pliki Odoo dev ops)
    builder.generate_all()
    
    compose = tmp_path / "docker-compose.yml"
    config = tmp_path / "config" / "odoo.conf"
    entrypoint = tmp_path / "entrypoint.sh"
    
    assert compose.exists()
    assert config.exists()
    assert entrypoint.exists()
    
    compose_text = compose.read_text("utf-8")
    assert "cont_odoo" in compose_text
    assert "16.0" in compose_text
    
    config_text = config.read_text("utf-8")
    assert "db_user = db_user" in config_text
    assert "db_password = dbpassword" in config_text
