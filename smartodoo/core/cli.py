import argparse
import asyncio
import shutil
import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

from smartodoo.core.config import AppConfig
from smartodoo.core.docker_manager import DockerManager
from smartodoo.core.git_manager import GitManager
from smartodoo.core.env_builder import EnvBuilder
from smartodoo.core.docker_hub import DockerHubFetcher

console = Console()

# ─── Szablony odwzorowane z oryginalnego repozytorium ──────────────────
DOCKER_COMPOSE_TEMPLATE = """services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - ODOO_VER=${{ODOO_VER}}
        - ODOO_REVISION=${{ODOO_REVISION}}
    container_name: ${{ODOO_CONT_NAME}}
    depends_on:
      - db
      - smtp4dev
    ports:
      - "{odoo_port}:8069"
    command: /usr/bin/python3 -m debugpy --listen 0.0.0.0:5858 /usr/bin/odoo --db_user=odoo --db_host=db --db_password=odoo -c /etc/odoo/odoo.conf --dev reload
    tty: true
    volumes:
      - ${{PROJECT_LOCATION}}/entrypoint.sh:/entrypoint.sh
      - ${{PROJECT_LOCATION}}/config:/etc/odoo
      - ${{PROJECT_LOCATION}}/addons:/mnt/extra-addons
      - ${{UPGRADE_UTIL_LOCATION}}:/mnt/upgrade-util
      - ${{ENTERPRISE_LOCATION}}:/mnt/enterprise
    restart: on-failure
  db:
    image: postgres:${{PSQL_VER}}
    container_name: ${{PSQL_CONT_NAME}}
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_USER=odoo
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - ${{PROJECT_LOCATION}}/psql:/var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
  smtp4dev:
    image: rnwood/smtp4dev:latest
    container_name: ${{SMTP_CONT_NAME}}
    ports:
      - "5080:80"
      - "25:25"
      - "143:143"
    hostname: smtp4dev_odoo
    restart: on-failure
"""


