from flask import Flask, render_template, request, redirect, url_for, session
from config import Config
import os
import random
import csv
from flask import Response
from models import db, Participant, Rating
from flask import jsonify

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["POST"])
def register():

    participant = Participant(
        name=request.form.get("name"),
        age=int(request.form.get("age")),
        profession=request.form.get("profession")
    )

    db.session.add(participant)
    db.session.commit()

    session["participant_id"] = participant.id
    session["current_image"] = 1

    return redirect(url_for("instructions"))


@app.route("/instructions")
def instructions():

    if "participant_id" not in session:
        return redirect(url_for("home"))

    return render_template("instructions.html")


@app.route("/evaluate")
def evaluate():

    if "participant_id" not in session:
        return redirect(url_for("home"))
    image_no = session.get("current_image", 1)

    # All available methods
    methods = [
        ("Ours", f"images/img{image_no:02d}/ours.png"),
        ("MDASR", f"images/img{image_no:02d}/mdasr.png"),
        ("UnCapSTSR", f"images/img{image_no:02d}/uncapstsr.png")
    ]

    # Create dictionary in session if not present
    if "image_mappings" not in session:
        session["image_mappings"] = {}

    mappings = session["image_mappings"]

    image_key = str(image_no)

    # First visit to this image
    if image_key not in mappings:

        shuffled = methods.copy()
        random.shuffle(shuffled)

        mappings[image_key] = [
            shuffled[0][0],
            shuffled[1][0],
            shuffled[2][0]
        ]

        session["image_mappings"] = mappings

    # Read stored order
    stored_order = mappings[image_key]

    ordered_methods = []

    for method_name in stored_order:
        for m in methods:
            if m[0] == method_name:
                ordered_methods.append(m)

    session["current_mapping"] = {
        "A": ordered_methods[0][0],
        "B": ordered_methods[1][0],
        "C": ordered_methods[2][0]
    }

    lr_image = f"images/img{image_no:02d}/lr.png"

    return render_template(
        "evaluate.html",
        image_no=image_no,
        lr_image=lr_image,
        methods=ordered_methods
    )

@app.route("/save_rating", methods=["POST"])
def save_rating():

    if "participant_id" not in session:
        return jsonify({"status": "error"}), 401

    data = request.get_json()

    participant = session["participant_id"]
    image_id = data["image"]

    # Already rated?
    existing = Rating.query.filter_by(
        participant_id=participant,
        image_id=image_id
    ).first()

    if existing:
        return jsonify({"status": "already_saved"})

    mapping = session["current_mapping"]
    ratings = data["ratings"]

    for letter in ["A", "B", "C"]:

        rating = Rating(
            participant_id=participant,
            image_id=image_id,
            shown_as=letter,
            method=mapping[letter],
            score=ratings[letter]
        )

        db.session.add(rating)

    db.session.commit()

    return jsonify({"status": "success"})

@app.route("/next_image")
def next_image():

    if "participant_id" not in session:
        return redirect(url_for("home"))

    current = session.get("current_image", 1)

    if current < 25:
        session["current_image"] = current + 1
        return redirect(url_for("evaluate"))

    return redirect(url_for("finish"))
@app.route("/finish")
def finish():

    session.clear()

    return render_template("finish.html")

@app.route("/export")
def export():

    rows = Rating.query.all()

    def generate():

        data = csv.writer(Echo())

        yield data.writerow([
            "Participant",
            "Image",
            "Method",
            "Shown_As",
            "Score",
            "Timestamp"
        ])

        for r in rows:

            yield data.writerow([
                r.participant_id,
                r.image_id,
                r.method,
                r.shown_as,
                r.score,
                r.timestamp
            ])

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=mos_results.csv"
        }
    )


class Echo:
    def write(self, value):
        return value

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

