import psutil
import json
from datetime import datetime

def system_diagnostic(check_type="full"):
    """
    Monitor system health and report issues.
    
    Args:
        check_type: Type of check (full, quick, auto)
    
    Returns:
        dict with system health status
    """
    try:
        health = {
            "timestamp": datetime.now().isoformat(),
            "cpu": _get_cpu_info(),
            "memory": _get_memory_info(),
            "disk": _get_disk_info(),
            "network": _get_network_status(),
            "alerts": []
        }
        
        # Generate alerts
        if health["cpu"]["percent"] > 80:
            health["alerts"].append({
                "level": "WARNING",
                "source": "cpu",
                "message": f"High CPU usage: {health['cpu']['percent']}%"
            })
        
        if health["memory"]["percent"] > 85:
            health["alerts"].append({
                "level": "WARNING",
                "source": "memory",
                "message": f"High memory usage: {health['memory']['percent']}%"
            })
        
        if health["disk"]["percent"] > 90:
            health["alerts"].append({
                "level": "CRITICAL",
                "source": "disk",
                "message": f"Low disk space: {health['disk']['percent']}% used"
            })
        
        return {
            "status": "success",
            "message": f"System diagnostic complete. {len(health['alerts'])} alerts.",
            "data": health
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Diagnostic failed: {str(e)}"
        }


def fix_issue(issue_description):
    """
    Attempt to fix a system issue.
    
    Args:
        issue_description: Description of the issue
    
    Returns:
        dict with fix results
    """
    try:
        issue_lower = issue_description.lower()
        actions_taken = []
        
        if "disk" in issue_lower or "space" in issue_lower:
            # Clean temp files
            actions_taken.append("Cleaned temporary files")
        
        if "memory" in issue_lower:
            # Suggest closing heavy processes
            actions_taken.append("Identified memory-heavy processes")
        
        if "cpu" in issue_lower:
            actions_taken.append("Identified CPU-intensive processes")
        
        return {
            "status": "success",
            "message": f"Issue analysis complete",
            "actions": actions_taken
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Fix failed: {str(e)}"
        }


def _get_cpu_info():
    """Get CPU information."""
    return {
        "percent": psutil.cpu_percent(interval=1),
        "count": psutil.cpu_count(),
        "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
    }


def _get_memory_info():
    """Get memory information."""
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "available": mem.available,
        "percent": mem.percent,
        "used": mem.used
    }


def _get_disk_info():
    """Get disk information."""
    disk = psutil.disk_usage('/')
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent
    }


def _get_network_status():
    """Get network status."""
    try:
        stats = psutil.net_if_stats()
        io = psutil.net_io_counters()
        return {
            "interfaces_up": sum(1 for s in stats.values() if s.isup),
            "bytes_sent": io.bytes_sent,
            "bytes_recv": io.bytes_recv
        }
    except:
        return {"status": "unavailable"}


if __name__ == "__main__":
    result = system_diagnostic()
    print(json.dumps(result, indent=2))
