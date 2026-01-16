import sqlite3
from datetime import datetime

DB_NAME = "appointments.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            surname TEXT,
            problems TEXT,
            mobile_no TEXT,
            gender TEXT,
            booking_date TEXT,
            booking_time TEXT,
            city TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_booking(data: dict):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bookings (name, surname, problems, mobile_no, gender, booking_date, booking_time, city)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["surname"],
        ",".join(data["problems"]),
        str(data["mobile_no"]),
        data["gender"],
        data["booking_date"],
        data["booking_time"],
        data["city"]
    ))
    conn.commit()
    conn.close()

def get_bookings_by_date(target_date: str):
    """Get all bookings for a specific date"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, surname, problems, mobile_no, gender, booking_date, booking_time, city, created_at
        FROM bookings
        WHERE booking_date = ?
        ORDER BY booking_time
    """, (target_date,))
    
    bookings = []
    for row in cur.fetchall():
        bookings.append({
            "id": row[0],
            "name": row[1],
            "surname": row[2],
            "problems": row[3],
            "mobile_no": row[4],
            "gender": row[5],
            "booking_date": row[6],
            "booking_time": row[7],
            "city": row[8],
            "created_at": row[9]
        })
    
    conn.close()
    return bookings

def get_all_bookings():
    """Get all bookings sorted by date and time"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, surname, problems, mobile_no, gender, booking_date, booking_time, city, created_at
        FROM bookings
        ORDER BY booking_date, booking_time
    """)
    
    bookings = []
    for row in cur.fetchall():
        bookings.append({
            "id": row[0],
            "name": row[1],
            "surname": row[2],
            "problems": row[3],
            "mobile_no": row[4],
            "gender": row[5],
            "booking_date": row[6],
            "booking_time": row[7],
            "city": row[8],
            "created_at": row[9]
        })
    
    conn.close()
    return bookings

def delete_booking(booking_id: int):
    """Delete a booking by ID"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

def get_booking_stats():
    """Get statistics about bookings"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Today's bookings
    cur.execute("SELECT COUNT(*) FROM bookings WHERE booking_date = ?", (today,))
    today_count = cur.fetchone()[0]
    
    # Total bookings
    cur.execute("SELECT COUNT(*) FROM bookings")
    total_count = cur.fetchone()[0]
    
    conn.close()
    
    return {
        "today": today_count,
        "total": total_count
    }