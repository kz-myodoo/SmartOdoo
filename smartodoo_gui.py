#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox, ttk


class DockerStartUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SmartOdoo: GUI")
        self.geometry("980x680")
        self.minsize(980, 680)

        self.normal_font = tkfont.nametofont("TkDefaultFont").copy()
        self.bold_font = tkfont.nametofont("TkDefaultFont").copy()
        self.bold_font.configure(weight="bold")

        self.script_path = Path(__file__).resolve().parent / "smartodoo.py"
        self.process: subprocess.Popen[str] | None = None
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.branch_fetch_after_id: str | None = None
        self.rebuild_fetch_after_id: str | None = None
        self.last_branch_source_url = ""
        self.last_rebuild_source_project = ""

        self._build_variables()
        self._build_layout()
        self._toggle_action_fields()
        self._load_odoo_versions_async()
        self._load_psql_versions_async()
        self.after(120, self._drain_output)

    def _build_variables(self) -> None:
        self.name_var = tk.StringVar()
        self.odoo_var = tk.StringVar(value="19.0")
        self.psql_var = tk.StringVar(value="16")
        self.addons_var = tk.StringVar()
        self.branch_var = tk.StringVar()
        self.enterprise_var = tk.BooleanVar(value=False)
        self.upgrade_var = tk.BooleanVar(value=False)

        self.action_var = tk.StringVar(value="start/create")
        self.db_var = tk.StringVar()
        self.module_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.rebuild_var = tk.StringVar()
        self.pip_var = tk.StringVar()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Frame(self, padding=12)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text="SmartOdoo: GUI", font=("Segoe UI", 14, "bold"))
        title.grid(row=0, column=0, sticky="w")

        form = ttk.LabelFrame(self, text="Parameters", padding=12)
        form.grid(row=1, column=0, sticky="nsew", padx=12)
        for col in range(4):
            form.columnconfigure(col, weight=1)

        self.action_label = ttk.Label(form, text="Action")
        self.action_label.grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.action_combo = ttk.Combobox(
            form,
            textvariable=self.action_var,
            values=["start/create", "delete", "test", "rebuild", "install", "pip_install"],
            state="readonly",
        )
        self.action_combo.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.action_combo.bind("<<ComboboxSelected>>", lambda _event: self._toggle_action_fields())

        self.odoo_label = ttk.Label(form, text="Odoo version")
        self.odoo_label.grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.odoo_combo = ttk.Combobox(form, textvariable=self.odoo_var, values=["19.0"], state="normal")
        self.odoo_combo.grid(row=0, column=3, sticky="ew", padx=4, pady=4)

        self.project_name_label = ttk.Label(form, text="Project name")
        self.project_name_label.grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.project_name_entry = ttk.Entry(form, textvariable=self.name_var)
        self.project_name_entry.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        self.psql_label = ttk.Label(form, text="Postgres version")
        self.psql_label.grid(row=1, column=2, sticky="w", padx=4, pady=4)
        self.psql_combo = ttk.Combobox(form, textvariable=self.psql_var, values=["16"], state="normal")
        self.psql_combo.grid(row=1, column=3, sticky="ew", padx=4, pady=4)

        self.addons_label = ttk.Label(form, text="Addons URL")
        self.addons_label.grid(row=2, column=0, sticky="w", padx=4, pady=4)
        self.addons_entry = ttk.Entry(form, textvariable=self.addons_var)
        self.addons_entry.grid(row=2, column=1, sticky="ew", padx=4, pady=4)

        self.branch_label = ttk.Label(form, text="Addons branch")
        self.branch_label.grid(row=2, column=2, sticky="w", padx=4, pady=4)
        self.branch_combo = ttk.Combobox(form, textvariable=self.branch_var, values=[], state="normal")
        self.branch_combo.grid(row=2, column=3, sticky="ew", padx=4, pady=4)

        self.enterprise_check = ttk.Checkbutton(form, text="Enterprise", variable=self.enterprise_var)
        self.enterprise_check.grid(row=3, column=0, sticky="w", padx=4, pady=4)
        self.upgrade_check = ttk.Checkbutton(form, text="Upgrade mode", variable=self.upgrade_var)
        self.upgrade_check.grid(row=3, column=1, sticky="w", padx=4, pady=4)

        self.db_label = ttk.Label(form, text="DB")
        self.db_entry = ttk.Entry(form, textvariable=self.db_var)
        self.module_label = ttk.Label(form, text="Module")
        self.module_entry = ttk.Entry(form, textvariable=self.module_var)
        self.tags_label = ttk.Label(form, text="Tags")
        self.tags_entry = ttk.Entry(form, textvariable=self.tags_var)
        self.rebuild_label = ttk.Label(form, text="Container to rebuild")
        self.rebuild_combo = ttk.Combobox(form, textvariable=self.rebuild_var, values=[], state="readonly")
        self.pip_label = ttk.Label(form, text="Pip package")
        self.pip_entry = ttk.Entry(form, textvariable=self.pip_var)

        self.db_label.grid(row=4, column=0, sticky="w", padx=4, pady=4)
        self.db_entry.grid(row=4, column=1, sticky="ew", padx=4, pady=4)
        self.module_label.grid(row=4, column=2, sticky="w", padx=4, pady=4)
        self.module_entry.grid(row=4, column=3, sticky="ew", padx=4, pady=4)

        self.tags_label.grid(row=5, column=0, sticky="w", padx=4, pady=4)
        self.tags_entry.grid(row=5, column=1, sticky="ew", padx=4, pady=4)
        self.rebuild_label.grid(row=5, column=2, sticky="w", padx=4, pady=4)
        self.rebuild_combo.grid(row=5, column=3, sticky="ew", padx=4, pady=4)

        self.pip_label.grid(row=6, column=0, sticky="w", padx=4, pady=4)
        self.pip_entry.grid(row=6, column=1, sticky="ew", padx=4, pady=4)

        actions = ttk.Frame(self, padding=(12, 8, 12, 8))
        actions.grid(row=2, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)

        self.command_preview_var = tk.StringVar(value="Command: ")
        self.command_preview_label = ttk.Label(actions, textvariable=self.command_preview_var, anchor="w")
        self.command_preview_label.grid(row=0, column=0, sticky="ew")
        self.command_preview_label.configure(wraplength=620)

        buttons = ttk.Frame(actions)
        buttons.grid(row=0, column=1, sticky="e")
        self.run_btn = ttk.Button(buttons, text="Run", command=self._run)
        self.run_btn.grid(row=0, column=0, padx=4, pady=2)
        self.copy_btn = ttk.Button(buttons, text="Copy command", command=self._copy_command)
        self.copy_btn.grid(row=0, column=1, padx=4, pady=2)
        self.clear_btn = ttk.Button(buttons, text="Clear logs", command=self._clear_logs)
        self.clear_btn.grid(row=1, column=0, padx=4, pady=2)
        self.copy_logs_btn = ttk.Button(buttons, text="Copy logs", command=self._copy_logs)
        self.copy_logs_btn.grid(row=1, column=1, padx=4, pady=2)

        output_frame = ttk.LabelFrame(self, text="Logs", padding=8)
        output_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_text = tk.Text(output_frame, wrap="word", height=18)
        self.output_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.configure(yscrollcommand=scrollbar.set)

        for var in (
            self.name_var,
            self.odoo_var,
            self.psql_var,
            self.addons_var,
            self.branch_var,
            self.enterprise_var,
            self.upgrade_var,
            self.action_var,
            self.db_var,
            self.module_var,
            self.tags_var,
            self.rebuild_var,
            self.pip_var,
        ):
            var.trace_add("write", lambda *_args: self._update_command_preview())

        self.addons_var.trace_add("write", lambda *_args: self._schedule_addons_branch_refresh())
        self.name_var.trace_add("write", lambda *_args: self._schedule_rebuild_containers_refresh())
        self.action_var.trace_add("write", lambda *_args: self._schedule_rebuild_containers_refresh())

        self._update_command_preview()

    def _toggle_action_fields(self) -> None:
        action = self.action_var.get()

        show_create_fields = action == "start/create"
        show_upgrade = action in {"start/create", "install"}

        show_db = action in {"test", "install"}
        show_module = action in {"test", "install"}
        show_tags = action == "test"
        show_rebuild = action == "rebuild"
        show_pip = action == "pip_install"

        self._set_widget_visible(self.odoo_label, self.odoo_combo, show_create_fields)
        self._set_widget_visible(self.psql_label, self.psql_combo, show_create_fields)
        self._set_widget_visible(self.addons_label, self.addons_entry, show_create_fields)
        self._set_widget_visible(self.branch_label, self.branch_combo, show_create_fields)
        self._set_single_widget_visible(self.enterprise_check, show_create_fields)
        self._set_single_widget_visible(self.upgrade_check, show_upgrade)

        self._set_widget_visible(self.db_label, self.db_entry, show_db)
        self._set_widget_visible(self.module_label, self.module_entry, show_module)
        self._set_widget_visible(self.tags_label, self.tags_entry, show_tags)
        self._set_widget_visible(self.rebuild_label, self.rebuild_combo, show_rebuild)
        self._set_widget_visible(self.pip_label, self.pip_entry, show_pip)

        self._update_required_labels(action)

        if show_rebuild:
            self._schedule_rebuild_containers_refresh()

        self._update_command_preview()

    def _set_widget_visible(self, label: ttk.Label, entry: ttk.Entry, visible: bool) -> None:
        if visible:
            label.grid()
            entry.grid()
        else:
            label.grid_remove()
            entry.grid_remove()

    def _set_single_widget_visible(self, widget: ttk.Widget, visible: bool) -> None:
        if visible:
            widget.grid()
        else:
            widget.grid_remove()

    def _set_label_required(self, label: ttk.Label, required: bool) -> None:
        label.configure(font=self.bold_font if required else self.normal_font)

    def _update_required_labels(self, action: str) -> None:
        self._set_label_required(self.project_name_label, True)
        self._set_label_required(self.odoo_label, action == "start/create")
        self._set_label_required(self.psql_label, action == "start/create")
        self._set_label_required(self.db_label, action in {"test", "install"})
        self._set_label_required(self.module_label, action in {"test", "install"})
        self._set_label_required(self.tags_label, action == "test")
        self._set_label_required(self.rebuild_label, action == "rebuild")
        self._set_label_required(self.pip_label, action == "pip_install")

    def _schedule_addons_branch_refresh(self) -> None:
        addons_url = self.addons_var.get().strip()
        if self.branch_fetch_after_id:
            self.after_cancel(self.branch_fetch_after_id)
            self.branch_fetch_after_id = None

        if "github.com" not in addons_url:
            self.branch_combo.configure(values=[])
            self.last_branch_source_url = ""
            return

        self.branch_fetch_after_id = self.after(450, self._refresh_addons_branches_async)

    def _schedule_rebuild_containers_refresh(self) -> None:
        if self.rebuild_fetch_after_id:
            self.after_cancel(self.rebuild_fetch_after_id)
            self.rebuild_fetch_after_id = None

        if self.action_var.get() != "rebuild":
            return

        project_name = self.name_var.get().strip()
        if not project_name:
            self.rebuild_combo.configure(values=[])
            self.last_rebuild_source_project = ""
            return

        self.rebuild_fetch_after_id = self.after(350, self._refresh_rebuild_containers_async)

    def _refresh_rebuild_containers_async(self) -> None:
        self.rebuild_fetch_after_id = None
        project_name = self.name_var.get().strip()
        if self.action_var.get() != "rebuild" or not project_name:
            return
        if project_name == self.last_rebuild_source_project:
            return

        threading.Thread(target=self._fetch_rebuild_containers_worker, args=(project_name,), daemon=True).start()

    def _fetch_rebuild_containers_worker(self, project_name: str) -> None:
        project_path = self._resolve_project_path(project_name)
        compose_base = self._detect_compose_base()
        cmd = compose_base + ["config", "--services"]
        try:
            if not project_path.exists():
                self.after(0, lambda: self._apply_rebuild_containers(project_name, []))
                return

            result = subprocess.run(cmd, cwd=str(project_path), text=True, capture_output=True, check=False)
            if result.returncode != 0:
                stderr = result.stderr.strip() if result.stderr else "no details"
                raise RuntimeError(stderr)

            names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            self.after(0, lambda: self._apply_rebuild_containers(project_name, names))
        except Exception as exc:
            self.after(0, lambda: self._on_rebuild_containers_error(project_name, exc))

    def _detect_compose_base(self) -> list[str]:
        docker_path = shutil.which("docker")
        if docker_path:
            test = subprocess.run([docker_path, "compose", "version"], text=True, capture_output=True, check=False)
            if test.returncode == 0:
                return [docker_path, "compose"]

        docker_compose_path = shutil.which("docker-compose")
        if docker_compose_path:
            return [docker_compose_path]

        raise RuntimeError("Neither 'docker compose' nor 'docker-compose' is available in PATH.")

    def _resolve_project_path(self, project_name: str) -> Path:
        documents_dir = self._detect_documents_dir()
        candidates = [
            documents_dir / "DockerProjects",
            Path.home() / "Dokumenty" / "DockerProjects",
            Path.home() / "Documents" / "DockerProjects",
        ]
        if os.name == "nt":
            cwd_based = Path(str(Path.cwd()).replace("SmartOdoo", "DockerProjects"))
            candidates = [cwd_based, documents_dir / "DockerProjects"]

        unique_candidates: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(candidate)

        base_path = unique_candidates[0]
        for candidate in unique_candidates:
            if candidate.exists():
                base_path = candidate
                break
        return base_path / project_name

    def _detect_documents_dir(self) -> Path:
        if os.name == "nt":
            user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
            return user_profile / "Documents"

        xdg_documents_dir = os.environ.get("XDG_DOCUMENTS_DIR")
        if xdg_documents_dir:
            expanded = xdg_documents_dir.replace("$HOME", str(Path.home()))
            return Path(expanded).expanduser()

        xdg_user_dir_cmd = shutil.which("xdg-user-dir")
        if xdg_user_dir_cmd:
            detected = subprocess.run([xdg_user_dir_cmd, "DOCUMENTS"], text=True, capture_output=True, check=False)
            detected_path = detected.stdout.strip()
            if detected.returncode == 0 and detected_path:
                return Path(detected_path).expanduser()

        for fallback_name in ["Documents", "Dokumenty"]:
            fallback_dir = Path.home() / fallback_name
            if fallback_dir.exists():
                return fallback_dir

        return Path.home() / "Documents"

    def _apply_rebuild_containers(self, project_name: str, containers: list[str]) -> None:
        if project_name != self.name_var.get().strip():
            return
        self.last_rebuild_source_project = project_name
        unique_containers = list(dict.fromkeys(containers))
        self.rebuild_combo.configure(values=unique_containers)
        current = self.rebuild_var.get().strip()
        if current and current in unique_containers:
            self.rebuild_var.set(current)
        elif "web" in unique_containers:
            self.rebuild_var.set("web")
        elif unique_containers:
            self.rebuild_var.set(unique_containers[0])
        else:
            self.rebuild_var.set("")

    def _on_rebuild_containers_error(self, project_name: str, error: Exception) -> None:
        if project_name != self.name_var.get().strip():
            return
        self.rebuild_combo.configure(values=[])
        self.last_rebuild_source_project = ""
        self._append_output(f"Failed to fetch project containers for rebuild: {error}\n")

    def _refresh_addons_branches_async(self) -> None:
        self.branch_fetch_after_id = None
        addons_url = self.addons_var.get().strip()
        normalized = self._normalize_github_repo_url(addons_url)
        if not normalized:
            self.branch_combo.configure(values=[])
            self.last_branch_source_url = ""
            return
        if normalized == self.last_branch_source_url:
            return

        threading.Thread(target=self._fetch_addons_branches_worker, args=(normalized,), daemon=True).start()

    def _normalize_github_repo_url(self, addons_url: str) -> str:
        url = addons_url.strip()
        if not url or "github.com" not in url:
            return ""

        if url.startswith("git@github.com:"):
            repo_part = url[len("git@github.com:"):].strip("/")
            segments = [segment for segment in repo_part.split("/") if segment]
            if len(segments) < 2:
                return ""
            owner, repo = segments[0], segments[1]
            repo = repo[:-4] if repo.endswith(".git") else repo
            return f"git@github.com:{owner}/{repo}.git"

        if "/tree/" in url:
            url = url.split("/tree/", 1)[0]
        url = url.split("?", 1)[0].split("#", 1)[0].rstrip("/")
        if not url.startswith("http://") and not url.startswith("https://"):
            return ""

        parts = [segment for segment in url.split("/") if segment]
        if len(parts) < 5:
            return ""
        owner, repo = parts[3], parts[4]
        repo = repo[:-4] if repo.endswith(".git") else repo
        return f"https://github.com/{owner}/{repo}.git"

    def _fetch_addons_branches_worker(self, repo_url: str) -> None:
        try:
            env = dict(os.environ)
            env["GIT_TERMINAL_PROMPT"] = "0"
            result = subprocess.run(
                ["git", "ls-remote", "--heads", repo_url],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip() if result.stderr else "no details"
                raise RuntimeError(stderr)

            branches: list[str] = []
            for line in result.stdout.splitlines():
                if "\trefs/heads/" not in line:
                    continue
                branch = line.split("\trefs/heads/", 1)[1].strip()
                if branch:
                    branches.append(branch)

            unique_branches = sorted(set(branches))
            self.after(0, lambda: self._apply_addons_branches(repo_url, unique_branches))
        except Exception as exc:
            self.after(0, lambda: self._on_addons_branches_error(repo_url, exc))

    def _apply_addons_branches(self, repo_url: str, branches: list[str]) -> None:
        self.last_branch_source_url = repo_url
        self.branch_combo.configure(values=branches)
        current = self.branch_var.get().strip()
        if current and current in branches:
            self.branch_var.set(current)
        elif "main" in branches:
            self.branch_var.set("main")
        elif "master" in branches:
            self.branch_var.set("master")

    def _on_addons_branches_error(self, repo_url: str, error: Exception) -> None:
        if repo_url == self.last_branch_source_url:
            return
        self.branch_combo.configure(values=[])
        self._append_output(f"Failed to fetch addons branches: {error}\n")

    def _build_command(self, help_only: bool = False) -> list[str]:
        python_executable = sys.executable or "python"
        cmd = [python_executable, str(self.script_path)]

        if help_only:
            cmd.append("--help")
            return cmd

        project_name = self.name_var.get().strip()
        if not project_name:
            raise ValueError("'Project name' is required.")

        cmd.extend(["-n", project_name])

        action = self.action_var.get()

        if action == "start/create":
            odoo = self.odoo_var.get().strip()
            if odoo:
                cmd.extend(["-o", odoo])

            psql = self.psql_var.get().strip()
            if psql:
                cmd.extend(["-p", psql])

            addons = self.addons_var.get().strip()
            if addons:
                cmd.extend(["-a", addons])

            branch = self.branch_var.get().strip()
            if branch:
                cmd.extend(["-b", branch])

            if self.enterprise_var.get():
                cmd.append("-e")

            if self.upgrade_var.get():
                cmd.append("-u")

        elif action == "install":
            if self.upgrade_var.get():
                cmd.append("-u")

            db = self.db_var.get().strip()
            module = self.module_var.get().strip()
            if not db or not module:
                raise ValueError("Action 'install' requires DB and Module.")
            cmd.append("--install")
            cmd.extend(["--db", db, "-m", module])

        elif action == "delete":
            cmd.append("-d")

        elif action == "test":
            cmd.append("-t")
            db = self.db_var.get().strip()
            if not db:
                raise ValueError("Action 'test' requires DB.")
            cmd.extend(["--db", db])

            module = self.module_var.get().strip()
            tags = self.tags_var.get().strip()
            if not module and not tags:
                raise ValueError("Action 'test' requires Module or Tags.")
            if module:
                cmd.extend(["-m", module])
            if tags:
                cmd.extend(["--tags", tags])
        elif action == "rebuild":
            rebuild_target = self.rebuild_var.get().strip()
            if not rebuild_target:
                raise ValueError("Action 'rebuild' requires 'Container to rebuild'.")
            cmd.extend(["-r", rebuild_target])
        elif action == "pip_install":
            pip_pkg = self.pip_var.get().strip()
            if not pip_pkg:
                raise ValueError("Action 'pip_install' requires 'Pip package'.")
            cmd.extend(["--pip_install", pip_pkg])

        return cmd

    def _set_running_state(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.run_btn.configure(state=state)

    def _load_odoo_versions_async(self) -> None:
        threading.Thread(target=self._load_odoo_versions_worker, daemon=True).start()

    def _load_psql_versions_async(self) -> None:
        threading.Thread(target=self._load_psql_versions_worker, daemon=True).start()

    def _load_odoo_versions_worker(self) -> None:
        python_executable = sys.executable or "python"
        cmd = [python_executable, str(self.script_path), "--list_odoo_tags"]
        try:
            result = subprocess.run(cmd, text=True, capture_output=True, check=False)
            if result.returncode != 0:
                stderr = result.stderr.strip() if result.stderr else "no details"
                raise RuntimeError(f"{stderr}")

            tags = json.loads(result.stdout)
            if not isinstance(tags, list):
                raise ValueError("Invalid JSON response format.")

            versions: list[str] = []
            for tag in tags:
                if not isinstance(tag, dict):
                    continue
                name = str(tag.get("name", "")).strip()
                if name:
                    versions.append(name)

            unique_versions = list(dict.fromkeys(versions))
            if not unique_versions:
                unique_versions = ["19.0"]

            self.after(0, lambda: self._apply_odoo_versions(unique_versions))
        except Exception as exc:
            self.after(0, lambda: self._on_odoo_versions_error(exc))

    def _load_psql_versions_worker(self) -> None:
        python_executable = sys.executable or "python"
        cmd = [python_executable, str(self.script_path), "--list_psql_tags"]
        try:
            result = subprocess.run(cmd, text=True, capture_output=True, check=False)
            if result.returncode != 0:
                stderr = result.stderr.strip() if result.stderr else "no details"
                raise RuntimeError(f"{stderr}")

            tags = json.loads(result.stdout)
            if not isinstance(tags, list):
                raise ValueError("Invalid JSON response format.")

            versions: list[str] = []
            for tag in tags:
                if not isinstance(tag, dict):
                    continue
                name = str(tag.get("name", "")).strip()
                if name:
                    versions.append(name)

            unique_versions = list(dict.fromkeys(versions))
            if not unique_versions:
                unique_versions = ["16"]

            self.after(0, lambda: self._apply_psql_versions(unique_versions))
        except Exception as exc:
            self.after(0, lambda: self._on_psql_versions_error(exc))

    def _apply_odoo_versions(self, versions: list[str]) -> None:
        self.odoo_combo.configure(values=versions)
        current = self.odoo_var.get().strip()
        if current in versions:
            self.odoo_var.set(current)
        else:
            self.odoo_var.set(versions[0])
        self._append_output(f"Loaded Odoo versions: {', '.join(versions[:10])}\n")

    def _on_odoo_versions_error(self, error: Exception) -> None:
        self.odoo_combo.configure(values=["19.0"])
        self.odoo_var.set("19.0")
        self._append_output(f"Failed to fetch Odoo versions from script: {error}\n")

    def _apply_psql_versions(self, versions: list[str]) -> None:
        self.psql_combo.configure(values=versions)
        current = self.psql_var.get().strip()
        if current in versions:
            self.psql_var.set(current)
        else:
            self.psql_var.set(versions[0])
        self._append_output(f"Loaded Postgres versions: {', '.join(versions[:10])}\n")

    def _on_psql_versions_error(self, error: Exception) -> None:
        self.psql_combo.configure(values=["16"])
        self.psql_var.set("16")
        self._append_output(f"Failed to fetch Postgres versions from script: {error}\n")

    def _update_command_preview(self) -> None:
        try:
            rendered = self._build_rendered_command()
            if len(rendered) > 180:
                rendered = f"{rendered[:120]} ... {rendered[-50:]}"
            self.command_preview_var.set(f"Command: {rendered}")
        except ValueError as exc:
            self.command_preview_var.set(f"Command: validation error ({exc})")

    def _build_rendered_command(self) -> str:
        cmd = self._build_command(help_only=False)
        return " ".join(self._shell_quote(part) for part in cmd)

    def _shell_quote(self, text: str) -> str:
        if not text:
            return '""'
        if any(char.isspace() for char in text) or any(char in text for char in '"\''):
            return f'"{text.replace("\"", "\\\"")}"'
        return text

    def _run(self) -> None:
        if self.process and self.process.poll() is None:
            messagebox.showinfo("Process running", "Wait for the current process to finish.")
            return

        if not self.script_path.exists():
            messagebox.showerror("File missing", f"Not found: {self.script_path}")
            return

        try:
            cmd = self._build_command(help_only=False)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self._append_output("\n=== START ===\n")
        self._append_output("$ " + " ".join(self._shell_quote(part) for part in cmd) + "\n")
        self._spawn_process(cmd)

    def _copy_command(self) -> None:
        try:
            rendered = self._build_rendered_command()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.clipboard_clear()
        self.clipboard_append(rendered)
        self.update_idletasks()
        self._append_output("Copied command to clipboard.\n")

    def _copy_logs(self) -> None:
        logs = self.output_text.get("1.0", "end-1c")
        if not logs.strip():
            self._append_output("No logs to copy.\n")
            return

        self.clipboard_clear()
        self.clipboard_append(logs)
        self.update_idletasks()
        self._append_output("Copied logs to clipboard.\n")

    def _spawn_process(self, cmd: list[str]) -> None:
        self._set_running_state(True)
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        threading.Thread(target=self._read_process_output, daemon=True).start()

    def _read_process_output(self) -> None:
        if not self.process or not self.process.stdout:
            return

        for line in self.process.stdout:
            self.output_queue.put(line)

        return_code = self.process.wait()
        self.output_queue.put(f"\n=== EXIT CODE: {return_code} ===\n")
        self.output_queue.put("__PROCESS_DONE__")

    def _drain_output(self) -> None:
        try:
            while True:
                chunk = self.output_queue.get_nowait()
                if chunk == "__PROCESS_DONE__":
                    self._set_running_state(False)
                    self.process = None
                else:
                    self._append_output(chunk)
        except queue.Empty:
            pass

        self.after(120, self._drain_output)

    def _append_output(self, text: str) -> None:
        self.output_text.insert("end", text)
        self.output_text.see("end")

    def _clear_logs(self) -> None:
        self.output_text.delete("1.0", "end")


def main() -> None:
    app = DockerStartUI()
    app.mainloop()


if __name__ == "__main__":
    main()
