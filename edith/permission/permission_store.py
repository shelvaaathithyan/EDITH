import threading
from typing import Optional, Dict
from edith.core.events import event_bus
from edith.permission.permission_models import PendingAction, PendingActionStatus
from edith.permission.permission_events import PermissionEvent

class PermissionStore:
    """Thread-safe storage for PendingActions with lazy expiration."""
    def __init__(self):
        self._lock = threading.RLock()
        self._pending_actions: Dict[str, PendingAction] = {}
        # Keep track of the currently active pending action for single-item flows
        self._active_action_id: Optional[str] = None

    def _evict_expired(self):
        """Removes expired pending actions."""
        expired_ids = []
        for action_id, action in self._pending_actions.items():
            if action.is_expired and action.status == PendingActionStatus.PENDING:
                expired_ids.append(action_id)
                
        for action_id in expired_ids:
            action = self._pending_actions.pop(action_id)
            action.status = PendingActionStatus.EXPIRED
            event_bus.publish(PermissionEvent.PERMISSION_EXPIRED, action)
            if self._active_action_id == action_id:
                self._active_action_id = None

    def store_action(self, action: PendingAction):
        with self._lock:
            self._evict_expired()
            self._pending_actions[action.id] = action
            self._active_action_id = action.id

    def get_action(self, action_id: str) -> Optional[PendingAction]:
        with self._lock:
            self._evict_expired()
            return self._pending_actions.get(action_id)

    def get_active_action(self) -> Optional[PendingAction]:
        with self._lock:
            self._evict_expired()
            if self._active_action_id:
                return self._pending_actions.get(self._active_action_id)
            return None

    def remove_action(self, action_id: str):
        with self._lock:
            if action_id in self._pending_actions:
                del self._pending_actions[action_id]
            if self._active_action_id == action_id:
                self._active_action_id = None
                
    def clear(self):
        with self._lock:
            self._pending_actions.clear()
            self._active_action_id = None
