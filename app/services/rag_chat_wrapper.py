"""
RAG-enhanced chat wrapper that integrates RAG capabilities with ChatService.
"""
import logging
import time
from typing import Optional, Dict, List

from app.services.chat_service import ChatService