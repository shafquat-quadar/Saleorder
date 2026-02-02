"""
SAP Connection Manager using PyRFC

Manages RFC connections to multiple SAP systems (DEV, QAS, PRD).
System configuration is loaded from config.py.
"""
from pyrfc import Connection
from typing import Optional
import os
from .config import get_sap_system


class SAPConnectionManager:
    """Manages SAP RFC connections with multi-system support."""

    def __init__(self, system_id: str = None):
        """
        Initialize connection manager for a specific SAP system.

        Args:
            system_id: System identifier (DEV, QAS, PRD). If None, uses legacy
                      environment variables for backwards compatibility.
        """
        self.system_id = system_id
        self.lang = os.environ.get('SAP_LANG', 'EN')

        if system_id:
            system_config = get_sap_system(system_id)
            if system_config:
                self.ashost = system_config['ashost']
                self.sysnr = system_config['sysnr']
            else:
                raise ValueError(f"Unknown SAP system: {system_id}")
        else:
            # Legacy fallback to environment variables
            self.ashost = os.environ.get('SAP_ASHOST', '')
            self.sysnr = os.environ.get('SAP_SYSNR', '00')

    def connect(self, user: str, password: str, client: str) -> Connection:
        """
        Create SAP connection with user credentials.

        Args:
            user: SAP user ID
            password: SAP password
            client: SAP client number

        Returns:
            PyRFC Connection object
        """
        return Connection(
            ashost=self.ashost,
            sysnr=self.sysnr,
            client=client,
            user=user,
            passwd=password,
            lang=self.lang
        )

    def test_connection(self, user: str, password: str, client: str) -> bool:
        """
        Test if credentials are valid by attempting connection.

        Args:
            user: SAP user ID
            password: SAP password
            client: SAP client number

        Returns:
            True if connection successful, False otherwise
        """
        try:
            conn = self.connect(user, password, client)
            conn.close()
            return True
        except Exception:
            return False

    def get_system_info(self) -> dict:
        """
        Get information about the configured SAP system.

        Returns:
            Dictionary with system configuration details
        """
        return {
            'system_id': self.system_id,
            'ashost': self.ashost,
            'sysnr': self.sysnr,
            'lang': self.lang
        }
