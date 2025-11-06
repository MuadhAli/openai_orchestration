#!/usr/bin/env python3
"""
Quick script to check the conversational RAG database
"""
import os
import sys
from sqlalchemy import create_engine, text

def check_database():
    """Check the database conten