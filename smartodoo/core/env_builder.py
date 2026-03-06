from pathlib import Path
from smartodoo.core.config import AppConfig

class EnvBuilder:
    """Implementacja wzorca Budowniczego środowiska. Odseparowuje logikę
    zapisu z dyskiem od parsera i CLI. Umożliwia łatwe mockowanie i testowanie."""
    
    def __init__(self, config: AppConfig, project_dir: Path):
        self.config = config
        self.project_dir = project_dir

    def generate_env(self) -> str:
        """Tworzy bezpieczną treść pliku .env, zapobiegając strzelaniu replace() po stringach."""
        content = [
            f"ODOO_VERSION={self.config.formatted_odoo_version}",
            f"PSQL_VERSION={self.config.formatted_psql_version}",
            "ODOO_PORT=8069",
            "CHATPWD=admin"
        ]
        if self.config.enterprise:
            content.append("ODOO_ENTERPRISE=True")
        
        return "\n".join(content)

    def write_env(self):
        """Zapisuje .env na dysku w przestrzeni projektu."""
        # Upewniamy się, że projekt istnieje przed pisaniem
        self.project_dir.mkdir(parents=True, exist_ok=True)
        env_file = self.project_dir / ".env"
        env_file.write_text(self.generate_env(), encoding="utf-8")
        
    def write_docker_compose(self, template_content: str):
        """Umieszcza docker-compose z gotowego szablonu w repozytorium zlecenia."""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        compose_file = self.project_dir / "docker-compose.yml"
        compose_file.write_text(template_content, encoding="utf-8")
