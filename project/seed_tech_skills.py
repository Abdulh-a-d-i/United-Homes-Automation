"""
Update technician skills in the database.
Run on server: cd /home/ubuntu/United-Homes-Automation && source venv/bin/activate && python project/seed_tech_skills.py
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

ALL_SKILLS = json.dumps(["chimney", "dryer_vent", "gutter", "power_washing", "air_duct"])

cur.execute("SELECT id, name, skills, home_latitude, home_longitude, status FROM technicians ORDER BY id")
techs = cur.fetchall()

print(f"\n=== Current Technicians ({len(techs)}) ===")
for t in techs:
    print(f"  ID={t['id']} | {t['name']} | skills={t.get('skills')} | status={t['status']}")

for t in techs:
    cur.execute("""
        UPDATE technicians
        SET skills = %s::jsonb, status = 'active',
            home_latitude = COALESCE(home_latitude, 35.2271),
            home_longitude = COALESCE(home_longitude, -80.8431),
            max_radius_miles = COALESCE(max_radius_miles, 50)
        WHERE id = %s
    """, (ALL_SKILLS, t["id"]))
    print(f"  Updated: {t['name']} -> {ALL_SKILLS}")

if not techs:
    print("\nNo techs found. Creating 3 sample technicians...")
    cur.execute("""
        INSERT INTO technicians (name, email, phone, skills, home_latitude, home_longitude, max_radius_miles, status)
        VALUES
        ('Mike Johnson', 'mike@unitedhome.com', '+17045551001', %s::jsonb, 35.2271, -80.8431, 50, 'active'),
        ('Sarah Davis', 'sarah@unitedhome.com', '+17045551002', %s::jsonb, 35.2000, -80.8500, 50, 'active'),
        ('James Wilson', 'james@unitedhome.com', '+17045551003', %s::jsonb, 35.1900, -80.8200, 50, 'active')
        RETURNING id, name
    """, (ALL_SKILLS, ALL_SKILLS, ALL_SKILLS))
    print(f"  Created: {[t['name'] for t in cur.fetchall()]}")

conn.commit()

cur.execute("SELECT id, name, skills, max_radius_miles, status FROM technicians WHERE status = 'active' ORDER BY id")
print(f"\n=== Final State ===")
for t in cur.fetchall():
    print(f"  ID={t['id']} | {t['name']} | skills={t['skills']} | radius={t['max_radius_miles']}mi")

cur.close()
conn.close()
print("\nDone!")
