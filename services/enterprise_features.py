"""
Enterprise Features for Onix
Provides multi-tenant support, RBAC, audit logging, and compliance reporting
"""

import time
import threading
import json
import hashlib
import uuid
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from constants import LogLevel


class UserRole(Enum):
    """User roles in the system."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


class Permission(Enum):
    """System permissions."""
    # Server management
    MANAGE_SERVERS = "manage_servers"
    VIEW_SERVERS = "view_servers"
    CONNECT_SERVERS = "connect_servers"

    # User management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"

    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_ANALYTICS = "export_analytics"

    # Settings
    MANAGE_SETTINGS = "manage_settings"
    VIEW_SETTINGS = "view_settings"

    # Plugins
    MANAGE_PLUGINS = "manage_plugins"
    INSTALL_PLUGINS = "install_plugins"

    # Security
    MANAGE_SECURITY = "manage_security"
    VIEW_SECURITY_LOGS = "view_security_logs"


@dataclass
class User:
    """User entity."""
    id: str
    username: str
    email: str
    role: UserRole
    permissions: Set[Permission]
    is_active: bool = True
    created_at: float = 0.0
    last_login: float = 0.0
    tenant_id: str = "default"


@dataclass
class Tenant:
    """Tenant entity for multi-tenancy."""
    id: str
    name: str
    domain: str
    max_users: int = 100
    max_servers: int = 50
    features: Set[str] = None
    is_active: bool = True
    created_at: float = 0.0


@dataclass
class AuditLog:
    """Audit log entry."""
    id: str
    user_id: str
    tenant_id: str
    action: str
    resource: str
    details: Dict[str, Any]
    timestamp: float
    ip_address: str = ""
    user_agent: str = ""


class RoleBasedAccessControl:
    """Role-Based Access Control system."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self.users: Dict[str, User] = {}
        self.roles_permissions: Dict[UserRole, Set[Permission]] = {
            UserRole.SUPER_ADMIN: set(Permission),
            UserRole.ADMIN: {
                Permission.MANAGE_SERVERS, Permission.VIEW_SERVERS, Permission.CONNECT_SERVERS,
                Permission.MANAGE_USERS, Permission.VIEW_USERS,
                Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS,
                Permission.MANAGE_SETTINGS, Permission.VIEW_SETTINGS,
                Permission.MANAGE_PLUGINS, Permission.INSTALL_PLUGINS,
                Permission.MANAGE_SECURITY, Permission.VIEW_SECURITY_LOGS
            },
            UserRole.MANAGER: {
                Permission.VIEW_SERVERS, Permission.CONNECT_SERVERS,
                Permission.VIEW_USERS,
                Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS,
                Permission.VIEW_SETTINGS,
                Permission.VIEW_SECURITY_LOGS
            },
            UserRole.USER: {
                Permission.VIEW_SERVERS, Permission.CONNECT_SERVERS,
                Permission.VIEW_ANALYTICS
            },
            UserRole.GUEST: {
                Permission.VIEW_SERVERS
            }
        }
        self._lock = threading.Lock()

    def create_user(self, username: str, email: str, role: UserRole,
                    tenant_id: str = "default") -> Optional[User]:
        """Create a new user."""
        try:
            with self._lock:
                user_id = str(uuid.uuid4())
                permissions = self.roles_permissions.get(role, set())

                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    role=role,
                    permissions=permissions,
                    created_at=time.time(),
                    tenant_id=tenant_id
                )

                self.users[user_id] = user
                self.log(
                    f"Created user: {username} with role {role.value}", LogLevel.INFO)
                return user

        except Exception as e:
            self.log(f"Error creating user: {e}", LogLevel.ERROR)
            return None

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """Update user role."""
        try:
            with self._lock:
                if user_id not in self.users:
                    return False

                user = self.users[user_id]
                user.role = new_role
                user.permissions = self.roles_permissions.get(new_role, set())

                self.log(
                    f"Updated user {user.username} role to {new_role.value}", LogLevel.INFO)
                return True

        except Exception as e:
            self.log(f"Error updating user role: {e}", LogLevel.ERROR)
            return False

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission."""
        try:
            user = self.get_user(user_id)
            if not user or not user.is_active:
                return False

            return permission in user.permissions

        except Exception as e:
            self.log(f"Error checking permission: {e}", LogLevel.ERROR)
            return False

    def list_users(self, tenant_id: str = None) -> List[User]:
        """List users, optionally filtered by tenant."""
        try:
            users = list(self.users.values())
            if tenant_id:
                users = [u for u in users if u.tenant_id == tenant_id]
            return users

        except Exception as e:
            self.log(f"Error listing users: {e}", LogLevel.ERROR)
            return []

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user."""
        try:
            with self._lock:
                if user_id not in self.users:
                    return False

                self.users[user_id].is_active = False
                self.log(
                    f"Deactivated user: {self.users[user_id].username}", LogLevel.INFO)
                return True

        except Exception as e:
            self.log(f"Error deactivating user: {e}", LogLevel.ERROR)
            return False


