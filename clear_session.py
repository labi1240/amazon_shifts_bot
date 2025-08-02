#!/usr/bin/env python3
"""
Utility script to manually clear expired/invalid session files
Usage: python clear_session.py
"""

import os
import sys
import logging
from session_manager import AmazonSessionManager

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Clear session files manually"""
    print("🧹 Amazon Session Cleaner")
    print("=" * 30)
    
    manager = AmazonSessionManager()
    
    # Check if files exist
    session_exists = os.path.exists(manager.session_file)
    cookies_exists = os.path.exists(manager.cookies_file)
    
    if not session_exists and not cookies_exists:
        print("✅ No session files found - nothing to clear")
        return
    
    print(f"📁 Session file exists: {session_exists}")
    print(f"🍪 Cookies file exists: {cookies_exists}")
    
    # Check if session is expired
    if session_exists:
        if manager.is_session_expired():
            print("🕐 Session is expired")
        else:
            print("⏰ Session is still valid (created within 12 hours)")
    
    # Ask for confirmation
    response = input("\n❓ Do you want to clear the session files? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        manager.clear_session()
        print("✅ Session files cleared successfully!")
    else:
        print("❌ Operation cancelled")

if __name__ == "__main__":
    main()