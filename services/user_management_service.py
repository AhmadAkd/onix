"""
User Management Service for Onix
Provides multi-user support and user profiles
"""

import json
import os
import hashlib
import threading
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
from constants import LogLevel


class UserProfile:
    """Represents a user profile."""

    def __init__(
        self,
        username: str,
        password_hash: str = None,
        is_admin: bool = False,
        settings: Dict[str, Any] = None,
    ):
        self.username = username
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.settings = settings or {}
        self.created_at = datetime.now()
        self.last_login = None
        self.login_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "is_admin": self.is_admin,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Create profile from dictionary."""
        profile = cls(
            username=data["username"],
            password_hash=data.get("password_hash"),
            is_admin=data.get("is_admin", False),
            settings=data.get("settings", {}),
        )

        if data.get("created_at"):
            profile.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("last_login"):
            profile.last_login = datetime.fromisoformat(data["last_login"])
        profile.login_count = data.get("login_count", 0)

        return profile


class UserManagementService:
    """Service for managing multiple users."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._users = {}
        self._current_user = None
        self._users_file = "users.json"
        self._lock = threading.Lock()
        self._load_users()

    def create_user(self, username: str, password: str, is_admin: bool = False) -> bool:
        """Create a new user."""
        try:
            with self._lock:
                if username in self._users:
                    self.log(f"User {username} already exists", LogLevel.WARNING)
                    return False

                password_hash = self._hash_password(password)
                profile = UserProfile(username, password_hash, is_admin)
                self._users[username] = profile
                self._save_users()

                self.log(f"Created user: {username}", LogLevel.SUCCESS)
                return True

        except Exception as e:
            self.log(f"Failed to create user: {e}", LogLevel.ERROR)
            return False

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        try:
            with self._lock:
                if username not in self._users:
                    return False

                profile = self._users[username]
                password_hash = self._hash_password(password)

                if profile.password_hash == password_hash:
                    profile.last_login = datetime.now()
                    profile.login_count += 1
                    self._current_user = profile
                    self._save_users()
                    self.log(f"User {username} authenticated", LogLevel.SUCCESS)
                    return True

                return False

        except Exception as e:
            self.log(f"Authentication failed: {e}", LogLevel.ERROR)
            return False

    def logout_user(self):
        """Logout current user."""
        if self._current_user:
            self.log(f"User {self._current_user.username} logged out", LogLevel.INFO)
            self._current_user = None

    def get_current_user(self) -> Optional[UserProfile]:
        """Get current user profile."""
        return self._current_user

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._current_user is not None

    def is_admin(self) -> bool:
        """Check if current user is admin."""
        return self._current_user and self._current_user.is_admin

    def update_user_settings(self, settings: Dict[str, Any]) -> bool:
        """Update current user settings."""
        try:
            if not self._current_user:
                return False

            with self._lock:
                self._current_user.settings.update(settings)
                self._save_users()
                self.log("User settings updated", LogLevel.SUCCESS)
                return True

        except Exception as e:
            self.log(f"Failed to update user settings: {e}", LogLevel.ERROR)
            return False

    def get_user_settings(self) -> Dict[str, Any]:
        """Get current user settings."""
        if self._current_user:
            return self._current_user.settings.copy()
        return {}

    def delete_user(self, username: str) -> bool:
        """Delete a user (admin only)."""
        try:
            if not self.is_admin():
                self.log("Only admins can delete users", LogLevel.WARNING)
                return False

            with self._lock:
                if username not in self._users:
                    return False

                del self._users[username]
                self._save_users()
                self.log(f"Deleted user: {username}", LogLevel.SUCCESS)
                return True

        except Exception as e:
            self.log(f"Failed to delete user: {e}", LogLevel.ERROR)
            return False

    def list_users(self) -> List[str]:
        """List all usernames (admin only)."""
        if not self.is_admin():
            return []
        return list(self._users.keys())

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information (admin only)."""
        if not self.is_admin() or username not in self._users:
            return None
        return self._users[username].to_dict()

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_users(self):
        """Load users from file."""
        try:
            if os.path.exists(self._users_file):
                with open(self._users_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for username, user_data in data.items():
                    self._users[username] = UserProfile.from_dict(user_data)

                self.log(f"Loaded {len(self._users)} users", LogLevel.INFO)
            else:
                # Create default admin user
                self.create_user("admin", "admin", True)
                self.log("Created default admin user", LogLevel.INFO)

        except Exception as e:
            self.log(f"Failed to load users: {e}", LogLevel.ERROR)

    def _save_users(self):
        """Save users to file."""
        try:
            data = {
                username: profile.to_dict() for username, profile in self._users.items()
            }
            with open(self._users_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.log(f"Failed to save users: {e}", LogLevel.ERROR)


class ConfigurationTemplate:
    """Represents a configuration template."""

    def __init__(
        self,
        name: str,
        description: str,
        config: Dict[str, Any],
        category: str = "general",
        tags: List[str] = None,
    ):
        self.name = name
        self.description = description
        self.config = config
        self.category = category
        self.tags = tags or []
        self.created_at = datetime.now()
        self.usage_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigurationTemplate":
        """Create template from dictionary."""
        template = cls(
            name=data["name"],
            description=data["description"],
            config=data["config"],
            category=data.get("category", "general"),
            tags=data.get("tags", []),
        )

        if data.get("created_at"):
            template.created_at = datetime.fromisoformat(data["created_at"])
        template.usage_count = data.get("usage_count", 0)

        return template


class ConfigurationTemplateManager:
    """Manager for configuration templates."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._templates = {}
        self._templates_file = "templates.json"
        self._load_templates()
        self._create_default_templates()

    def create_template(
        self,
        name: str,
        description: str,
        config: Dict[str, Any],
        category: str = "general",
        tags: List[str] = None,
    ) -> bool:
        """Create a new configuration template."""
        try:
            if name in self._templates:
                self.log(f"Template {name} already exists", LogLevel.WARNING)
                return False

            template = ConfigurationTemplate(name, description, config, category, tags)
            self._templates[name] = template
            self._save_templates()

            self.log(f"Created template: {name}", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(f"Failed to create template: {e}", LogLevel.ERROR)
            return False

    def get_template(self, name: str) -> Optional[ConfigurationTemplate]:
        """Get a template by name."""
        return self._templates.get(name)

    def list_templates(self, category: str = None) -> List[ConfigurationTemplate]:
        """List templates, optionally filtered by category."""
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return sorted(templates, key=lambda t: t.usage_count, reverse=True)

    def search_templates(self, query: str) -> List[ConfigurationTemplate]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        results = []

        for template in self._templates.values():
            if (
                query_lower in template.name.lower()
                or query_lower in template.description.lower()
                or any(query_lower in tag.lower() for tag in template.tags)
            ):
                results.append(template)

        return sorted(results, key=lambda t: t.usage_count, reverse=True)

    def apply_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Apply a template and increment usage count."""
        template = self._templates.get(name)
        if template:
            template.usage_count += 1
            self._save_templates()
            self.log(f"Applied template: {name}", LogLevel.SUCCESS)
            return template.config.copy()
        return None

    def delete_template(self, name: str) -> bool:
        """Delete a template."""
        try:
            if name in self._templates:
                del self._templates[name]
                self._save_templates()
                self.log(f"Deleted template: {name}", LogLevel.SUCCESS)
                return True
            return False

        except Exception as e:
            self.log(f"Failed to delete template: {e}", LogLevel.ERROR)
            return False

    def _load_templates(self):
        """Load templates from file."""
        try:
            if os.path.exists(self._templates_file):
                with open(self._templates_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for name, template_data in data.items():
                    self._templates[name] = ConfigurationTemplate.from_dict(
                        template_data
                    )

                self.log(f"Loaded {len(self._templates)} templates", LogLevel.INFO)

        except Exception as e:
            self.log(f"Failed to load templates: {e}", LogLevel.ERROR)

    def _save_templates(self):
        """Save templates to file."""
        try:
            data = {
                name: template.to_dict() for name, template in self._templates.items()
            }
            with open(self._templates_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.log(f"Failed to save templates: {e}", LogLevel.ERROR)

    def _create_default_templates(self):
        """Create default configuration templates."""
        if not self._templates:  # Only create if no templates exist
            default_templates = [
                {
                    "name": "High Performance",
                    "description": "Optimized for maximum speed and performance",
                    "category": "performance",
                    "tags": ["speed", "performance", "optimized"],
                    "config": {
                        "connection_mode": "Global",
                        "mux_enabled": True,
                        "mux_protocol": "smux",
                        "tls_fragment_enabled": True,
                        "connection_pool_size": 20,
                        "thread_pool_size": 10,
                        "buffer_size": 16384,
                        "compression_enabled": True,
                        "tcp_fast_open": True,
                        "congestion_control": "BBR",
                    },
                },
                {
                    "name": "Maximum Security",
                    "description": "Maximum security and privacy settings",
                    "category": "security",
                    "tags": ["security", "privacy", "secure"],
                    "config": {
                        "connection_mode": "Rule-Based",
                        "mux_enabled": False,
                        "tls_fragment_enabled": False,
                        "enable_ipv6": False,
                        "allow_insecure": False,
                        "cert_verification": True,
                        "connection_timeout": 60,
                        "retry_attempts": 2,
                        "disable_telemetry": True,
                        "disable_crash_reports": True,
                        "disable_usage_stats": True,
                    },
                },
                {
                    "name": "Balanced",
                    "description": "Balanced performance and security",
                    "category": "general",
                    "tags": ["balanced", "general", "default"],
                    "config": {
                        "connection_mode": "Rule-Based",
                        "mux_enabled": True,
                        "mux_protocol": "smux",
                        "tls_fragment_enabled": False,
                        "enable_ipv6": True,
                        "allow_insecure": False,
                        "cert_verification": True,
                        "connection_timeout": 30,
                        "retry_attempts": 3,
                        "connection_pool_size": 10,
                        "thread_pool_size": 5,
                        "buffer_size": 8192,
                    },
                },
            ]

            for template_data in default_templates:
                self.create_template(
                    template_data["name"],
                    template_data["description"],
                    template_data["config"],
                    template_data["category"],
                    template_data["tags"],
                )
