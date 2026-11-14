import json
import re
from typing import Dict, Any, List

def parse_block_devices(stdout: str) -> Dict[str, Any]:
    """Parses lsblk -J output into structured block device summary."""
    try:
        data = json.loads(stdout)
        devices = []
        for dev in data.get("blockdevices", []):
            devices.append({
                "name": dev.get("name"),
                "size": dev.get("size"),
                "type": dev.get("type"),
                "mountpoint": dev.get("mountpoint"),
                "model": dev.get("model", "Generic/Virtual"),
                "transport": dev.get("tran", "nvme" if "nvme" in dev.get("name", "") else "sata"),
                "rotational": bool(dev.get("rota", False))
            })
        return {"block_devices": devices}
    except Exception as e:
        return {"error": f"Failed to parse lsblk JSON: {str(e)}"}

def parse_cpu_info(stdout: str) -> Dict[str, Any]:
    """Parses lscpu stdout into structured key-value dict."""
    cpu_data = {}
    for line in stdout.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            cpu_data[key.strip()] = val.strip()

    return {
        "architecture": cpu_data.get("Architecture", "Unknown"),
        "model_name": cpu_data.get("Model name", cpu_data.get("Vendor ID", "Unknown")),
        "cores_total": int(cpu_data.get("CPU(s)", 1)) if cpu_data.get("CPU(s)", "").isdigit() else 1,
        "threads_per_core": int(cpu_data.get("Thread(s) per core", 1)) if cpu_data.get("Thread(s) per core", "").isdigit() else 1,
        "max_freq_mhz": cpu_data.get("CPU max MHz", "Unknown"),
        "virtualization": cpu_data.get("Virtualization", "None")
    }

def parse_dmi_memory(stdout: str) -> Dict[str, Any]:
    """
    Parses dmidecode -t memory output to extract physical topology:
    - Maximum capacity supported by the motherboard
    - Total slots
    - Used vs free slots
    - Installed RAM details
    """
    max_cap_match = re.search(r"Maximum Capacity:\s*(.+)", stdout)
    max_capacity = max_cap_match.group(1).strip() if max_cap_match else "Unknown"

    # Find each Memory Device block
    device_blocks = stdout.split("Memory Device")
    installed_modules = []
    empty_slots = 0

    for block in device_blocks[1:]:
        size_match = re.search(r"Size:\s*(.+)", block)
        type_match = re.search(r"Type:\s*(.+)", block)
        speed_match = re.search(r"Speed:\s*(.+)", block)

        if size_match:
            size_val = size_match.group(1).strip()
            if "No Module Installed" in size_val or "Not Installed" in size_val:
                empty_slots += 1
            else:
                installed_modules.append({
                    "size": size_val,
                    "type": type_match.group(1).strip() if type_match else "Unknown",
                    "speed": speed_match.group(1).strip() if speed_match else "Unknown"
                })

    total_slots = len(installed_modules) + empty_slots

    return {
        "maximum_capacity": max_capacity,
        "total_slots": total_slots,
        "used_slots": len(installed_modules),
        "free_slots": empty_slots,
        "installed_modules": installed_modules
    }

def parse_memory_summary(stdout: str) -> Dict[str, Any]:
    """Parses free -b or /proc/meminfo to report current RAM usage."""
    lines = stdout.strip().splitlines()
    if len(lines) >= 2 and "Mem:" in lines[1]:
        parts = lines[1].split()
        total_b = int(parts[1])
        used_b = int(parts[2])
        free_b = int(parts[3])
        avail_b = int(parts[6]) if len(parts) > 6 else free_b
        return {
            "total_gb": round(total_b / (1024**3), 2),
            "used_gb": round(used_b / (1024**3), 2),
            "available_gb": round(avail_b / (1024**3), 2)
        }
    return {"raw_output": stdout}

def parse_tool_output(tool_name: str, stdout: str) -> Dict[str, Any]:
    """Dispatcher to normalize tool output into structured JSON."""
    if tool_name == "get_block_devices":
        return parse_block_devices(stdout)
    elif tool_name == "get_cpu_info":
        return parse_cpu_info(stdout)
    elif tool_name == "get_dmi_memory":
        return parse_dmi_memory(stdout)
    elif tool_name == "get_memory_summary":
        return parse_memory_summary(stdout)
    elif tool_name == "get_proc_meminfo":
        # Fallback memory reader
        mem_total = re.search(r"MemTotal:\s*(\d+)\s*kB", stdout)
        mem_avail = re.search(r"MemAvailable:\s*(\d+)\s*kB", stdout)
        total_kb = int(mem_total.group(1)) if mem_total else 0
        avail_kb = int(mem_avail.group(1)) if mem_avail else 0
        return {
            "total_gb": round(total_kb / (1024**2), 2),
            "available_gb": round(avail_kb / (1024**2), 2),
            "source": "/proc/meminfo"
        }
    return {"raw_output": stdout}
