"""
Session Management using Azure Table Storage

Provides secure session storage with:
- Encrypted password storage
- Configurable session expiry
- Multi-system support
"""
from azure.data.tables import TableServiceClient
from datetime import datetime, timedelta
from typing import Optional
import uuid
import os
from .config import SESSION_EXPIRY_HOURS


class SessionStore:
    """Session storage using Azure Table Storage."""

    def __init__(self):
        """Initialize connection to Azure Table Storage."""
        conn_str = os.environ.get('AzureWebJobsStorage')
        self.table_client = TableServiceClient.from_connection_string(conn_str)
        self.table = self.table_client.get_table_client('sessions')

        # Create table if not exists
        try:
            self.table_client.create_table('sessions')
        except Exception:
            pass  # Table already exists

    def create_session(
        self,
        user: str,
        client: str,
        system: str,
        password_encrypted: str
    ) -> str:
        """
        Create new session and return session ID.

        Args:
            user: SAP user ID
            client: SAP client number
            system: SAP system ID (DEV, QAS, PRD)
            password_encrypted: Fernet-encrypted password

        Returns:
            Unique session ID (UUID)
        """
        session_id = str(uuid.uuid4())
        expires = datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)

        entity = {
            'PartitionKey': 'session',
            'RowKey': session_id,
            'user': user,
            'client': client,
            'system': system,
            'password': password_encrypted,
            'expires': expires.isoformat(),
            'created': datetime.utcnow().isoformat()
        }

        self.table.create_entity(entity)
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data if valid and not expired.

        Args:
            session_id: Session ID to look up

        Returns:
            Dictionary with user, client, system, password or None if invalid/expired
        """
        try:
            entity = self.table.get_entity('session', session_id)
            expires = datetime.fromisoformat(entity['expires'])

            if datetime.utcnow() > expires:
                self.delete_session(session_id)
                return None

            return {
                'user': entity['user'],
                'client': entity['client'],
                'system': entity.get('system', 'PRD'),  # Default to PRD for legacy sessions
                'password': entity['password']
            }
        except Exception:
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            self.table.delete_entity('session', session_id)
            return True
        except Exception:
            return False

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions deleted
        """
        deleted = 0
        try:
            now = datetime.utcnow().isoformat()
            query = f"PartitionKey eq 'session'"
            entities = self.table.query_entities(query)

            for entity in entities:
                if entity.get('expires', '') < now:
                    try:
                        self.table.delete_entity('session', entity['RowKey'])
                        deleted += 1
                    except Exception:
                        pass
        except Exception:
            pass

        return deleted