class MultiTenantManager:
    """Multi-tenant management system."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_resources: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        # Create default tenant
        self._create_default_tenant()

    def _create_default_tenant(self):
        """Create default tenant."""
        default_tenant = Tenant(
            id="default",
            name="Default Tenant",
            domain="localhost",
            max_users=1000,
            max_servers=100,
            features={"all"}
        )
        self.tenants["default"] = default_tenant
        self.tenant_resources["default"] = {
            "servers": [],
            "users": [],
            "settings": {}
        }

    def create_tenant(self, name: str, domain: str, max_users: int = 100,
                      max_servers: int = 50, features: Set[str] = None) -> Optional[Tenant]:
        """Create a new tenant."""
        try:
            with self._lock:
                tenant_id = str(uuid.uuid4())
                tenant = Tenant(
                    id=tenant_id,
                    name=name,
                    domain=domain,
                    max_users=max_users,
                    max_servers=max_servers,
                    features=features or {"basic"},
                    created_at=time.time()
                )

                self.tenants[tenant_id] = tenant
                self.tenant_resources[tenant_id] = {
                    "servers": [],
                    "users": [],
                    "settings": {}
                }

                self.log(f"Created tenant: {name} ({domain})", LogLevel.INFO)
                return tenant

        except Exception as e:
            self.log(f"Error creating tenant: {e}", LogLevel.ERROR)
            return None

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self.tenants.get(tenant_id)

    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain."""
        for tenant in self.tenants.values():
            if tenant.domain == domain:
                return tenant
        return None

    def add_resource_to_tenant(self, tenant_id: str, resource_type: str, resource_id: str) -> bool:
        """Add resource to tenant."""
        try:
            with self._lock:
                if tenant_id not in self.tenant_resources:
                    return False

                if resource_type not in self.tenant_resources[tenant_id]:
                    self.tenant_resources[tenant_id][resource_type] = []

                if resource_id not in self.tenant_resources[tenant_id][resource_type]:
                    self.tenant_resources[tenant_id][resource_type].append(
                        resource_id)

                return True

        except Exception as e:
            self.log(f"Error adding resource to tenant: {e}", LogLevel.ERROR)
            return False

    def get_tenant_resources(self, tenant_id: str, resource_type: str = None) -> Dict[str, Any]:
        """Get tenant resources."""
        try:
            resources = self.tenant_resources.get(tenant_id, {})
            if resource_type:
                return {resource_type: resources.get(resource_type, [])}
            return resources

        except Exception as e:
            self.log(f"Error getting tenant resources: {e}", LogLevel.ERROR)
            return {}

    def check_tenant_limits(self, tenant_id: str, resource_type: str) -> bool:
        """Check if tenant is within resource limits."""
        try:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return False

            resources = self.get_tenant_resources(tenant_id, resource_type)
            current_count = len(resources.get(resource_type, []))

            if resource_type == "users":
                return current_count < tenant.max_users
            elif resource_type == "servers":
                return current_count < tenant.max_servers

            return True

        except Exception as e:
            self.log(f"Error checking tenant limits: {e}", LogLevel.ERROR)
            return False


