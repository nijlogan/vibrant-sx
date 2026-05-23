import sys
import subprocess
import threading
import sublime
import sublime_plugin

_lsp_plugin_class = None

def _check_python():
    kwargs = {}

    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True, text=True,
            **kwargs
        )

        version = result.stdout.strip() or result.stderr.strip()
        parts = version.split(" ")[1].split(".")

        if int(parts[0]) < 3 or (int(parts[0]) == 3 and int(parts[1]) < 8):
            sublime.message_dialog(
                (
                    "dnh: Python 3.8 or higher is required for LSP support. "
                    "Python {}.{} was the newest detected version installed. "
                    "Please install Python 3.8 or higher from python.org and ensure it is in your PATH."
                ).format(parts[0], parts[1])
            )

    except FileNotFoundError:
        sublime.message_dialog(
            "dnh: Python was not found. "
            "Please install Python 3.8 or higher from python.org and ensure it is in your PATH."
        )

def plugin_loaded():
    global _lsp_plugin_class

    threading.Thread(target=_check_python, daemon=True).start()

    try:
        from LSP.plugin import AbstractPlugin, register_plugin

        class DnhLanguageServer(AbstractPlugin):
            @classmethod
            def name(cls):
                return "dnh"

            @classmethod
            def configuration(cls):
                basename = "LSP-dnh"
                filepath = "Packages/dnh/LSP-dnh.sublime-settings"
                return basename, filepath

            @classmethod
            def get_startupinfo(cls):
                return None

        _lsp_plugin_class = DnhLanguageServer
        register_plugin(DnhLanguageServer)

    except ImportError:
        sublime.message_dialog(
            "dnh: The LSP package is required. "
            "Please install it via Package Control."
        )

def plugin_unloaded():
    if _lsp_plugin_class is not None:
        from LSP.plugin import unregister_plugin
        unregister_plugin(_lsp_plugin_class)


# class DnhEventListener(sublime_plugin.EventListener):
#     def on_init(self, views):
#         sublime.active_window().run_command("lsp_show_diagnostics_panel")
