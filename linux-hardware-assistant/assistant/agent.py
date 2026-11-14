import json
from typing import Dict, Any, List, Optional
from assistant.execution import system_executor, ExecutionSafetyError
from assistant.parsers import parse_tool_output
from assistant.discovery import discover_available_tools

SYSTEM_PROMPT = """You are a safe, precise Linux Hardware Q&A Assistant.
RULES:
1. Base your answer SOLELY on the verified structured JSON tool outputs provided.
2. DO NOT hallucinate or guess any hardware specs.
3. If the JSON output lacks sufficient information or a tool returned an error, explicitly state:
   "I cannot determine this hardware detail from system data" and mention which data is unavailable.
4. Keep explanations clear, technical, and concise.
"""

class HardwareAssistantAgent:
    """
    Orchestrates Intent Detection -> Safe Allow-Listed Tool Execution -> Structured Output Synthesis.
    Enforces strict anti-hallucination and session memory caching.
    """

    def __init__(self, executor=system_executor):
        self.executor = executor
        self.session_cache: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, str]] = []

    def select_tools_for_query(self, query: str) -> List[str]:
        """
        Maps natural language query intents to required allow-listed tools.
        """
        q = query.lower()
        tools = []

        if any(w in q for w in ["ram", "memory", "upgrade", "capacity", "slot", "dimm"]):
            tools.append("get_dmi_memory")
            tools.append("get_memory_summary")

        if any(w in q for w in ["cpu", "processor", "core", "frequency", "ghz", "threads", "architecture"]):
            tools.append("get_cpu_info")

        if any(w in q for w in ["ssd", "nvme", "disk", "storage", "drive", "hdd", "space"]):
            tools.append("get_block_devices")

        # Fallback if no specific keyword matched
        if not tools:
            tools.append("get_memory_summary")
            tools.append("get_cpu_info")

        return tools

    def answer_query(self, user_query: str) -> Dict[str, Any]:
        """
        Complete tool-calling pipeline:
        1. Select safe allow-listed tools.
        2. Execute via safe executor (or retrieve from session cache).
        3. Parse outputs into structured JSON.
        4. Synthesize grounded answer.
        """
        tools_to_run = self.select_tools_for_query(user_query)
        collected_data = {}
        executed_tools = []

        for tool_name in tools_to_run:
            # Check cache first for instant response on follow-ups
            if tool_name in self.session_cache:
                collected_data[tool_name] = self.session_cache[tool_name]
                continue

            try:
                exec_result = self.executor.execute_tool(tool_name)
                executed_tools.append(tool_name)

                if exec_result.get("status") == "success":
                    raw_stdout = exec_result.get("stdout", "")
                    parsed = parse_tool_output(tool_name, raw_stdout)
                    collected_data[tool_name] = parsed
                    self.session_cache[tool_name] = parsed
                else:
                    collected_data[tool_name] = {"error": exec_result.get("error")}
            except ExecutionSafetyError as err:
                collected_data[tool_name] = {"security_error": str(err)}

        # Synthesize final natural language answer grounded on collected data
        answer = self._synthesize_answer(user_query, collected_data)

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_query})
        self.conversation_history.append({"role": "assistant", "content": answer})

        return {
            "query": user_query,
            "tools_called": executed_tools,
            "structured_data": collected_data,
            "answer": answer
        }

    def _synthesize_answer(self, query: str, data: Dict[str, Any]) -> str:
        """Grounded synthesis adhering strictly to verified JSON specs."""
        q = query.lower()

        # Case 1: RAM & Upgrade capacity
        if any(w in q for w in ["ram", "upgrade", "memory", "slot"]):
            dmi = data.get("get_dmi_memory", {})
            summary = data.get("get_memory_summary", {})

            if "error" in dmi or not dmi.get("maximum_capacity"):
                # Fallback to summary if DMI requires root
                total_gb = summary.get("total_gb", "Unknown")
                return (
                    f"You have {total_gb} GB of RAM installed. "
                    "Detailed physical slot topology and maximum motherboard capacity require elevated DMI permissions (dmidecode). "
                    "Please configure scoped sudoers to enable hardware slot inspection."
                )

            max_cap = dmi.get("maximum_capacity", "Unknown")
            total_slots = dmi.get("total_slots", 0)
            used_slots = dmi.get("used_slots", 0)
            free_slots = dmi.get("free_slots", 0)
            installed = dmi.get("installed_modules", [])
            installed_str = ", ".join([f"{m.get('size')} {m.get('type')}" for m in installed]) if installed else "Unknown"

            if free_slots > 0:
                return (
                    f"Yes, you can upgrade your RAM. You currently have {used_slots} of {total_slots} memory slots populated "
                    f"({installed_str}). The motherboard supports a maximum capacity of {max_cap}. "
                    f"You have {free_slots} free slot(s) available for expansion."
                )
            else:
                return (
                    f"All {total_slots} memory slots are currently in use ({installed_str}). "
                    f"The board supports up to {max_cap}. To upgrade, you would need to replace existing modules with higher capacity sticks."
                )

        # Case 2: CPU Info
        if any(w in q for w in ["cpu", "processor", "core"]):
            cpu = data.get("get_cpu_info", {})
            model = cpu.get("model_name", "Unknown")
            cores = cpu.get("cores_total", "Unknown")
            threads = cpu.get("threads_per_core", "Unknown")
            arch = cpu.get("architecture", "Unknown")
            return f"Your CPU is an {model} ({arch} architecture) featuring {cores} total cores with {threads} thread(s) per core."

        # Case 3: Storage & NVMe
        if any(w in q for w in ["ssd", "nvme", "disk", "storage", "drive"]):
            block = data.get("get_block_devices", {})
            devices = block.get("block_devices", [])
            if not devices:
                return "I cannot determine storage details: no block devices were returned by the system."

            dev_summaries = []
            has_nvme = False
            for d in devices:
                tran = d.get("transport", "")
                if "nvme" in tran or "nvme" in d.get("name", ""):
                    has_nvme = True
                dev_summaries.append(f"{d.get('name')} ({d.get('size')}, {d.get('type')}, transport: {tran})")

            nvme_note = "Yes, your primary storage uses the high-speed NVMe protocol." if has_nvme else "No native NVMe transport detected on primary block devices."
            return f"{nvme_note} Detected storage devices: {'; '.join(dev_summaries)}."

        return "I have collected the requested system data. Please see the structured JSON output."
