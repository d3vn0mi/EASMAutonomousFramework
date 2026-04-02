from .base import ToolRunner


class Wafw00fRunner(ToolRunner):
    name = "wafw00f"
    timeout = 120

    def build_command(self, target, options=None):
        cmd = ["wafw00f", target]
        return cmd

    def parse_output(self, raw_output):
        waf_detected = None
        for line in raw_output.splitlines():
            if "is behind" in line:
                waf_detected = line.strip()
                break
            elif "No WAF" in line:
                waf_detected = "No WAF detected"
                break
        return {"waf": waf_detected}
