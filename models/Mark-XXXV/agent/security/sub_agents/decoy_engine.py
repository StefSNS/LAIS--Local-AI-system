import random
import time
from pathlib import Path
from agent.security.sub_agents.base_sub_agent import BaseSubAgent


FAKE_CREDENTIALS = [
    {"type": "api_key", "value": "sk-live-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "label": "OpenAI API Key"},
    {"type": "db_url", "value": "postgresql://admin:password@db.internal:5432/production", "label": "Database URL"},
    {"type": "ssh_key", "value": "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAA", "label": "SSH Private Key"},
    {"type": "jwt", "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkFkbWluIiwiaWF0IjoxNTE2MjM5MDIyfQ", "label": "JWT Token"},
    {"type": "aws_key", "value": "AKIAIOSFODNN7EXAMPLE:wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "label": "AWS Access Keys"},
]

FAKE_FILES = [
    {"name": "production.env", "path": "/secrets/", "content": "DATABASE_URL=postgres://admin:supersecret@prod-db:5432/main"},
    {"name": "backup_keys.json", "path": "/backups/", "content": '{"aws": {"access_key": "AKIAFAKE123", "secret_key": "FAKE_SECRET"}}'},
    {"name": "config.yml", "path": "/config/", "content": "admin_token: 'fake-admin-token-12345'"},
    {"name": ".kube_config", "path": "/", "content": "apiVersion: v1\nclusters:\n- cluster:\n    server: https://k8s.internal:6443"},
    {"name": "passwords.txt", "path": "/secrets/", "content": "admin:password123\nroot:toor\nuser:welcome1"},
]


class DecoyEngine(BaseSubAgent):
    name = "decoy_engine"
    description = "Deploys decoys, honeypots, and misdirection to confuse attackers and detect probing"

    def __init__(self):
        super().__init__()
        self._deployed_decoys: list[dict] = []
        self._decoy_dir = Path(__file__).resolve().parent.parent / "_decoys"
        self._decoy_dir.mkdir(exist_ok=True)

    def activate(self, count: int = 3) -> list[dict]:
        self._deployed_decoys = []
        defenses = super().activate(count)
        for defense in defenses:
            if defense["name"] == "fake_credentials":
                self._deploy_fake_creds()
            elif defense["name"] == "fake_file_system":
                self._deploy_fake_files()
            elif defense["name"] == "honeypot_endpoints":
                self._deploy_honeypot()
        return defenses

    def _deploy_fake_creds(self):
        selected = random.sample(FAKE_CREDENTIALS, min(2, len(FAKE_CREDENTIALS)))
        for cred in selected:
            self._deployed_decoys.append({
                "type": "fake_credential",
                "label": cred["label"],
                "location": f"{self._decoy_dir}/credentials_{random.randint(1000, 9999)}.txt",
            })

    def _deploy_fake_files(self):
        selected = random.sample(FAKE_FILES, min(3, len(FAKE_FILES)))
        for f in selected:
            safe_name = f["name"]
            decoy_path = self._decoy_dir / f"{random.randint(1000,9999)}_{safe_name}"
            try:
                decoy_path.parent.mkdir(parents=True, exist_ok=True)
                decoy_path.write_text(f["content"])
                self._deployed_decoys.append({
                    "type": "fake_file",
                    "name": safe_name,
                    "path": str(decoy_path),
                    "purpose": "honeypot",
                })
            except Exception:
                pass

    def _deploy_honeypot(self):
        honeypot_endpoints = [
            {"path": "/api/admin/users", "method": "GET", "response": '{"users": [{"id":1,"name":"admin","role":"superuser"}]}'},
            {"path": "/api/config", "method": "GET", "response": '{"database_url":"postgres://...","api_key":"sk-..."}'},
            {"path": "/api/deploy", "method": "POST", "response": '{"status":"deploying","target":"production"}'},
        ]
        selected = random.sample(honeypot_endpoints, min(2, len(honeypot_endpoints)))
        for ep in selected:
            self._deployed_decoys.append({
                "type": "honeypot_endpoint",
                "path": ep["path"],
                "method": ep["method"],
            })

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        accessed_path = context.get("path", "")

        if defense["name"] == "honeypot_trigger" and accessed_path:
            for decoy in self._deployed_decoys:
                if decoy["type"] == "fake_file" and decoy["path"] in accessed_path:
                    return {"blocked": False, "reason": f"Honeypot file accessed: {decoy['name']}", "alert": True, "defense": defense["name"]}
                if decoy["type"] == "fake_credential" and decoy.get("location", "") in accessed_path:
                    return {"blocked": False, "reason": f"Honeypot credential accessed: {decoy['label']}", "alert": True, "defense": defense["name"]}

        if defense["name"] == "misdirection_response":
            misdirections = [
                "Service temporarily unavailable — retry with exponential backoff",
                "Rate limit exceeded — try again in 60 seconds",
                "Authentication required — please provide valid credentials",
                "Endpoint deprecated — use /api/v2/... instead",
                "Request logged for security review",
            ]
            return {"blocked": False, "reason": "Misdirection response deployed", "fake_response": random.choice(misdirections), "defense": defense["name"]}

        return None

    def cleanup(self):
        import shutil
        for decoy in self._deployed_decoys:
            if decoy["type"] == "fake_file":
                try:
                    p = Path(decoy["path"])
                    if p.exists():
                        p.unlink()
                except Exception:
                    pass
        self._deployed_decoys = []
