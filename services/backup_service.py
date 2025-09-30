"""
Backup Service for Onix
Provides automatic backup and restore functionality
"""

import json
import os
import shutil
import threading
import zipfile
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List
from constants import LogLevel


class BackupService:
    """Service for automatic backup and restore."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._backup_dir = "backups"
        self._auto_backup_enabled = False
        self._backup_interval = 3600  # 1 hour
        self._max_backups = 10
        self._backup_thread = None
        self._stop_event = threading.Event()
        self._ensure_backup_dir()

    def enable_auto_backup(self, enabled: bool = True, interval: int = 3600):
        """Enable or disable automatic backup."""
        self._auto_backup_enabled = enabled
        self._backup_interval = interval

        if enabled:
            self._start_auto_backup()
            self.log(
                f"Auto-backup enabled (interval: {interval}s)", LogLevel.SUCCESS)
        else:
            self._stop_auto_backup()
            self.log("Auto-backup disabled", LogLevel.INFO)

    def is_auto_backup_enabled(self) -> bool:
        """Check if auto-backup is enabled."""
        return self._auto_backup_enabled

    def create_backup(self, name: str = None) -> Optional[str]:
        """Create a manual backup."""
        try:
            if not name:
                name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            backup_path = os.path.join(self._backup_dir, f"{name}.zip")

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup settings
                if os.path.exists("settings.json"):
                    zipf.write("settings.json", "settings.json")

                # Backup servers
                if os.path.exists("servers.json"):
                    zipf.write("servers.json", "servers.json")

                # Backup users
                if os.path.exists("users.json"):
                    zipf.write("users.json", "users.json")

                # Backup templates
                if os.path.exists("templates.json"):
                    zipf.write("templates.json", "templates.json")

                # Backup logs
                log_files = ["xray_core.log", "singbox_core.log"]
                for log_file in log_files:
                    if os.path.exists(log_file):
                        zipf.write(log_file, f"logs/{log_file}")

                # Backup cache
                if os.path.exists("cache.db"):
                    zipf.write("cache.db", "cache.db")

                # Create backup metadata
                metadata = {
                    "name": name,
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "files": []
                }

                for file_info in zipf.infolist():
                    metadata["files"].append(file_info.filename)

                zipf.writestr("backup_metadata.json",
                              json.dumps(metadata, indent=2))

            self.log(f"Backup created: {name}", LogLevel.SUCCESS)
            self._cleanup_old_backups()
            return backup_path

        except Exception as e:
            self.log(f"Failed to create backup: {e}", LogLevel.ERROR)
            return None

    def restore_backup(self, backup_path: str) -> bool:
        """Restore from a backup."""
        try:
            if not os.path.exists(backup_path):
                self.log(
                    f"Backup file not found: {backup_path}", LogLevel.ERROR)
                return False

            # Create restore directory
            restore_dir = f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(restore_dir, exist_ok=True)

            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Extract all files
                zipf.extractall(restore_dir)

                # Read metadata
                # metadata_path = os.path.join(
                #     restore_dir, "backup_metadata.json")
                # Restore files
                files_to_restore = [
                    ("settings.json", "settings.json"),
                    ("servers.json", "servers.json"),
                    ("users.json", "users.json"),
                    ("templates.json", "templates.json"),
                    ("cache.db", "cache.db")
                ]

                for src, dst in files_to_restore:
                    src_path = os.path.join(restore_dir, src)
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, dst)

                # Restore logs
                logs_dir = os.path.join(restore_dir, "logs")
                if os.path.exists(logs_dir):
                    for log_file in os.listdir(logs_dir):
                        shutil.copy2(
                            os.path.join(logs_dir, log_file),
                            log_file
                        )

            # Cleanup restore directory
            shutil.rmtree(restore_dir)

            self.log(f"Backup restored: {backup_path}", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(f"Failed to restore backup: {e}", LogLevel.ERROR)
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []

        try:
            for filename in os.listdir(self._backup_dir):
                if filename.endswith('.zip'):
                    backup_path = os.path.join(self._backup_dir, filename)
                    stat = os.stat(backup_path)

                    backup_info = {
                        "name": filename[:-4],  # Remove .zip extension
                        "path": backup_path,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime)
                    }

                    # Try to read metadata
                    try:
                        with zipfile.ZipFile(backup_path, 'r') as zipf:
                            if "backup_metadata.json" in zipf.namelist():
                                metadata_str = zipf.read(
                                    "backup_metadata.json").decode('utf-8')
                                metadata = json.loads(metadata_str)
                                backup_info.update(metadata)
                    except Exception:
                        pass  # Use file system info if metadata unavailable

                    backups.append(backup_info)

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            self.log(f"Failed to list backups: {e}", LogLevel.ERROR)

        return backups

    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup."""
        try:
            backup_path = os.path.join(self._backup_dir, f"{backup_name}.zip")

            if os.path.exists(backup_path):
                os.remove(backup_path)
                self.log(f"Backup deleted: {backup_name}", LogLevel.SUCCESS)
                return True
            else:
                self.log(f"Backup not found: {backup_name}", LogLevel.WARNING)
                return False

        except Exception as e:
            self.log(f"Failed to delete backup: {e}", LogLevel.ERROR)
            return False

    def _start_auto_backup(self):
        """Start automatic backup thread."""
        if self._backup_thread and self._backup_thread.is_alive():
            return

        self._stop_event.clear()
        self._backup_thread = threading.Thread(
            target=self._auto_backup_loop,
            daemon=True
        )
        self._backup_thread.start()

    def _stop_auto_backup(self):
        """Stop automatic backup thread."""
        self._stop_event.set()
        if self._backup_thread and self._backup_thread.is_alive():
            self._backup_thread.join(timeout=2)

    def _auto_backup_loop(self):
        """Automatic backup loop."""
        while not self._stop_event.is_set():
            try:
                self.create_backup()
                self._stop_event.wait(self._backup_interval)
            except Exception as e:
                self.log(f"Auto-backup error: {e}", LogLevel.ERROR)
                self._stop_event.wait(300)  # Wait 5 minutes on error

    def _cleanup_old_backups(self):
        """Remove old backups to keep only max_backups."""
        try:
            backups = self.list_backups()

            if len(backups) > self._max_backups:
                # Sort by creation time and remove oldest
                backups.sort(key=lambda x: x["created_at"])
                backups_to_remove = backups[:-self._max_backups]

                for backup in backups_to_remove:
                    self.delete_backup(backup["name"])

        except Exception as e:
            self.log(f"Failed to cleanup old backups: {e}", LogLevel.ERROR)

    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        try:
            os.makedirs(self._backup_dir, exist_ok=True)
        except Exception as e:
            self.log(f"Failed to create backup directory: {e}", LogLevel.ERROR)


