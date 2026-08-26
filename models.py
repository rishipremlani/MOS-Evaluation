from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# -----------------------------
# Participant Table
# -----------------------------
class Participant(db.Model):

    __tablename__ = "participants"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=True
    )

    age = db.Column(
        db.Integer
    )

    profession = db.Column(
        db.String(100)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# -----------------------------
# Rating Table
# -----------------------------
class Rating(db.Model):

    __tablename__ = "ratings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("participants.id"),
        nullable=False
    )

    # Evaluation image number: 1–25
    image_id = db.Column(
        db.Integer,
        nullable=False
    )

    # Actual SR method
    # Ours / MDASR / UnCapSTSR / TUDASR
    method = db.Column(
        db.String(50),
        nullable=False
    )

    # Randomized blind label
    # A / B / C / D
    shown_as = db.Column(
        db.String(1),
        nullable=False
    )

    # MOS score: 1–5
    score = db.Column(
        db.Integer,
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )