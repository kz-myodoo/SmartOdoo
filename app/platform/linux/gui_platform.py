from pathlib import Path
import shlex
import shutil
import subprocess


def open_settings_file(file_path: Path) -> None:
    """Open a settings file using Linux desktop opener."""
    if not file_path.exists():
        raise FileNotFoundError(f"Not found: {file_path}")

    xdg_open = shutil.which("xdg-open")
    if not xdg_open:
        raise RuntimeError("'xdg-open' is not available in PATH.")

    subprocess.Popen([xdg_open, str(file_path)])


def launch_installer(installer_path: Path) -> None:
    """Install .deb package in a terminal and show full dpkg output."""
    if not installer_path.exists():
        raise FileNotFoundError(f"Not found: {installer_path}")

    dpkg_path = shutil.which("dpkg")
    if not dpkg_path:
        raise RuntimeError("'dpkg' is not available in PATH.")

    if installer_path.suffix.lower() != ".deb":
        raise RuntimeError(f"Unsupported Linux installer format: {installer_path.name}")

    sudo_path = shutil.which("sudo")
    if sudo_path:
        install_cmd = (
            f"{shlex.quote(sudo_path)} {shlex.quote(dpkg_path)} -i {shlex.quote(str(installer_path))}"
        )
    else:
        pkexec_path = shutil.which("pkexec")
        if not pkexec_path:
            raise RuntimeError("No privilege escalation tool available. Install 'sudo' or 'pkexec'.")
        install_cmd = (
            f"{shlex.quote(pkexec_path)} {shlex.quote(dpkg_path)} -i {shlex.quote(str(installer_path))}"
        )

    script = (
        f"{install_cmd}; "
        "exit_code=$?; "
        "echo; "
        "echo Installation finished with exit code $exit_code.; "
        "read -r -p 'Press Enter to close...' _; "
        "exit $exit_code"
    )

    gnome_terminal = shutil.which("gnome-terminal")
    if gnome_terminal:
        subprocess.Popen([gnome_terminal, "--", "bash", "-lc", script])
        return

    konsole = shutil.which("konsole")
    if konsole:
        subprocess.Popen([konsole, "-e", "bash", "-lc", script])
        return

    x_terminal_emulator = shutil.which("x-terminal-emulator")
    if x_terminal_emulator:
        subprocess.Popen([x_terminal_emulator, "-e", "bash", "-lc", script])
        return

    xterm = shutil.which("xterm")
    if xterm:
        subprocess.Popen([xterm, "-e", "bash", "-lc", script])
        return

    raise RuntimeError(
        "No supported terminal emulator found. Install one of: gnome-terminal, konsole, x-terminal-emulator, xterm."
    )
