import subprocess
import os
import time
import json
import threading
import winreg
import ctypes
import sys
import utils
from constants import PROXY_SERVER_ADDRESS, PROXY_BYPASS

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)

class SingboxManager:
    def __init__(self, settings, callbacks):
        self.settings = settings
        self.callbacks = callbacks
        self.singbox_process = None
        self.singbox_pid = None
        self.current_config_file = None
        self.is_running = False

    def start(self, config):
        if self.is_running:
            self.log("Switching servers... Stopping previous connection first.")
            self.stop()
            time.sleep(0.5)

        self.current_config_file = f"temp_config_{int(time.time()*1000)}.json"
        
        self.log("Starting connection...")
        self.callbacks['on_status_change']("Connecting...", "yellow")

        thread = threading.Thread(target=self._run_and_log, args=(config, self.current_config_file), daemon=True)
        thread.start()
        
        # Schedule connection check
        threading.Timer(2.0, self.check_connection).start()

    def _run_and_log(self, config, config_filename):
        try:
            # 1. Generate config
            full_config = utils.generate_config_json(config, self.settings)
            with open(config_filename, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2)

            # 2. Validate config
            self.log("Validating configuration...")
            check_command = [get_resource_path('sing-box.exe'), 'check', '-c', config_filename]
            result = subprocess.run(check_command, capture_output=True, text=True,
                                    encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode != 0:
                error_message = result.stdout.strip() or result.stderr.strip()
                self.log("Configuration check failed!")
                self.log(f"Error: {error_message}")
                self.stop()
                return

            self.log("Configuration is valid. Starting process...")

            # 3. Run process
            command = [get_resource_path('sing-box.exe'), 'run', '-c', config_filename]
            self.singbox_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                    text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
            self.singbox_pid = self.singbox_process.pid
            self.is_running = True

            for line in iter(self.singbox_process.stdout.readline, ''):
                self.log(line.strip())

        except FileNotFoundError:
            self.log(f"Error: sing-box.exe not found at '{get_resource_path('sing-box.exe')}'!")
            self.is_running = False
        except Exception as e:
            self.log(f"An unexpected error occurred: {type(e).__name__}: {e}")
            self.is_running = False
        finally:
            # When process finishes or fails, update state
            self.is_running = False
            self.callbacks['on_stop']()


    def stop(self):
        pid_to_kill = self.singbox_pid
        process_to_kill = self.singbox_process

        self.singbox_process = None
        self.singbox_pid = None
        self.is_running = False

        if process_to_kill and process_to_kill.poll() is None:
            try:
                process_to_kill.kill()
                self.log("Sing-box process terminated.")
            except Exception as e:
                self.log(f"Failed to terminate process object: {e}. Falling back to PID kill.")
                if pid_to_kill:
                    self._kill_pid(pid_to_kill)
        elif pid_to_kill:
            self.log(f"Process object not active, attempting to clean up PID {pid_to_kill}.")
            self._kill_pid(pid_to_kill)

        try:
            if self.current_config_file and os.path.exists(self.current_config_file):
                os.remove(self.current_config_file)
        except OSError as e:
            self.log(f"Error removing config file: {e}")

        self.set_system_proxy(False)
        self.callbacks['on_stop']()

    def _kill_pid(self, pid):
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False,
                           capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log(f"Killed process with PID {pid} as a fallback.")
        except Exception as e:
            self.log(f"Fallback PID kill failed: {e}")

    def check_connection(self):
        result = utils.url_test(PROXY_SERVER_ADDRESS)
        if result != -1:
            self.log(f"Connection successful! Latency: {result} ms.")
            self.set_system_proxy(True)
            self.callbacks['on_connect'](result)
        else:
            self.log("Error: Connection test failed. Check server config.")
            self.callbacks['on_status_change']("Connection Failed", "red")
            self.stop()

    def set_system_proxy(self, enable):
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            internet_settings = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            
            if enable:
                user_domains = self.settings.get("bypass_domains", "")
                bypass_list = PROXY_BYPASS
                if user_domains:
                    user_domains_semicolon = ";".join(d.strip() for d in user_domains.split(','))
                    bypass_list = f"{PROXY_BYPASS};{user_domains_semicolon}"

                winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(internet_settings, "ProxyServer", 0, winreg.REG_SZ, PROXY_SERVER_ADDRESS)
                winreg.SetValueEx(internet_settings, "ProxyOverride", 0, winreg.REG_SZ, bypass_list)
            else:
                winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            
            winreg.CloseKey(internet_settings)

            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)  # INTERNET_OPTION_SETTINGS_CHANGED
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)  # INTERNET_OPTION_REFRESH
        except Exception as e:
            self.log(f"Failed to set system proxy: {e}")

    def log(self, message):
        self.callbacks['log'](message)