class AuditLogger:
    """Audit logging system."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self.audit_logs: List[AuditLog] = []
        self._lock = threading.Lock()
        self.max_logs = 10000  # Keep last 10k logs

    def log_action(self, user_id: str, tenant_id: str, action: str,
                   resource: str, details: Dict[str, Any] = None,
                   ip_address: str = "", user_agent: str = "") -> str:
        """Log an action."""
        try:
            with self._lock:
                log_id = str(uuid.uuid4())
                audit_log = AuditLog(
                    id=log_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    action=action,
                    resource=resource,
                    details=details or {},
                    timestamp=time.time(),
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                self.audit_logs.append(audit_log)

                # Keep only recent logs
                if len(self.audit_logs) > self.max_logs:
                    self.audit_logs = self.audit_logs[-self.max_logs:]

                self.log(
                    f"Audit log: {action} on {resource} by {user_id}", LogLevel.INFO)
                return log_id

        except Exception as e:
            self.log(f"Error logging action: {e}", LogLevel.ERROR)
            return ""

    def get_audit_logs(self, user_id: str = None, tenant_id: str = None,
                       action: str = None, limit: int = 100) -> List[AuditLog]:
        """Get audit logs with optional filters."""
        try:
            with self._lock:
                logs = self.audit_logs.copy()

                # Apply filters
                if user_id:
                    logs = [log for log in logs if log.user_id == user_id]
                if tenant_id:
                    logs = [log for log in logs if log.tenant_id == tenant_id]
                if action:
                    logs = [log for log in logs if log.action == action]

                # Sort by timestamp (newest first)
                logs.sort(key=lambda x: x.timestamp, reverse=True)

                return logs[:limit]

        except Exception as e:
            self.log(f"Error getting audit logs: {e}", LogLevel.ERROR)
            return []

    def export_audit_logs(self, start_time: float = None, end_time: float = None) -> List[Dict[str, Any]]:
        """Export audit logs for compliance."""
        try:
            with self._lock:
                logs = self.audit_logs.copy()

                # Apply time filters
                if start_time:
                    logs = [log for log in logs if log.timestamp >= start_time]
                if end_time:
                    logs = [log for log in logs if log.timestamp <= end_time]

                # Convert to dictionaries for export
                export_data = []
                for log in logs:
                    export_data.append({
                        "id": log.id,
                        "user_id": log.user_id,
                        "tenant_id": log.tenant_id,
                        "action": log.action,
                        "resource": log.resource,
                        "details": log.details,
                        "timestamp": log.timestamp,
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent
                    })

                return export_data

        except Exception as e:
            self.log(f"Error exporting audit logs: {e}", LogLevel.ERROR)
            return []


class ComplianceReporter:
    """Compliance reporting system."""

    def __init__(self, audit_logger: AuditLogger, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self.audit_logger = audit_logger

    def generate_security_report(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Generate security compliance report."""
        try:
            end_time = time.time()
            start_time = end_time - (days * 24 * 3600)

            logs = self.audit_logger.get_audit_logs(tenant_id=tenant_id)
            filtered_logs = [
                log for log in logs if start_time <= log.timestamp <= end_time]

            # Analyze security events
            security_events = [
                log for log in filtered_logs if "security" in log.action.lower()]
            failed_logins = [
                log for log in filtered_logs if log.action == "login_failed"]
            admin_actions = [
                log for log in filtered_logs if "admin" in log.action.lower()]

            report = {
                "period": {
                    "start": start_time,
                    "end": end_time,
                    "days": days
                },
                "summary": {
                    "total_events": len(filtered_logs),
                    "security_events": len(security_events),
                    "failed_logins": len(failed_logins),
                    "admin_actions": len(admin_actions)
                },
                "compliance_score": self._calculate_compliance_score(filtered_logs),
                "recommendations": self._generate_recommendations(filtered_logs)
            }

            return report

        except Exception as e:
            self.log(f"Error generating security report: {e}", LogLevel.ERROR)
            return {}

    def _calculate_compliance_score(self, logs: List[AuditLog]) -> float:
        """Calculate compliance score based on logs."""
        try:
            if not logs:
                return 100.0

            # Base score
            score = 100.0

            # Deduct points for security issues
            security_issues = [
                log for log in logs if "security" in log.action.lower()]
            score -= len(security_issues) * 2

            # Deduct points for failed logins
            failed_logins = [
                log for log in logs if log.action == "login_failed"]
            score -= len(failed_logins) * 0.5

            # Deduct points for suspicious activities
            suspicious = [
                log for log in logs if "suspicious" in log.details.get("reason", "")]
            score -= len(suspicious) * 5

            return max(0.0, min(100.0, score))

        except Exception:
            return 50.0

    def _generate_recommendations(self, logs: List[AuditLog]) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []

        try:
            # Check for failed logins
            failed_logins = [
                log for log in logs if log.action == "login_failed"]
            if len(failed_logins) > 10:
                recommendations.append(
                    "High number of failed login attempts detected. Consider implementing account lockout policy.")

            # Check for admin actions
            admin_actions = [
                log for log in logs if "admin" in log.action.lower()]
            if len(admin_actions) > 50:
                recommendations.append(
                    "High number of admin actions. Consider implementing additional approval workflows.")

            # Check for security events
            security_events = [
                log for log in logs if "security" in log.action.lower()]
            if len(security_events) > 5:
                recommendations.append(
                    "Multiple security events detected. Review security policies and user training.")

            return recommendations

        except Exception as e:
            self.log(f"Error generating recommendations: {e}", LogLevel.ERROR)
            return ["Error generating recommendations"]


