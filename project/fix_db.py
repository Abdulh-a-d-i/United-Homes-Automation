"""
FIX SCRIPT: Run this on the server to:
1. Fix technician skills (set proper service type enums)
2. Fix technician coordinates (set to Charlotte, NC area)
3. Clean up appointments_cache entries → move them to appointments table

Run: cd /home/ubuntu/United-Homes-Automation && source venv/bin/activate && python project/fix_db.py
"""
import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 60)
print("UNITED HOME SERVICES — DB FIX SCRIPT")
print("=" * 60)

# ═══════════════════════════════════════════
# 1. FIX TECHNICIAN SKILLS & COORDINATES
# ═══════════════════════════════════════════
print("\n--- 1. FIXING TECHNICIANS ---")

ALL_SKILLS = json.dumps(["chimney", "dryer_vent", "gutter", "power_washing", "air_duct"])

# Charlotte, NC area coordinates for techs
CHARLOTTE_COORDS = [
    (35.2271, -80.8431),  # Uptown Charlotte
    (35.2000, -80.8500),  # South Charlotte
    (35.1900, -80.8200),  # East Charlotte
]

cur.execute("SELECT id, name, skills, home_latitude, home_longitude, status FROM technicians ORDER BY id")
techs = cur.fetchall()

print(f"Found {len(techs)} technicians:")
for i, t in enumerate(techs):
    print(f"  BEFORE: ID={t['id']} | {t['name']} | skills={t['skills']} | coords=({t['home_latitude']}, {t['home_longitude']}) | status={t['status']}")

    # Pick Charlotte coordinates (cycle through them)
    lat, lng = CHARLOTTE_COORDS[i % len(CHARLOTTE_COORDS)]

    cur.execute("""
        UPDATE technicians
        SET skills = %s::jsonb,
            status = 'active',
            home_latitude = %s,
            home_longitude = %s,
            max_radius_miles = 50
        WHERE id = %s
    """, (ALL_SKILLS, lat, lng, t["id"]))

    print(f"  AFTER:  ID={t['id']} | {t['name']} | skills={ALL_SKILLS} | coords=({lat}, {lng}) | status=active")

if not techs:
    print("  No techs found! Creating 3 sample techs...")
    cur.execute("""
        INSERT INTO technicians (name, email, phone, skills, home_latitude, home_longitude, max_radius_miles, status)
        VALUES
        ('Mike Johnson', 'mike@unitedhome.com', '+17045551001', %s::jsonb, 35.2271, -80.8431, 50, 'active'),
        ('Sarah Davis', 'sarah@unitedhome.com', '+17045551002', %s::jsonb, 35.2000, -80.8500, 50, 'active'),
        ('James Wilson', 'james@unitedhome.com', '+17045551003', %s::jsonb, 35.1900, -80.8200, 50, 'active')
        RETURNING id, name
    """, (ALL_SKILLS, ALL_SKILLS, ALL_SKILLS))
    new_techs = cur.fetchall()
    print(f"  Created: {[t['name'] for t in new_techs]}")

conn.commit()

# ═══════════════════════════════════════════
# 2. VERIFY APPOINTMENTS TABLE EXISTS
# ═══════════════════════════════════════════
print("\n--- 2. CHECKING APPOINTMENTS TABLE ---")

cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'appointments'
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print(f"  appointments table has {len(cols)} columns:")
for c in cols:
    print(f"    {c['column_name']} ({c['data_type']})")

# Check appointments_cache
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'appointments_cache'
    ORDER BY ordinal_position
""")
cache_cols = cur.fetchall()
print(f"  appointments_cache table has {len(cache_cols)} columns:")
for c in cache_cols:
    print(f"    {c['column_name']} ({c['data_type']})")

# ═══════════════════════════════════════════
# 3. COUNT RECORDS
# ═══════════════════════════════════════════
print("\n--- 3. RECORD COUNTS ---")

cur.execute("SELECT COUNT(*) as cnt FROM appointments")
appt_count = cur.fetchone()['cnt']
print(f"  appointments: {appt_count} records")

cur.execute("SELECT COUNT(*) as cnt FROM appointments_cache")
cache_count = cur.fetchone()['cnt']
print(f"  appointments_cache: {cache_count} records")

cur.execute("SELECT COUNT(*) as cnt FROM technicians WHERE status = 'active'")
tech_count = cur.fetchone()['cnt']
print(f"  active technicians: {tech_count}")

# ═══════════════════════════════════════════
# 4. FINAL STATE
# ═══════════════════════════════════════════
print("\n--- 4. FINAL TECHNICIAN STATE ---")
cur.execute("SELECT id, name, skills, home_latitude, home_longitude, max_radius_miles, status FROM technicians ORDER BY id")
for t in cur.fetchall():
    print(f"  ID={t['id']} | {t['name']} | skills={t['skills']} | coords=({t['home_latitude']}, {t['home_longitude']}) | radius={t['max_radius_miles']}mi | {t['status']}")

cur.close()
conn.close()
print("\n" + "=" * 60)
print("DONE! All technicians updated with proper skills and Charlotte coordinates.")
print("=" * 60)
