"""Template: drop-in self-declaring Enforcer module.
Copy to modules/remote/yourmodule.py, fill in MODULE dict, implement run().
Zero framework edits needed — auto-discovered on startup."""

import subprocess, sys
from pathlib import Path

SCRIPTS_DIR = Path("/root/sploits/Enforcer")

MODULE = {
    "name": "module_name_here",
    "type": "remote",         # remote | recon | local
    "cve": "CVE-XXXX-XXXXX",
    "desc": "Short description shown in 'list' and 'use'",
    "script": "exploit_script.py",
    
    # Options shown in 'set' and 'options'
    "options": {
        "RHOST":    {"default": "",    "required": True,  "desc": "Target host"},
        "RPORT":    {"default": "443", "required": False, "desc": "Target port"},
        "TIMEOUT":  {"default": "10",  "required": False, "desc": "Request timeout"},
        "COMMAND":  {"default": "id",  "required": False, "desc": "Command to run"},
    },
    
    # Payloads: each has a --flag. Optional: "takes" = option whose value to pass
    "payloads": {
        "check":      {"flag": "--check",              "desc": "Vulnerability detection"},
        "harvest":    {"flag": "--harvest",            "desc": "Data harvesting"},
        "exploit":    {"flag": "--exploit",  "takes": "COMMAND", "desc": "Exploit + command"},
    },
    
    # arg_map: only map REGULAR options (not handled by payloads above)
    "arg_map": {
        "RPORT":   "-p",
        "TIMEOUT": "-t",
    },
    
    # Flags: boolean options passed as --flag (no value)
    "flags": {
        "STEALTH": "--stealth",
    },
    
    # Settings
    "no_json": True,    # Set if exploit script doesn't support --json
    "https": False,     # True = prepend https:// to RHOST
}

def run(options: dict, dry: bool = False) -> tuple:
    """Execute the exploit. Called by enforcer-console.py's do_run."""
    script = SCRIPTS_DIR / MODULE["script"]
    if not script.exists():
        return False, f"Script not found: {script}"
    
    argv = [sys.executable, str(script)]
    
    # Add host
    host = options.get("RHOST", "")
    if host:
        prefix = "https://" if MODULE.get("https") else ""
        argv.append(f"{prefix}{host}")
    
    # Map options to CLI flags
    payload = options.get("PAYLOAD", "")
    for opt, val in options.items():
        if opt == "RHOST" or not val or val in ("", "auto", "false", "none"):
            continue
        
        # Payload handling
        if opt == "PAYLOAD":
            pl = MODULE["payloads"].get(val, {})
            if pl.get("flag"):
                argv.append(pl["flag"])
                # If payload takes a value (e.g., --exploit <COMMAND>)
                if pl.get("takes") and options.get(pl["takes"]):
                    argv.append(options[pl["takes"]])
            continue
        
        # Boolean flags
        if opt in MODULE.get("flags", {}):
            if val.lower() in ("true", "yes", "1"):
                argv.append(MODULE["flags"][opt])
            continue
        
        # Regular arg_map flags
        flag = MODULE["arg_map"].get(opt, "")
        if flag:
            argv.append(flag)
            argv.append(str(val))
    
    if not MODULE.get("no_json"):
        argv.append("--json")
    
    if dry:
        return True, "DRY RUN: " + " ".join(map(str, argv))
    
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=120)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT — exploit execution exceeded time limit"
    except Exception as e:
        return False, str(e)
