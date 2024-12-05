from flask import Flask, render_template, request, redirect, url_for
import sqlite3

DB_NAME = 'reservations.db'

def get_cost_matrix():
    """
    Generate a cost matrix for flight seats.
    Each column in the seating chart corresponds to a specific cost:
        Column 0: $100
        Column 1: $75
        Column 2: $50
        Column 3: $100
    """
    cost_matrix = []
    for _ in range(12):  # Assuming 12 rows
        cost_matrix.append([100, 75, 50, 100])
    return cost_matrix




def generate_eticket_number(passenger_name, string_2):
    # Initialize an empty list to store the result
    eticket_number = []
    
    # Find the shortest length of the two strings
    min_length = min(len(passenger_name), len(string_2))
    
    # Alternate characters between both strings
    for i in range(min_length):
        eticket_number.append(passenger_name[i])
        eticket_number.append(string_2[i])
    
    # Append any remaining characters from the longer string
    if len(passenger_name) > min_length:
        eticket_number.append(passenger_name[min_length:])
    elif len(string_2) > min_length:
        eticket_number.append(string_2[min_length:])
    
    # Join the list to form the final eTicket number string
    return ''.join(eticket_number)



app = Flask(__name__)

# Database setup function
def get_db_connection():
    conn = sqlite3.connect('reservations.db')
    conn.row_factory = sqlite3.Row
    return conn

# Home page (Main Menu)
@app.route('/')
def index():
    return render_template('index.html')

# Test database connection (Optional)
@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    conn = get_db_connection()

    # Fetch all reserved seats
    reservations = conn.execute('SELECT seatRow, seatColumn FROM reservations').fetchall()
    conn.close()

    # Initialize a 12x4 seating chart
    seating_data = [['O' for _ in range(4)] for _ in range(12)]

    # Mark reserved seats as 'X'
    for reservation in reservations:
        row = reservation['seatRow']
        col = reservation['seatColumn']
        seating_data[row][col] = 'X'

    # Format the seating chart for display
    formatted_seating_chart = [
        f"({','.join(row)})" for row in seating_data
    ]

    # Initialize variables for the message
    success_message = None
    error_message = None
    passenger_name = None
    seat_row = None
    seat_column = None
    e_ticket_number = None

    if request.method == 'POST':
        # Get data from form submission
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        seat_row = int(request.form['seat_row'])
        seat_column = int(request.form['seat_column'])

        # Check if the seat is already taken
        if seating_data[seat_row][seat_column] == 'X':
            error_message = "Seat already taken. Please choose a different seat."
        else:
            # Generate the eTicketNumber
            passenger_name = f"{first_name} {last_name}"
            e_ticket_number = generate_eticket_number(passenger_name, 'IT4320')

            # Insert the reservation into the database with the eTicketNumber
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute(
                    'INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)',
                    (passenger_name, seat_row, seat_column, e_ticket_number)
                )
                conn.commit()

            # Success message with seat info and eTicket
            success_message = f"Reservation successful! You have booked Seat Row {seat_row + 1}, Column {seat_column + 1}. Your eTicket number is {e_ticket_number}."

    # Render the reservation page with the seating chart and any messages
    return render_template('reserve.html', seating_chart=formatted_seating_chart, 
                           success_message=success_message, error_message=error_message)








# Admin login page
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check the credentials in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'

    return render_template('admin_login.html', error=error)

# Admin dashboard page (view all reservations)
@app.route('/admin/dashboard')
def admin_dashboard():
    conn = get_db_connection()

    # Query all the reservations from the database
    reservations = conn.execute('SELECT seatRow, seatColumn FROM reservations').fetchall()
    conn.close()

    # Create a seating chart with 4 columns and 12 rows (4x12 matrix)
    seating_data = [['O' for _ in range(4)] for _ in range(12)]  # Initialize all seats as available ('O')

    # Mark reserved seats with 'X' based on the database values
    for reservation in reservations:
        row = reservation['seatRow']
        col = reservation['seatColumn']
        seating_data[row][col] = 'X'  # Mark the seat as reserved ('X')

    # Generate cost matrix
    cost_matrix = [[100, 75, 50, 100] for _ in range(12)]

    # Calculate total sales using the cost matrix
    total_sales = sum(cost_matrix[row][col] for row, col in [(r['seatRow'], r['seatColumn']) for r in reservations])

    # Render the dashboard template with seating chart and total sales
    return render_template('admin_dashboard.html', seating_data=seating_data, total_sales=total_sales)


# Running the Flask app
if __name__ == '__main__':
    app.run(debug=True)
