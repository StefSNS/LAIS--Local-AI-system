"""
n8n Workflow Bridge v1.0
Integrates Omnis with n8n automation workflows via webhooks.
Based on n8n webhook patterns and Dify workflow integration.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Optional


N8N_CONFIG_FILE = Path(
    r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\memory\n8n_config.json"
)
N8N_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)


class N8nWorkflow:
    """Represents an n8n workflow connection."""

    def __init__(
        self,
        workflow_id: str,
        name: str,
        webhook_url: str,
        description: str = "",
        category: str = "general",
        tags: list[str] = None,
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.webhook_url = webhook_url
        self.description = description
        self.category = category
        self.tags = tags or []
        self.created = datetime.now()
        self.call_count = 0
        self.last_call = None
        self.last_result = None

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "webhook_url": self.webhook_url,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "created": self.created.isoformat(),
            "call_count": self.call_count,
            "last_call": self.last_call,
            "last_result": self.last_result,
        }


class N8nBridge:
    """
    Bridge between Omnis and n8n workflows.
    Supports: trigger workflows, receive webhooks, manage workflow configs.
    """

    def __init__(self):
        self._workflows: dict[str, N8nWorkflow] = {}
        self._webhook_handlers: dict[str, callable] = {}
        self._load()

    def register_workflow(
        self,
        workflow_id: str,
        name: str,
        webhook_url: str,
        description: str = "",
        category: str = "general",
        tags: list[str] = None,
    ) -> N8nWorkflow:
        workflow = N8nWorkflow(
            workflow_id=workflow_id,
            name=name,
            webhook_url=webhook_url,
            description=description,
            category=category,
            tags=tags,
        )
        self._workflows[workflow_id] = workflow
        self._save()
        return workflow

    def trigger(
        self,
        workflow_id: str,
        inputs: dict = None,
        wait_for_response: bool = False,
    ) -> dict:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return {"error": f"Workflow '{workflow_id}' not found"}

        payload = {
            "source": "omnis",
            "timestamp": datetime.now().isoformat(),
            "inputs": inputs or {},
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                workflow.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            if wait_for_response:
                with urllib.request.urlopen(req, timeout=60) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    workflow.call_count += 1
                    workflow.last_call = datetime.now().isoformat()
                    workflow.last_result = str(result)[:500]
                    self._save()
                    return {"success": True, "result": result}
            else:
                urllib.request.urlopen(req, timeout=10)
                workflow.call_count += 1
                workflow.last_call = datetime.now().isoformat()
                workflow.last_result = "triggered (async)"
                self._save()
                return {"success": True, "result": "Workflow triggered (async)"}

        except urllib.error.URLError as e:
            return {"error": f"Webhook error: {e}", "workflow": workflow.name}
        except Exception as e:
            return {"error": str(e), "workflow": workflow.name}

    def trigger_by_name(
        self,
        name: str,
        inputs: dict = None,
        wait_for_response: bool = False,
    ) -> dict:
        for wf in self._workflows.values():
            if wf.name.lower() == name.lower():
                return self.trigger(wf.workflow_id, inputs, wait_for_response)
        return {"error": f"Workflow '{name}' not found"}

    def register_webhook_handler(self, event_type: str, handler: callable):
        self._webhook_handlers[event_type] = handler

    def handle_incoming_webhook(self, event_type: str, data: dict) -> dict:
        handler = self._webhook_handlers.get(event_type)
        if handler:
            try:
                result = handler(data)
                return {"success": True, "result": result}
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"No handler for event type: {event_type}"}

    def get_workflow(self, workflow_id: str) -> Optional[N8nWorkflow]:
        return self._workflows.get(workflow_id)

    def list_workflows(self, category: str = None, tag: str = None) -> list[dict]:
        workflows = list(self._workflows.values())
        if category:
            workflows = [w for w in workflows if w.category == category]
        if tag:
            workflows = [w for w in workflows if tag in w.tags]
        return [w.to_dict() for w in workflows]

    def remove_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            self._save()
            return True
        return False

    def get_stats(self) -> dict:
        total_calls = sum(w.call_count for w in self._workflows.values())
        by_category = {}
        for w in self._workflows.values():
            by_category[w.category] = by_category.get(w.category, 0) + 1
        return {
            "total_workflows": len(self._workflows),
            "total_calls": total_calls,
            "by_category": by_category,
        }

    def _load(self):
        if N8N_CONFIG_FILE.exists():
            try:
                data = json.loads(N8N_CONFIG_FILE.read_text(encoding="utf-8"))
                for w_data in data.get("workflows", []):
                    wf = N8nWorkflow(
                        workflow_id=w_data["workflow_id"],
                        name=w_data["name"],
                        webhook_url=w_data["webhook_url"],
                        description=w_data.get("description", ""),
                        category=w_data.get("category", "general"),
                        tags=w_data.get("tags", []),
                    )
                    wf.call_count = w_data.get("call_count", 0)
                    wf.last_call = w_data.get("last_call")
                    wf.last_result = w_data.get("last_result")
                    self._workflows[wf.workflow_id] = wf
            except Exception as e:
                pass

_global_n8n_bridge: Optional[N8nBridge] = None


def get_n8n_bridge(cloud_webhook: str = "") -> tuple[N8nBridge, "TaskScheduler"]:
    global _global_n8n_bridge
    if _global_n8n_bridge is None:
        _global_n8n_bridge = N8nBridge()
    from unified_layer.scheduler import load_scheduler
    scheduler = load_scheduler(cloud_webhook=cloud_webhook)
    return _global_n8n_bridge, scheduler