class OdooCliOrchestrator:
    """Fasada łącząca subcommands CLI z logiką menedżerów Dockera, Gita i EnvBuildera"""

    def __init__(self, config: AppConfig, docker: DockerManager, git: GitManager):
        self.config = config
        self.docker = docker
        self.git = git
        self.project_path = Path.home() / "Dokumenty" / "DockerProjects" / self.config.project_name
        self.env_builder = EnvBuilder(self.config, self.project_path)

    # ─── Subcommand: create ─────────────────────────────────────────
    def create_project(self, addons_url: str = "", enterprise: bool = False):
        console.print(f"\n[bold cyan]⚡ Tworzenie projektu:[/] [green]{self.config.project_name}[/]")
        console.print(f"   Odoo: [yellow]{self.config.formatted_odoo_version}[/]  |  PostgreSQL: [yellow]{self.config.formatted_psql_version}[/]\n")

        # 1. Generowanie .env
        with console.status("[dim]Generowanie plików konfiguracyjnych...[/]"):
            self.env_builder.write_env()
            compose = DOCKER_COMPOSE_TEMPLATE.format(odoo_port="8069")
            self.env_builder.write_docker_compose(compose)
            # Kopiuj szablonowe pliki pomocnicze
            self._copy_template_files()
        console.print("   [green]✓[/] Pliki .env i docker-compose.yml wygenerowane")

        # 2. Klonowanie repozytoriów
        odoo_path = self.project_path / "odoo"
        if not odoo_path.exists():
            with console.status(f"[bold green]Klonowanie Odoo {self.config.formatted_odoo_version}...[/]"):
                self.git.clone(odoo_path, "https://github.com/odoo/odoo.git", branch=self.config.formatted_odoo_version)
            console.print("   [green]✓[/] Repozytorium Odoo Community zklonowane")
        else:
            console.print("   [yellow]⟳[/] Odoo istnieje, aktualizacja...")
            self.git.pull(odoo_path)

        if addons_url:
            addons_path = self.project_path / "addons"
            if not addons_path.exists():
                with console.status("[bold]Klonowanie addons...[/]"):
                    self.git.clone(addons_path, addons_url, branch=self.config.formatted_odoo_version)
                console.print("   [green]✓[/] Addons zklonowane")

        if enterprise:
            ent_path = self.project_path / "enterprise"
            if not ent_path.exists():
                with console.status("[bold]Klonowanie Enterprise...[/]"):
                    self.git.clone(ent_path, "https://github.com/odoo/enterprise.git", branch=self.config.formatted_odoo_version)
                console.print("   [green]✓[/] Enterprise zklonowane")

        # 3. Start docker
        console.print("\n[bold blue]🐳 Uruchamianie Docker Compose...[/]")
        try:
            self.docker.execute(self.project_path, ["up", "-d"])
            console.print("[bold green]\n✅ Projekt uruchomiony!  →  http://localhost:8069[/]\n")
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Błąd Dockera:[/] {e.stderr if hasattr(e,'stderr') else e}")
            sys.exit(1)

    # ─── Subcommand: delete ─────────────────────────────────────────
    def delete_project(self):
        console.print(f"[bold yellow]🗑  Usuwanie projektu:[/] {self.config.project_name}")
        self.docker.execute(self.project_path, ["down", "-v"], check=False)
        if self.project_path.exists():
            shutil.rmtree(self.project_path, ignore_errors=True)
        console.print("[green]Zakończono.[/]")

    # ─── Subcommand: test ───────────────────────────────────────────
    def run_tests(self, db: str, module: str):
        console.print(f"[bold cyan]🧪 Testy:[/] moduł={module}  baza={db}")
        self.docker.run_tests(self.project_path, db, module)
        console.print("[green]Gotowe.[/]")

    # ─── Subcommand: list ───────────────────────────────────────────
    @staticmethod
    def list_projects():
        base = Path.home() / "Dokumenty" / "DockerProjects"
        if not base.exists():
            console.print("[dim]Brak projektów.[/]")
            return
        table = Table(title="Projekty SmartOdoo")
        table.add_column("Nazwa", style="cyan")
        table.add_column("Ścieżka", style="dim")
        table.add_column(".env", style="green")
        for d in sorted(base.iterdir()):
            if d.is_dir():
                has_env = "✓" if (d / ".env").exists() else "✗"
                table.add_row(d.name, str(d), has_env)
        console.print(table)

    # ─── Subcommand: tags ───────────────────────────────────────────
    @staticmethod
    def show_tags():
        fetcher = DockerHubFetcher()
        tags = asyncio.run(fetcher.get_odoo_tags(limit=20))
        if not tags:
            console.print("[red]Nie udało się pobrać tagów (sprawdź internet)[/]")
            return
        table = Table(title="Dostępne wersje Odoo (Docker Hub)")
        table.add_column("Tag", style="cyan")
        for t in tags:
            table.add_row(t)
        console.print(table)

    # ─── Helpers ────────────────────────────────────────────────────
    def _copy_template_files(self):
        """Kopiuje szablonowe pliki (Dockerfile, entrypoint, config) do nowego projektu."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        for name in ["Dockerfile", "entrypoint.sh"]:
            src = repo_root / name
            dst = self.project_path / name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
        config_src = repo_root / "config"
        config_dst = self.project_path / "config"
        if config_src.exists() and not config_dst.exists():
            shutil.copytree(config_src, config_dst)


# ─── CLI Parser z subcommands ──────────────────────────────────────────
def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="so",
        description="SmartOdoo CLI — szybkie środowiska Odoo w terminalu",
    )
    sub = parser.add_subparsers(dest="command", help="Dostępne komendy")

    # so create -n MyProject
    create_cmd = sub.add_parser("create", help="Utwórz nowy projekt Odoo")
    create_cmd.add_argument("-n", "--name", required=True, help="Nazwa projektu")
    create_cmd.add_argument("-o", "--odoo", default="19.0", help="Wersja Odoo (np. 17.0)")
    create_cmd.add_argument("-p", "--psql", default="16", help="Wersja PostgreSQL")
    create_cmd.add_argument("--addons", default="", help="URL repozytorium addons")
    create_cmd.add_argument("--enterprise", action="store_true", help="Klonuj Enterprise")

    # so delete -n MyProject
    delete_cmd = sub.add_parser("delete", help="Usuń projekt")
    delete_cmd.add_argument("-n", "--name", required=True)

    # so test -n MyProject --db testdb --module sale
    test_cmd = sub.add_parser("test", help="Uruchom testy Odoo")
    test_cmd.add_argument("-n", "--name", required=True)
    test_cmd.add_argument("--db", required=True)
    test_cmd.add_argument("-m", "--module", required=True)

    # so list
    sub.add_parser("list", help="Wyświetl istniejące projekty")

    # so tags
    sub.add_parser("tags", help="Pokaż dostępne wersje Odoo z Docker Hub")

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Komendy bezstanowe
    if args.command == "list":
        OdooCliOrchestrator.list_projects()
        return
    if args.command == "tags":
        OdooCliOrchestrator.show_tags()
        return

    # Komendy wymagające projektu
    config = AppConfig(
        project_name=args.name,
        odoo_version=getattr(args, "odoo", "19.0"),
        psql_version=getattr(args, "psql", "16"),
    )

    try:
        docker = DockerManager()
        git = GitManager()
    except RuntimeError as e:
        console.print(f"[bold red]System Error:[/] {e}")
        sys.exit(1)

    orch = OdooCliOrchestrator(config, docker, git)

    if args.command == "create":
        orch.create_project(addons_url=args.addons, enterprise=args.enterprise)
    elif args.command == "delete":
        orch.delete_project()
    elif args.command == "test":
        orch.run_tests(args.db, args.module)
