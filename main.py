from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.twiml.messaging_response import MessagingResponse
from agent import build_graph
from db import init_db, get_bookings_by_date, get_all_bookings, delete_booking, get_booking_stats
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = FastAPI()
workflow = build_graph()
init_db()

user_states = {}
@app.post("/whatsapp")
async def whatsapp_bot(request: Request):
    form = await request.form()
    incoming_msg = form.get("Body")
    user_number = form.get("From")

    if not incoming_msg:
        resp = MessagingResponse()
        resp.message("❌ Sorry, I could not read your message.")
        return Response(content=str(resp), media_type="application/xml")

    # Initialize user state if new user
    if user_number not in user_states:
        user_states[user_number] = {
            "messages": [],
            "done": False
        }

    state = user_states[user_number]

    # Add user message
    state["messages"].append(HumanMessage(content=incoming_msg))

    # Run LangGraph workflow
    state = workflow.invoke(state)
    user_states[user_number] = state

    # Get last AI reply
    last_reply = state["messages"][-1].content

    resp = MessagingResponse()
    resp.message(last_reply)

    # ✅ IMPORTANT: Clear context after booking
    if state.get("done"):
        user_states[user_number] = {
            "messages": [],
            "done": False
        }

    return Response(content=str(resp), media_type="application/xml")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Appointment Management Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                transition: transform 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
            }
            
            .stat-card h3 {
                color: #667eea;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }
            
            .stat-card .number {
                font-size: 2.5rem;
                font-weight: bold;
                color: #333;
            }
            
            .filters {
                background: white;
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .filter-buttons {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            .filter-btn {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                background: #667eea;
                color: white;
                cursor: pointer;
                font-size: 0.95rem;
                transition: all 0.3s ease;
            }
            
            .filter-btn:hover {
                background: #5568d3;
                transform: translateY(-2px);
            }
            
            .filter-btn.active {
                background: #764ba2;
            }
            
            .bookings-container {
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .booking-card {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
            
            .booking-card:hover {
                transform: translateX(5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            
            .booking-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .booking-name {
                font-size: 1.3rem;
                font-weight: bold;
                color: #333;
            }
            
            .booking-time {
                background: #667eea;
                color: white;
                padding: 8px 15px;
                border-radius: 20px;
                font-weight: 600;
            }
            
            .booking-details {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 15px;
            }
            
            .detail-item {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .detail-label {
                font-weight: 600;
                color: #555;
            }
            
            .detail-value {
                color: #333;
            }
            
            .problems {
                background: #fff3cd;
                padding: 10px 15px;
                border-radius: 8px;
                margin-bottom: 10px;
                border-left: 4px solid #ffc107;
            }
            
            .delete-btn {
                background: #dc3545;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            }
            
            .delete-btn:hover {
                background: #c82333;
                transform: scale(1.05);
            }
            
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #999;
            }
            
            .empty-state svg {
                width: 100px;
                height: 100px;
                margin-bottom: 20px;
                opacity: 0.5;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                font-size: 1.2rem;
                color: #667eea;
            }
            
            @media (max-width: 768px) {
                .header h1 {
                    font-size: 1.8rem;
                }
                
                .booking-header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 10px;
                }
                
                .booking-details {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Appointment Management Dashboard</h1>
                <p>Manage your hospital appointments efficiently</p>
            </div>
            
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <h3>Today's Appointments</h3>
                    <div class="number" id="todayCount">-</div>
                </div>
                <div class="stat-card">
                    <h3>Tomorrow's Appointments</h3>
                    <div class="number" id="tomorrowCount">-</div>
                </div>
                <div class="stat-card">
                    <h3>Total Appointments</h3>
                    <div class="number" id="totalCount">-</div>
                </div>
            </div>
            
            <div class="filters">
                <h3 style="margin-bottom: 15px; color: #333;">Filter by Date</h3>
                <div class="filter-buttons">
                    <button class="filter-btn active" onclick="filterBookings('all')">All Appointments</button>
                    <button class="filter-btn" onclick="filterBookings('today')">Today</button>
                    <button class="filter-btn" onclick="filterBookings('tomorrow')">Tomorrow</button>
                    <button class="filter-btn" onclick="filterBookings('upcoming')">Upcoming (7 days)</button>
                </div>
            </div>
            
            <div class="bookings-container">
                <h2 style="margin-bottom: 20px; color: #333;">Appointments</h2>
                <div id="bookingsList" class="loading">Loading appointments...</div>
            </div>
        </div>
        
        <script>
            let allBookings = [];
            let currentFilter = 'all';
            
            async function loadBookings() {
                try {
                    const response = await fetch('/api/bookings');
                    allBookings = await response.json();
                    updateStats();
                    renderBookings();
                } catch (error) {
                    console.error('Error loading bookings:', error);
                    document.getElementById('bookingsList').innerHTML = '<p class="empty-state">Error loading appointments</p>';
                }
            }
            
            function updateStats() {
                const today = new Date().toISOString().split('T')[0];
                const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
                
                const todayBookings = allBookings.filter(b => b.booking_date === today);
                const tomorrowBookings = allBookings.filter(b => b.booking_date === tomorrow);
                
                document.getElementById('todayCount').textContent = todayBookings.length;
                document.getElementById('tomorrowCount').textContent = tomorrowBookings.length;
                document.getElementById('totalCount').textContent = allBookings.length;
            }
            
            function filterBookings(filter) {
                currentFilter = filter;
                
                // Update active button
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
                renderBookings();
            }
            
            function renderBookings() {
                const bookingsList = document.getElementById('bookingsList');
                
                let filteredBookings = [...allBookings];
                const today = new Date().toISOString().split('T')[0];
                const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
                const nextWeek = new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0];
                
                if (currentFilter === 'today') {
                    filteredBookings = filteredBookings.filter(b => b.booking_date === today);
                } else if (currentFilter === 'tomorrow') {
                    filteredBookings = filteredBookings.filter(b => b.booking_date === tomorrow);
                } else if (currentFilter === 'upcoming') {
                    filteredBookings = filteredBookings.filter(b => b.booking_date >= today && b.booking_date <= nextWeek);
                }
                
                if (filteredBookings.length === 0) {
                    bookingsList.innerHTML = `
                        <div class="empty-state">
                            <svg fill="#ccc" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/>
                            </svg>
                            <h3>No appointments found</h3>
                            <p>There are no appointments matching your filter.</p>
                        </div>
                    `;
                    return;
                }
                
                bookingsList.innerHTML = filteredBookings.map(booking => `
                    <div class="booking-card">
                        <div class="booking-header">
                            <div class="booking-name">${booking.name} ${booking.surname}</div>
                            <div class="booking-time">📅 ${formatDate(booking.booking_date)} • 🕐 ${formatTime(booking.booking_time)}</div>
                        </div>
                        
                        <div class="booking-details">
                            <div class="detail-item">
                                <span class="detail-label">📱 Mobile:</span>
                                <span class="detail-value">${booking.mobile_no}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">⚧ Gender:</span>
                                <span class="detail-value">${booking.gender}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">🏙️ City:</span>
                                <span class="detail-value">${booking.city}</span>
                            </div>
                        </div>
                        
                        <div class="problems">
                            <strong>🩺 Problems/Symptoms:</strong> ${booking.problems}
                        </div>
                        
                        <button class="delete-btn" onclick="deleteBooking(${booking.id})">
                            🗑️ Remove from Queue
                        </button>
                    </div>
                `).join('');
            }
            
            function formatDate(dateStr) {
                const date = new Date(dateStr + 'T00:00:00');
                const today = new Date().toISOString().split('T')[0];
                const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
                
                if (dateStr === today) return 'Today';
                if (dateStr === tomorrow) return 'Tomorrow';
                
                const options = { weekday: 'short', month: 'short', day: 'numeric' };
                return date.toLocaleDateString('en-US', options);
            }
            
            function formatTime(timeStr) {
                const [hours, minutes] = timeStr.split(':');
                const hour = parseInt(hours);
                const ampm = hour >= 12 ? 'PM' : 'AM';
                const displayHour = hour % 12 || 12;
                return `${displayHour}:${minutes} ${ampm}`;
            }
            
            async function deleteBooking(id) {
                if (!confirm('Are you sure you want to remove this appointment?')) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/bookings/${id}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        await loadBookings();
                    } else {
                        alert('Failed to delete appointment');
                    }
                } catch (error) {
                    console.error('Error deleting booking:', error);
                    alert('Error deleting appointment');
                }
            }
            
            // Load bookings on page load
            loadBookings();
            
            // Auto-refresh every 30 seconds
            setInterval(loadBookings, 3000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/bookings")
async def get_bookings():
    bookings = get_all_bookings()
    return JSONResponse(content=bookings)


@app.delete("/api/bookings/{booking_id}")
async def remove_booking(booking_id: int):
    try:
        delete_booking(booking_id)
        return JSONResponse(content={"success": True, "message": "Booking deleted"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)