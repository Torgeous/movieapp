from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from data import *
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = app_secret_key
 
# BOOTSTRAP SETUP
Bootstrap(app)

# DATABASE SETUP
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///best-10-movies-store.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# API REQUEST LINKS
TMDM_API_KEY = api_secret_key
TMDM_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDM_MOVIE_DB = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.String(250), nullable=False)
    review = db.Column(db.Integer, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class EditingForm(FlaskForm):
    rating = StringField(label="Your Rating Out of 10. eg 6.5", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


def get_movie(key):
    movie_location = Movie.query.get(key)
    return movie_location


def get_id():
    return request.args.get("id")


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    ranked_movie = []
    for i in range(len(all_movies)):
        # all_movies[i].ranking = len(all_movies) - i
        ranked_movie.append(all_movies[i])
        db.session.commit()
        print(all_movies[i].ranking)
    print(ranked_movie)
    return render_template("index.html", movies=ranked_movie)


@app.route("/add", methods=["GET", "POST"])
def add():
    finding_form = FindMovieForm()
    if finding_form.validate_on_submit():
        response = requests.get(TMDM_SEARCH_URL, params={"api_key": TMDM_API_KEY,
                                                         "query": finding_form.title.data})
        tmdm_web_data = response.json()

        return render_template("select.html", data=tmdm_web_data['results'])

    return render_template("add.html", form=finding_form)


@app.route("/find")
def find():
    movie_id = get_id()
    movie_year = request.args.get("year")
    detailed_response = requests.get(f"{TMDM_MOVIE_DB}/{movie_id}", params={"api_key": TMDM_API_KEY})
    d_json = detailed_response.json()
    img_path = None

    if d_json["poster_path"] is not None:
        img_path = f"{MOVIE_DB_IMAGE_URL}/{d_json['poster_path']}"

    new_movie = Movie(
        title=d_json['original_title'],
        year=movie_year.split("-")[0],
        description=d_json['overview'],
        rating=0,
        ranking=0,
        review=0,
        img_url=img_path
    )

    print(new_movie.title)
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))




@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditingForm()
    movie_id = request.args.get("id")
    movie = get_movie(movie_id)

    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("edit.html", form=form, movie=movie)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = get_movie(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
