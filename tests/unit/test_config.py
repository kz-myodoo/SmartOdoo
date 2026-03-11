import pytest
from pydantic import ValidationError
from smartodoo.core.config import Settings

def test_settings_raises_error_on_missing_fields(monkeypatch):
    """
    Test sprawdza czy brakujące kluczowe zmienne wywołają błąd walidacji pydantic.
    Gwarantuje to, że środowisko nie wstanie z pusto zdefiniowaną konfiguracją.
    """
    # Czyścimy środowisko z ewentualnych domyślnych zmiennych
    monkeypatch.delenv("PROJECT_NAME", raising=False)
    monkeypatch.delenv("ODOO_VER", raising=False)
    
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    
    errors = str(exc_info.value)
    assert "PROJECT_NAME" in errors
    assert "ODOO_VER" in errors

def test_settings_valid_initialization(monkeypatch):
    """
    Test sprawdza poprawne załadowanie wszystkich wymaganych 16 zmiennych z environmentu/pliku.
    """
    env_vars = {
        "PROJECT_LOCATION": "/test/loc",
        "ENTERPRISE_LOCATION": "/test/ent",
        "UPGRADE_UTIL_LOCATION": "/test/upg",
        "PROJECT_NAME": "test_proj",
        "ODOO_VER": "16.0",
        "ODOO_REVISION": "",
        "PSQL_VER": "15",
        "ODOO_CONT_NAME": "odoo_test",
        "PSQL_CONT_NAME": "psql_test",
        "SMTP_CONT_NAME": "smtp_test",
        "ODOO_VOLUME": "odoo_vol",
        "PSQL_VOLUME": "psql_vol",
        "SMTP_VOLUME": "smtp_vol",
        "PSQL_DB_NAME": "postgres",
        "PSQL_DB_PASSWORD": "odoo",
        "PSQL_DB_USERNAME": "odoo"
    }
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
        
    settings = Settings()
    
    assert settings.PROJECT_NAME == "test_proj"
    assert settings.ODOO_VER == "16.0"
    assert settings.PSQL_DB_USERNAME == "odoo"
    assert settings.ODOO_REVISION == "" 
    # Oczekujemy, że ułoży się poprawnie z modelami pydantic
