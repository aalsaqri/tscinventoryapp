# forms.py

from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired, ValidationError

class UploadCSVForm(FlaskForm):
    file = FileField(
        'CSV File',
        validators=[
            DataRequired(message="Please upload a CSV file."),
        ]
    )
    submit = SubmitField('Upload')

    # Custom validator to validate filename
    def validate_file(form, field):
        if not field.data.filename.endswith('.csv'):
            raise ValidationError("Only CSV files are allowed.")
