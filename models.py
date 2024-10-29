from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    process_number = db.Column(db.String, nullable=True)
    date = db.Column(db.String, nullable=False)  # Agora como String
    time = db.Column(db.String, nullable=False)   # Agora como String
    task = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String, nullable=True)
    notes = db.Column(db.String, nullable=True)
    notified = db.Column(db.Boolean, default=False)
    situation = db.Column(db.Integer, default=0)

