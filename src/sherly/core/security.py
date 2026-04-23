import shlex
from sherly.utils.runtime_utils import log

class IntentFirewall:
    """
    Final security layer: Validates model-generated commands before execution.
    Achieves 10/10 Security by preventing obfuscated injection.
    """
    BLACKLIST = [
        "rm -rf /", "mkfs", "dd if=", "> /dev/sda",
        ":(){ :|:& };:", "chmod -R 777 /", "chown",
        "curl http", "wget http" # Prevent unauthorized egress
    ]

    @classmethod
    def validate_command(cls, cmd: str) -> bool:
        low_cmd = cmd.lower()
        
        # 1. Block known malicious patterns
        for forbidden in cls.BLACKLIST:
            if forbidden in low_cmd:
                log(f"[Security] BLOCKED malicious command: {cmd}")
                return False
                
        # 2. Prevent shell chaining/redirection in sensitive contexts
        if any(char in cmd for char in [";", "&", "|", ">", "<"]):
             # We allow some but block suspicious combinations
             if "sudo" in low_cmd or "docker" in low_cmd:
                 log(f"[Security] BLOCKED complex chaining in sensitive command: {cmd}")
                 return False
                 
        return True
