import os
import io
import csv
import pytz
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, Item, StockRecord, User  # Ensure this is imported correctly
from forms import UploadCSVForm

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize database and migration tools
db.init_app(app)
migrate = Migrate(app, db)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define local timezone
LOCAL_TZ = pytz.timezone('America/New_York')

# Create 'downloads' directory if it doesn't exist
if not os.path.exists('downloads'):
    os.mkdir('downloads')

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes

@app.route('/', methods=['GET', 'POST'])
def index():
    items = Item.query.all()
    if request.method == 'POST':
        try:
            submission_data = []
            for item in items:
                stock_input = request.form.get(item.name)
                if stock_input is not None:
                    stock = int(stock_input)
                    if stock < 0:
                        raise ValueError(f"Negative stock for {item.name}.")
                    stock_record = StockRecord(item_id=item.id, current_stock=stock)
                    db.session.add(stock_record)
                    submission_data.append([item.name, stock, item.par])
            db.session.commit()
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            csv_filename = f"{timestamp}.csv"
            csv_file_path = os.path.join('downloads', csv_filename)
            with open(csv_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Item Name', 'Stock Quantity', 'PAR'])
                writer.writerows(submission_data)
            flash('Stock levels submitted and CSV generated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
            db.session.rollback()
    return render_template('index.html', items=items)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_items():
    form = UploadCSVForm()
    if form.validate_on_submit():
        file = form.file.data
        stream = io.StringIO(file.stream.read().decode('UTF-8'))
        reader = csv.DictReader(stream)
        if 'name' not in reader.fieldnames or 'par' not in reader.fieldnames:
            flash('CSV must contain "name" and "par" headers.', 'danger')
            return redirect(url_for('import_items'))
        for row in reader:
            name = row.get('name')
            par = row.get('par')
            if not name or not par:
                flash(f"Skipping row with missing data: {row}", 'warning')
                continue
            try:
                par = int(par)
            except ValueError:
                flash(f"Invalid PAR value for {name}: {par}", 'warning')
                continue
            existing_item = Item.query.filter_by(name=name).first()
            if existing_item:
                existing_item.par = par
                flash(f"Updated PAR for '{name}' to {par}.", 'info')
            else:
                new_item = Item(name=name, par=par)
                db.session.add(new_item)
                flash(f"Added new item: {name} with PAR {par}.", 'success')
        db.session.commit()
        flash('Items imported successfully!', 'success')
    return render_template('import.html', form=form)

@app.route('/downloads', methods=['GET'])
@login_required
def downloads():
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    files = sorted(
        [f for f in os.listdir(downloads_dir) if f.endswith('.csv')],
        key=lambda x: os.path.getmtime(os.path.join(downloads_dir, x)),
        reverse=True
    )
    return render_template('downloads.html', files=files)

@app.route('/download/<filename>', methods=['GET'])
@login_required
def download_file(filename):
    file_path = os.path.join(os.getcwd(), 'downloads', filename)
    if not os.path.exists(file_path):
        flash(f"File '{filename}' not found.", 'danger')
        return redirect(url_for('downloads'))
    return send_file(file_path, as_attachment=True)

@app.route('/history', methods=['GET'])
@login_required
def history():
    stock_records = StockRecord.query.order_by(StockRecord.timestamp.desc()).all()
    all_dates = sorted({
        record.timestamp.replace(tzinfo=timezone.utc)
        .astimezone(LOCAL_TZ)
        .strftime('%Y-%m-%d') for record in stock_records
    }, reverse=True)[:5]
    items_with_submissions = []
    items = Item.query.all()
    for item in items:
        submissions_by_date = {
            record.timestamp.replace(tzinfo=timezone.utc)
            .astimezone(LOCAL_TZ)
            .strftime('%Y-%m-%d'): record.current_stock
            for record in item.stock_records
        }
        items_with_submissions.append({
            'name': item.name,
            'par': item.par,
            'submissions_by_date': submissions_by_date,
        })
    return render_template(
        'history.html',
        items_with_submissions=items_with_submissions,
        unique_dates=all_dates
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
