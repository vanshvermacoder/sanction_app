from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import os
import logging
from datetime import datetime
from fpdf import FPDF
from num2words import num2words

# Setup logging for Render debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def init_db():
    try:
        db_path = os.path.join(os.getcwd(), "sanctions.db")
        logger.debug(f"Attempting to initialize database at {db_path}")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        logger.debug("Connected to SQLite")
        c.execute('''CREATE TABLE IF NOT EXISTS sanctions 
                     (id INTEGER PRIMARY KEY, total_amount TEXT, month TEXT, issued_date TEXT, file_path TEXT)''')
        logger.debug("Created sanctions table")
        c.execute('''CREATE TABLE IF NOT EXISTS teachers 
                     (id INTEGER PRIMARY KEY, app_id TEXT UNIQUE, name TEXT, designation TEXT, nic_pin TEXT)''')
        logger.debug("Created teachers table")
        c.execute('''CREATE TABLE IF NOT EXISTS sanction_teachers 
                     (id INTEGER PRIMARY KEY, sanction_id INTEGER, app_id TEXT, days INTEGER,
                      FOREIGN KEY(sanction_id) REFERENCES sanctions(id),
                      FOREIGN KEY(app_id) REFERENCES teachers(app_id))''')
        logger.debug("Created sanction_teachers table")
        conn.commit()
        conn.close()
        seed_teachers()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise  # Ensure startup fails visibly in logs

def seed_teachers():
    try:
        teachers_data = [
            ("2013034577", "VANDNA", "LECTURER POLITICAL SCIENCE", "59282970"),
            ("2013034578", "RAJESH KUMAR", "LECTURER MATHEMATICS", "59282971"),
            ("2013034579", "ANITA SHARMA", "LECTURER ENGLISH", "59282972"),
            # Add all 39 teachers here—replace with your full list if different...
            ("21011177022", "HITESH KUMARI", "TGT SOCIAL SCIENCE", "22123096"),
        ]
        conn = sqlite3.connect(os.path.join(os.getcwd(), "sanctions.db"))
        c = conn.cursor()
        logger.debug("Seeding teachers into database")
        for teacher in teachers_data:
            c.execute("INSERT OR IGNORE INTO teachers (app_id, name, designation, nic_pin) VALUES (?, ?, ?, ?)", teacher)
        conn.commit()
        conn.close()
        logger.debug("Teachers seeded successfully")
    except Exception as e:
        logger.error(f"Failed to seed teachers: {str(e)}")
        raise

init_db()  # Runs on startup when app.py is imported by Gunicorn

def calculate_payment(designation, days):
    if "LECTURER" in designation.upper():
        return days * 1445
    elif "TGT" in designation.upper():
        return days * 1403
    return 0

def format_indian_number(number):
    num_str = str(int(number))
    if len(num_str) <= 3:
        return num_str
    result = num_str[-3:]
    remaining = num_str[:-3]
    while remaining:
        result = remaining[-2:] + "," + result
        remaining = remaining[:-2]
    return result

def generate_pdf(order_data, file_path):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Sanction Order", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"Month: {order_data['month']}", ln=True)
        pdf.cell(0, 10, f"Date: {order_data['date']}", ln=True)
        pdf.cell(0, 10, f"Total: Rs. {order_data['total_amount']}", ln=True)
        pdf.cell(0, 10, f"In Words: {order_data['total_amount_words']}", ln=True)
        for teacher in order_data['teachers']:
            pdf.cell(0, 10, f"{teacher['name']} ({teacher['designation']}): {teacher['days']} days, Rs. {teacher['amount']}", ln=True)
        pdf.output(file_path)
        logger.info(f"PDF generated at {file_path}")
    except Exception as e:
        logger.error(f"Failed to generate PDF: {str(e)}")
        raise

@app.route('/')
def home():
    return redirect(url_for('issue_sanction'))

@app.route('/issue', methods=['GET', 'POST'])
def issue_sanction():
    try:
        if request.method == 'POST':
            month = request.form['month']
            selected_teachers = request.form.getlist('teachers')
            days = {key: int(value) for key, value in request.form.items() if key.startswith('days_') and value}

            if not month or not selected_teachers:
                return "Please enter a month and select teachers!", 400

            issued_date = datetime.now().strftime("%Y-%m-%d")
            year = issued_date.split('-')[0]
            teachers_data = []
            total_amount = 0

            conn = sqlite3.connect(os.path.join(os.getcwd(), "sanctions.db"))
            c = conn.cursor()
            for app_id in selected_teachers:
                c.execute("SELECT name, designation, nic_pin FROM teachers WHERE app_id = ?", (app_id,))
                result = c.fetchone()
                if result:
                    name, designation, nic_pin = result
                    teacher_days = days.get(f"days_{app_id}", 0)
                    if teacher_days > 0:
                        amount = calculate_payment(designation, teacher_days)
                        total_amount += amount
                        teachers_data.append({'app_id': app_id, 'name': name, 'designation': designation, 'nic_pin': nic_pin, 'days': teacher_days, 'amount': amount})
            total_amount_str = format_indian_number(total_amount)
            total_amount_words = num2words(total_amount, lang='en_IN').replace(',', '').title() + " Only"

            c.execute("INSERT INTO sanctions (total_amount, month, issued_date, file_path) VALUES (?, ?, ?, ?)",
                      (total_amount_str, month, issued_date, ""))
            order_id = c.lastrowid
            for teacher in teachers_data:
                c.execute("INSERT INTO sanction_teachers (sanction_id, app_id, days) VALUES (?, ?, ?)",
                          (order_id, teacher['app_id'], teacher['days']))
            conn.commit()
            conn.close()

            file_path = f"sanctions/hos_{month}_{year}.pdf"
            order_data = {"total_amount": total_amount_str, "total_amount_words": total_amount_words, "month": month, "date": issued_date, "teachers": teachers_data}
            generate_pdf(order_data, file_path)
            return send_file(file_path, as_attachment=True)

        conn = sqlite3.connect(os.path.join(os.getcwd(), "sanctions.db"))
        c = conn.cursor()
        c.execute("SELECT app_id, name, designation, nic_pin FROM teachers")
        teachers = c.fetchall()
        conn.close()
        return render_template('issue_form.html', teachers=teachers)
    except Exception as e:
        logger.error(f"Error in issue_sanction: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(debug=True)  # For local testing only