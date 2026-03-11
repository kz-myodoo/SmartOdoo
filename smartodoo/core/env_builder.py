from pathlib import Path
import jinja2
from smartodoo.core.config import Settings

class EnvBuilder:
    """Implementacja wzorca Budowniczego środowiska z renderingiem szablonów Jinja2."""
    
    def __init__(self, config: Settings, project_dir: Path):
        self.config = config
        self.project_dir = project_dir
        
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=False
        )

    def generate_env(self) -> str:
        """Tworzy bezpieczną treść pliku .env, zapobiegając strzelaniu replace() po stringach."""
        odoo_ver = self.config.formatted_odoo_version
        proj_name = self.config.project_name
        
        content = [
            f"ODOO_VERSION={odoo_ver}",
            f"PSQL_VERSION={self.config.formatted_psql_version}",
            "ODOO_PORT=8069",
            "CHATPWD=admin",
            f"ODOO_VER={odoo_ver}",
            f"ODOO_REVISION=latest",
            f"ODOO_CONT_NAME=odoo_{odoo_ver}_{proj_name}",
            f"PROJECT_LOCATION={self.project_dir.absolute()}",
            f"UPGRADE_UTIL_LOCATION={(self.project_dir / 'upgrade-util').absolute()}",
            f"ENTERPRISE_LOCATION={(self.project_dir / 'enterprise').absolute()}",
            f"PSQL_VER={self.config.formatted_psql_version}",
            f"PSQL_CONT_NAME=db_{odoo_ver}_{proj_name}",
            f"SMTP_CONT_NAME=smtp_{odoo_ver}_{proj_name}",
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
        """Zarezerwowane API do utrzymania kompatybilności wstecznej CLI,
        jeśli jest używane."""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        compose_file = self.project_dir / "docker-compose.yml"
        compose_file.write_text(template_content, encoding="utf-8")

    def generate_all(self):
        """Nowy pipeline do generowania i zapisu wszystkich szablonów infrastruktury w projekcie."""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        conf_dir = self.project_dir / "config"
        conf_dir.mkdir(exist_ok=True)
        
        files_to_render = [
            ("docker-compose.yml.j2", self.project_dir / "docker-compose.yml"),
            ("odoo.conf.j2", conf_dir / "odoo.conf"),
            ("entrypoint.sh.j2", self.project_dir / "entrypoint.sh")
        ]
        
        for template_name, out_path in files_to_render:
            template = self.jinja_env.get_template(template_name)
            rendered = template.render(config=self.config)
            # Używamy newline='\n' by wymusić format uniksowy, zwłaszcza dla .sh używanych wewnątrz dockera
            out_path.write_text(rendered, encoding="utf-8", newline="\n")
