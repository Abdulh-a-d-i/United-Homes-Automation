"""
Seed script to insert sample appointments data for frontend integration testing.
Run: python seed_appointments.py
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

# First check existing technicians
cur.execute("SELECT id, name FROM technicians LIMIT 5")
techs = cur.fetchall()

if not techs:
    print("No technicians found. Creating a sample technician...")
    cur.execute("""
        INSERT INTO technicians (name, email, phone, skills, home_latitude, home_longitude, status)
        VALUES
        ('Mike Johnson', 'mike@unitedhome.com', '+17045551001', '["chimney","gutter","power_washing"]', 35.2271, -80.8431, 'active'),
        ('Sarah Davis', 'sarah@unitedhome.com', '+17045551002', '["air_duct","dryer_vent"]', 35.2000, -80.8500, 'active'),
        ('James Wilson', 'james@unitedhome.com', '+17045551003', '["chimney","dryer_vent","gutter"]', 35.1900, -80.8200, 'active')
        RETURNING id, name
    """)
    techs = cur.fetchall()
    conn.commit()
    print(f"Created {len(techs)} technicians")

print(f"Using technicians: {[t['name'] for t in techs]}")

# Sample appointment data
now = datetime.now()
sample_appointments = [
    # Upcoming appointments
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[0]["id"],
        "customer_name": "John Smith",
        "customer_phone": "+17045559001",
        "customer_email": "john.smith@email.com",
        "service_type": "chimney",
        "address": "1234 Oak Street, Charlotte, NC 28202",
        "latitude": 35.2271,
        "longitude": -80.8431,
        "start_time": now + timedelta(days=1, hours=2),
        "end_time": now + timedelta(days=1, hours=3),
        "duration_minutes": 60,
        "status": "scheduled",
        "notes": "First floor chimney. Customer has a dog."
    },
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[0]["id"],
        "customer_name": "Emily Brown",
        "customer_phone": "+17045559002",
        "customer_email": "emily.brown@email.com",
        "service_type": "gutter",
        "address": "5678 Maple Ave, Charlotte, NC 28203",
        "latitude": 35.2150,
        "longitude": -80.8550,
        "start_time": now + timedelta(days=1, hours=5),
        "end_time": now + timedelta(days=1, hours=6),
        "duration_minutes": 60,
        "status": "scheduled",
        "notes": "Two-story house. Bring extension ladder."
    },
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[min(1, len(techs)-1)]["id"],
        "customer_name": "Robert Garcia",
        "customer_phone": "+17045559003",
        "customer_email": "robert.garcia@email.com",
        "service_type": "air_duct",
        "address": "910 Pine Road, Charlotte, NC 28204",
        "latitude": 35.2050,
        "longitude": -80.8300,
        "start_time": now + timedelta(days=2, hours=3),
        "end_time": now + timedelta(days=2, hours=4),
        "duration_minutes": 60,
        "status": "scheduled",
        "notes": "2 systems. Customer wants morning slot."
    },
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[min(1, len(techs)-1)]["id"],
        "customer_name": "Lisa Martinez",
        "customer_phone": "+17045559004",
        "customer_email": "lisa.martinez@email.com",
        "service_type": "dryer_vent",
        "address": "2345 Elm Street, Charlotte, NC 28205",
        "latitude": 35.2300,
        "longitude": -80.8100,
        "start_time": now + timedelta(days=3, hours=1),
        "end_time": now + timedelta(days=3, hours=2),
        "duration_minutes": 60,
        "status": "confirmed",
        "notes": None
    },
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[min(2, len(techs)-1)]["id"],
        "customer_name": "David Lee",
        "customer_phone": "+17045559005",
        "customer_email": "david.lee@email.com",
        "service_type": "power_washing",
        "address": "6789 Cedar Blvd, Charlotte, NC 28206",
        "latitude": 35.2400,
        "longitude": -80.8600,
        "start_time": now + timedelta(days=4, hours=4),
        "end_time": now + timedelta(days=4, hours=5),
        "duration_minutes": 60,
        "status": "scheduled",
        "notes": "Front porch and driveway."
    },
    # Past appointments (completed)
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[0]["id"],
        "customer_name": "Amanda Wilson",
        "customer_phone": "+17045559006",
        "customer_email": "amanda.wilson@email.com",
        "service_type": "chimney",
        "address": "111 Birch Lane, Charlotte, NC 28207",
        "latitude": 35.1950,
        "longitude": -80.8250,
        "start_time": now - timedelta(days=3, hours=5),
        "end_time": now - timedelta(days=3, hours=4),
        "duration_minutes": 60,
        "status": "completed",
        "notes": "Completed. No issues found."
    },
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[0]["id"],
        "customer_name": "Chris Taylor",
        "customer_phone": "+17045559007",
        "customer_email": "chris.taylor@email.com",
        "service_type": "gutter",
        "address": "222 Walnut Court, Charlotte, NC 28208",
        "latitude": 35.2100,
        "longitude": -80.8700,
        "start_time": now - timedelta(days=5, hours=3),
        "end_time": now - timedelta(days=5, hours=2),
        "duration_minutes": 60,
        "status": "completed",
        "notes": "Heavy debris removed."
    },
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[min(1, len(techs)-1)]["id"],
        "customer_name": "Jennifer Adams",
        "customer_phone": "+17045559008",
        "customer_email": "jennifer.adams@email.com",
        "service_type": "air_duct",
        "address": "333 Spruce Drive, Charlotte, NC 28209",
        "latitude": 35.1800,
        "longitude": -80.8400,
        "start_time": now - timedelta(days=7, hours=2),
        "end_time": now - timedelta(days=7, hours=1),
        "duration_minutes": 60,
        "status": "completed",
        "notes": "Single system cleaned."
    },
    # Cancelled appointment
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[min(2, len(techs)-1)]["id"],
        "customer_name": "Mark Thompson",
        "customer_phone": "+17045559009",
        "customer_email": "mark.thompson@email.com",
        "service_type": "power_washing",
        "address": "444 Ash Street, Charlotte, NC 28210",
        "latitude": 35.1700,
        "longitude": -80.8150,
        "start_time": now - timedelta(days=1, hours=4),
        "end_time": now - timedelta(days=1, hours=3),
        "duration_minutes": 60,
        "status": "cancelled",
        "notes": "Customer cancelled due to weather."
    },
    # Redo appointment
    {
        "calendar_event_id": str(uuid.uuid4()),
        "technician_id": techs[0]["id"],
        "customer_name": "Sarah Connor",
        "customer_phone": "+17045559010",
        "customer_email": "sarah.connor@email.com",
        "service_type": "dryer_vent",
        "address": "555 Hickory Way, Charlotte, NC 28211",
        "latitude": 35.1600,
        "longitude": -80.8350,
        "start_time": now + timedelta(days=2, hours=6),
        "end_time": now + timedelta(days=2, hours=7),
        "duration_minutes": 60,
        "status": "scheduled",
        "notes": "REDO - Lint still blowing out after first service."
    }
]

inserted = 0
for appt in sample_appointments:
    try:
        cur.execute("""
            INSERT INTO appointments
            (calendar_event_id, technician_id, customer_name, customer_phone,
             customer_email, service_type, address, latitude, longitude,
             start_time, end_time, duration_minutes, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            appt["calendar_event_id"], appt["technician_id"],
            appt["customer_name"], appt["customer_phone"],
            appt["customer_email"], appt["service_type"],
            appt["address"], appt["latitude"], appt["longitude"],
            appt["start_time"], appt["end_time"],
            appt["duration_minutes"], appt["status"], appt["notes"]
        ))
        inserted += 1
        print(f"  Inserted: {appt['customer_name']} - {appt['service_type']} ({appt['status']})")
    except Exception as e:
        print(f"  Error inserting {appt['customer_name']}: {e}")
        conn.rollback()

conn.commit()
cur.close()
conn.close()

print(f"\nDone! Inserted {inserted} sample appointments.")
print(f"  - 5 upcoming (scheduled/confirmed)")
print(f"  - 3 past (completed)")
print(f"  - 1 cancelled")
print(f"  - 1 redo")
