from sherly.core.plugin_sdk import BasePlugin

class WeatherPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "Weather"

    @property
    def description(self) -> str:
        return "Fetch current weather information for a city."

    def run(self, query: str) -> str:
        # Simple extraction logic for the example
        city = query.lower().replace("weather in", "").strip()
        if not city:
            return "Please specify a city. (e.g., 'weather in London')"
        
        # Placeholder for actual API call
        return f"The current weather in {city.capitalize()} is sunny with a light breeze. (Mock data)"

    def on_load(self):
        print("[WeatherPlugin] Loaded.")

    def on_unload(self):
        print("[WeatherPlugin] Unloaded.")
