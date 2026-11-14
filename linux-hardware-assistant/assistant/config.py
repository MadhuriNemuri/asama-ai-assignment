import os
from typing import Dict, List

# Strict Allow-List: Maps internal tool names directly to static system commands and fixed arguments
ALLOW_LISTED_TOOLS: Dict[str, List[str]] = {
    "get_cpu_info": ["lscpu"],
    "get_block_devices": ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA,TRAN"],
    "get_memory_summary": ["free", "-b"],
    "get_pci_devices": ["lspci", "-mm"],
    "get_dmi_memory": ["sudo", "/usr/sbin/dmidecode", "-t", "memory"],
    "get_proc_meminfo": ["cat", "/proc/meminfo"]
}

# Execution safety defaults
EXECUTION_TIMEOUT_SECONDS = 5
MAX_OUTPUT_BYTES = 512 * 1024  # 512 KB protection against buffer overflow
