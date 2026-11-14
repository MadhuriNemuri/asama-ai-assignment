# Local Linux Hardware Q&A Assistant

> **Asama.ai AI Engineering Assignment — Problem 2**  
> A local, natural-language conversational assistant that inspects a host Linux laptop's hardware specifications and answers user queries with high precision using a deterministic, safe tool-calling engine.

---

## 1. System Architecture & Tool-Calling Pipeline

```
                       +-----------------------------------+
                       |    User Chat Interface (CLI/UI)   |
                       +-----------------------------------+
                                         |
                                         v
                       +-----------------------------------+
                       |    Conversation State & Context   |
                       +-----------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           LLM ORCHESTRATION ENGINE                                |
|                                                                                   |
|  +---------------------------+                +--------------------------------+  |
|  | Function / Tool Selector  | <============> | System Prompt & Dynamic Specs  |  |
|  +---------------------------+                +--------------------------------+  |
+-----------------------------------------------------------------------------------+
                                         |
                       (Structured Tool Call Request)
                                         v
+-----------------------------------------------------------------------------------+
|                     SAFE EXECUTION & PARSING SERVICE                              |
|                                                                                   |
|  +------------------------+  +------------------------+  +---------------------+  |
|  | Command Allow-List     |  | Privileged Helper      |  | Regex/Text Parsers  |  |
|  | Verification           |  | (Polkit / Sudo Daemon) |  | (Structured JSON)   |  |
|  +------------------------+  +------------------------+  +---------------------+  |
+-----------------------------------------------------------------------------------+
                                         |
                            (Normalized Data JSON)
                                         v
+-----------------------------------------------------------------------------------+
|                       FINAL RESPONSE GENERATOR (LLM)                              |
+-----------------------------------------------------------------------------------+
```

---

## 2. Security & Execution Safety Model

The core priority is **Zero Arbitrary Execution**:
1. **Strict Command Allow-List**: The LLM never generates arbitrary bash strings. It only selects pre-defined Tool Names (`get_dmi_memory`, `get_cpu_info`, `get_block_devices`, etc.).
2. **No Subshell Spawning (`shell=False`)**: Commands are invoked directly via OS syscalls (`execve`), bypassing `/bin/sh` to make command chaining (`;`, `&&`, `|`) impossible.
3. **Fixed Arguments & Regex Validation**: Tools map to static system command lists with fixed parameters.
4. **Execution Timeouts & Output Capping**: Subprocesses timeout after 5 seconds to prevent hung or frozen processes.

```
       [LLM Request: "run_command('dmidecode; rm -rf /')"]
                                |
                                v
                +-------------------------------+
                |  Is function in Allow-List?   |
                +-------------------------------+
                     |                     |
                  (No / Invalid)       (Yes: Safe Tool ID)
                     |                     |
                     v                     v
            [REJECT EXECUTION]     [Map to Fixed Binary Path]
                                   `execve("/usr/sbin/dmidecode", ["-t", "memory"])`
```

---

## 3. Handling `root` Permissions Safely

Running the whole assistant as `root` is a dangerous anti-pattern. This project supports three safe privilege models:

| Strategy | Mechanism | Recommended For |
| :--- | :--- | :--- |
| **A. Scoped Sudo Rule** | Add `/etc/sudoers.d/hw-assistant`:<br>`user ALL=(ALL) NOPASSWD: /usr/sbin/dmidecode` | Production & CLI setups |
| **B. Privilege Helper Daemon** | A small root daemon exposing a local Unix domain socket with strict RPC methods (`GetDmiInfo`). | Desktop & GUI Applications |
| **C. Non-Root Fallback** | Falls back to unprivileged paths (`/proc/meminfo`, `/sys/class/dmi/id/`, `lscpu`, `lsblk`). | Zero-install fallback |

---

## 4. Anti-Hallucination & Uncertainty Handling

The assistant enforces a strict grounding prompt:
* *"Base your response solely on the provided JSON tool output. If the JSON does not contain the answer, state 'I cannot determine this hardware detail from system data' and list missing tools."*
* If `dmidecode` is unavailable or denied, it reports installed memory from unprivileged `/proc/meminfo` and explicitly explains that motherboard slot topology requires elevated permissions.

---

## 5. Quick Start & Running the Demo

### Prerequisites
Activate your virtual environment and install requirements:
```bash
cd linux-hardware-assistant
pip install -r requirements.txt
```

### Run the Interactive Simulation Demo
```bash
python demo.py
```
This executes:
1. **RAM Upgrade Query**: Inspects slot count, used vs. free DIMM sockets, and maximum motherboard capacity.
2. **Follow-Up Storage Query**: Verifies NVMe transport protocol without re-querying RAM.
3. **Follow-Up CPU Query**: Reports architecture, model, and physical cores.
4. **Security Defense Test**: Rejects an attempted arbitrary shell injection (`dmidecode; rm -rf /`).

### Run Test Suite
```bash
pytest tests/ -v
```
