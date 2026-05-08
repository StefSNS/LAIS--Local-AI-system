from agent.security.sub_agents.base_sub_agent import BaseSubAgent


class NetworkShield(BaseSubAgent):
    name = "network_shield"
    description = "Monitors and blocks network-level threats: SSRF, MITM, unauthorized egress"

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        target_url = context.get("target_url", "")
        if defense["name"] == "url_allowlist" and target_url:
            allowed = defense["params"].get("allowed", [])
            if allowed and not any(d in target_url for d in allowed):
                return {"blocked": True, "reason": f"URL not in allowlist: {target_url}", "defense": defense["name"]}

        if defense["name"] == "internal_ip_block":
            blocked_ips = context.get("resolved_ips", [])
            if any(ip.startswith(("10.", "172.16.", "192.168.", "127.", "169.254.")) for ip in blocked_ips):
                return {"blocked": True, "reason": "Internal IP blocked", "defense": defense["name"]}

        if defense["name"] == "protocol_restrict" and target_url:
            if not target_url.startswith("https://"):
                return {"blocked": True, "reason": f"Non-HTTPS protocol blocked: {target_url}", "defense": defense["name"]}

        return None
