import warnings
from ost_zak import security
def run_security_check(excel_path: str) -> str:
    return security.run_web(excel_path)
