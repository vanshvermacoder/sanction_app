from flask import Flask, request, render_template, redirect, url_for, send_file
import sqlite3
from fpdf import FPDF
from datetime import datetime
import os
from num2words import num2words

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect("sanctions.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sanctions 
                 (id INTEGER PRIMARY KEY, total_amount TEXT, month TEXT, issued_date TEXT, file_path TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS teachers 
                 (id INTEGER PRIMARY KEY, app_id TEXT UNIQUE, name TEXT, designation TEXT, nic_pin TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sanction_teachers 
                 (id INTEGER PRIMARY KEY, sanction_id INTEGER, app_id TEXT, days INTEGER,
                  FOREIGN KEY(sanction_id) REFERENCES sanctions(id),
                  FOREIGN KEY(app_id) REFERENCES teachers(app_id))''')
    conn.commit()
    conn.close()
    seed_teachers()

def seed_teachers():
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
        ("21011177022", "HITESH KUMARI", "TGT SOCIAL SCIENCE", "22123096"),
    ]
    conn = sqlite3.connect("sanctions.db")
    c = conn.cursor()
    for teacher in teachers_data:
        c.execute("INSERT OR IGNORE INTO teachers (app_id, name, designation, nic_pin) VALUES (?, ?, ?, ?)", teacher)
    conn.commit()
    conn.close()

# Payment calculation function
def calculate_payment(designation, days):
    if "LECTURER" in designation.upper():
        return days * 1445
    elif "TGT" in designation.upper():
        return days * 1403
    return 0

# Function to format numbers in Indian comma system
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

# PDF generation with FPDF
def generate_pdf(order_data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "OFFICE OF HEAD OF SCHOOL", ln=True, align="C")
    pdf.cell(0, 1, "", ln=True)
    pdf.cell(0, 6, "GOVT. GIRLS SR. SEC. SCHOOL SABHAPUR DELHI-90.", ln=True, align="C")
    pdf.cell(0, 1, "", ln=True)
    pdf.cell(0, 6, "(SCHOOL ID-1104011)", ln=True, align="C")
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y() + 3, 200, pdf.get_y() + 3)
    pdf.ln(4)
    pdf.set_font("Arial", "B", 11)
    title = "SANCTION ORDER"
    title_width = pdf.get_string_width(title)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.line((210 - title_width) / 2, pdf.get_y() - 1, (210 + title_width) / 2, pdf.get_y() - 1)
    pdf.ln(4)
    pdf.set_font("Arial", size=10)
    year = order_data['date'].split('-')[0]
    pdf.set_font("Arial", "", 10)
    pdf.write(5, "Sanction of HOS/HOO is hereby accorded for incurring an expenditure of Rs. ")
    pdf.set_font("Arial", "B", 10)
    pdf.write(5, f"{order_data['total_amount']}/-")
    pdf.set_font("Arial", "", 10)
    pdf.write(5, " (")
    pdf.set_font("Arial", "B", 10)
    pdf.write(5, order_data['total_amount_words'])
    pdf.set_font("Arial", "", 10)
    pdf.write(5, ") toward payment to Guest Teacher Salary for the M/o ")
    pdf.set_font("Arial", "B", 10)
    pdf.write(5, order_data['month'])
    pdf.set_font("Arial", "", 10)
    pdf.write(5, " on account of GGSSS Sabhapur ")
    pdf.set_font("Arial", "B", 10)
    pdf.write(5, year)
    pdf.set_font("Arial", "", 10)
    pdf.write(5, ". The Details as under :")
    pdf.ln(10)
    pdf.set_font("Arial", size=8)
    col_widths = [10, 25, 45, 60, 20, 12, 18]
    headers = ["S.No.", "Application Id", "Teacher Name", "Designation", "NIC PIN", "Days", "Amount"]
    pdf.set_font("Arial", "B", 8)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align="C")
    pdf.ln()
    pdf.set_font("Arial", size=8)
    for i, teacher in enumerate(order_data['teachers'], 1):
        pdf.cell(col_widths[0], 8, str(i), border=1, align="C")
        pdf.cell(col_widths[1], 8, teacher['app_id'], border=1, align="C")
        pdf.cell(col_widths[2], 8, teacher['name'], border=1, align="C")
        pdf.cell(col_widths[3], 8, teacher['designation'], border=1, align="C")
        pdf.cell(col_widths[4], 8, teacher['nic_pin'], border=1, align="C")
        pdf.cell(col_widths[5], 8, str(teacher['days']), border=1, align="C")
        pdf.cell(col_widths[6], 8, str(teacher['amount']), border=1, align="C")
        pdf.ln()
    pdf.set_font("Arial", "B", 8)
    pdf.cell(sum(col_widths[:-2]), 8, "", border=1)
    pdf.cell(col_widths[-2], 8, "Total", border=1, align="C")
    pdf.cell(col_widths[-1], 8, f"{order_data['total_amount']}/-", border=1, align="C")
    pdf.ln(15)
    if pdf.get_y() > 195:
        pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.write(5, "This sanction has been accorded in exercise of the power delegated by the finance Department, ")
    pdf.write(5, "Govt. of NCT of Delhi and in the consultation with the accounts functionary of the Department. ")
    pdf.write(5, "The expenditure would be debatable to major head ")
    pdf.set_font("Arial", "B", 10)
    pdf.write(5, "2202 02 109 8700 02 - ASF Wages")
    pdf.set_font("Arial", "", 10)
    pdf.write(5, " for financial year 2024-2025 under grant No.6")
    pdf.ln(20)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Principal", align="R", ln=True)
    pdf.cell(0, 5, "(Anuradha)", align="R", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", size=10)
    pdf.cell(0, 5, "Ref. No. GGSSS/SP/2025/", ln=False)
    pdf.set_x(170)
    pdf.cell(0, 5, "Dated: __________", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, "Copy to:-", ln=True)
    pdf.cell(0, 5, "1. PAO VIII, GTB Hospital Complex Dilshad Garden Delhi-93.", ln=True)
    pdf.cell(0, 5, "2. DDO GGSSS SABHAPUR", ln=True)
    pdf.cell(0, 5, "3. Guard File.", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Principal", align="R", ln=True)
    pdf.cell(0, 5, "(Anuradha)", align="R", ln=True)
    pdf.output(file_path)

@app.route('/')
def home():
    return redirect(url_for('issue_sanction'))

@app.route('/issue', methods=['GET', 'POST'])
def issue_sanction():
    conn = sqlite3.connect("sanctions.db")
    c = conn.cursor()
    c.execute("SELECT app_id, name, designation, nic_pin FROM teachers")
    all_teachers = [{'app_id': row[0], 'name': row[1], 'designation': row[2], 'nic_pin': row[3]} for row in c.fetchall()]
    conn.close()

    if request.method == 'POST':
        month = request.form['month']
        issued_date = datetime.now().strftime("%Y-%m-%d")
        year = issued_date.split('-')[0]
        selected_teachers = request.form.getlist('selected_teachers')
        teacher_days = {key.split('_')[1]: int(value) for key, value in request.form.items() if key.startswith('days_')}

        teachers = []
        total_amount = 0
        for app_id in selected_teachers:
            teacher = next(t for t in all_teachers if t['app_id'] == app_id)
            days = teacher_days.get(teacher['app_id'], 0)
            amount = calculate_payment(teacher['designation'], days)
            total_amount += amount
            teachers.append({
                'app_id': teacher['app_id'],
                'name': teacher['name'],
                'designation': teacher['designation'],
                'nic_pin': teacher['nic_pin'],
                'days': days,
                'amount': amount
            })

        total_amount_str = format_indian_number(total_amount)
        total_amount_words = num2words(total_amount, lang='en_IN').replace(',', '').title() + " Only"

        conn = sqlite3.connect("sanctions.db")
        c = conn.cursor()
        c.execute("INSERT INTO sanctions (total_amount, month, issued_date, file_path) VALUES (?, ?, ?, ?)",
                  (total_amount_str, month, issued_date, ""))
        order_id = c.lastrowid

        for teacher in teachers:
            c.execute("INSERT INTO sanction_teachers (sanction_id, app_id, days) VALUES (?, ?, ?)",
                      (order_id, teacher['app_id'], teacher['days']))
        conn.commit()
        conn.close()

        file_path = f"sanctions/hos_{month}_{year}.pdf"
        order_data = {
            "total_amount": total_amount_str,
            "total_amount_words": total_amount_words,
            "month": month,
            "date": issued_date,
            "teachers": teachers
        }
        generate_pdf(order_data, file_path)

        conn = sqlite3.connect("sanctions.db")
        c = conn.cursor()
        c.execute("UPDATE sanctions SET file_path = ? WHERE id = ?", (file_path, order_id))
        conn.commit()
        conn.close()

        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"hos_{month}_{year}.pdf",
            mimetype='application/pdf'
        )
    
    return render_template('issue_form.html', teachers=all_teachers)

@app.route('/sanctions')
def list_sanctions():
    conn = sqlite3.connect("sanctions.db")
    c = conn.cursor()
    c.execute("SELECT id, total_amount, month, issued_date, file_path FROM sanctions ORDER BY issued_date DESC")
    sanctions = [{'id': row[0], 'total_amount': row[1], 'month': row[2], 'issued_date': row[3], 'file_path': row[4]} for row in c.fetchall()]
    conn.close()
    return render_template('sanctions_list.html', sanctions=sanctions)

@app.route('/edit_sanction/<int:order_id>', methods=['GET', 'POST'])
def edit_sanction(order_id):
    conn = sqlite3.connect("sanctions.db")
    c = conn.cursor()
    
    c.execute("SELECT month, issued_date, file_path FROM sanctions WHERE id = ?", (order_id,))
    sanction = c.fetchone()
    if not sanction:
        return "Sanction not found", 404
    month, issued_date, file_path = sanction
    
    c.execute("""
        SELECT st.app_id, t.name, t.designation, t.nic_pin, st.days
        FROM sanction_teachers st
        JOIN teachers t ON st.app_id = t.app_id
        WHERE st.sanction_id = ?
    """, (order_id,))
    teachers = [{'app_id': row[0], 'name': row[1], 'designation': row[2], 'nic_pin': row[3], 'days': row[4]} for row in c.fetchall()]
    conn.close()

    if request.method == 'POST':
        teacher_days = {key.split('_')[1]: int(value) for key, value in request.form.items() if key.startswith('days_')}

        total_amount = 0
        updated_teachers = []
        conn = sqlite3.connect("sanctions.db")
        c = conn.cursor()
        for teacher in teachers:
            new_days = teacher_days.get(teacher['app_id'], teacher['days'])
            amount = calculate_payment(teacher['designation'], new_days)
            total_amount += amount
            updated_teachers.append({
                'app_id': teacher['app_id'],
                'name': teacher['name'],
                'designation': teacher['designation'],
                'nic_pin': teacher['nic_pin'],
                'days': new_days,
                'amount': amount
            })
            c.execute("UPDATE sanction_teachers SET days = ? WHERE sanction_id = ? AND app_id = ?",
                      (new_days, order_id, teacher['app_id']))

        total_amount_str = format_indian_number(total_amount)
        total_amount_words = num2words(total_amount, lang='en_IN').replace(',', '').title() + " Only"
        c.execute("UPDATE sanctions SET total_amount = ? WHERE id = ?", (total_amount_str, order_id))
        conn.commit()
        conn.close()

        year = issued_date.split('-')[0]
        file_path = f"sanctions/hos_{month}_{year}.pdf"
        order_data = {
            "total_amount": total_amount_str,
            "total_amount_words": total_amount_words,
            "month": month,
            "date": issued_date,
            "teachers": updated_teachers
        }
        generate_pdf(order_data, file_path)

        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"hos_{month}_{year}.pdf",
            mimetype='application/pdf'
        )

    return render_template('edit_sanction.html', order_id=order_id, month=month, teachers=teachers)

@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    app_id = request.form['app_id']
    name = request.form['name']
    designation = request.form['designation']
    nic_pin = request.form['nic_pin']
    conn = sqlite3.connect("sanctions.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO teachers (app_id, name, designation, nic_pin) VALUES (?, ?, ?, ?)",
              (app_id, name, designation, nic_pin))
    conn.commit()
    conn.close()
    return redirect(url_for('issue_sanction'))

@app.route('/remove_teacher/<app_id>', methods=['POST'])
def remove_teacher(app_id):
    conn = sqlite3.connect("sanctions.db")
    c = conn.cursor()
    c.execute("DELETE FROM teachers WHERE app_id = ?", (app_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('issue_sanction'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)