# fixed_otp_reader.py

import email
from email.header import decode_header
import imaplib
import re
from datetime import datetime, timedelta
from typing import Optional
import time

IMAP_SERVER = 'imap.gmail.com'
EMAIL_ACCOUNT = 'lovepreet@teamarora.com'
EMAIL_PASSWORD = 'wuhb rteu rthu ghin'

def get_recent_otp_from_gmail(hours_back: int = 2, unread_only: bool = False) -> Optional[str]:
    """Find OTP from recent emails with option to check unread only"""
    
    try:
        search_type = "unread" if unread_only else "all"
        print(f"🔍 Searching for OTP in {search_type} emails from last {hours_back} hours...")
        
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")

        # Calculate date for search (emails from last X hours)
        since_date = (datetime.now() - timedelta(hours=hours_back)).strftime("%d-%b-%Y")
        
        # Multiple search patterns for Amazon OTP emails
        base_patterns = [
            f'FROM "no-reply@jobs.amazon.com" SINCE "{since_date}"',
            f'FROM "no-reply@amazon.work" SINCE "{since_date}"',
            f'FROM "no-reply@amazon.com" SINCE "{since_date}"',
            f'SUBJECT "verification" SINCE "{since_date}"',
            f'SUBJECT "code" SINCE "{since_date}"',
            f'BODY "verification code" SINCE "{since_date}"',
        ]
        
        # Add UNSEEN flag for unread emails only
        if unread_only:
            search_patterns = [f'(UNSEEN {pattern})' for pattern in base_patterns]
        else:
            search_patterns = [f'({pattern})' for pattern in base_patterns]
        
        email_ids = []
        for pattern in search_patterns:
            try:
                status, messages = mail.search(None, pattern)
                if messages[0]:
                    email_ids.extend(messages[0].split())
                    print(f"📧 Found {len(messages[0].split())} emails with pattern: {pattern}")
            except Exception as e:
                print(f"⚠️ Search pattern failed: {pattern} - {e}")
        
        # Remove duplicates and get latest emails
        email_ids = list(set(email_ids))
        
        if not email_ids:
            status_msg = "unread Amazon emails" if unread_only else "recent Amazon emails"
            print(f"❌ No {status_msg} found")
            mail.close()
            mail.logout()
            return None

        print(f"📬 Checking {len(email_ids)} emails...")
        
        # Check the most recent emails first
        email_ids.sort(reverse=True)
        
        for email_id in email_ids:
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Get email subject and sender
                        subject = decode_header(msg["Subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()
                        
                        sender = msg.get("From", "Unknown")
                        date = msg.get("Date", "Unknown")
                        
                        print(f"📧 Checking: {subject} from {sender}")
                        
                        # Extract body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                                elif part.get_content_type() == "text/html":
                                    # Also check HTML content
                                    html_body = part.get_payload(decode=True).decode()
                                    body += " " + html_body
                        else:
                            body = msg.get_payload(decode=True).decode()

                        # Enhanced OTP extraction patterns
                        otp_patterns = [
                            r'\b\d{6}\b',  # Basic 6-digit pattern
                            r'(?:code is|verification code|OTP)[:\s]*([0-9]{6})',
                            r'([0-9]{6})(?:\s*is your|\s*verification)',
                            r'Your verification code is[:\s]*([0-9]{6})',
                            r'Enter this code[:\s]*([0-9]{6})',
                            r'<h3>([0-9]{6})</h3>',  # HTML format like in your email
                        ]
                        
                        for pattern in otp_patterns:
                            otp_match = re.search(pattern, body, re.IGNORECASE)
                            if otp_match:
                                otp = otp_match.group(1) if otp_match.groups() else otp_match.group(0)
                                if len(otp) == 6 and otp.isdigit():
                                    print(f"✅ OTP Found: {otp} in email: {subject}")
                                    
                                    # Mark email as read if we found OTP in unread email
                                    if unread_only:
                                        try:
                                            mail.store(email_id, '+FLAGS', '\\Seen')
                                            print(f"📖 Marked email as read")
                                        except:
                                            pass
                                    
                                    mail.close()
                                    mail.logout()
                                    return otp
                        
                        # Debug: show part of body if no OTP found
                        print(f"🔍 Body preview: {body[:100]}...")
                        
            except Exception as e:
                print(f"⚠️ Error processing email {email_id}: {e}")
                continue

        mail.close()
        mail.logout()
        status_msg = "unread emails" if unread_only else "recent emails"
        print(f"❌ No valid OTP found in {status_msg}")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_fresh_otp_with_retry(max_wait_minutes: int = 3, check_interval: int = 15) -> Optional[str]:
    """Wait for fresh unread OTP with simple retry logic"""
    print(f"⏳ Waiting for fresh unread OTP (max {max_wait_minutes} minutes)...")
    
    start_time = datetime.now()
    max_wait_time = start_time + timedelta(minutes=max_wait_minutes)
    
    retry_count = 0
    while datetime.now() < max_wait_time:
        retry_count += 1
        print(f"🔄 Attempt {retry_count}: Checking for unread OTP emails...")
        
        # Check for unread OTP emails only
        otp = get_recent_otp_from_gmail(hours_back=1, unread_only=True)
        
        if otp:
            print(f"🎉 Fresh unread OTP found: {otp}")
            return otp
        
        # Wait before next check
        remaining = max_wait_time - datetime.now()
        if remaining.total_seconds() > check_interval:
            print(f"⏱️ No unread OTP yet, waiting {check_interval} seconds...")
            time.sleep(check_interval)
        else:
            # Less than check_interval remaining, wait for remaining time
            if remaining.total_seconds() > 0:
                print(f"⏱️ Waiting final {int(remaining.total_seconds())} seconds...")
                time.sleep(remaining.total_seconds())
            break
    
    print(f"⏰ Timeout reached after {max_wait_minutes} minutes")
    print("💡 Falling back to most recent OTP (including read emails)...")
    
    # Fallback: return the most recent OTP from all emails
    return get_recent_otp_from_gmail(hours_back=2, unread_only=False)

# Usage
if __name__ == "__main__":
    # Test unread OTP retrieval
    print("🆕 Testing unread OTP retrieval...")
    unread_otp = get_recent_otp_from_gmail(hours_back=2, unread_only=True)
    if unread_otp:
        print(f"🎉 Unread OTP: {unread_otp}")
    else:
        print("💔 No unread OTP found")
        
        # Fallback to all emails
        print("\n🔄 Trying all emails...")
        any_otp = get_recent_otp_from_gmail(hours_back=2, unread_only=False)
        if any_otp:
            print(f"🎉 Found OTP: {any_otp}")
        else:
            print("💔 No OTP found at all")
    
    # Test fresh OTP waiting
    print("\n⏳ Testing fresh OTP waiting...")
    fresh_otp = get_fresh_otp_with_retry(max_wait_minutes=2, check_interval=10)
    if fresh_otp:
        print(f"🎉 Fresh OTP: {fresh_otp}")
    else:
        print("💔 No fresh OTP found")