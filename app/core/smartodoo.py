#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.request import urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.core.tools import load_platform_paths, resolve_odoo_conf_path  # noqa: E402  # isort: skip


ENV_FILE = ROOT / ".env"
DOCKERFILE = ROOT / "docker" / "Dockerfile"
DOCKERIGNORE = ROOT / "docker" / ".dockerignore"
DOCKER_COMPOSE = ROOT / "docker" / "docker-compose.yml"
ENTRYPOINT = ROOT / "docker" / "entrypoint.sh"
LAUNCH_JSON = ROOT / ".vscode" / "launch.json"
ENCPASS = ROOT / "scripts" / "encpass.sh"
WINDOWS_SECRET_DIR = ROOT / "secret"

ODOO_VER = "19.0"
PSQL_VER = "16"
ODOO_REVISION = ""
ODOO_GITHUB_NAME = "odoo"
ODOO_ENTERPRISE_REPOSITORY = "enterprise"
UPGRADE_UTIL_REPOSITORY = "git@github.com:odoo/upgrade-util.git"

IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    from app.platform.windows.env_paths import normalize_project_env_paths, to_compose_path
    from app.platform.windows.passwd import get_secret as platform_get_secret
    from app.platform.windows.privileged_ops import try_delete_with_admin as platform_try_delete_with_admin
    from app.platform.windows.process import run as platform_run
else:
    from app.platform.linux.env_paths import to_compose_path
    from app.platform.linux.passwd import get_secret as platform_get_secret
    from app.platform.linux.privileged_ops import try_delete_with_admin as platform_try_delete_with_admin
    from app.platform.linux.process import run as platform_run

    def normalize_project_env_paths(_project_fullpath: Path) -> None:
        """Linux adapter: no path normalization is required for .env values."""
        return


def eprint(msg: str) -> None:
    """Print a message to stderr."""
    print(msg, file=sys.stderr)


def resolve_launch_json_path() -> Path:
    """Resolve launch.json template path with legacy fallback."""
    primary = ROOT / ".vscode" / "launch.json"
    if primary.exists():
        return primary
    fallback = ROOT / "launch.json"
    if fallback.exists():
        return fallback
    return primary


def resolve_encpass_path() -> Path:
    """Resolve encpass.sh path for both legacy and packaged Linux layouts."""
    primary = ROOT / "scripts" / "encpass.sh"
    if primary.exists():
        return primary
    fallback = ROOT / "encpass.sh"
    if fallback.exists():
        return fallback
    return primary


PLATFORM_PATHS = load_platform_paths(root_dir=ROOT)
PROJECTS_DIR = PLATFORM_PATHS["PROJECTS_DIR"]
ENTERPRISE_LOCATION = PLATFORM_PATHS["ENTERPRISE_LOCATION"]
UPGRADE_UTIL_LOCATION = PLATFORM_PATHS["UPGRADE_UTIL_LOCATION"]


