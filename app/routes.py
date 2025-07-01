from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
import os, json, qrcode, pyotp, io, shutil
from datetime import datetime
from PIL import Image
from fpdf import FPDF
from .utils import save_data, load_data, allowed_file

main = Blueprint('main', __name__)
DATA_FILE = 'app/data.json'
USER_FILE = 'app/users.json'
LABEL_FOLDER = os.path.join(os.path.dirname(__file__), 'labels')
os.makedirs(LABEL_FOLDER, exist_ok=True)

bins = load_data(DATA_FILE)

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=2)

users = load_users()

@main.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin = request.form.get('pin')
        totp_code = request.form.get('totp')
        user = users.get(pin)
        if user and pyotp.TOTP(user['secret']).verify(totp_code):
            session.permanent = True
            session['user'] = pin
            return redirect(url_for('main.index'))
        return render_template('login.html', error="❌ Invalid credentials. Try again.")
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('main.login'))

@main.route('/generate_credentials', methods=['POST'])
def generate_credentials():
    pin = str(len(users) + 1).zfill(4)
    secret = pyotp.random_base32()
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=pin, issuer_name="BinDex")
    qr = qrcode.make(totp_uri)
    qr_file = f"{pin}.png"
    qr_path = os.path.join('app/static/qrcodes', qr_file)
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
    qr.save(qr_path)
    users[pin] = {'secret': secret}
    save_users(users)
    creds = {'pin': pin, 'secret': secret, 'qr_image': qr_file}
    return render_template('login.html', creds=creds)

@main.route('/dashboard')
def index():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user_id = session['user']
    user_bins = bins.get(user_id, {})
    query = request.args.get('q', '').lower()
    result_text = ""
    filtered = {}

    if query:
        for k, v in user_bins.items():
            if query in k.lower() or any(query in item['name'].lower() for item in v['items']):
                filtered[k] = v
        result_text = f"Query '{query}' found in: " + ", ".join(filtered.keys()) if filtered else f"Query '{query}' not found."
    else:
        filtered = user_bins

    icons = [f for f in os.listdir('app/static/prefix_images') if f.endswith('.png')]
    return render_template('index.html', bins=filtered, query=query, icons=icons, result=result_text)

@main.route('/add_bin', methods=['POST'])
def add_bin():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    prefix = request.form.get('prefix', 'BN').upper()
    location = request.form.get('location', '').strip()
    file = request.files.get('prefix_image')
    selected_icon = request.form.get('selected_icon', '')
    user_id = session['user']
    user_bins = bins.setdefault(user_id, {})
    bin_id = f"{prefix}{len(user_bins)+1:02d} {len(user_bins)+1}"
    icon_path = f'app/static/prefix_images/{prefix.lower()}.png'

    if file and allowed_file(file.filename):
        file.save(icon_path)
    elif selected_icon:
        src = os.path.join('app/static/prefix_images', selected_icon)
        if os.path.exists(src):
            shutil.copy(src, icon_path)
    elif not os.path.exists(icon_path):
        Image.new('RGB', (128, 128), (73, 109, 137)).save(icon_path)

    user_bins[bin_id] = {
        'items': [],
        'created_at': datetime.utcnow().isoformat(),
        'last_accessed': None,
        'times_accessed': 0,
        'prefix': prefix,
        'location': location
    }
    save_data(bins, DATA_FILE)
    return redirect(url_for('main.index'))

@main.route('/qr/<bin_id>')
def qr(bin_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user_id = session['user']
    user_bins = bins.get(user_id, {})
    if bin_id in user_bins:
        user_bins[bin_id]['last_accessed'] = datetime.utcnow().isoformat()
        user_bins[bin_id]['times_accessed'] += 1
        save_data(bins, DATA_FILE)

    img = qrcode.make(bin_id)
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@main.route('/print_qr/<bin_id>')
def print_qr(bin_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    try:
        qr = qrcode.make(bin_id)
        qr_img_path = os.path.join(LABEL_FOLDER, f"{bin_id.replace(' ', '_')}_qr.png")
        qr.save(qr_img_path)

        pdf = FPDF("P", "in", "Letter")
        pdf.add_page()
        for y in [0.5, 5.75]:
            pdf.set_y(y)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 0.4, f"Bin: {bin_id}", ln=True, align="C")
            pdf.image(qr_img_path, x=3.375, y=y + 0.5, w=1.75, h=1.75)

        pdf_file = os.path.join(LABEL_FOLDER, f"{bin_id.replace(' ', '_')}.pdf")
        pdf.output(pdf_file)
        os.remove(qr_img_path)
        return send_file(pdf_file, as_attachment=True)
    except Exception as e:
        return f"PDF generation failed: {e}"

@main.route('/add_item/<bin_id>', methods=['POST'])
def add_item(bin_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user_id = session['user']
    name = request.form['item']
    upc = request.form['upc']
    if not name:
        return redirect(url_for('main.index'))
    bins[user_id][bin_id]['items'].append({"name": name, "upc": upc})
    save_data(bins, DATA_FILE)
    return redirect(url_for('main.index'))

@main.route('/delete_item/<bin_id>/<int:item_index>', methods=['POST'])
def delete_item(bin_id, item_index):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user_id = session['user']
    try:
        bins[user_id][bin_id]['items'].pop(item_index)
        save_data(bins, DATA_FILE)
    except Exception as e:
        print(f"Delete error: {e}")
    return redirect(url_for('main.index'))
