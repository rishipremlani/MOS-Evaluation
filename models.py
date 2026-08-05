from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# -----------------------------
# Participant Table
# -----------------------------
class Participant(db.Model):

    __tablename__ = "participants"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=True)

    age = db.Column(db.Integer)

    profession = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -----------------------------
# Image Table
# -----------------------------
class Image(db.Model):

    __tablename__ = "images"

    id = db.Column(db.Integer, primary_key=True)

    image_name = db.Column(db.String(100), unique=True)

    ours = db.Column(db.String(200))

    method1 = db.Column(db.String(200))

    method2 = db.Column(db.String(200))


# -----------------------------
# Rating Table
# -----------------------------
class Rating(db.Model):

    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)

    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("participants.id"),
        nullable=False
    )

    image_id = db.Column(db.Integer, nullable=False)

    method = db.Column(db.String(50), nullable=False)

    shown_as = db.Column(db.String(1), nullable=False)

    score = db.Column(db.Integer, nullable=False)

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )