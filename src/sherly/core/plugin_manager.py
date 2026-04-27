import importlib
import sys
from pathlib import Path
from typing import Dict, Any, Type
from sherly.core.plugin_sdk import BasePlugin
from sherly.config.config_manager import get_plugin_enabled, set_plugin_enabled as store_plugin_setting

plugins: Dict[str, BasePlugin] = {}
_all_plugins_meta = {}

def load_plugins():
    """Reload plugins from the plugins/ directory."""
    global plugins
    
    # Unload existing plugins correctly
    for p in plugins.values():
        try:
            p.on_unload()
        except Exception:
            pass
            
    plugins.clear()
    _all_plugins_meta.clear()

    plugin_dir = Path(__file__).parent / "plugins"
    plugin_dir.mkdir(exist_ok=True)

    if str(plugin_dir) not in sys.path:
        sys.path.append(str(plugin_dir))

    for file in plugin_dir.iterdir():
        if not file.is_file() or file.suffix != ".py" or file.stem.startswith("_"):
            continue

        module_name = file.stem
        try:
            # Hot-reloading: remove from sys.modules if it exists
            if f"plugins.{module_name}" in sys.modules:
                del sys.modules[f"plugins.{module_name}"]
            
            module = importlib.import_module(f"plugins.{module_name}")
            importlib.reload(module)
            
            # Find the plugin class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                    instance = attr()
                    p_name = instance.name
                    enabled = get_plugin_enabled(p_name)
                    
                    _all_plugins_meta[p_name] = {
                        "instance": instance,
                        "enabled": enabled,
                        "module": module
                    }
                    
                    if enabled:
                        instance.on_load()
                        plugins[p_name] = instance
                    break
        except Exception as err:
            print(f"Failed to load plugin {module_name}: {err}")

def _ensure_plugin_venv(plugin_name: str):
    """
    Long-term vision: Isolated Plugin Registry.
    Ensures each plugin has its own virtual environment.
    """
    import subprocess
    import venv
    
    plugin_data_dir = Path.home() / ".sherly" / "plugins" / plugin_name
    venv_dir = plugin_data_dir / "venv"
    
    if not venv_dir.exists():
        print(f"[PluginManager] Creating isolated venv for {plugin_name}...")
        venv.create(venv_dir, with_pip=True)
        
    return venv_dir

def run_plugin(name: str, query: str) -> Any:
    plugin = plugins.get(name)
    if not plugin:
        return None
    try:
        return plugin.run(query)
    except Exception as err:
        return f"Plugin error ({name}): {err}"

def get_enabled_plugin_names():
    return list(plugins.keys())

def get_all_plugin_states():
    return {name: meta["enabled"] for name, meta in _all_plugins_meta.items()}


def set_plugin_enabled(name: str, enabled: bool):
    store_plugin_setting(name, bool(enabled))
    load_plugins()


# ---------------------------------------------------------------------------
# OE-4 — Plugin Marketplace Stub (opt-in, disabled by default)
# ---------------------------------------------------------------------------

def fetch_marketplace(url: str = "https://sherly-plugins.example.com/registry.json") -> list[dict]:
    """
    OE-4: Fetch a list of community plugins from the marketplace registry.

    Returns a list of plugin dicts:
      [{"name": ..., "description": ..., "install": ..., "version": ...}]

    Only active when config.json → plugin_marketplace = true.
    Completely safe to call; silently returns [] if disabled or unreachable.
    """
    try:
        from sherly.config.config_manager import get_plugin_marketplace_enabled
        if not get_plugin_marketplace_enabled():
            return []

        import requests
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        plugins_list = data if isinstance(data, list) else data.get("plugins", [])
        print(f"[PluginMarketplace] Found {len(plugins_list)} plugins in registry.")
        return plugins_list
    except Exception as err:
        print(f"[PluginMarketplace] Could not fetch registry: {err}")
        return []


load_plugins()
