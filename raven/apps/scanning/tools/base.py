"""
Base ToolRunner abstraction for all recon tools.
Each tool wrapper inherits from ToolRunner and implements:
  - build_command(target, options) -> list of strings
  - parse_output(raw_output) -> dict of structured results
  - validate_target(target) -> bool
"""
import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class ToolRunner(ABC):
    """Abstract base for wrapping CLI recon tools."""

    name: str = ""
    timeout: int = 600  # seconds

    @abstractmethod
    def build_command(self, target: str, options: dict | None = None) -> list[str]:
        """Build the CLI command as a list (never use shell=True)."""
        ...

    @abstractmethod
    def parse_output(self, raw_output: str) -> dict:
        """Parse raw stdout/file output into structured data."""
        ...

    def validate_target(self, target: str) -> bool:
        """Validate that the target is safe and appropriate for this tool."""
        if not target or not target.strip():
            return False
        # Block shell metacharacters
        dangerous = set(";|&$`\\\"'(){}<>!")
        if any(c in target for c in dangerous):
            return False
        return True

    def run(self, target: str, options: dict | None = None, output_dir: str | None = None, stdin_input: str | None = None) -> dict:
        """Execute the tool and return structured results."""
        if not self.validate_target(target):
            return {"error": f"Invalid target: {target}", "status": "failed"}

        cmd = self.build_command(target, options or {})
        logger.info("Running %s: %s", self.name, " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                input=stdin_input,
            )
            raw_output = result.stdout
            parsed = self.parse_output(raw_output)

            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "raw_output": raw_output,
                "stderr": result.stderr[:5000] if result.stderr else "",
                "parsed": parsed,
                "command": " ".join(cmd),
            }
        except subprocess.TimeoutExpired:
            logger.error("%s timed out after %ds on %s", self.name, self.timeout, target)
            return {"status": "failed", "error": f"Timeout after {self.timeout}s", "command": " ".join(cmd)}
        except FileNotFoundError:
            logger.error("%s binary not found", self.name)
            return {"status": "failed", "error": f"{self.name} binary not found"}
        except Exception as e:
            logger.exception("Unexpected error running %s", self.name)
            return {"status": "failed", "error": str(e)}
