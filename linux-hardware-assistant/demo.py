"""
Demonstration Runner for Problem 2: Local Linux Hardware Q&A Assistant
Works on live Linux machines or via realistic mock outputs.
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from assistant.execution import SystemExecutor, ExecutionSafetyError
from assistant.agent import HardwareAssistantAgent

# Realistic sample outputs from Linux host utilities
MOCK_LINUX_OUTPUTS = {
    "get_dmi_memory": """# dmidecode 3.5
Getting SMBIOS data from sysfs.
SMBIOS 3.3.0 present.

Handle 0x0010, DMI type 16, 23 bytes
Physical Memory Array
	Location: System Board
	Use: System Memory
	Error Correction Type: None
	Maximum Capacity: 64 GB
	Number Of Devices: 2

Handle 0x0011, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x0010
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16 GB
	Form Factor: SODIMM
	Type: DDR4
	Speed: 3200 MT/s
	Manufacturer: Samsung

Handle 0x0012, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x0010
	Total Width: Unknown
	Data Width: Unknown
	Size: No Module Installed
	Form Factor: SODIMM
	Type: Unknown
	Speed: Unknown
""",
    "get_memory_summary": """               total        used        free      shared  buff/cache   available
Mem:     16654761984  4219432960  8210341888   419430400  4224987136 12015898624
Swap:     4294967296           0  4294967296
""",
    "get_cpu_info": """Architecture:            x86_64
  CPU op-mode(s):        32-bit, 64-bit
  Address sizes:         39 bits physical, 48 bits virtual
  Byte Order:            Little Endian
CPU(s):                  8
  On-line CPU(s) list:   0-7
Vendor ID:               GenuineIntel
  Model name:            11th Gen Intel(R) Core(TM) i7-1165G7 @ 2.80GHz
    Thread(s) per core:  2
    Core(s) per socket:  4
    Socket(s):           1
CPU max MHz:             4700.0000
Virtualization:          VT-x
""",
    "get_block_devices": """{
   "blockdevices": [
      {
         "name": "nvme0n1",
         "size": "512G",
         "type": "disk",
         "mountpoint": null,
         "model": "Samsung PM981a NVMe 512GB",
         "rota": false,
         "tran": "nvme"
      },
      {
         "name": "nvme0n1p1",
         "size": "512M",
         "type": "part",
         "mountpoint": "/boot/efi",
         "model": null,
         "rota": false,
         "tran": null
      },
      {
         "name": "nvme0n1p2",
         "size": "511.5G",
         "type": "part",
         "mountpoint": "/",
         "model": null,
         "rota": false,
         "tran": null
      }
   ]
}"""
}

def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def main():
    print_separator("ASAMA.AI - LOCAL LINUX HARDWARE Q&A ASSISTANT DEMO")

    # Initialize agent with deterministic safe executor
    executor = SystemExecutor(mock_mode=True, mock_outputs=MOCK_LINUX_OUTPUTS)
    agent = HardwareAssistantAgent(executor=executor)

    # Demo Turn 1: Memory upgrade question
    q1 = "Can I upgrade my RAM, and by how much?"
    print(f"\n[User Query 1]: \"{q1}\"")
    res1 = agent.answer_query(q1)
    print(f"Tools Selected  : {res1['tools_called']}")
    print(f"Structured Data :\n{json.dumps(res1['structured_data']['get_dmi_memory'], indent=2)}")
    print(f"\n[Assistant Answer]:\n{res1['answer']}")

    # Demo Turn 2: Follow-up storage question (relies on conversation state)
    q2 = "Is my primary SSD NVMe?"
    print_separator("FOLLOW-UP CONVERSATION TURN")
    print(f"[User Query 2]: \"{q2}\"")
    res2 = agent.answer_query(q2)
    print(f"Tools Selected  : {res2['tools_called']}")
    print(f"Structured Data :\n{json.dumps(res2['structured_data']['get_block_devices'], indent=2)}")
    print(f"\n[Assistant Answer]:\n{res2['answer']}")

    # Demo Turn 3: Follow-up CPU question
    q3 = "What processor is installed in this laptop?"
    print_separator("FOLLOW-UP CONVERSATION TURN")
    print(f"[User Query 3]: \"{q3}\"")
    res3 = agent.answer_query(q3)
    print(f"Tools Selected  : {res3['tools_called']}")
    print(f"Structured Data :\n{json.dumps(res3['structured_data']['get_cpu_info'], indent=2)}")
    print(f"\n[Assistant Answer]:\n{res3['answer']}")

    # Demo Turn 4: Security test (Arbitrary Code Execution / Shell Injection defense)
    print_separator("SECURITY TEST: ARBITRARY CODE EXECUTION REJECTION")
    malicious_tool = "dmidecode; rm -rf /"
    print(f"Simulating rogue LLM attempting unauthorized command: '{malicious_tool}'")
    try:
        executor.execute_tool(malicious_tool)
    except ExecutionSafetyError as err:
        print(f"\n[BLOCKED] Security Engine successfully rejected unauthorized execution:")
        print(f"Reason: {err}")

    print_separator("DEMO COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    main()
