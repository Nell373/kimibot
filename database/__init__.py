"""
Database module for Kimibot.
This module contains utilities for database operations.
"""

# 使用簡單明確的相對導入
from .db_utils import DatabaseUtils

# 明確指定可被外部導入的名稱
__all__ = ['DatabaseUtils'] 