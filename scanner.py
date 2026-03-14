#!/usr/bin/env python3
"""
Global Entry Appointment Scanner
Checks for available appointments and sends email alerts
Uses Unsend (self-hosted email service) like Fakesharp
"""

import requests
import time
from datetime import datetime
import os
from typing import List, Dict

# Configuration
LOCATION_IDS = [
    5444,  # Newark Liberty International Airport (for testing - has available slots)
]

CHECK_INTERVAL = 60  # seconds between checks

# Email configuration (Unsend API - same as Fakesharp)
USESEND_HOST = os.getenv("USESEND_HOST", "http://usesend:3000")
USESEND_API_URL = f"{USESEND_HOST}/api/v1/emails"
USESEND_API_KEY = os.getenv("USESEND_API_KEY")
EMAIL_FROM = os.getenv("NOTIFICATION_FROM", "Global Entry Scanner <scanner@raydoug.com>")
EMAIL_TO = ["jefflawson@gmail.com", "kate.r.lawson@gmail.com"]

# DHS API endpoint
API_BASE = "https://ttp.cbp.dhs.gov/schedulerapi/slots"


def check_appointments(location_id: int) -> List[Dict]:
    """Check for available appointments at a location"""
    try:
        url = f"{API_BASE}?orderBy=soonest&limit=1&locationId={location_id}&minimum=1"
        
        # Add headers to avoid 403 Forbidden
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://ttp.cbp.dhs.gov/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data if isinstance(data, list) else []
        
    except Exception as e:
        print(f"Error checking location {location_id}: {e}")
        return []


def send_email(subject: str, body: str):
    """Send email via Unsend API (same pattern as Fakesharp)"""
    if not USESEND_API_KEY:
        print(f"⚠️  Email not configured (USESEND_API_KEY missing). Would send: {subject}")
        return
    
    try:
        # Send to each recipient
        for recipient in EMAIL_TO:
            payload = {
                "from": EMAIL_FROM,
                "to": recipient,
                "subject": subject,
                "html": body,
                "text": body  # Fallback plain text
            }
            
            headers = {
                "Authorization": f"Bearer {USESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Create session without proxy (same as Fakesharp)
            session = requests.Session()
            session.trust_env = False
            
            response = session.post(USESEND_API_URL, json=payload, headers=headers, timeout=10)
            session.close()
            
            if response.status_code >= 400:
                print(f"❌ Email failed to {recipient}: {response.status_code} - {response.text[:200]}")
            else:
                print(f"✅ Email sent to {recipient}")
        
        print(f"📧 Sent to {len(EMAIL_TO)} recipients: {subject}")
        
    except Exception as e:
        print(f"❌ Email error: {e}")


def format_appointment_email(appointments: List[Dict], location_name: str) -> str:
    """Format appointment data into helpful HTML email"""
    from datetime import datetime
    
    # Parse and format the first slot nicely
    first_slot = appointments[0] if appointments else {}
    slot_time = first_slot.get('startTimestamp', '')
    
    try:
        dt = datetime.fromisoformat(slot_time.replace('Z', '+00:00'))
        formatted_date = dt.strftime('%A, %B %d, %Y')
        formatted_time = dt.strftime('%I:%M %p')
    except:
        formatted_date = slot_time
        formatted_time = ''
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px; }}
            .content {{ padding: 20px; }}
            .slot {{ background: #f0f9ff; padding: 15px; margin: 10px 0; border-left: 4px solid #2563eb; }}
            .cta {{ background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; 
                    border-radius: 5px; display: inline-block; margin: 20px 0; font-weight: bold; }}
            .warning {{ background: #fef3c7; padding: 15px; border-left: 4px solid #f59e0b; margin: 20px 0; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Global Entry Appointment Alert!</h1>
            <p style="margin: 0; font-size: 18px;">New slots just opened at {location_name}</p>
        </div>
        
        <div class="content">
            <h2>✨ First Available Slot:</h2>
            <div class="slot">
                <p style="margin: 0; font-size: 20px; font-weight: bold;">{formatted_date}</p>
                <p style="margin: 5px 0 0 0; font-size: 24px; color: #2563eb;">{formatted_time}</p>
            </div>
            
            <h3>📅 All Available Slots ({len(appointments)} total):</h3>
            <ul>
    """
    
    for apt in appointments[:10]:  # Show first 10
        slot_dt = apt.get('startTimestamp', 'Unknown')
        try:
            dt = datetime.fromisoformat(slot_dt.replace('Z', '+00:00'))
            formatted = dt.strftime('%a, %b %d at %I:%M %p')
        except:
            formatted = slot_dt
        html += f"<li>⏰ {formatted}</li>"
    
    if len(appointments) > 10:
        html += f"<li><em>...and {len(appointments) - 10} more slots</em></li>"
    
    html += f"""
            </ul>
            
            <div class="warning">
                <strong>⚡ Act Fast!</strong> These slots typically disappear within 2-5 minutes. 
                Have your login ready and book immediately!
            </div>
            
            <h3>📝 How to Book:</h3>
            <ol>
                <li>Click the button below to go to the DHS website</li>
                <li>Log in to your Trusted Traveler account</li>
                <li>Navigate to "Manage Appointment"</li>
                <li>Select <strong>{location_name}</strong></li>
                <li>Choose your preferred time slot</li>
                <li>Confirm your appointment</li>
            </ol>
            
            <a href="https://ttp.cbp.dhs.gov/" class="cta">📲 Book Your Appointment Now →</a>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                💡 <strong>Tip:</strong> If the slot is gone when you get there, don't worry! 
                You'll receive another alert as soon as new slots open up.
            </p>
            
            <p style="color: #6b7280; font-size: 12px; margin-top: 20px; border-top: 1px solid #e5e7eb; padding-top: 20px;">
                This is an automated alert from your Global Entry Appointment Scanner. 
                Monitoring {location_name} every 60 seconds.
            </p>
        </div>
    </body>
    </html>
    """
    
    return html


def get_location_name(location_id: int) -> str:
    """Get human-readable location name"""
    locations = {
        5444: "Newark Liberty International Airport",
        14321: "Charlotte-Douglas Airport (CLT)",
    }
    return locations.get(location_id, f"Location {location_id}")


def main():
    """Main scanner loop"""
    print("🔍 Global Entry Appointment Scanner Started")
    print(f"📧 Alerts will be sent to: {', '.join(EMAIL_TO)}")
    print(f"🔄 Checking every {CHECK_INTERVAL} seconds")
    print(f"📍 Monitoring {len(LOCATION_IDS)} locations\n")
    
    last_alerts = {}  # Track when we last alerted for each location
    
    while True:
        try:
            for location_id in LOCATION_IDS:
                location_name = get_location_name(location_id)
                
                print(f"Checking {location_name}...", end=" ")
                appointments = check_appointments(location_id)
                
                if appointments:
                    print(f"✅ {len(appointments)} slots found!")
                    
                    # Only send email if we haven't alerted in the last hour
                    last_alert = last_alerts.get(location_id, 0)
                    if time.time() - last_alert > 3600:  # 1 hour cooldown
                        subject = f"🚨 Global Entry Slots Available - {location_name}"
                        body = format_appointment_email(appointments, location_name)
                        send_email(subject, body)
                        last_alerts[location_id] = time.time()
                    else:
                        print("   (Cooldown active, skipping email)")
                else:
                    print("No slots")
                
                time.sleep(2)  # Small delay between locations
            
            print(f"\n💤 Sleeping {CHECK_INTERVAL}s...\n")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n👋 Scanner stopped")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
