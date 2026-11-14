import subprocess
import shutil
from typing import Dict, Any, List, Optional
from assistant.config import ALLOW_LISTED_TOOLS, EXECUTION_TIMEOUT_SECONDS

class ExecutionSafetyError(Exception):
    """Raised when an unauthorized command or execution parameter is detected."""
    pass

class SystemExecutor:
    """
    Safe execution engine adhering to the Principle of Least Privilege:
    1. Strict Allow-List: Only registered commands can run.
    2. No Subshell Spawning (shell=False): Prevents command chaining (;, &&, |).
    3. Fixed Binary Paths: Binaries are resolved deterministically.
    4. Execution Timeouts & Resource Limits: Prevents hung processes.
    """

    def __init__(self, mock_mode: bool = False, mock_outputs: Optional[Dict[str, str]] = None):
        self.mock_mode = mock_mode
        self.mock_outputs = mock_outputs or {}

    def is_tool_allowed(self, tool_name: str) -> bool:
        return tool_name in ALLOW_LISTED_TOOLS

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Safely executes an allow-listed tool without shell injection risks."""
        if not self.is_tool_allowed(tool_name):
            raise ExecutionSafetyError(f"Security Alert: Unauthorized tool execution attempt: '{tool_name}'")

        # In mock mode (e.g., during testing or non-Linux execution)
        if self.mock_mode:
            raw_stdout = self.mock_outputs.get(tool_name, "")
            return {"status": "success", "stdout": raw_stdout, "tool_name": tool_name}

        cmd_args = ALLOW_LISTED_TOOLS[tool_name]
        binary = cmd_args[0]

        # Verify binary presence
        if binary != "sudo" and not shutil.which(binary):
            return {
                "status": "error",
                "error": f"Binary '{binary}' is not installed on this system.",
                "tool_name": tool_name
            }

        try:
            # shell=False ensures the command is invoked directly via execve syscall
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                check=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                shell=False
            )
            return {
                "status": "success",
                "stdout": result.stdout,
                "tool_name": tool_name
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": f"Tool '{tool_name}' timed out after {EXECUTION_TIMEOUT_SECONDS}s.",
                "tool_name": tool_name
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": f"Execution failed with returncode {e.returncode}: {e.stderr.strip()}",
                "tool_name": tool_name
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"System error: {str(e)}",
                "tool_name": tool_name
            }

system_executor = SystemExecutor()
