import pytest
from pathlib import Path
from smartodoo.core.config import Settings
from smartodoo.core.env_builder import EnvBuilder

def test_enforce_lf_line_endings_in_sh_scripts(tmp_path, monkeypatch):
    """
    Sprawdza, czy generator wymusza znak \n w zapisywanych skryptach bash i konfiguracjach,
    zabezpieczając użycie Dockera na maszynach Windows. \r ucegła skrypty .sh podczas wykonywania w kontenerze linuxowym.
    """
    env_vars = {
        "PROJECT_LOCATION": str(tmp_path),
        "ENTERPRISE_LOCATION": str(tmp_path / "ent"),
        "UPGRADE_UTIL_LOCATION": str(tmp_path / "util"),
        "PROJECT_NAME": "test_proj",
        "ODOO_VER": "16.0",
        "ODOO_REVISION": "",
        "PSQL_VER": "15",
        "ODOO_CONT_NAME": "cont",
        "PSQL_CONT_NAME": "cont",
        "SMTP_CONT_NAME": "cont",
        "ODOO_VOLUME": "vol",
        "PSQL_VOLUME": "vol",
        "SMTP_VOLUME": "vol",
        "PSQL_DB_NAME": "pg",
        "PSQL_DB_PASSWORD": "odoo",
        "PSQL_DB_USERNAME": "odoo"
    }
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
        
    settings = Settings(_env_file=None)
    builder = EnvBuilder(config=settings, project_dir=tmp_path)
    
    # Generujemy pliki (w tym docker-compose, konf i najważniejszy: entrypoint.sh)
    builder.generate_all()
    
    entrypoint = tmp_path / "entrypoint.sh"
    
    # Odczytujemy binarnie, aby upewnić się na najniższym poziomie
    content_raw = entrypoint.read_bytes()
    
    # Skrypt musi istnieć
    assert entrypoint.exists()
    
    # Nie może być ani jednego carriage return \r w rawcie pliku sh
    assert b"\r\n" not in content_raw, "Skrypt shell posiada zakończenia CRLF (Windows) - Docker rzuci błędem o nieznanej komendzie!"
    
    # Upewniamy się, że mimo wszystko jakieś nowe linie ma (\n)
    assert b"\n" in content_raw
