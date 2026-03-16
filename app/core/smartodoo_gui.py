#!/usr/bin/env python3

import pygubu
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.core.tools import (  # noqa: E402  # isort: skip
    load_platform_paths,
    resolve_config_json_path,
    resolve_odoo_conf_path,
)


IS_WINDOWS = sys.platform.startswith("win")
if IS_WINDOWS:
    from app.platform.windows.gui_platform import open_settings_file as platform_open_settings_file
    from app.platform.windows.process import windows_hidden_subprocess_kwargs as platform_subprocess_kwargs
else:
    from app.platform.linux.gui_platform import open_settings_file as platform_open_settings_file

    def platform_subprocess_kwargs() -> dict[str, object]:
        return {}


PLATFORM_PATHS = load_platform_paths(root_dir=ROOT)
PROJECTS_DIR = PLATFORM_PATHS["PROJECTS_DIR"]


class SmartOdooUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SmartOdoo: GUI")
        self.geometry("980x680")
        self.minsize(980, 680)

        self.normal_font = tkfont.nametofont("TkDefaultFont").copy()
        self.bold_font = tkfont.nametofont("TkDefaultFont").copy()
        self.bold_font.configure(weight="bold")

        self.script_path = SCRIPT_DIR / "smartodoo.py"
        self.view_path = SCRIPT_DIR / "ui" / "smartodoo_view.xml"
        self.config_json_path = resolve_config_json_path(root_dir=ROOT)
        self.odoo_conf_path = resolve_odoo_conf_path(root_dir=ROOT)
        self.projects_dir = PROJECTS_DIR

        self.process: subprocess.Popen[str] | None = None
        self.is_process_running = False
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.branch_fetch_after_id: str | None = None
        self.rebuild_fetch_after_id: str | None = None
        self.last_branch_source_url = ""
        self.last_rebuild_source_project = ""
        self._prompt_tail = ""
        self._awaiting_secret_input = False
        self._pending_secret_value: str | None = None

        self._build_variables()
        self._load_ui_settings()
        self._build_ui_from_xml()
        self._build_menu()
        self._apply_theme()
        self._connect_events()

        self._toggle_action_fields()
        self._refresh_project_names()
        self._load_docker_image_tags_async(
            list_flag="--list_odoo_tags",
            fallback="19.0",
            apply_callback=self._apply_odoo_versions,
            error_callback=self._on_odoo_versions_error,
        )
        self._load_docker_image_tags_async(
            list_flag="--list_psql_tags",
            fallback="16",
            apply_callback=self._apply_psql_versions,
            error_callback=self._on_psql_versions_error,
        )
        self.after(120, self._drain_output)

    def _platform_subprocess_kwargs(self) -> dict[str, object]:
        return platform_subprocess_kwargs()

    def _build_variables(self) -> None:
        self.name_var = tk.StringVar()
        self.odoo_var = tk.StringVar(value="19.0")
        self.psql_var = tk.StringVar(value="16")
        self.addons_var = tk.StringVar()
        self.branch_var = tk.StringVar()
        self.enterprise_var = tk.BooleanVar(value=True)
        self.upgrade_var = tk.BooleanVar(value=False)

        self.action_var = tk.StringVar(value="start/create")
        self.db_var = tk.StringVar()
        self.module_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.rebuild_var = tk.StringVar()
        self.pip_var = tk.StringVar()
        self.dark_mode_var = tk.BooleanVar(value=False)

        self.command_preview_var = tk.StringVar(value="Command: ")

    def _load_ui_settings(self) -> None:
        try:
            if not self.config_json_path.exists():
                return
            payload = json.loads(self.config_json_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return
            ui_settings = payload.get("ui", {})
            if not isinstance(ui_settings, dict):
                return
            dark_mode = ui_settings.get("dark_mode")
            if isinstance(dark_mode, bool):
                self.dark_mode_var.set(dark_mode)
        except (json.JSONDecodeError, OSError):
            return

    def _save_ui_settings(self) -> None:
        payload: dict[str, object]
        try:
            if self.config_json_path.exists():
                loaded = json.loads(self.config_json_path.read_text(encoding="utf-8"))
                payload = loaded if isinstance(loaded, dict) else {}
            else:
                payload = {}
        except (json.JSONDecodeError, OSError):
            payload = {}

        ui_settings = payload.get("ui")
        if not isinstance(ui_settings, dict):
            ui_settings = {}
            payload["ui"] = ui_settings

        ui_settings["dark_mode"] = bool(self.dark_mode_var.get())

        try:
            self.config_json_path.write_text(
                json.dumps(payload, indent=4, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            messagebox.showerror("Save settings failed", f"Cannot save UI settings: {exc}")

    def _build_ui_from_xml(self) -> None:
        if not self.view_path.exists():
            raise FileNotFoundError(f"View file not found: {self.view_path}")

        self.builder = pygubu.Builder()
        self.builder.add_from_file(str(self.view_path))
        self.mainframe = self.builder.get_object("mainframe", self)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(3, weight=1)

        self.form = self.builder.get_object("form", self)
        for col in range(4):
            self.form.columnconfigure(col, weight=1)

        self.actions = self.builder.get_object("actions", self)
        self.actions.columnconfigure(0, weight=1)

        self.output_frame = self.builder.get_object("output_frame", self)
        self.output_frame.columnconfigure(0, weight=1)
        self.output_frame.rowconfigure(0, weight=1)

        self.action_label: ttk.Label = self.builder.get_object("action_label", self)
        self.title_label: ttk.Label = self.builder.get_object("title_label", self)
        self.action_combo: ttk.Combobox = self.builder.get_object("action_combo", self)
        self.odoo_label: ttk.Label = self.builder.get_object("odoo_label", self)
        self.odoo_combo: ttk.Combobox = self.builder.get_object("odoo_combo", self)
        self.project_name_label: ttk.Label = self.builder.get_object("project_name_label", self)
        self.project_name_entry: ttk.Combobox = self.builder.get_object("project_name_entry", self)
        self.psql_label: ttk.Label = self.builder.get_object("psql_label", self)
        self.psql_combo: ttk.Combobox = self.builder.get_object("psql_combo", self)
        self.addons_label: ttk.Label = self.builder.get_object("addons_label", self)
        self.addons_entry: ttk.Entry = self.builder.get_object("addons_entry", self)
        self.branch_label: ttk.Label = self.builder.get_object("branch_label", self)
        self.branch_combo: ttk.Combobox = self.builder.get_object("branch_combo", self)
        self.enterprise_check: ttk.Checkbutton = self.builder.get_object("enterprise_check", self)
        self.upgrade_check: ttk.Checkbutton = self.builder.get_object("upgrade_check", self)

        self.db_label: ttk.Label = self.builder.get_object("db_label", self)
        self.db_entry: ttk.Entry = self.builder.get_object("db_entry", self)
        self.module_label: ttk.Label = self.builder.get_object("module_label", self)
        self.module_entry: ttk.Entry = self.builder.get_object("module_entry", self)
        self.tags_label: ttk.Label = self.builder.get_object("tags_label", self)
        self.tags_entry: ttk.Entry = self.builder.get_object("tags_entry", self)
        self.rebuild_label: ttk.Label = self.builder.get_object("rebuild_label", self)
        self.rebuild_combo: ttk.Combobox = self.builder.get_object("rebuild_combo", self)
        self.pip_label: ttk.Label = self.builder.get_object("pip_label", self)
        self.pip_entry: ttk.Entry = self.builder.get_object("pip_entry", self)

        self.run_btn: ttk.Button = self.builder.get_object("run_btn", self)
        self.copy_btn: ttk.Button = self.builder.get_object("copy_btn", self)
        self.clear_btn: ttk.Button = self.builder.get_object("clear_btn", self)
        self.copy_logs_btn: ttk.Button = self.builder.get_object("copy_logs_btn", self)

        self.command_preview_label: ttk.Label = self.builder.get_object("command_preview_label", self)
        self.output_text: tk.Text = self.builder.get_object("output_text", self)
        self.logs_scroll: ttk.Scrollbar = self.builder.get_object("logs_scroll", self)

        self.action_combo.configure(textvariable=self.action_var, values=[
            "start/create", "delete", "test", "rebuild", "install", "pip_install"], state="readonly")
        self.odoo_combo.configure(textvariable=self.odoo_var, values=["19.0"], state="normal")
        self.project_name_entry.configure(textvariable=self.name_var, values=[], state="normal",
                                          postcommand=self._refresh_project_names)
        self.psql_combo.configure(textvariable=self.psql_var, values=["16"], state="normal")
        self.addons_entry.configure(textvariable=self.addons_var)
        self.branch_combo.configure(textvariable=self.branch_var, values=[], state="normal")
        self.enterprise_check.configure(variable=self.enterprise_var)
        self.upgrade_check.configure(variable=self.upgrade_var)

        self.db_entry.configure(textvariable=self.db_var)
        self.module_entry.configure(textvariable=self.module_var)
        self.tags_entry.configure(textvariable=self.tags_var)
        self.rebuild_combo.configure(textvariable=self.rebuild_var, values=[], state="readonly")
        self.pip_entry.configure(textvariable=self.pip_var)

        self.command_preview_label.configure(textvariable=self.command_preview_var, wraplength=620)
        self.title_label.configure(font=("Segoe UI", 14, "bold"))
        self.logs_scroll.configure(command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=self.logs_scroll.set)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        settings_menu = tk.Menu(menubar, tearoff=False)
        settings_menu.add_checkbutton(
            label="Dark mode",
            variable=self.dark_mode_var,
            command=self._on_dark_mode_toggle,
        )
        settings_menu.add_separator()
        settings_menu.add_command(
            label="config.json",
            command=lambda: self._open_settings_file(self.config_json_path),
        )
        settings_menu.add_command(
            label="odoo.conf",
            command=lambda: self._open_settings_file(self.odoo_conf_path),
        )
        menubar.add_cascade(label="Settings", menu=settings_menu)
        self.config(menu=menubar)
        self.settings_menu = settings_menu

    def _on_dark_mode_toggle(self) -> None:
        self._apply_theme()
        self._save_ui_settings()

    def _apply_theme(self) -> None:
        dark_mode = self.dark_mode_var.get()

        if dark_mode:
            colors = {
                "bg": "#1f2437",
                "fg": "#e6e8ef",
                "input_bg": "#2a3044",
                "input_fg": "#f2f4fa",
                "input_border": "#4e566f",
                "panel_bg": "#383f53",
                "accent": "#875a7b",
                "accent_hover": "#9c6b8f",
                "focus": "#00cfc8",
                "focus_fg": "#102127",
                "list_bg": "#3a4258",
                "list_fg": "#f2f4fa",
                "disabled": "#8f96aa",
            }
        else:
            colors = {
                "bg": "#f3f4f6",
                "fg": "#1b1f24",
                "input_bg": "#ffffff",
                "input_fg": "#1b1f24",
                "input_border": "#cbd5e1",
                "panel_bg": "#ffffff",
                "accent": "#2563eb",
                "accent_hover": "#1d4ed8",
                "focus": "#dbeafe",
                "focus_fg": "#1e3a8a",
                "list_bg": "#ffffff",
                "list_fg": "#1b1f24",
                "disabled": "#9ca3af",
            }

        button_bg = colors["accent"] if dark_mode else colors["input_bg"]
        button_fg = "#f8ecf4" if dark_mode else colors["fg"]
        button_active_fg = "#fff4fa" if dark_mode else "#ffffff"

        self.configure(bg=colors["bg"])
        self.mainframe.configure(style="Main.TFrame")
        self.form.configure(style="Main.TFrame")
        self.actions.configure(style="Main.TFrame")
        self.output_frame.configure(style="Main.TFrame")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=colors["bg"], foreground=colors["fg"])
        style.configure("Main.TFrame", background=colors["bg"])
        style.configure("TFrame", background=colors["bg"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        style.configure("TCheckbutton", background=colors["bg"], foreground=colors["fg"])
        style.map("TCheckbutton", background=[("active", colors["bg"])])
        style.configure(
            "TButton",
            background=button_bg,
            foreground=button_fg,
            bordercolor=colors["accent"],
            lightcolor=colors["accent"],
            darkcolor=colors["accent"],
        )
        style.map(
            "TButton",
            background=[("active", colors["accent_hover"]), ("disabled", colors["input_bg"])],
            foreground=[("active", button_active_fg), ("disabled", colors["disabled"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=colors["input_bg"],
            foreground=colors["input_fg"],
            insertcolor=colors["input_fg"],
            bordercolor=colors["input_border"],
            lightcolor=colors["input_border"],
            darkcolor=colors["input_border"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=colors["input_bg"],
            foreground=colors["input_fg"],
            background=colors["panel_bg"],
            selectbackground=colors["focus"],
            selectforeground=colors["focus_fg"],
            bordercolor=colors["input_border"],
            lightcolor=colors["input_border"],
            darkcolor=colors["input_border"],
            arrowcolor=colors["fg"],
            arrowsize=16,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["input_bg"]), ("disabled", colors["input_bg"])],
            foreground=[("readonly", colors["input_fg"]), ("disabled", colors["disabled"])],
            background=[("readonly", colors["panel_bg"]), ("active", colors["panel_bg"])],
            selectbackground=[("readonly", colors["focus"])],
            selectforeground=[("readonly", colors["focus_fg"])],
            arrowcolor=[("disabled", colors["disabled"]), ("active", colors["focus"]), ("readonly", colors["fg"])],
        )

        self.option_add("*TCombobox*Listbox.background", colors["list_bg"])
        self.option_add("*TCombobox*Listbox.foreground", colors["list_fg"])
        self.option_add("*TCombobox*Listbox.selectBackground", colors["focus"])
        self.option_add("*TCombobox*Listbox.selectForeground", colors["focus_fg"])
        self.option_add("*TCombobox*Listbox.highlightBackground", colors["input_border"])
        self.option_add("*TCombobox*Listbox.highlightColor", colors["focus"])
        self.option_add("*Listbox.background", colors["list_bg"])
        self.option_add("*Listbox.foreground", colors["list_fg"])
        self.option_add("*Listbox.selectBackground", colors["focus"])
        self.option_add("*Listbox.selectForeground", colors["focus_fg"])
        self._refresh_combobox_popdown_colors(colors)

        self.output_text.configure(
            background=colors["input_bg"],
            foreground=colors["input_fg"],
            insertbackground=colors["input_fg"],
            selectbackground=colors["focus"],
            selectforeground=colors["fg"],
            highlightthickness=1,
            highlightbackground=colors["input_border"],
            highlightcolor=colors["focus"],
        )

        if hasattr(self, "settings_menu"):
            self.settings_menu.configure(
                background=colors["input_bg"],
                foreground=colors["fg"],
                activebackground=colors["accent"],
                activeforeground=colors["fg"],
            )

    def _refresh_combobox_popdown_colors(self, colors: dict[str, str]) -> None:
        for widget in (self.action_combo, self.project_name_entry, self.odoo_combo, self.psql_combo, self.branch_combo, self.rebuild_combo):
            try:
                popdown = self.tk.call("ttk::combobox::PopdownWindow", str(widget))
                listbox = f"{popdown}.f.l"
                self.tk.call(
                    listbox,
                    "configure",
                    "-background",
                    colors["list_bg"],
                    "-foreground",
                    colors["list_fg"],
                    "-selectbackground",
                    colors["focus"],
                    "-selectforeground",
                    colors["focus_fg"],
                    "-highlightbackground",
                    colors["input_border"],
                    "-highlightcolor",
                    colors["focus"],
                )
            except tk.TclError:
                continue

    def _open_settings_file(self, file_path: Path) -> None:
        if not file_path.exists():
            messagebox.showerror("File missing", f"Not found: {file_path}")
            return

        try:
            platform_open_settings_file(file_path)
        except (RuntimeError, OSError, subprocess.SubprocessError, FileNotFoundError) as exc:
            messagebox.showerror("Open file failed", f"Cannot open file: {file_path}\n\n{exc}")

    def _connect_events(self) -> None:
        self.action_combo.bind("<<ComboboxSelected>>", lambda _event: self._toggle_action_fields())
        self.run_btn.configure(command=self._run)
        self.copy_btn.configure(command=self._copy_command)
        self.clear_btn.configure(command=self._clear_logs)
        self.copy_logs_btn.configure(command=self._copy_logs)

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
        self._refresh_run_button_state()

    def _set_widget_visible(self, label: ttk.Widget, entry: ttk.Widget, visible: bool) -> None:
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

    def _refresh_project_names(self) -> None:
        project_names = self._list_existing_projects()
        current = self.name_var.get().strip()
        self.project_name_entry.configure(values=project_names)
        if current and current in project_names:
            self.name_var.set(current)

    def _list_existing_projects(self) -> list[str]:
        base_dir = self.projects_dir
        if not base_dir.exists() or not base_dir.is_dir():
            return []

        return sorted(
            item.name
            for item in base_dir.iterdir()
            if item.is_dir() and not item.name.startswith(".")
        )

    def _refresh_rebuild_containers_async(self) -> None:
        self.rebuild_fetch_after_id = None
        project_name = self.name_var.get().strip()
        if self.action_var.get() != "rebuild" or not project_name:
            return
        if project_name == self.last_rebuild_source_project:
            return

        threading.Thread(target=self._fetch_rebuild_containers_worker, args=(project_name,), daemon=True).start()

    def _fetch_rebuild_containers_worker(self, project_name: str) -> None:
        project_path = self.projects_dir / project_name
        compose_base = self._detect_compose_base()
        cmd = compose_base + ["config", "--services"]
        try:
            if not project_path.exists():
                self.after(0, lambda: self._apply_rebuild_containers(project_name, []))
                return

            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                text=True,
                capture_output=True,
                check=False,
                **self._platform_subprocess_kwargs(),
            )
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
            test = subprocess.run(
                [docker_path, "compose", "version"],
                text=True,
                capture_output=True,
                check=False,
                **self._platform_subprocess_kwargs(),
            )
            if test.returncode == 0:
                return [docker_path, "compose"]

        docker_compose_path = shutil.which("docker-compose")
        if docker_compose_path:
            return [docker_compose_path]

        raise RuntimeError("Neither 'docker compose' nor 'docker-compose' is available in PATH.")

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
                **self._platform_subprocess_kwargs(),
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
        self.is_process_running = running
        self._refresh_run_button_state()

    def _required_fields_filled(self) -> bool:
        action = self.action_var.get()
        project_name = self.name_var.get().strip()
        if not project_name:
            return False

        if action == "start/create":
            return bool(self.odoo_var.get().strip() and self.psql_var.get().strip())

        if action == "install":
            return bool(self.db_var.get().strip() and self.module_var.get().strip())

        if action == "test":
            has_db = bool(self.db_var.get().strip())
            has_target = bool(self.module_var.get().strip() or self.tags_var.get().strip())
            return has_db and has_target

        if action == "rebuild":
            return bool(self.rebuild_var.get().strip())

        if action == "pip_install":
            return bool(self.pip_var.get().strip())

        return True

    def _refresh_run_button_state(self) -> None:
        enabled = (not self.is_process_running) and self._required_fields_filled()
        self.run_btn.configure(state="normal" if enabled else "disabled")

    def _load_docker_image_tags_async(
        self,
        list_flag: str,
        fallback: str,
        apply_callback,
        error_callback,
    ) -> None:
        threading.Thread(
            target=self._load_docker_image_tags,
            args=(list_flag, fallback, apply_callback, error_callback),
            daemon=True,
        ).start()

    def _load_docker_image_tags(
        self,
        list_flag: str,
        fallback: str,
        apply_callback,
        error_callback,
    ) -> None:
        python_executable = sys.executable or "python"
        cmd = [python_executable, str(self.script_path), list_flag]
        try:
            result = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                check=False,
                **self._platform_subprocess_kwargs(),
            )
            if result.returncode != 0:
                stderr = result.stderr.strip() if result.stderr else "no details"
                raise RuntimeError(f"{stderr}")

            tags = json.loads(result.stdout)
            if not isinstance(tags, list):
                raise ValueError("Invalid JSON response format.")

            versions = [str(tag.get("name", "")).strip() for tag in tags if isinstance(tag, dict)]
            versions = [name for name in versions if name]
            unique_versions = list(dict.fromkeys(versions)) or [fallback]
            self.after(0, lambda: apply_callback(unique_versions))
        except Exception as exc:
            self.after(0, lambda: error_callback(exc))

    def _apply_odoo_versions(self, versions: list[str]) -> None:
        self.odoo_combo.configure(values=versions)
        current = self.odoo_var.get().strip()
        self.odoo_var.set(current if current in versions else versions[0])
        self._append_output(f"Loaded Odoo versions: {', '.join(versions[:10])}\n")

    def _on_odoo_versions_error(self, error: Exception) -> None:
        self.odoo_combo.configure(values=["19.0"])
        self.odoo_var.set("19.0")
        self._append_output(f"Failed to fetch Odoo versions from script: {error}\n")

    def _apply_psql_versions(self, versions: list[str]) -> None:
        self.psql_combo.configure(values=versions)
        current = self.psql_var.get().strip()
        self.psql_var.set(current if current in versions else versions[0])
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
        finally:
            self._refresh_run_button_state()

    def _build_rendered_command(self) -> str:
        cmd = self._build_command(help_only=False)
        return " ".join(self._shell_quote(part) for part in cmd)

    def _shell_quote(self, text: str) -> str:
        if not text:
            return '""'
        if any(char.isspace() for char in text) or any(char in text for char in '"\''):
            text = text.replace('"', '\\"')
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
        self._prompt_tail = ""
        self._awaiting_secret_input = False
        self._pending_secret_value = None
        child_env = dict(os.environ)
        child_env["SMARTODOO_ALLOW_STDIN_PROMPTS"] = "1"
        child_env["SMARTODOO_GUI_MODE"] = "1"
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=child_env,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            universal_newlines=True,
            **self._platform_subprocess_kwargs(),
        )
        threading.Thread(target=self._read_process_output, daemon=True).start()

    def _read_process_output(self) -> None:
        if not self.process or not self.process.stdout:
            return

        while True:
            chunk = self.process.stdout.read(1)
            if chunk == "":
                break
            self.output_queue.put(chunk)

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
        self._detect_secret_prompt(text)

    def _detect_secret_prompt(self, text: str) -> None:
        self._prompt_tail = (self._prompt_tail + text)[-300:]

        if self._awaiting_secret_input:
            return

        match = re.search(r"(Enter [^:\n]+:|Confirm [^:\n]+:)\s*$", self._prompt_tail)
        if not match:
            return

        prompt_text = match.group(1)
        self._awaiting_secret_input = True
        self.after(0, lambda: self._request_secret_input(prompt_text))

    def _request_secret_input(self, prompt_text: str) -> None:
        if not self.process or self.process.poll() is not None or not self.process.stdin:
            self._awaiting_secret_input = False
            return

        value = self._pending_secret_value
        is_confirm_prompt = prompt_text.startswith("Confirm ")

        if value is None or not is_confirm_prompt:
            value = simpledialog.askstring("Secret required", prompt_text, parent=self, show="*")

        if value is not None and not is_confirm_prompt:
            self._pending_secret_value = value

        if value is None:
            self._append_output("\nSecret entry canceled. Stopping process.\n")
            self.process.terminate()
            self._awaiting_secret_input = False
            return

        try:
            self.process.stdin.write(value + "\n")
            self.process.stdin.flush()
        except Exception as exc:
            self._append_output(f"\nFailed to pass secret input to process: {exc}\n")
            self.process.terminate()
        finally:
            if is_confirm_prompt:
                self._pending_secret_value = None
            self._awaiting_secret_input = False
            self._prompt_tail = ""

    def _clear_logs(self) -> None:
        self.output_text.delete("1.0", "end")


def main() -> None:
    app = SmartOdooUI()
    app.mainloop()


if __name__ == "__main__":
    main()
