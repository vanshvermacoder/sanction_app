from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import os
import logging
from datetime import datetime
from fpdf import FPDF
from num2words import num2words

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def init_db():
    try:
        db_path = os.path.join(os.getcwd(), "sanctions.db")
        logger.debug(f"Current working directory: {os.getcwd()}")
        logger.debug(f"Attempting to initialize database at {db_path}")
        if not os.access(os.getcwd(), os.W_OK):
            logger.error(f"No write permission in {os.getcwd()}")
            raise PermissionError(f"No write permission in {os.getcwd()}")
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
        raise

def seed_teachers():
    try:
        db_path = os.path.join(os.getcwd(), "sanctions.db")
        teachers_data = [
        ("2013034577", "VANDNA", "LECTURER POLITICAL SCIENCE", "59282970"),
        ("2013051618", "RASHMI SHARMA", "LECTURER ENGLISH", "81517653"),
        ("2013052791", "KIRAN MAURYA", "TGT SOCIAL SCIENCE", "51659484"),
        ("2013216208", "SMTRAJESRI DEVI", "TGT SANSKRIT", "86837591"),
        ("2013262057", "ALKA SHARMA", "TGT NATURAL SCIENCE", "53417529"),
        ("2013529085", "JOOLI", "TGT PET", "63667860"),
        ("2014009064", "DOLI", "TGT SPECIAL EDUCATION TEACHER", "52147318"),
        ("2014017594", "SARITA KUMARI", "LECTURER POLITICAL SCIENCE", "50803800"),
        ("2014020702", "SEEMA KUMARI", "LECTURER HINDI", "26879010"),
        ("2014023937", "POOJA GOYAL", "TGT SANSKRIT", "99135751"),
        ("2014042910", "SUNEETA MEENA", "LECTURER SANSKRIT", "65512895"),
        ("2014054513", "VARSHA SHARMA", "LECTURER POLITICAL SCIENCE", "50270586"),
        ("2014061685", "KM MAMTA KUMARI", "LECTURER GEOGRAPHY", "14817956"),
        ("2014072375", "PRABHA", "LECTURER HISTORY", "12378599"),
        ("2014082977", "POONAM RANI", "TGT HINDI", "41725605"),
        ("2014132606", "SHALU TOMAR", "LECTURER HISTORY", "14049094"),
        ("2014133920", "MEENAKSHI VERMA", "LECTURER HINDI", "92739631"),
        ("2014144738", "KM NEHA GUPTA", "TGT NATURAL SCIENCE", "10907985"),
        ("2017020486", "LALIT CHOUDHARY", "TGT PET", "56877285"),
        ("2017048499", "RAJENDRA PRASAD MEENA", "LECTURER GEOGRAPHY", "22057398"),
        ("2017052969", "RUBY", "TGT ENGLISH", "98783133"),
        ("2017056803", "MANJU RANI", "TGT SOCIAL SCIENCE", "21500386"),
        ("2017057835", "SHANVIKA GAUR", "LECTURER MATH", "98894471"),
        ("2017077447", "DEEPAK KUMAR", "LECTURER PHYSICAL EDUCATION", "86357860"),
        ("2017078692", "REENA", "TGT ENGLISH", "88259229"),
        ("2017090786", "DEEPA", "TGT MATH", "76623091"),
        ("2017092747", "ABHILASHA GUJER", "TGT NATURAL SCIENCE", "22753889"),
        ("2017112432", "JYOTI", "LECTURER GEOGRAPHY", "90148442"),
        ("2017124568", "REENA KUMARI", "LECTURER ENGLISH", "32550162"),
        ("2017126314", "SUMAN RANI", "TGT ENGLISH", "44550504"),
        ("2017133091", "KM PRAGGYA KUMARI", "LECTURER HISTORY", "73689092"),
        ("2017138324", "GAURI SHARMA", "TGT MATH", "20675132"),
        ("2020000081", "PRIYA", "TGT MATH", "66708566"),
        ("2020032667", "ARCHANA CHAUBEY", "TGT MATH", "28560314"),
        ("2020037257", "PRIYA MISHRA", "TGT MATH", "56539258"),
        ("2020038678", "CHANDNI", "TGT SPECIAL EDUCATION TEACHER", "46172837"),
        ("2020046161", "KAJAL", "TGT MATH", "81378001"),
        ("21011155319", "PREETI SHARMA", "TGT HINDI", "10959365"),
        ("21011177022", "HITESH KUMARI", "TGT SOCIAL SCIENCE", "22123096")
        ]
        conn = sqlite3.connect(db_path)
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

logger.info("Starting app initialization")
init_db()
logger.info("App initialization complete")

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
        logger.debug("Fetching teachers for /issue")
        c.execute("SELECT app_id, name, designation, nic_pin FROM teachers")
        teachers = c.fetchall()
        conn.close()
        logger.debug(f"Fetched {len(teachers)} teachers")
        return render_template('issue_form.html', teachers=teachers)
    except Exception as e:
        logger.error(f"Error in issue_sanction: {str(e)}")
        raise

@app.route('/sanctions')
def list_sanctions():
    try:
        conn = sqlite3.connect(os.path.join(os.getcwd(), "sanctions.db"))
        c = conn.cursor()
        # Join sanctions with sanction_teachers and teachers to get teacher names
        c.execute('''
            SELECT s.id, s.total_amount, s.month, s.issued_date, s.file_path, 
                   t.name, st.days
            FROM sanctions s
            LEFT JOIN sanction_teachers st ON s.id = st.sanction_id
            LEFT JOIN teachers t ON st.app_id = t.app_id
            ORDER BY s.id DESC
        ''')
        sanctions_data = c.fetchall()
        conn.close()

        # Group teachers by sanction ID
        sanctions = {}
        for row in sanctions_data:
            sanction_id = row[0]
            if sanction_id not in sanctions:
                sanctions[sanction_id] = {
                    'id': row[0],
                    'total_amount': row[1],
                    'month': row[2],
                    'issued_date': row[3],
                    'file_path': row[4],
                    'teachers': []
                }
            if row[5]:  # If teacher name exists
                sanctions[sanction_id]['teachers'].append({
                    'name': row[5],
                    'days': row[6]
                })

        logger.debug(f"Fetched {len(sanctions)} sanctions with teacher details")
        return render_template('sanctions_list.html', sanctions=sanctions.values())
    except Exception as e:
        logger.error(f"Error in list_sanctions: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(debug=True)