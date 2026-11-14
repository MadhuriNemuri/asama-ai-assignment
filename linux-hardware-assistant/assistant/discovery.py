import shutil
from typing import Dict, List, Any

# Tool descriptions presented to the LLM router
TOOL_DEFINITIONS = [
    {
        "name": "get_dmi_memory",
        "description": "Retrieves physical RAM topology including installed capacity, total slots, available slots, speed, and maximum supported motherboard capacity (requires root/sudo).",
        "binary": "dmidecode",
        "parameters": {}
    },
    {
        "name": "get_cpu_info",
        "description": "Retrieves CPU architecture, model name, core counts, threads, and clock speed.",
        "binary": "lscpu",
        "parameters": {}
    },
    {
        "name": "get_block_devices",
        "description": "Lists all storage devices (SSDs, NVMe drives, HDDs), partition mounts, and transport types.",
        "binary": "lsblk",
        "parameters": {}
    },
    {
        "name": "get_memory_summary",
        "description": "Gets current RAM usage, total installed OS memory, and available memory.",
        "binary": "free",
        "parameters": {}
    },
    {
        "name": "get_proc_meminfo",
        "description": "Unprivileged fallback to read system memory capacity from /proc/meminfo when dmidecode is restricted.",
        "binary": "cat",
        "parameters": {}
    }
]

def discover_available_tools() -> List[Dict[str, Any]]:
    """
    Scans the host system to determine which tools are executable.
    Dynamically registers only available tools with the LLM router.
    """
    available = []
    for tool in TOOL_DEFINITIONS:
        binary = tool["binary"]
        if shutil.which(binary) or binary == "cat":
            available.append(tool)
    return available
