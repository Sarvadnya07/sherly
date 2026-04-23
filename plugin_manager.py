"""Simple plugin loader that watches the `plugins/` folder."""

import importlib
from pathlib import Path

from config_manager import get_plugin_enabled, set_plugin_enabled as store_plugin_setting

plugins = {}
_all_plugins = {}


def load_plugins():
    """Reload every plugin module and cache their enabled state."""

    plugins.clear()
    _all_plugins.clear()

    plugin_dir = Path(__file__).parent / "plugins"
    plugin_dir.mkdir(exist_ok=True)

    for file in plugin_dir.iterdir():
        if not file.is_file() or file.suffix != ".py" or file.stem.startswith("_"):
            continue

        module_name = file.stem

        try:
            module = importlib.import_module(f"plugins.{module_name}")
            importlib.reload(module)
        except Exception as err:
            print(f"Failed to load plugin {module_name}: {err}")
            continue

        plugin_name = getattr(module, "name", module_name)
        enabled = get_plugin_enabled(plugin_name)

        _all_plugins[plugin_name] = {
            "module": module,
            "enabled": enabled
        }

        if enabled and hasattr(module, "run"):
            plugins[plugin_name] = module


def run_plugin(name, query):
    """Dispatch to the named plugin, if it is enabled."""

    module = plugins.get(name)
    if not module:
        return None

    try:
        return module.run(query)
    except Exception as err:
        return f"Plugin error ({name}): {err}"


def get_enabled_plugin_names():
    return list(plugins.keys())


def get_all_plugin_states():
    return {name: meta["enabled"] for name, meta in _all_plugins.items()}


def set_plugin_enabled(name, enabled):
    store_plugin_setting(name, bool(enabled))
    load_plugins()


load_plugins()
