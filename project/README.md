# AI Receptionist Scheduling System - FastAPI Backend

A FastAPI-based backend for intelligent appointment scheduling with automatic technician assignment based on location, availability, and skills.

## Features

- Address verification and geocoding via Radar.io
- Intelligent technician matching based on distance and availability
- Real-time calendar integration with GoHighLevel (GHL)
- Automatic route optimization and cache invalidation
- Webhook support for GHL appointment events
- PostgreSQL database with appointment and technician management

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` with your credentials:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
GHL_API_KEY=your_ghl_api_key_here
RADAR_API_KEY=your_radar_api_key_here
```

### 3. Run the Application
```bash
uvicorn main:app --reload
```

### 4. Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Appointments
- `POST /api/appointments/verify-address` - Geocode and validate addresses
- `POST /api/appointments/find-technician-availability` - Find best available technician
- `POST /api/appointments/book-appointment` - Book appointment with technician

### Technicians
- `GET /api/technicians` - List all active technicians
- `POST /api/technicians` - Create new technician

### Webhooks
- `POST /api/webhooks/appointment-created` - Handle GHL appointment creation
- `POST /api/webhooks/appointment-deleted` - Handle GHL appointment deletion

## How It Works

### Intelligent Technician Matching
1. Filters technicians by required skill
2. Estimates technician location based on current schedule
3. Calculates distance using Haversine formula
4. Filters by service radius
5. Checks calendar availability
6. Returns closest available technician

### Location Estimation
- Before first appointment: technician is at home
- Between appointments: technician is at last job location
- During appointment: technician is at current job location

This provides realistic travel time calculations.

## Database Schema

- **technicians** - Technician profiles with skills, location, and preferences
- **appointments_cache** - Cached appointment data for quick lookups
- **route_cache** - Pre-calculated route data (auto-invalidated on changes)

## Code Standards

- PEP 8 compliant
- Clean, simple logic
- Clear separation of concerns
- Comprehensive error handling

## License

Proprietary
