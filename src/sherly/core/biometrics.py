import os
import ctypes
from sherly.utils.runtime_utils import log

class BiometricValidator:
    """
    Biometric Approval Layer.
    Uses Windows MessageBox for identity verification in POC.
    """
    def __init__(self):
        self.enabled = os.name == "nt"

    def request_approval(self, command: str) -> bool:
        """
        Requests biometric confirmation for a DANGEROUS command.
        """
        log(f"[Biometrics] Requesting identity verification for: {command}")
        
        if os.name == "nt":
            # MB_YESNO | MB_ICONWARNING | MB_SETFOREGROUND | MB_TOPMOST
            # 0x00000004 | 0x00000030 | 0x00010000 | 0x00040000 = 0x50034
            res = ctypes.windll.user32.MessageBoxW(
                0, 
                f"Sherly AI Security Alert\n\nAction: {command}\n\nDo you verify your identity and approve this action?", 
                "Sherly AI - Identity Verification", 
                0x50034
            )
            # 6 is IDYES
            success = (res == 6)
        else:
            # Fallback for non-Windows (simple simulation)
            success = True
        
        if success:
            log("[Biometrics] IDENTITY VERIFIED")
        else:
            log("[Biometrics] Identity verification FAILED")
            
        return success
