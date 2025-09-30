"""
Cloud Sync Service for Onix
Provides multi-device configuration synchronization and cloud backup
"""

import time
import threading
import json
import hashlib
import requests
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from constants import LogLevel
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class SyncConfig:
    """Configuration for cloud sync."""
    server_url: str
    api_key: str
    user_id: str
    device_id: str
    encryption_key: str
    sync_interval: int = 300  # 5 minutes
    max_retries: int = 3
    timeout: int = 30


@dataclass
class SyncItem:
    """Item to be synchronized."""
    id: str
    type: str  # "settings", "servers", "profiles", "plugins"
    data: Dict[str, Any]
    version: int
    last_modified: float
    device_id: str
    checksum: str


@dataclass
class SyncConflict:
    """Sync conflict resolution."""
    item_id: str
    local_version: SyncItem
    remote_version: SyncItem
    conflict_type: str  # "version", "data", "deletion"
    resolution: str = "pending"  # "local", "remote", "merge", "pending"


class CloudSyncService:
    """Cloud synchronization service."""
    
    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (lambda msg, level: print(f"[{level}] {msg}"))
        self.config: Optional[SyncConfig] = None
        self.sync_queue: List[SyncItem] = []
        self.conflicts: List[SyncConflict] = []
        self.is_syncing = False
        self.sync_thread = None
        self.stop_sync = threading.Event()
        self._lock = threading.Lock()
        self.encryption_key = None
        
    def configure(self, server_url: str, api_key: str, user_id: str, 
                 device_id: str, password: str = None) -> bool:
        """Configure cloud sync service."""
        try:
            # Generate encryption key from password
            if password:
                self.encryption_key = self._generate_encryption_key(password)
            else:
                self.encryption_key = Fernet.generate_key()
            
            self.config = SyncConfig(
                server_url=server_url,
                api_key=api_key,
                user_id=user_id,
                device_id=device_id,
                encryption_key=base64.b64encode(self.encryption_key).decode()
            )
            
            self.log("Cloud sync configured successfully", LogLevel.INFO)
            return True
            
        except Exception as e:
            self.log(f"Error configuring cloud sync: {e}", LogLevel.ERROR)
            return False
    
    def _generate_encryption_key(self, password: str) -> bytes:
        """Generate encryption key from password."""
        try:
            password_bytes = password.encode()
            salt = b'onix_cloud_sync_salt'  # In production, use random salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            return key
        except Exception as e:
            self.log(f"Error generating encryption key: {e}", LogLevel.ERROR)
            return Fernet.generate_key()
    
    def start_sync(self) -> bool:
        """Start automatic synchronization."""
        try:
            if not self.config:
                self.log("Cloud sync not configured", LogLevel.WARNING)
                return False
            
            if self.sync_thread and self.sync_thread.is_alive():
                self.log("Sync already running", LogLevel.WARNING)
                return False
            
            self.stop_sync.clear()
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            
            self.log("Cloud sync started", LogLevel.INFO)
            return True
            
        except Exception as e:
            self.log(f"Error starting sync: {e}", LogLevel.ERROR)
            return False
    
    def stop_sync(self) -> None:
        """Stop automatic synchronization."""
        try:
            self.stop_sync.set()
            if self.sync_thread and self.sync_thread.is_alive():
                self.sync_thread.join(timeout=5)
            
            self.log("Cloud sync stopped", LogLevel.INFO)
            
        except Exception as e:
            self.log(f"Error stopping sync: {e}", LogLevel.ERROR)
    
    def _sync_loop(self) -> None:
        """Main sync loop."""
        while not self.stop_sync.is_set():
            try:
                if self.sync_queue:
                    self._process_sync_queue()
                
                # Sync with cloud
                self._sync_with_cloud()
                
                # Wait for next sync
                self.stop_sync.wait(self.config.sync_interval)
                
            except Exception as e:
                self.log(f"Error in sync loop: {e}", LogLevel.ERROR)
                self.stop_sync.wait(60)  # Wait 1 minute on error
    
    def _process_sync_queue(self) -> None:
        """Process items in sync queue."""
        try:
            with self._lock:
                items_to_sync = self.sync_queue.copy()
                self.sync_queue.clear()
            
            for item in items_to_sync:
                self._upload_item(item)
                
        except Exception as e:
            self.log(f"Error processing sync queue: {e}", LogLevel.ERROR)
    
    def _upload_item(self, item: SyncItem) -> bool:
        """Upload item to cloud."""
        try:
            if not self.config:
                return False
            
            # Encrypt data
            encrypted_data = self._encrypt_data(item.data)
            
            payload = {
                "user_id": self.config.user_id,
                "device_id": self.config.device_id,
                "item": {
                    "id": item.id,
                    "type": item.type,
                    "data": encrypted_data,
                    "version": item.version,
                    "last_modified": item.last_modified,
                    "checksum": item.checksum
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.config.server_url}/api/sync/upload",
                json=payload,
                headers=headers,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                self.log(f"Uploaded item {item.id} successfully", LogLevel.DEBUG)
                return True
            else:
                self.log(f"Failed to upload item {item.id}: {response.status_code}", LogLevel.WARNING)
                return False
                
        except Exception as e:
            self.log(f"Error uploading item: {e}", LogLevel.ERROR)
            return False
    
    def _sync_with_cloud(self) -> None:
        """Sync with cloud server."""
        try:
            if not self.config:
                return
            
            # Download updates from cloud
            self._download_updates()
            
        except Exception as e:
            self.log(f"Error syncing with cloud: {e}", LogLevel.ERROR)
    
    def _download_updates(self) -> None:
        """Download updates from cloud."""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "user_id": self.config.user_id,
                "device_id": self.config.device_id,
                "since": int(time.time() - 3600)  # Last hour
            }
            
            response = requests.get(
                f"{self.config.server_url}/api/sync/download",
                headers=headers,
                params=params,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                updates = response.json()
                self._process_remote_updates(updates)
            else:
                self.log(f"Failed to download updates: {response.status_code}", LogLevel.WARNING)
                
        except Exception as e:
            self.log(f"Error downloading updates: {e}", LogLevel.ERROR)
    
    def _process_remote_updates(self, updates: List[Dict[str, Any]]) -> None:
        """Process remote updates."""
        try:
            for update in updates:
                # Decrypt data
                decrypted_data = self._decrypt_data(update["data"])
                
                # Check for conflicts
                local_item = self._find_local_item(update["id"])
                if local_item:
                    if self._has_conflict(local_item, update):
                        self._handle_conflict(local_item, update)
                    else:
                        self._apply_remote_update(update, decrypted_data)
                else:
                    self._apply_remote_update(update, decrypted_data)
                    
        except Exception as e:
            self.log(f"Error processing remote updates: {e}", LogLevel.ERROR)
    
    def _has_conflict(self, local_item: SyncItem, remote_item: Dict[str, Any]) -> bool:
        """Check if there's a conflict between local and remote items."""
        try:
            # Version conflict
            if local_item.version != remote_item["version"]:
                return True
            
            # Data conflict (different checksums)
            if local_item.checksum != remote_item["checksum"]:
                return True
            
            return False
            
        except Exception:
            return True
    
    def _handle_conflict(self, local_item: SyncItem, remote_item: Dict[str, Any]) -> None:
        """Handle sync conflict."""
        try:
            remote_sync_item = SyncItem(
                id=remote_item["id"],
                type=remote_item["type"],
                data=remote_item["data"],
                version=remote_item["version"],
                last_modified=remote_item["last_modified"],
                device_id=remote_item["device_id"],
                checksum=remote_item["checksum"]
            )
            
            conflict = SyncConflict(
                item_id=local_item.id,
                local_version=local_item,
                remote_version=remote_sync_item,
                conflict_type="version"
            )
            
            self.conflicts.append(conflict)
            self.log(f"Sync conflict detected for item {local_item.id}", LogLevel.WARNING)
            
        except Exception as e:
            self.log(f"Error handling conflict: {e}", LogLevel.ERROR)
    
    def _apply_remote_update(self, remote_item: Dict[str, Any], decrypted_data: Dict[str, Any]) -> None:
        """Apply remote update to local data."""
        try:
            # This would integrate with the main application to update local data
            # For now, just log the update
            self.log(f"Applied remote update for item {remote_item['id']}", LogLevel.DEBUG)
            
        except Exception as e:
            self.log(f"Error applying remote update: {e}", LogLevel.ERROR)
    
    def _find_local_item(self, item_id: str) -> Optional[SyncItem]:
        """Find local item by ID."""
        try:
            for item in self.sync_queue:
                if item.id == item_id:
                    return item
            return None
            
        except Exception:
            return None
    
    def add_to_sync(self, item_type: str, data: Dict[str, Any]) -> str:
        """Add item to sync queue."""
        try:
            item_id = str(int(time.time() * 1000))  # Simple ID generation
            checksum = self._calculate_checksum(data)
            
            sync_item = SyncItem(
                id=item_id,
                type=item_type,
                data=data,
                version=1,
                last_modified=time.time(),
                device_id=self.config.device_id if self.config else "unknown",
                checksum=checksum
            )
            
            with self._lock:
                self.sync_queue.append(sync_item)
            
            self.log(f"Added item {item_id} to sync queue", LogLevel.DEBUG)
            return item_id
            
        except Exception as e:
            self.log(f"Error adding item to sync: {e}", LogLevel.ERROR)
            return ""
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data."""
        try:
            data_str = json.dumps(data, sort_keys=True)
            return hashlib.md5(data_str.encode()).hexdigest()
            
        except Exception:
            return ""
    
    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt data for cloud storage."""
        try:
            if not self.encryption_key:
                return json.dumps(data)
            
            fernet = Fernet(self.encryption_key)
            data_str = json.dumps(data)
            encrypted_data = fernet.encrypt(data_str.encode())
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            self.log(f"Error encrypting data: {e}", LogLevel.ERROR)
            return json.dumps(data)
    
    def _decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt data from cloud storage."""
        try:
            if not self.encryption_key:
                return json.loads(encrypted_data)
            
            fernet = Fernet(self.encryption_key)
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            self.log(f"Error decrypting data: {e}", LogLevel.ERROR)
            return {}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status."""
        try:
            return {
                "configured": self.config is not None,
                "syncing": self.is_syncing,
                "queue_size": len(self.sync_queue),
                "conflicts": len(self.conflicts),
                "last_sync": getattr(self, 'last_sync_time', 0)
            }
            
        except Exception as e:
            self.log(f"Error getting sync status: {e}", LogLevel.ERROR)
            return {}
    
    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        """Resolve sync conflict."""
        try:
            for i, conflict in enumerate(self.conflicts):
                if conflict.item_id == conflict_id:
                    conflict.resolution = resolution
                    
                    if resolution == "local":
                        # Keep local version
                        self._upload_item(conflict.local_version)
                    elif resolution == "remote":
                        # Use remote version
                        self._apply_remote_update(
                            asdict(conflict.remote_version),
                            conflict.remote_version.data
                        )
                    elif resolution == "merge":
                        # Merge versions (implementation depends on data type)
                        self._merge_items(conflict.local_version, conflict.remote_version)
                    
                    # Remove resolved conflict
                    self.conflicts.pop(i)
                    self.log(f"Resolved conflict for item {conflict_id}", LogLevel.INFO)
                    return True
            
            return False
            
        except Exception as e:
            self.log(f"Error resolving conflict: {e}", LogLevel.ERROR)
            return False
    
    def _merge_items(self, local_item: SyncItem, remote_item: SyncItem) -> None:
        """Merge local and remote items."""
        try:
            # Simple merge strategy - use remote data
            merged_data = remote_item.data.copy()
            merged_data.update(local_item.data)
            
            # Create new merged item
            merged_item = SyncItem(
                id=local_item.id,
                type=local_item.type,
                data=merged_data,
                version=max(local_item.version, remote_item.version) + 1,
                last_modified=time.time(),
                device_id=local_item.device_id,
                checksum=self._calculate_checksum(merged_data)
            )
            
            self._upload_item(merged_item)
            self.log(f"Merged items for {local_item.id}", LogLevel.INFO)
            
        except Exception as e:
            self.log(f"Error merging items: {e}", LogLevel.ERROR)
    
    def get_conflicts(self) -> List[SyncConflict]:
        """Get list of sync conflicts."""
        return self.conflicts.copy()
    
    def clear_conflicts(self) -> None:
        """Clear all conflicts."""
        self.conflicts.clear()
        self.log("Cleared all sync conflicts", LogLevel.INFO)
