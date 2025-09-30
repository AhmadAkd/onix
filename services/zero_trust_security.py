"""
Zero-Trust Security Service
سرویس امنیتی Zero-Trust Architecture
"""

import threading
import time
import json
import hashlib
import hmac
import secrets
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque, defaultdict
from constants import LogLevel
import ipaddress
import socket
import ssl
import requests

class TrustLevel(Enum):
    """سطوح اعتماد"""
    UNTRUSTED = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    FULLY_TRUSTED = 4

class SecurityPolicy(Enum):
    """سیاست‌های امنیتی"""
    DENY_ALL = "deny_all"
    ALLOW_VERIFIED = "allow_verified"
    TRUST_AFTER_VERIFICATION = "trust_after_verification"
    CONTINUOUS_VERIFICATION = "continuous_verification"

@dataclass
class Identity:
    """هویت کاربر/دستگاه"""
    id: str
    name: str
    type: str  # user, device, service
    trust_level: TrustLevel
    last_verified: float
    verification_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AccessRequest:
    """درخواست دسترسی"""
    id: str
    identity_id: str
    resource: str
    action: str
    timestamp: float
    source_ip: str
    user_agent: str
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}

@dataclass
class SecurityEvent:
    """رویداد امنیتی"""
    id: str
    type: str
    severity: str
    timestamp: float
    identity_id: str
    description: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

class IdentityVerifier:
    """تأییدکننده هویت"""
    
    def __init__(self):
        self.identities: Dict[str, Identity] = {}
        self.verification_tokens: Dict[str, str] = {}
        self.failed_attempts: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def register_identity(self, identity: Identity) -> bool:
        """ثبت هویت جدید"""
        with self._lock:
            if identity.id in self.identities:
                return False
            
            self.identities[identity.id] = identity
            print(f"[{LogLevel.INFO}] Identity registered: {identity.name} ({identity.type})")
            return True
    
    def verify_identity(self, identity_id: str, credentials: Dict[str, Any]) -> Tuple[bool, TrustLevel]:
        """تأیید هویت"""
        with self._lock:
            if identity_id not in self.identities:
                return False, TrustLevel.UNTRUSTED
            
            identity = self.identities[identity_id]
            
            # بررسی تلاش‌های ناموفق
            if self.failed_attempts[identity_id] >= 5:
                print(f"[{LogLevel.WARNING}] Too many failed attempts for identity: {identity_id}")
                return False, TrustLevel.UNTRUSTED
            
            # تأیید اعتبارنامه‌ها
            if self._validate_credentials(identity, credentials):
                identity.last_verified = time.time()
                identity.verification_count += 1
                self.failed_attempts[identity_id] = 0
                
                # افزایش سطح اعتماد بر اساس تعداد تأییدها
                if identity.verification_count > 10:
                    identity.trust_level = TrustLevel.FULLY_TRUSTED
                elif identity.verification_count > 5:
                    identity.trust_level = TrustLevel.HIGH
                elif identity.verification_count > 2:
                    identity.trust_level = TrustLevel.MEDIUM
                else:
                    identity.trust_level = TrustLevel.LOW
                
                print(f"[{LogLevel.INFO}] Identity verified: {identity.name} (trust: {identity.trust_level.name})")
                return True, identity.trust_level
            else:
                self.failed_attempts[identity_id] += 1
                print(f"[{LogLevel.WARNING}] Identity verification failed: {identity_id}")
                return False, TrustLevel.UNTRUSTED
    
    def _validate_credentials(self, identity: Identity, credentials: Dict[str, Any]) -> bool:
        """اعتبارسنجی اعتبارنامه‌ها"""
        # شبیه‌سازی اعتبارسنجی
        if identity.type == "user":
            return credentials.get("password") == "valid_password"
        elif identity.type == "device":
            return credentials.get("device_cert") == "valid_cert"
        elif identity.type == "service":
            return credentials.get("api_key") == "valid_api_key"
        
        return False
    
    def generate_verification_token(self, identity_id: str) -> str:
        """تولید توکن تأیید"""
        token = secrets.token_urlsafe(32)
        self.verification_tokens[identity_id] = token
        return token
    
    def verify_token(self, identity_id: str, token: str) -> bool:
        """تأیید توکن"""
        return self.verification_tokens.get(identity_id) == token
    
    def get_identity(self, identity_id: str) -> Optional[Identity]:
        """دریافت هویت"""
        with self._lock:
            return self.identities.get(identity_id)

