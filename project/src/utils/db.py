import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS technicians (
            id SERIAL PRIMARY KEY,
            ghl_user_id VARCHAR(255) UNIQUE,
            ghl_calendar_id VARCHAR(255) UNIQUE,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            skills JSONB,
            home_latitude DECIMAL(10, 8),
            home_longitude DECIMAL(11, 8),
            max_radius_miles INTEGER DEFAULT 20,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments_cache (
            id SERIAL PRIMARY KEY,
            ghl_appointment_id VARCHAR(255) UNIQUE,
            technician_id INTEGER REFERENCES technicians(id),
            customer_name VARCHAR(255),
            customer_phone VARCHAR(50),
            service_type VARCHAR(255),
            address TEXT,
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS route_cache (
            id SERIAL PRIMARY KEY,
            technician_id INTEGER REFERENCES technicians(id),
            date DATE,
            route_data JSONB,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()


def get_technician(tech_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM technicians WHERE id = %s", (tech_id,))
    tech = cur.fetchone()
    cur.close()
    conn.close()
    return dict(tech) if tech else None


def get_techs_with_skill(service_type):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM technicians 
        WHERE status = 'active' 
        AND skills @> %s::jsonb
    """, (f'["{service_type}"]',))
    techs = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(tech) for tech in techs]


def get_tech_appointments_for_day(tech_id, date):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM appointments_cache 
        WHERE technician_id = %s 
        AND DATE(start_time) = %s 
        ORDER BY start_time
    """, (tech_id, date))
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(appt) for appt in appointments]


def insert_appointment_cache(ghl_appointment_id, technician_id, customer_name, 
                            customer_phone, service_type, address, latitude, 
                            longitude, start_time, end_time, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO appointments_cache 
        (ghl_appointment_id, technician_id, customer_name, customer_phone, 
         service_type, address, latitude, longitude, start_time, end_time, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ghl_appointment_id) DO UPDATE SET
        technician_id = EXCLUDED.technician_id,
        customer_name = EXCLUDED.customer_name,
        customer_phone = EXCLUDED.customer_phone,
        service_type = EXCLUDED.service_type,
        address = EXCLUDED.address,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        start_time = EXCLUDED.start_time,
        end_time = EXCLUDED.end_time,
        status = EXCLUDED.status
    """, (ghl_appointment_id, technician_id, customer_name, customer_phone, 
          service_type, address, latitude, longitude, start_time, end_time, status))
    conn.commit()
    cur.close()
    conn.close()


def delete_appointment_cache(ghl_appointment_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM appointments_cache WHERE ghl_appointment_id = %s", 
                (ghl_appointment_id,))
    conn.commit()
    cur.close()
    conn.close()


def delete_route_cache(tech_id, date):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM route_cache 
        WHERE technician_id = %s AND date = %s
    """, (tech_id, date))
    conn.commit()
    cur.close()
    conn.close()


def insert_technician(name, email, phone, skills, home_latitude, home_longitude, 
                     ghl_user_id, ghl_calendar_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        INSERT INTO technicians 
        (name, email, phone, skills, home_latitude, home_longitude, 
         ghl_user_id, ghl_calendar_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """, (name, email, phone, skills, home_latitude, home_longitude, 
          ghl_user_id, ghl_calendar_id))
    tech = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return dict(tech) if tech else None


def get_all_technicians():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM technicians WHERE status = 'active'")
    techs = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(tech) for tech in techs]


def get_technician_by_ghl_user_id(ghl_user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM technicians WHERE ghl_user_id = %s", (ghl_user_id,))
    tech = cur.fetchone()
    cur.close()
    conn.close()
    return dict(tech) if tech else None


def upsert_technician_from_ghl(ghl_user_id, ghl_calendar_id, name, email, phone, 
                               skills=None, home_latitude=None, home_longitude=None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        INSERT INTO technicians 
        (ghl_user_id, ghl_calendar_id, name, email, phone, skills, home_latitude, home_longitude)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ghl_user_id) DO UPDATE SET
        ghl_calendar_id = EXCLUDED.ghl_calendar_id,
        name = EXCLUDED.name,
        email = EXCLUDED.email,
        phone = EXCLUDED.phone,
        skills = COALESCE(EXCLUDED.skills, technicians.skills),
        home_latitude = COALESCE(EXCLUDED.home_latitude, technicians.home_latitude),
        home_longitude = COALESCE(EXCLUDED.home_longitude, technicians.home_longitude)
        RETURNING *
    """, (ghl_user_id, ghl_calendar_id, name, email, phone, skills, home_latitude, home_longitude))
    
    tech = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return dict(tech) if tech else None