class EnterpriseManager:
    """Main enterprise features manager."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self.rbac = RoleBasedAccessControl(log_callback)
        self.tenant_manager = MultiTenantManager(log_callback)
        self.audit_logger = AuditLogger(log_callback)
        self.compliance_reporter = ComplianceReporter(
            self.audit_logger, log_callback)

    def initialize_enterprise(self) -> bool:
        """Initialize enterprise features."""
        try:
            # Create default admin user
            admin_user = self.rbac.create_user(
                username="admin",
                email="admin@onix.local",
                role=UserRole.SUPER_ADMIN
            )

            if admin_user:
                self.audit_logger.log_action(
                    user_id=admin_user.id,
                    tenant_id="default",
                    action="system_initialized",
                    resource="enterprise_features",
                    details={"admin_created": True}
                )

            self.log("Enterprise features initialized", LogLevel.INFO)
            return True

        except Exception as e:
            self.log(
                f"Error initializing enterprise features: {e}", LogLevel.ERROR)
            return False

    def check_access(self, user_id: str, permission: Permission) -> bool:
        """Check if user has access to a resource."""
        return self.rbac.has_permission(user_id, permission)

    def log_user_action(self, user_id: str, action: str, resource: str,
                        details: Dict[str, Any] = None, ip_address: str = "",
                        user_agent: str = "") -> str:
        """Log a user action."""
        user = self.rbac.get_user(user_id)
        tenant_id = user.tenant_id if user else "default"

        return self.audit_logger.log_action(
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def get_enterprise_summary(self) -> Dict[str, Any]:
        """Get enterprise features summary."""
        try:
            return {
                "users": {
                    "total": len(self.rbac.users),
                    "active": len([u for u in self.rbac.users.values() if u.is_active]),
                    "by_role": {
                        role.value: len(
                            [u for u in self.rbac.users.values() if u.role == role])
                        for role in UserRole
                    }
                },
                "tenants": {
                    "total": len(self.tenant_manager.tenants),
                    "active": len([t for t in self.tenant_manager.tenants.values() if t.is_active])
                },
                "audit_logs": {
                    "total": len(self.audit_logger.audit_logs),
                    "recent": len([log for log in self.audit_logger.audit_logs
                                   if time.time() - log.timestamp < 3600])  # Last hour
                }
            }

        except Exception as e:
            self.log(f"Error getting enterprise summary: {e}", LogLevel.ERROR)
            return {}