def ensure_workspace_layout() -> None:
    """Create required base directories lazily if they are missing."""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def run(
    cmd: list[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    capture_output: bool = False,
    env: Optional[dict[str, str]] = None,
    stdin: Any = None,
) -> subprocess.CompletedProcess:
    """Run a subprocess command using platform-specific behavior."""
    return platform_run(cmd, cwd=cwd, check=check, capture_output=capture_output, env=env, stdin=stdin)


def detect_compose_base() -> list[str]:
    """Detect whether Docker Compose should use plugin or legacy binary."""
    docker_path = shutil.which("docker")
    if docker_path:
        test = run([docker_path, "compose", "version"], capture_output=True, check=False)
        if test.returncode == 0:
            return [docker_path, "compose"]
    docker_compose_path = shutil.which("docker-compose")
    if docker_compose_path:
        return [docker_compose_path]
    raise RuntimeError("Neither 'docker compose' nor 'docker-compose' is available in PATH.")


COMPOSE_BASE = detect_compose_base()


def run_compose(project_path: Path, compose_args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a docker compose command inside the selected project directory."""
    return run(COMPOSE_BASE + compose_args, cwd=project_path, check=check)


def fetch_odoo_docker_tags(page_size: int = 100) -> list[dict[str, str | int | None]]:
    """Fetch Odoo tags from Docker Hub and return selected fields."""
    url = f"https://hub.docker.com/v2/repositories/library/odoo/tags?page_size={page_size}"
    with urlopen(url, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    results = payload.get("results", [])
    return [
        {
            "name": item.get("name"),
            "last_updated": item.get("last_updated"),
            "full_size": item.get("full_size"),
        }
        for item in results
    ]


def fetch_psql_docker_tags(page_size: int = 100) -> list[dict[str, str | int | None]]:
    """Fetch PostgreSQL tags from Docker Hub and return selected fields."""
    url = f"https://hub.docker.com/v2/repositories/library/postgres/tags?page_size={page_size}"
    with urlopen(url, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    results = payload.get("results", [])
    return [
        {
            "name": item.get("name"),
            "last_updated": item.get("last_updated"),
            "full_size": item.get("full_size"),
        }
        for item in results
    ]


def read_text(path: Path) -> str:
    """Read UTF-8 text content from a file."""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text content to a file."""
    path.write_text(content, encoding="utf-8")


def write_text_lf(path: Path, content: str) -> None:
    """Write UTF-8 text content using LF line endings."""
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def normalize_to_lf(path: Path) -> None:
    """Normalize a text file to LF line endings."""
    content = read_text(path)
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    write_text_lf(path, content)


def replace_line(content: str, key: str, value: str) -> str:
    """Replace a KEY=value line in env-like text content."""
    pattern = rf"^{re.escape(key)}=.*$"
    replacement = f"{key}={value}"
    return re.sub(pattern, lambda _match: replacement, content, flags=re.MULTILINE)


def customize_env(project_name: str, project_fullpath: Path, odoo_ver: str, psql_ver: str) -> None:
    """Populate .env template with values for the current project."""
    content = read_text(ENV_FILE)
    enterprise_location = to_compose_path(ENTERPRISE_LOCATION / odoo_ver)
    upgrade_util_location = to_compose_path(UPGRADE_UTIL_LOCATION)
    project_location = to_compose_path(project_fullpath)
    content = replace_line(content, "PROJECT_NAME", project_name)
    content = replace_line(content, "ENTERPRISE_LOCATION", enterprise_location)
    content = replace_line(content, "UPGRADE_UTIL_LOCATION", upgrade_util_location)
    content = replace_line(content, "ODOO_VER", odoo_ver)
    content = replace_line(content, "ODOO_REVISION", ODOO_REVISION)
    content = replace_line(content, "PSQL_VER", psql_ver)
    content = replace_line(content, "ODOO_CONT_NAME", f"{project_name}-web")
    content = replace_line(content, "PSQL_CONT_NAME", f"{project_name}-db")
    content = replace_line(content, "SMTP_CONT_NAME", f"{project_name}-smtp")
    content = replace_line(content, "PROJECT_LOCATION", project_location)
    write_text(ENV_FILE, content)
    print()
    print(content)


def standarize_env() -> None:
    """Restore .env template values to defaults."""
    content = read_text(ENV_FILE)
    content = replace_line(content, "PROJECT_NAME", "TEST_PROJECT")
    content = replace_line(content, "ENTERPRISE_LOCATION", "TEST_ENTERPRISE_LOCATION")
    content = replace_line(content, "UPGRADE_UTIL_LOCATION", "TEST_UTIL_LOCATION")
    content = replace_line(content, "ODOO_VER", "15.0")
    content = replace_line(content, "ODOO_REVISION", "")
    content = replace_line(content, "PSQL_VER", "13")
    content = replace_line(content, "ODOO_CONT_NAME", "ODOO_TEMP_CONT ")
    content = replace_line(content, "PSQL_CONT_NAME", "PSQL_TEMP_CONT ")
    content = replace_line(content, "SMTP_CONT_NAME", "SMTP_TEMP_CONT ")
    content = replace_line(content, "PROJECT_LOCATION", "TEST_LOCATION ")
    write_text(ENV_FILE, content)


def get_secret(secret_name: str) -> str:
    """Resolve a secret using platform-specific storage backends."""
    if IS_WINDOWS:
        return platform_get_secret(secret_name, WINDOWS_SECRET_DIR)
    return platform_get_secret(secret_name, resolve_encpass_path())


def compose_exec_with_fallback(project_fullpath: Path, primary: list[str], fallback: list[str]) -> None:
    """Run compose command and retry with fallback args on failure."""
    result = run_compose(project_fullpath, primary, check=False)
    if result.returncode != 0:
        run_compose(project_fullpath, fallback, check=True)


def addons_link_compose(addons_url: str) -> str:
    """Validate addons URL and build authenticated clone URL when needed."""
    if "github.com" not in addons_url and not addons_url.startswith("git@github.com"):
        display_help("Currently only github URLs accepted")
    if addons_url.startswith("https://"):
        trimmed = addons_url[8:]
        token = get_secret("github_addons_token")
        return f"https://{token}@{trimmed}"
    if addons_url.startswith("git@github.com"):
        return addons_url
    display_help("Currently only HTTPS/SSH URLs are accepted")
    raise SystemExit(2)


def enterprise_link_compose() -> str:
    """Build enterprise repository clone URL with token authentication."""
    token = get_secret("github_enterprise_token")
    return f"https://{token}@github.com/{ODOO_GITHUB_NAME}/{ODOO_ENTERPRISE_REPOSITORY}.git"


def clone_addons(project_fullpath: Path, addons_clone_url: Optional[str], branch_name: Optional[str]) -> None:
    """Clone addons repository or create placeholder requirements file."""
    if addons_clone_url:
        cmd = ["git", "-C", str(project_fullpath), "clone"]
        if branch_name:
            cmd.extend(["--branch", branch_name])
        cmd.append(addons_clone_url)
        cmd.append("addons")
        run(cmd)
    else:
        (project_fullpath / "addons" / "requirements.txt").touch(exist_ok=True)


def clone_enterprise(odoo_ver: str, install_enterprise_modules: bool) -> None:
    """Clone or update enterprise repository for selected Odoo version."""
    if not install_enterprise_modules:
        return
    enterprise_clone_url = enterprise_link_compose()
    target = ENTERPRISE_LOCATION / odoo_ver

    def clone_fresh() -> None:
        """Clone enterprise repository into target directory from scratch."""
        target.mkdir(parents=True, exist_ok=True)
        run([
            "git",
            "-C",
            str(target),
            "clone",
            "--depth",
            "1",
            "--branch",
            odoo_ver,
            enterprise_clone_url,
            ".",
        ])

    if not target.exists():
        clone_fresh()
        return

    if (target / ".git").exists():
        run(["git", "-C", str(target), "pull", "--ff-only"])
        return

    has_files = any(target.iterdir())
    if has_files:
        eprint(f"enterprise/{odoo_ver} exists and is not a git repository. Using existing files.")
    else:
        clone_fresh()


def get_upgrade_util() -> None:
    """Clone or update the upgrade-util repository."""
    def clone_fresh() -> None:
        """Clone upgrade-util repository into configured location from scratch."""
        UPGRADE_UTIL_LOCATION.mkdir(parents=True, exist_ok=True)
        run(["git", "-C", str(UPGRADE_UTIL_LOCATION), "clone", "--depth", "1", UPGRADE_UTIL_REPOSITORY, "."])

    if not UPGRADE_UTIL_LOCATION.exists():
        clone_fresh()
        return

    if not (UPGRADE_UTIL_LOCATION / ".git").exists():
        eprint("upgrade-util exists but is not a git repository. Recreating...")
        shutil.rmtree(UPGRADE_UTIL_LOCATION, ignore_errors=True)
        clone_fresh()
        return

    pull_result = run(["git", "-C", str(UPGRADE_UTIL_LOCATION), "pull", "--ff-only"], check=False)
    if pull_result.returncode == 0:
        return

    eprint("upgrade-util pull failed. Re-cloning repository...")
    shutil.rmtree(UPGRADE_UTIL_LOCATION, ignore_errors=True)
    clone_fresh()


def _make_tree_writable(path: Path) -> None:
    """Try to make a directory tree writable before deletion."""
    if not path.exists():
        return
    for root, dirs, files in os.walk(path, topdown=False):
        root_path = Path(root)
        for file_name in files:
            try:
                os.chmod(root_path / file_name, 0o666)
            except OSError:
                pass
        for dir_name in dirs:
            try:
                os.chmod(root_path / dir_name, 0o777)
            except OSError:
                pass
    try:
        os.chmod(path, 0o777)
    except OSError:
        pass


def _try_delete_with_admin(project_fullpath: Path) -> None:
    """Attempt privileged deletion using platform-specific helper."""
    platform_try_delete_with_admin(project_fullpath)


def delete_project(project_fullpath: Path) -> None:
    """Stop compose stack with volumes and remove project directory."""
    print("DELETING PROJECT AND VOLUMES")
    run_compose(project_fullpath, ["down", "-v"], check=False)
    print("DELETING PROJECT DIRECTORY")
    try:
        shutil.rmtree(project_fullpath)
    except OSError as first_error:
        print(f"Standard delete failed: {first_error}")
        _make_tree_writable(project_fullpath)
        try:
            shutil.rmtree(project_fullpath)
        except OSError as second_error:
            print(f"Retry delete failed: {second_error}")
            print("TRYING DELETE WITH ADMIN PRIVILEGES")
            _try_delete_with_admin(project_fullpath)

    if project_fullpath.exists():
        raise RuntimeError(f"Failed to delete project directory: {project_fullpath}")


def run_with_upgrade(project_fullpath: Path) -> None:
    """Run Odoo container in upgrade-util mode."""
    get_upgrade_util()
    run_compose(project_fullpath, ["stop", "web"], check=False)
    run_compose(
        project_fullpath,
        [
            "run",
            "--rm",
            "--name=web_upgrade",
            "web",
            "/usr/bin/python3",
            "-m",
            "debugpy",
            "--listen",
            "0.0.0.0:5858",
            "/usr/bin/odoo",
            "--db_user=odoo",
            "--db_host=db",
            "--db_password=odoo",
            "-c",
            "/etc/odoo/odoo.conf",
            "--upgrade-path=/mnt/upgrade-util/src",
            "--dev",
            "reload",
        ],
    )


def project_start(project_name: str, project_fullpath: Path, with_upgrade: bool) -> None:
    """Start or restart project services and optionally run upgrade mode."""
    result = run(["docker", "ps"], capture_output=True)
    running = result.stdout
    if project_name in running:
        print(f"RESTARTING {project_name}")
        if with_upgrade:
            run_with_upgrade(project_fullpath)
        else:
            run_compose(project_fullpath, ["restart"], check=False)
    else:
        print("UPDATE GIT REPO")
        addons_dir = project_fullpath / "addons"
        if (addons_dir / ".git").exists():
            run(["git", "-C", str(addons_dir), "stash"], check=False)
            run(["git", "-C", str(addons_dir), "pull"], check=False)
            run(["git", "-C", str(addons_dir), "stash", "pop"], check=False)
        print(f"STARTING {project_name}")
        if with_upgrade:
            run_with_upgrade(project_fullpath)
        else:
            run_compose(project_fullpath, ["start"], check=False)


def run_tests(project_fullpath: Path, db: Optional[str], module: Optional[str], test_tags: Optional[str]) -> None:
    """Run Odoo test suite by module or test tags."""
    if not db:
        display_help("You need to specify database to run tests on. Use --db.")
    if module:
        print(f"START ODOO UNIT TESTS ON ({db}) DB FOR ({module}) MODULE")
        run_compose(project_fullpath, ["run", "--rm", "web", "--test-enable",
                    "--log-level=test", "--stop-after-init", "-d", db, "-i", module])
    elif test_tags:
        print(f"START ODOO UNIT TESTS ON ({db}) DB FOR ({test_tags}) TAGS")
        run_compose(project_fullpath, ["run", "--rm", "web", "--test-enable",
                    "--log-level=test", "--stop-after-init", "-d", db, f"--test-tags={test_tags}"])
    else:
        display_help("You need to specify module or tags. Use -m or --tags")


def rebuild_container(project_fullpath: Path, container_name: Optional[str]) -> None:
    """Rebuild a single container in the compose project."""
    if not container_name:
        display_help("You need to specify container name that you want to rebuild. Use -r or --rebuild")
    run_compose(project_fullpath, ["up", "-d", "--no-deps", "--force-recreate", "--build", container_name])


def install_module(project_fullpath: Path, db: Optional[str], module: Optional[str]) -> None:
    """Install an Odoo module in a selected database."""
    if not module:
        display_help("You need to specify module name that you want to install. Use --install with -m")
    if not db:
        display_help("You need to specify database. Use --db")
    run_compose(project_fullpath, ["exec", "web", "/usr/bin/odoo", "--db_user=odoo", "--db_host=db",
                "--db_password=odoo", "-c", "/etc/odoo/odoo.conf", "--stop-after-init", "-d", db, "-i", module])


def pip_install(project_fullpath: Path, pip_module: Optional[str]) -> None:
    """Install a Python package inside the running web container."""
    if not pip_module:
        display_help("You need to specify module name that you want to install. Use --pip_install")
    compose_exec_with_fallback(
        project_fullpath,
        ["exec", "web", "python3", "-m", "pip", "install", pip_module],
        ["exec", "web", "python3", "-m", "pip", "install", "--break-system-packages", pip_module],
    )


def project_exist(args: argparse.Namespace, project_fullpath: Path) -> None:
    """Execute action flow for an existing project."""
    entrypoint_path = project_fullpath / "entrypoint.sh"
    if entrypoint_path.exists():
        normalize_to_lf(entrypoint_path)

    normalize_project_env_paths(project_fullpath)

    if args.delete:
        delete_project(project_fullpath)
        raise SystemExit(1)
    if args.test:
        run_tests(project_fullpath, args.db, args.module, args.tags)
    elif args.rebuild:
        rebuild_container(project_fullpath, args.rebuild)
    elif args.install:
        install_module(project_fullpath, args.db, args.module)
    elif args.pip_install:
        pip_install(project_fullpath, args.pip_install)
    else:
        project_start(args.name, project_fullpath, args.upgrade)


def create_project_directories(project_fullpath: Path) -> None:
    """Create base directory structure for a new project."""
    (project_fullpath / "addons").mkdir(parents=True, exist_ok=True)
    (project_fullpath / "config").mkdir(parents=True, exist_ok=True)
    (project_fullpath / ".vscode").mkdir(parents=True, exist_ok=True)


def copy_required_files(project_fullpath: Path) -> None:
    """Copy template files needed to bootstrap a project."""
    shutil.copy2(DOCKERFILE, project_fullpath / "Dockerfile")
    shutil.copy2(DOCKERIGNORE, project_fullpath / ".dockerignore")
    shutil.copy2(DOCKER_COMPOSE, project_fullpath / "docker-compose.yml")
    shutil.copy2(ENTRYPOINT, project_fullpath / "entrypoint.sh")
    normalize_to_lf(project_fullpath / "entrypoint.sh")
    launch_json_path = resolve_launch_json_path()
    if not launch_json_path.exists():
        raise RuntimeError(
            "Missing launch.json template. Expected '/opt/smartodoo/.vscode/launch.json' "
            "or '/opt/smartodoo/launch.json'."
        )
    shutil.copy2(launch_json_path, project_fullpath / ".vscode" / "launch.json")

    odoo_conf_path = resolve_odoo_conf_path(root_dir=ROOT)
    if odoo_conf_path.exists():
        shutil.copy2(odoo_conf_path, project_fullpath / "config" / "odoo.conf")


def adjust_project_odoo_conf(project_fullpath: Path, install_enterprise_modules: bool) -> None:
    """Adjust copied odoo.conf based on enterprise installation mode."""
    conf_path = project_fullpath / "config" / "odoo.conf"
    if install_enterprise_modules or not conf_path.exists():
        return

    content = read_text(conf_path)
    pattern = r"^(addons_path\s*=\s*)(.+)$"

    def replace_addons_path(match: re.Match) -> str:
        """Remove enterprise mount path from addons_path when enterprise is disabled."""
        prefix = match.group(1)
        paths = [part.strip() for part in match.group(2).split(",") if part.strip()]
        filtered = [path for path in paths if path != "/mnt/enterprise"]
        return f"{prefix}{','.join(filtered)}"

    updated = re.sub(pattern, replace_addons_path, content, flags=re.MULTILINE)
    write_text(conf_path, updated)


def create_project(args: argparse.Namespace, project_fullpath: Path, addons_clone_url: Optional[str]) -> None:
    """Initialize and start a new Docker project workspace."""
    print("CREATE PROJECT")
    customize_env(args.name, project_fullpath, args.odoo, args.psql)
    copy_required_files(project_fullpath)
    adjust_project_odoo_conf(project_fullpath, args.enterprise)
    clone_addons(project_fullpath, addons_clone_url, args.branch)
    clone_enterprise(args.odoo, args.enterprise)
    if args.upgrade:
        get_upgrade_util()
    shutil.copy2(ENV_FILE, project_fullpath / ".env")
    run_compose(project_fullpath, ["pull", "web"], check=False)
    run_compose(project_fullpath, ["pull", "db"], check=False)
    run_compose(project_fullpath, ["pull", "smtp4dev"], check=False)
    run_compose(project_fullpath, ["-p", args.name, "up", "--detach", "--build"], check=False)
    standarize_env()
    if not IS_WINDOWS:
        os.chmod(project_fullpath / "config", 0o777)
        conf_path = project_fullpath / "config" / "odoo.conf"
        if conf_path.exists():
            os.chmod(conf_path, 0o666)


def check_odoo_version(value: str):
    """Normalize Odoo version: add .0 for digits and extract revision suffix."""
    global ODOO_VER, ODOO_REVISION
    if '-' in value:
        version, revision = value.split('-', 1)
        if re.match(r'^\d+$', version):
            version = f"{version}.0"
        ODOO_VER = version
        ODOO_REVISION = f"-{revision}"
    else:
        if re.match(r'^\d+$', value):
            ODOO_VER = f"{value}.0"
        else:
            ODOO_VER = value
        ODOO_REVISION = ""


def check_psql_version(value: str) -> str:
    """Normalize PostgreSQL version by removing trailing .0."""
    return value[:-2] if value.endswith(".0") else value


def display_help(error: Optional[str] = None) -> None:
    """Print usage information and exit with code 2."""
    if error:
        eprint(error)
    print("Usage: python3 smartodoo.py -n {project_name} [parameters...]")
    print()
    print("Examples:")
    print("  python3 smartodoo.py -n Test_Project -e -o 14.0 -p 12")
    print("  python3 smartodoo.py -n Test_Project")
    print("  python3 smartodoo.py -n Test_Project -t --db=test_db -m my_module")
    print("  smartodoo.py -n Test_Project -t --db=test_db --tags=my_tag,my_tag2")
    print()
    print("  -n, --name                 (required) project name")
    print("  -o, --odoo                 Odoo version")
    print("  -p, --psql                 PostgreSQL version")
    print("  -a, --addons               Addons repository URL")
    print("  -b, --branch               Addons repository branch")
    print("  -e, --enterprise           Install enterprise modules")
    print("  -d, --delete               Delete project if exists")
    print("      --pip_install          Install pip module on web container")
    print("      --install              Install module (-m, --db required)")
    print("  -u, --upgrade              Run with upgrade-util")
    print("  -r, --rebuild              Rebuild selected container")
    print("  -t, --test                 Run tests")
    print("  -m, --module               Module to test/install")
    print("      --tags                 Tags to test")
    print("      --db                   Database for tests/install")
    print("      --list_odoo_tags       Print Odoo Docker tags as JSON")
    print("      --list_psql_tags       Print PostgreSQL Docker tags as JSON")
    raise SystemExit(2)


def parse_args() -> argparse.Namespace:
    """Parse and validate CLI arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-n", "--name")
    parser.add_argument("-o", "--odoo", default=ODOO_VER)
    parser.add_argument("-p", "--psql", default=PSQL_VER)
    parser.add_argument("-a", "--addons")
    parser.add_argument("-b", "--branch")
    parser.add_argument("-e", "--enterprise", action="store_true")
    parser.add_argument("-d", "--delete", action="store_true")
    parser.add_argument("-u", "--upgrade", action="store_true")
    parser.add_argument("-t", "--test", action="store_true")
    parser.add_argument("-m", "--module")
    parser.add_argument("-r", "--rebuild")
    parser.add_argument("--pip_install")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--db")
    parser.add_argument("--tags")
    parser.add_argument("--list_odoo_tags", action="store_true")
    parser.add_argument("--list_psql_tags", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args()
    if args.help:
        display_help()
    if args.list_odoo_tags or args.list_psql_tags:
        return args
    if not args.name:
        display_help("ERROR Need to specify project name.")
    check_odoo_version(args.odoo)
    args.odoo = ODOO_VER
    args.psql = check_psql_version(args.psql)
    return args


def main() -> None:
    """Entry point for project lifecycle orchestration."""
    args = parse_args()

    if args.list_odoo_tags:
        print(json.dumps(fetch_odoo_docker_tags(page_size=100), ensure_ascii=False))
        return

    if args.list_psql_tags:
        print(json.dumps(fetch_psql_docker_tags(page_size=100), ensure_ascii=False))
        return

    addons_clone_url = addons_link_compose(args.addons) if args.addons else None

    ensure_workspace_layout()
    project_base = PROJECTS_DIR

    project_fullpath = project_base / args.name
    if project_fullpath.exists():
        project_exist(args, project_fullpath)
    elif args.delete:
        print("PROJECT DOESN'T EXIST")
        raise SystemExit(1)
    else:
        create_project_directories(project_fullpath)
        create_project(args, project_fullpath, addons_clone_url)


if __name__ == "__main__":
    main()
