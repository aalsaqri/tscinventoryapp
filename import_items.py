import csv
import io
from flask import flash, redirect, url_for

def import_items(form):
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

            # Check if the item already exists
            existing_item = Item.query.filter_by(name=name).first()
            if existing_item:
                existing_item.par = par
                flash(f"Updated PAR for '{name}' to {par}.", 'info')
            else:
                # Create a new item with the correct 'par' field
                new_item = Item(name=name, par=par)
                db.session.add(new_item)
                flash(f"Added new item: {name} with PAR {par}.", 'success')

        # Commit changes to the database
        db.session.commit()
        flash('Items imported successfully!', 'success')
