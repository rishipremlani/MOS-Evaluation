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
with app.app_context():
    db.create_all()

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

    # Four available methods
    methods = [
        ("Ours", f"images/img{image_no:02d}/ours.png"),
        ("MDASR", f"images/img{image_no:02d}/mdasr.png"),
        ("UnCapSTSR", f"images/img{image_no:02d}/uncapstsr.png"),
        ("TUDASR", f"images/img{image_no:02d}/tudasr.png")
    ]

    # Create image mappings dictionary if it doesn't exist
    if "image_mappings" not in session:
        session["image_mappings"] = {}

    mappings = session["image_mappings"]

    image_key = str(image_no)

    # Create a new random order if:
    # 1. this image has never been visited, OR
    # 2. an old 3-model mapping exists
    if image_key not in mappings or len(mappings[image_key]) != 4:

        shuffled = methods.copy()
        random.shuffle(shuffled)

        mappings[image_key] = [
            shuffled[0][0],
            shuffled[1][0],
            shuffled[2][0],
            shuffled[3][0]
        ]

        session["image_mappings"] = mappings

    # Read stored random order
    stored_order = mappings[image_key]

    ordered_methods = []

    for method_name in stored_order:

        for method in methods:

            if method[0] == method_name:
                ordered_methods.append(method)
                break

    # Safety check
    if len(ordered_methods) != 4:
        return "Error: Could not construct all four image methods.", 500

    # Store A/B/C/D mapping
    session["current_mapping"] = {
        "A": ordered_methods[0][0],
        "B": ordered_methods[1][0],
        "C": ordered_methods[2][0],
        "D": ordered_methods[3][0]
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
        return jsonify({
            "status": "error",
            "message": "Participant session missing"
        }), 401

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data received"
            }), 400

        participant_id = session["participant_id"]

        image_id = int(data["image"])

        ratings = data["ratings"]

        required_letters = ["A", "B", "C", "D"]

        for letter in required_letters:

            if letter not in ratings:
                return jsonify({
                    "status": "error",
                    "message": f"Missing rating for {letter}"
                }), 400

            score = int(ratings[letter])

            if score < 1 or score > 5:
                return jsonify({
                    "status": "error",
                    "message": f"Invalid score for {letter}"
                }), 400


        # ==========================================
        # PREVENT DUPLICATE SUBMISSION
        # ==========================================

        existing = Rating.query.filter_by(
            participant_id=participant_id,
            image_id=image_id
        ).first()

        if existing:

            return jsonify({
                "status": "already_saved"
            })


        # ==========================================
        # CURRENT RANDOM A/B/C/D MAPPING
        # ==========================================

        mapping = session.get("current_mapping")

        if not mapping:

            return jsonify({
                "status": "error",
                "message": "Image mapping missing from session"
            }), 400


        # ==========================================
        # SAVE FOUR RATINGS
        # ==========================================

        for letter in required_letters:

            rating = Rating(
                participant_id=participant_id,
                image_id=image_id,
                shown_as=letter,
                method=mapping[letter],
                score=int(ratings[letter])
            )

            db.session.add(rating)


        db.session.commit()


        # ==========================================
        # VERIFY DATABASE WRITE
        # ==========================================

        saved_count = Rating.query.filter_by(
            participant_id=participant_id,
            image_id=image_id
        ).count()


        if saved_count != 4:

            db.session.rollback()

            return jsonify({
                "status": "error",
                "message": "Ratings were not saved correctly"
            }), 500


        return jsonify({
            "status": "success"
        })


    except Exception as error:

        db.session.rollback()

        app.logger.exception(
            "Error while saving ratings"
        )

        return jsonify({
            "status": "error",
            "message": "Database error while saving ratings"
        }), 500

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

    rows = (
        db.session.query(Rating, Participant)
        .join(
            Participant,
            Participant.id == Rating.participant_id
        )
        .order_by(
            Rating.image_id,
            Rating.participant_id,
            Rating.shown_as
        )
        .all()
    )

    def generate():

        data = csv.writer(Echo())

        # ==========================================
        # RAW RATINGS
        # ==========================================

        yield data.writerow([
            "Participant_ID",
            "Participant_Name",
            "Participant_Age",
            "Participant_Profession",
            "Image",
            "Method",
            "Shown_As",
            "Score",
            "Timestamp"
        ])

        for rating, participant in rows:

            yield data.writerow([
                participant.id,
                participant.name or "",
                participant.age if participant.age is not None else "",
                participant.profession or "",
                rating.image_id,
                rating.method,
                rating.shown_as,
                rating.score,
                rating.timestamp
            ])


        # ==========================================
        # MODEL AVERAGE MOS
        # ==========================================

        yield data.writerow([])
        yield data.writerow([])

        yield data.writerow([
            "MODEL AVERAGE MOS"
        ])

        yield data.writerow([
            "Method",
            "Average MOS",
            "Number of Ratings"
        ])

        methods = [
            "Ours",
            "MDASR",
            "UnCapSTSR",
            "TUDASR"
        ]

        for method in methods:

            method_scores = [
                rating.score
                for rating, participant in rows
                if rating.method == method
            ]

            if method_scores:

                average = (
                    sum(method_scores)
                    / len(method_scores)
                )

                yield data.writerow([
                    method,
                    round(average, 3),
                    len(method_scores)
                ])

            else:

                yield data.writerow([
                    method,
                    "",
                    0
                ])


    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=mos_results.csv"
        }
    )

# @app.route("/reset_database")
# def reset_database():

#     # DELETE ALL RATINGS
#     Rating.query.delete()

#     # DELETE ALL PARTICIPANTS
#     Participant.query.delete()

#     db.session.commit()

#     return "DATABASE RESET SUCCESSFULLY"

class Echo:
    def write(self, value):
        return value

if __name__ == "__main__":


    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5001))
    )
