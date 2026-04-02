import logging
from django.conf import settings
from .base import ToolRunner

logger = logging.getLogger(__name__)


class GitHubRunner(ToolRunner):
    name = "github"
    timeout = 120

    def build_command(self, target, options=None):
        return ["echo", "github-api-runner"]

    def parse_output(self, raw_output):
        return {}

    def run(self, target, options=None, output_dir=None, stdin_input=None):
        if not self.validate_target(target):
            return {"error": f"Invalid target: {target}", "status": "failed"}

        api_token = getattr(settings, "GITHUB_API_TOKEN", "")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        try:
            import requests

            repos = []
            members = []
            code_results = []

            # Search for organization repos
            resp = requests.get(
                f"https://api.github.com/orgs/{target}/repos",
                headers=headers, timeout=30, params={"per_page": 100},
            )
            if resp.status_code == 200:
                for repo in resp.json():
                    repos.append({
                        "name": repo.get("name", ""),
                        "full_name": repo.get("full_name", ""),
                        "private": repo.get("private", False),
                        "description": repo.get("description", ""),
                        "language": repo.get("language", ""),
                        "archived": repo.get("archived", False),
                        "html_url": repo.get("html_url", ""),
                        "updated_at": repo.get("updated_at", ""),
                    })

            # Search for org members
            resp = requests.get(
                f"https://api.github.com/orgs/{target}/members",
                headers=headers, timeout=30, params={"per_page": 100},
            )
            if resp.status_code == 200:
                for member in resp.json():
                    members.append({
                        "login": member.get("login", ""),
                        "html_url": member.get("html_url", ""),
                    })

            # Code search for potential secrets
            search_queries = [
                f"org:{target} password",
                f"org:{target} api_key",
                f"org:{target} secret",
            ]
            for query in search_queries:
                resp = requests.get(
                    "https://api.github.com/search/code",
                    headers=headers, timeout=30,
                    params={"q": query, "per_page": 10},
                )
                if resp.status_code == 200:
                    for item in resp.json().get("items", []):
                        code_results.append({
                            "repository": item.get("repository", {}).get("full_name", ""),
                            "file": item.get("name", ""),
                            "path": item.get("path", ""),
                            "html_url": item.get("html_url", ""),
                        })

            parsed = {
                "repos": repos,
                "members": members,
                "code_results": code_results,
                "repo_count": len(repos),
                "member_count": len(members),
            }

            return {
                "status": "completed",
                "exit_code": 0,
                "raw_output": str(parsed)[:50000],
                "parsed": parsed,
                "command": f"GitHub API: {target}",
            }
        except Exception as e:
            logger.exception("GitHub query failed for %s", target)
            return {"status": "failed", "error": str(e)}
