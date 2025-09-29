import winreg
import ctypes
from constants import PROXY_SERVER_ADDRESS, PROXY_BYPASS, LogLevel


def set_system_proxy(enable, settings, log_callback):
    """Sets or unsets the system-wide proxy settings for Windows."""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE
        ) as internet_settings:
            if enable:
                user_domains = settings.get("bypass_domains", "")
                bypass_list = PROXY_BYPASS
                if user_domains:
                    user_domains_semicolon = ";".join(
                        d.strip() for d in user_domains.split(",")
                    )
                    bypass_list = f"{PROXY_BYPASS};{user_domains_semicolon}"

                winreg.SetValueEx(
                    internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 1
                )
                winreg.SetValueEx(
                    internet_settings,
                    "ProxyServer",
                    0,
                    winreg.REG_SZ,
                    PROXY_SERVER_ADDRESS,
                )
                winreg.SetValueEx(
                    internet_settings, "ProxyOverride", 0, winreg.REG_SZ, bypass_list
                )
            else:
                winreg.SetValueEx(
                    internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 0
                )

        ctypes.windll.Wininet.InternetSetOptionW(
            0, 39, 0, 0
        )  # INTERNET_OPTION_SETTINGS_CHANGED
        ctypes.windll.Wininet.InternetSetOptionW(
            0, 37, 0, 0)  # INTERNET_OPTION_REFRESH
    except (OSError, PermissionError) as e:
        error_msg = f"Failed to set system proxy due to permissions or OS error: {e}"
        if log_callback:
            log_callback(error_msg, LogLevel.ERROR)
    except Exception as e:
        error_msg = f"An unexpected error occurred while setting system proxy: {e}"
        if log_callback:
            log_callback(error_msg, LogLevel.ERROR)
