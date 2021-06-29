from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
movie_api_key = os.environ["MOVIE_API_KEY"]
Bootstrap(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///best-movies.db"
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=True)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=True)


class UpdateForm(FlaskForm):
    rating = StringField(
        label="Your rating out of 10 e.g. 7.5",
        validators=[DataRequired(), Length(max=3)]
    )
    review = StringField(
        label="Your review",
        validators=[DataRequired()]
    )
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    movie_title = StringField(
        label="Movie Title",
        validators=[DataRequired()],
    )
    submit = SubmitField(label="Add")

db.create_all()

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, "
#                 "pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, "
#                 "Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg",
# )
#
# db.session.add(new_movie)
# db.session.commit()


@app.route("/")
def home():
    all_movies = db.session.query(Movie).order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
        print(len(all_movies) - i)
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit/<movie_id>", methods=["GET", "POST"])
def edit(movie_id):
    form = UpdateForm()
    movie_to_update = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_to_update.rating = request.form.get("rating")
        movie_to_update.review = request.form.get("review")
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie_title=movie_to_update.title)


@app.route("/delete/<movie_id>")
def delete(movie_id):
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        movie_to_add = request.form.get("movie_title")

        headers = {
            "Authorization": f"Bearer {movie_api_key}",
        }

        parameters = {
            "query": movie_to_add
        }

        response = requests.get(url="https://api.themoviedb.org/3/search/movie", params=parameters, headers=headers)
        response.raise_for_status()
        movies_data = response.json()
        return render_template("select.html", movies_data=movies_data)

    return render_template("add.html", form=form)


@app.route("/select/<movie_api_id>")
def select(movie_api_id):

    headers = {
        "Authorization": f"Bearer {movie_api_key}",
    }

    response = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_api_id}", headers=headers)
    response.raise_for_status()
    movie_data = response.json()

    movie_to_add = Movie(
        title=movie_data["original_title"],
        year=int(movie_data["release_date"][:4]),
        description=movie_data["overview"],
        rating=0,
        ranking=0,
        review="",
        img_url=f"https://image.tmdb.org/t/p/w500/{movie_data['poster_path']}"
    )
    db.session.add(movie_to_add)
    db.session.commit()
    return redirect(url_for("edit", movie_id=movie_to_add.id))


if __name__ == '__main__':
    app.run(debug=True)
