import json
from .base import ToolRunner


class WhatWebRunner(ToolRunner):
    name = "whatweb"
    timeout = 300

    def build_command(self, target, options=None):
        return ["whatweb", "--log-json=-", "--color=never", target]

    def parse_output(self, raw_output):
        technologies = []
        for line in raw_output.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                plugins = entry.get("plugins", {})
                for plugin_name, plugin_data in plugins.items():
                    tech = {"name": plugin_name}
                    if isinstance(plugin_data, dict):
                        if plugin_data.get("version"):
                            tech["version"] = plugin_data["version"][0] if isinstance(plugin_data["version"], list) else str(plugin_data["version"])
                        if plugin_data.get("string"):
                            tech["detail"] = plugin_data["string"][0] if isinstance(plugin_data["string"], list) else str(plugin_data["string"])
                    technologies.append(tech)
            except json.JSONDecodeError:
                continue
        return {"technologies": technologies, "count": len(technologies)}
