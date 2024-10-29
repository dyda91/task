from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TimeField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional

class EventForm(FlaskForm):
    task = SelectField('Tarefa', choices=[
        ('0', 'Audiência'), 
        ('1', 'Recurso'), 
        ('2', 'Emendas')
    ], validators=[DataRequired()])
    
    name = StringField('Nome', validators=[DataRequired()])
    process_number = StringField('Número do Processo', validators=[Optional()])
    date = DateField('Data', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Hora', format='%H:%M', validators=[DataRequired()])
    link = StringField('Link', validators=[Optional()])
    notes = TextAreaField('Notas', validators=[Optional()])
    submit = SubmitField('Adicionar Evento')