class PolicyEngine:
    """موتور سیاست‌های امنیتی"""
    
    def __init__(self):
        self.policies: Dict[str, Dict[str, Any]] = {}
        self.default_policy = SecurityPolicy.DENY_ALL
        self._lock = threading.Lock()
    
    def add_policy(self, name: str, policy: Dict[str, Any]):
        """اضافه کردن سیاست"""
        with self._lock:
            self.policies[name] = policy
            print(f"[{LogLevel.INFO}] Security policy added: {name}")
    
    def evaluate_access(self, request: AccessRequest, identity: Identity) -> Tuple[bool, str]:
        """ارزیابی دسترسی"""
        with self._lock:
            # بررسی سیاست‌های موجود
            for policy_name, policy in self.policies.items():
                if self._matches_policy(request, identity, policy):
                    return self._apply_policy(request, identity, policy)
            
            # اعمال سیاست پیش‌فرض
            return self._apply_default_policy(request, identity)
    
    def _matches_policy(self, request: AccessRequest, identity: Identity, policy: Dict[str, Any]) -> bool:
        """بررسی تطبیق با سیاست"""
        # بررسی نوع هویت
        if "identity_types" in policy:
            if identity.type not in policy["identity_types"]:
                return False
        
        # بررسی سطح اعتماد
        if "min_trust_level" in policy:
            if identity.trust_level.value < policy["min_trust_level"]:
                return False
        
        # بررسی منبع IP
        if "allowed_ips" in policy:
            if not self._ip_in_range(request.source_ip, policy["allowed_ips"]):
                return False
        
        # بررسی منابع
        if "resources" in policy:
            if request.resource not in policy["resources"]:
                return False
        
        return True
    
    def _ip_in_range(self, ip: str, ranges: List[str]) -> bool:
        """بررسی IP در محدوده"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for range_str in ranges:
                if "/" in range_str:
                    network = ipaddress.ip_network(range_str, strict=False)
                    if ip_obj in network:
                        return True
                else:
                    if ip == range_str:
                        return True
        except ValueError:
            pass
        return False
    
    def _apply_policy(self, request: AccessRequest, identity: Identity, policy: Dict[str, Any]) -> Tuple[bool, str]:
        """اعمال سیاست"""
        action = policy.get("action", "deny")
        
        if action == "allow":
            return True, f"Allowed by policy: {policy.get('name', 'unknown')}"
        elif action == "deny":
            return False, f"Denied by policy: {policy.get('name', 'unknown')}"
        elif action == "require_verification":
            return identity.trust_level.value >= TrustLevel.MEDIUM.value, "Requires verification"
        
        return False, "Unknown policy action"
    
    def _apply_default_policy(self, request: AccessRequest, identity: Identity) -> Tuple[bool, str]:
        """اعمال سیاست پیش‌فرض"""
        if self.default_policy == SecurityPolicy.DENY_ALL:
            return False, "Denied by default policy"
        elif self.default_policy == SecurityPolicy.ALLOW_VERIFIED:
            return identity.trust_level.value >= TrustLevel.MEDIUM.value, "Requires verification"
        
        return False, "Access denied"

class ThreatDetector:
    """تشخیص‌دهنده تهدیدات"""
    
    def __init__(self):
        self.suspicious_activities: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.threat_patterns: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def add_threat_pattern(self, name: str, pattern: Dict[str, Any]):
        """اضافه کردن الگوی تهدید"""
        with self._lock:
            self.threat_patterns[name] = pattern
            print(f"[{LogLevel.INFO}] Threat pattern added: {name}")
    
    def analyze_request(self, request: AccessRequest, identity: Identity) -> List[SecurityEvent]:
        """تحلیل درخواست برای تهدیدات"""
        events = []
        
        with self._lock:
            # بررسی الگوهای تهدید
            for pattern_name, pattern in self.threat_patterns.items():
                if self._matches_threat_pattern(request, identity, pattern):
                    event = SecurityEvent(
                        id=f"threat_{int(time.time())}",
                        type="threat_detected",
                        severity=pattern.get("severity", "medium"),
                        timestamp=time.time(),
                        identity_id=identity.id,
                        description=f"Threat pattern detected: {pattern_name}",
                        details={
                            "pattern": pattern_name,
                            "request": request.__dict__,
                            "identity": identity.__dict__
                        }
                    )
                    events.append(event)
            
            # ثبت فعالیت مشکوک
            self.suspicious_activities[identity.id].append({
                "timestamp": time.time(),
                "request": request.__dict__,
                "trust_level": identity.trust_level.value
            })
            
            # حذف فعالیت‌های قدیمی
            cutoff_time = time.time() - 3600  # 1 ساعت
            self.suspicious_activities[identity.id] = [
                activity for activity in self.suspicious_activities[identity.id]
                if activity["timestamp"] > cutoff_time
            ]
        
        return events
    
    def _matches_threat_pattern(self, request: AccessRequest, identity: Identity, pattern: Dict[str, Any]) -> bool:
        """بررسی تطبیق با الگوی تهدید"""
        # بررسی تعداد درخواست‌ها
        if "max_requests_per_minute" in pattern:
            recent_requests = [
                activity for activity in self.suspicious_activities[identity.id]
                if time.time() - activity["timestamp"] < 60
            ]
            if len(recent_requests) > pattern["max_requests_per_minute"]:
                return True
        
        # بررسی IP مشکوک
        if "suspicious_ips" in pattern:
            if request.source_ip in pattern["suspicious_ips"]:
                return True
        
        # بررسی User Agent مشکوک
        if "suspicious_user_agents" in pattern:
            for suspicious_ua in pattern["suspicious_user_agents"]:
                if suspicious_ua in request.user_agent:
                    return True
        
        return False
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """دریافت خلاصه تهدیدات"""
        with self._lock:
            total_activities = sum(len(activities) for activities in self.suspicious_activities.values())
            suspicious_identities = len([
                identity for activities in self.suspicious_activities.values()
                if len(activities) > 10
            ])
            
            return {
                "total_suspicious_activities": total_activities,
                "suspicious_identities": suspicious_identities,
                "threat_patterns_count": len(self.threat_patterns),
                "active_identities": len(self.suspicious_activities)
            }

class ContinuousVerification:
    """تأیید مداوم"""
    
    def __init__(self):
        self.verification_sessions: Dict[str, Dict[str, Any]] = {}
        self.verification_interval = 300  # 5 دقیقه
        self.is_running = False
        self._verification_thread = None
        self._stop_event = threading.Event()
    
    def start_verification(self):
        """شروع تأیید مداوم"""
        if self.is_running:
            return
        
        self.is_running = True
        self._stop_event.clear()
        self._verification_thread = threading.Thread(target=self._verification_loop, daemon=True)
        self._verification_thread.start()
        print(f"[{LogLevel.INFO}] Continuous verification started")
    
    def stop_verification(self):
        """توقف تأیید مداوم"""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_event.set()
        
        if self._verification_thread and self._verification_thread.is_alive():
            self._verification_thread.join(timeout=5)
        
        print(f"[{LogLevel.INFO}] Continuous verification stopped")
    
    def _verification_loop(self):
        """حلقه تأیید مداوم"""
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                # بررسی جلسات تأیید
                expired_sessions = []
                for session_id, session in self.verification_sessions.items():
                    if current_time - session["last_verified"] > self.verification_interval:
                        expired_sessions.append(session_id)
                
                # حذف جلسات منقضی
                for session_id in expired_sessions:
                    del self.verification_sessions[session_id]
                    print(f"[{LogLevel.WARNING}] Verification session expired: {session_id}")
                
                time.sleep(60)  # بررسی هر دقیقه
                
            except Exception as e:
                print(f"[{LogLevel.ERROR}] Verification loop error: {e}")
                time.sleep(30)
    
    def create_verification_session(self, identity_id: str) -> str:
        """ایجاد جلسه تأیید"""
        session_id = secrets.token_urlsafe(16)
        self.verification_sessions[session_id] = {
            "identity_id": identity_id,
            "created_at": time.time(),
            "last_verified": time.time(),
            "status": "active"
        }
        return session_id
    
    def verify_session(self, session_id: str) -> bool:
        """تأیید جلسه"""
        if session_id not in self.verification_sessions:
            return False
        
        session = self.verification_sessions[session_id]
        session["last_verified"] = time.time()
        return True

class ZeroTrustSecurityService:
    """سرویس امنیتی Zero-Trust"""
    
    def __init__(self, log_callback: Callable = None):
        self.log = log_callback or print
        self.identity_verifier = IdentityVerifier()
        self.policy_engine = PolicyEngine()
        self.threat_detector = ThreatDetector()
        self.continuous_verification = ContinuousVerification()
        
        self.access_log: deque = deque(maxlen=10000)
        self.security_events: deque = deque(maxlen=1000)
        
        self.is_running = False
        self._setup_default_policies()
        self._setup_default_threat_patterns()
    
    def start(self):
        """شروع سرویس"""
        if self.is_running:
            return
        
        self.is_running = True
        self.continuous_verification.start_verification()
        self.log(f"[{LogLevel.INFO}] Zero-Trust security service started")
    
    def stop(self):
        """توقف سرویس"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.continuous_verification.stop_verification()
        self.log(f"[{LogLevel.INFO}] Zero-Trust security service stopped")
    
    def _setup_default_policies(self):
        """راه‌اندازی سیاست‌های پیش‌فرض"""
        # سیاست برای کاربران تأیید شده
        self.policy_engine.add_policy("verified_users", {
            "name": "Verified Users",
            "identity_types": ["user"],
            "min_trust_level": TrustLevel.MEDIUM.value,
            "resources": ["*"],
            "action": "allow"
        })
        
        # سیاست برای دستگاه‌های تأیید شده
        self.policy_engine.add_policy("verified_devices", {
            "name": "Verified Devices",
            "identity_types": ["device"],
            "min_trust_level": TrustLevel.HIGH.value,
            "resources": ["*"],
            "action": "allow"
        })
        
        # سیاست برای سرویس‌ها
        self.policy_engine.add_policy("trusted_services", {
            "name": "Trusted Services",
            "identity_types": ["service"],
            "min_trust_level": TrustLevel.FULLY_TRUSTED.value,
            "resources": ["*"],
            "action": "allow"
        })
    
    def _setup_default_threat_patterns(self):
        """راه‌اندازی الگوهای تهدید پیش‌فرض"""
        # الگوی درخواست‌های زیاد
        self.threat_detector.add_threat_pattern("high_frequency_requests", {
            "name": "High Frequency Requests",
            "max_requests_per_minute": 100,
            "severity": "medium"
        })
        
        # الگوی IP مشکوک
        self.threat_detector.add_threat_pattern("suspicious_ip", {
            "name": "Suspicious IP",
            "suspicious_ips": ["192.168.1.100", "10.0.0.100"],
            "severity": "high"
        })
        
        # الگوی User Agent مشکوک
        self.threat_detector.add_threat_pattern("suspicious_user_agent", {
            "name": "Suspicious User Agent",
            "suspicious_user_agents": ["bot", "crawler", "scanner"],
            "severity": "low"
        })
    
    def register_identity(self, identity: Identity) -> bool:
        """ثبت هویت"""
        return self.identity_verifier.register_identity(identity)
    
    def verify_identity(self, identity_id: str, credentials: Dict[str, Any]) -> Tuple[bool, TrustLevel]:
        """تأیید هویت"""
        return self.identity_verifier.verify_identity(identity_id, credentials)
    
    def request_access(self, identity_id: str, resource: str, action: str, 
                      source_ip: str, user_agent: str, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """درخواست دسترسی"""
        # دریافت هویت
        identity = self.identity_verifier.get_identity(identity_id)
        if not identity:
            return False, "Identity not found"
        
        # ایجاد درخواست دسترسی
        request = AccessRequest(
            id=f"req_{int(time.time())}",
            identity_id=identity_id,
            resource=resource,
            action=action,
            timestamp=time.time(),
            source_ip=source_ip,
            user_agent=user_agent,
            context=context
        )
        
        # تحلیل تهدیدات
        threat_events = self.threat_detector.analyze_request(request, identity)
        if threat_events:
            for event in threat_events:
                self.security_events.append(event)
                self.log(f"[{LogLevel.WARNING}] Security event: {event.description}")
        
        # ارزیابی دسترسی
        allowed, reason = self.policy_engine.evaluate_access(request, identity)
        
        # ثبت در لاگ
        self.access_log.append({
            "request": request.__dict__,
            "identity": identity.__dict__,
            "allowed": allowed,
            "reason": reason,
            "timestamp": time.time()
        })
        
        return allowed, reason
    
    def get_security_status(self) -> Dict[str, Any]:
        """دریافت وضعیت امنیتی"""
        return {
            "is_running": self.is_running,
            "registered_identities": len(self.identity_verifier.identities),
            "active_policies": len(self.policy_engine.policies),
            "threat_patterns": len(self.threat_detector.threat_patterns),
            "access_requests": len(self.access_log),
            "security_events": len(self.security_events),
            "threat_summary": self.threat_detector.get_threat_summary()
        }
    
    def cleanup(self):
        """پاکسازی منابع"""
        self.stop()
        self.access_log.clear()
        self.security_events.clear()
        self.log(f"[{LogLevel.INFO}] Zero-Trust security service cleaned up")

# نمونه سراسری
_zero_trust_service = None

def get_zero_trust_service() -> ZeroTrustSecurityService:
    """دریافت نمونه سراسری سرویس Zero-Trust"""
    global _zero_trust_service
    if _zero_trust_service is None:
        _zero_trust_service = ZeroTrustSecurityService()
    return _zero_trust_service
