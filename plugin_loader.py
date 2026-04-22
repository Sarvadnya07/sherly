import os
import importlib

def load_plugins():

    plugins = {}
    
    if not os.path.exists("plugins"):
        return plugins

    for file in os.listdir("plugins"):

        if file.endswith(".py"):

            module = importlib.import_module(
                "plugins." + file[:-3]
            )

            plugins[file] = module

    return plugins