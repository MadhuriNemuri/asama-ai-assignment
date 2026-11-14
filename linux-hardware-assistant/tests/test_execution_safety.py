import sys
import os

# Ensure package root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from assistant.execution import SystemExecutor, ExecutionSafetyError
from assistant.parsers import parse_dmi_memory, parse_cpu_info, parse_block_devices

def test_unauthorized_tool_rejected():
    executor = SystemExecutor(mock_mode=True)
    
    # Verify unauthorized tool rejection
    rejected_1 = False
    try:
        executor.execute_tool("rm -rf /")
    except ExecutionSafetyError:
        rejected_1 = True
    assert rejected_1, "Expected ExecutionSafetyError for 'rm -rf /'"

    # Verify shell injection attempt rejection
    rejected_2 = False
    try:
        executor.execute_tool("get_cpu_info; cat /etc/shadow")
    except ExecutionSafetyError:
        rejected_2 = True
    assert rejected_2, "Expected ExecutionSafetyError for command injection attempt"

def test_parse_dmi_memory():
    sample = """
Maximum Capacity: 64 GB
Number Of Devices: 2
Memory Device
	Size: 16 GB
	Type: DDR4
	Speed: 3200 MT/s
Memory Device
	Size: No Module Installed
"""
    parsed = parse_dmi_memory(sample)
    assert parsed["maximum_capacity"] == "64 GB"
    assert parsed["total_slots"] == 2
    assert parsed["used_slots"] == 1
    assert parsed["free_slots"] == 1

def test_parse_cpu_info():
    sample = """
Architecture: x86_64
Model name: Intel Core i7-1165G7
CPU(s): 8
Thread(s) per core: 2
"""
    parsed = parse_cpu_info(sample)
    assert parsed["architecture"] == "x86_64"
    assert "i7" in parsed["model_name"]
    assert parsed["cores_total"] == 8

if __name__ == "__main__":
    print("Running tests in test_execution_safety.py...")
    test_unauthorized_tool_rejected()
    print("  [✓] test_unauthorized_tool_rejected passed")
    test_parse_dmi_memory()
    print("  [✓] test_parse_dmi_memory passed")
    test_parse_cpu_info()
    print("  [✓] test_parse_cpu_info passed")
    print("\nALL TESTS PASSED SUCCESSFULLY!")