class AdvancedConfigurationManager:
    """Manager for advanced configuration options."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._config_schema = self._load_config_schema()
        self._validation_rules = self._load_validation_rules()

    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration against schema and rules."""
        errors = []

        try:
            # Validate against schema
            for key, value in config.items():
                if key in self._config_schema:
                    schema = self._config_schema[key]
                    error = self._validate_value(key, value, schema)
                    if error:
                        errors.append(error)

            # Validate against rules
            for rule in self._validation_rules:
                error = rule(config)
                if error:
                    errors.append(error)

        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return self._config_schema.copy()

    def get_validation_rules(self) -> List[Callable]:
        """Get validation rules."""
        return self._validation_rules.copy()

    def _validate_value(self, key: str, value: Any, schema: Dict[str, Any]) -> Optional[str]:
        """Validate a single value against its schema."""
        try:
            # Type validation
            expected_type = schema.get("type")
            if expected_type and not isinstance(value, expected_type):
                return f"{key}: expected {expected_type.__name__}, got {type(value).__name__}"

            # Range validation
            if "min" in schema and value < schema["min"]:
                return f"{key}: value {value} is less than minimum {schema['min']}"
            if "max" in schema and value > schema["max"]:
                return f"{key}: value {value} is greater than maximum {schema['max']}"

            # Enum validation
            if "enum" in schema and value not in schema["enum"]:
                return f"{key}: value {value} is not in allowed values {schema['enum']}"

            # Pattern validation
            if "pattern" in schema:
                import re
                if not re.match(schema["pattern"], str(value)):
                    return f"{key}: value {value} does not match pattern {schema['pattern']}"

        except Exception as e:
            return f"{key}: validation error - {e}"

        return None

    def _load_config_schema(self) -> Dict[str, Any]:
        """Load configuration schema."""
        return {
            "connection_mode": {
                "type": str,
                "enum": ["Rule-Based", "Global", "Direct"]
            },
            "dns_servers": {
                "type": str,
                "pattern": r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(,\s*)?)+$"
            },
            "bypass_domains": {
                "type": str
            },
            "bypass_ips": {
                "type": str,
                "pattern": r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(/\d{1,2})?(,\s*)?)+$"
            },
            "tun_enabled": {
                "type": bool
            },
            "mux_enabled": {
                "type": bool
            },
            "mux_protocol": {
                "type": str,
                "enum": ["smux", "yamux"]
            },
            "mux_max_streams": {
                "type": int,
                "min": 1,
                "max": 100
            },
            "tls_fragment_enabled": {
                "type": bool
            },
            "tls_fragment_size": {
                "type": str,
                "pattern": r"^\d+-\d+$"
            },
            "connection_timeout": {
                "type": int,
                "min": 5,
                "max": 300
            },
            "retry_attempts": {
                "type": int,
                "min": 0,
                "max": 10
            },
            "connection_pool_size": {
                "type": int,
                "min": 1,
                "max": 100
            },
            "thread_pool_size": {
                "type": int,
                "min": 1,
                "max": 50
            },
            "buffer_size": {
                "type": int,
                "min": 1024,
                "max": 65536
            },
            "statistics_interval": {
                "type": int,
                "min": 1,
                "max": 60
            }
        }

    def _load_validation_rules(self) -> List[Callable]:
        """Load validation rules."""
        return [
            # Rule: If mux is enabled, mux_protocol must be specified
            lambda config: (
                "mux_protocol must be specified when mux is enabled"
                if config.get("mux_enabled") and not config.get("mux_protocol")
                else None
            ),

            # Rule: If TLS fragment is enabled, fragment size must be specified
            lambda config: (
                "tls_fragment_size must be specified when TLS fragment is enabled"
                if config.get("tls_fragment_enabled") and not config.get("tls_fragment_size")
                else None
            ),

            # Rule: Connection timeout should be reasonable
            lambda config: (
                "connection_timeout should be at least 10 seconds for stability"
                if config.get("connection_timeout", 30) < 10
                else None
            ),

            # Rule: Buffer size should be power of 2
            lambda config: (
                "buffer_size should be a power of 2 for optimal performance"
                if config.get("buffer_size") and not (config["buffer_size"] & (config["buffer_size"] - 1)) == 0
                else None
            )
        ]
