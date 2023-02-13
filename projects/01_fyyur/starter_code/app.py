#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import db, Artist, Venue, Show
import sys
import collections
collections.Callable = collections.abc.Callable
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  venuesByCityAndState = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()  
  
  for venue in venuesByCityAndState:
    venuesResult = Venue.query.filter_by(city=venue.city, state=venue.state).all()   
    innerData = []
    for venue in venuesResult:
        resultObject = {}
        resultObject['id'] = venue.id
        resultObject['name'] = venue.name
        resultObject['num_upcoming_shows'] = Show.query.filter(Show.venue_id==venue.id, Show.start_time>datetime.now()).count()
        innerData.append(resultObject)

    data.append({
      "city": venue.city,
      "state": venue.state,
      "venues": innerData
      })
  
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_phrase = request.form['search_term']
  venuesResult = Venue.query.filter(
        Venue.name.ilike('%{}%'.format(search_phrase))).all()

  data = []
  for venue in venuesResult:
        resultObject = {}
        resultObject['id'] = venue.id
        resultObject['name'] = venue.name
        resultObject['num_upcoming_shows'] = Show.query.filter(Show.venue_id==venue.id, Show.start_time>datetime.now()).count()
        data.append(resultObject)

  response = {}
  response['count'] = len(venuesResult)
  response['data'] = data

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venueResultById = Venue.query.get(venue_id)
  
  past_show_data=[]
  future_show_data =[]
  future_shows = Show.query.filter_by(venue_id=venue_id).filter(Show.start_time > datetime.now()).all()
  past_shows = Show.query.filter_by(venue_id=venue_id).filter(Show.start_time <= datetime.now()).all()
  for show in future_shows:
    artist_id = show.artist_id
    body={}
    artist = Artist.query.get(artist_id)
    body['artist_id']=artist.id
    body['artist_name']=artist.name
    body['artist_image_link']=artist.image_link
    body['start_time']=str(show.start_time)
    future_show_data.append(body)   
  for show in past_shows:
    artist_id = show.artist_id
    body={}
    artist = Artist.query.get(artist_id)
    body['artist_id']=artist.id
    body['artist_name']=artist.name
    body['artist_image_link']=artist.image_link
    body['start_time']=str(show.start_time)
    past_show_data.append(body)   
  print(venueResultById.genres)
  convertedgenres = venueResultById.genres.replace('{', '').replace('}', '').split(',')
  print(convertedgenres)
  data =({
    "id": venue_id,
    "name": venueResultById.name, 
    "genres": convertedgenres,
    "address":venueResultById.address ,
    "city": venueResultById.city,
    "state": venueResultById.state,
    "phone": venueResultById.phone,
    "website": venueResultById.website_link,
    "facebook_link": venueResultById.facebook_link,
    "seeking_talent": venueResultById.seeking_talent,
    "seeking_description": venueResultById.seeking_description,
    "image_link": venueResultById.image_link,
    "past_shows":past_show_data,
    "upcoming_shows": future_show_data,
    "past_shows_count": len(past_show_data),
    "upcoming_shows_count":len(future_show_data) ,

  })
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        form = request.form
        converted_seeking_talent=False
        print("entry")
        if form.get("seeking_talent", False)=='y':
          print("if loop")
          converted_seeking_talent=True
        else :
          print("else  loop")
          converted_seeking_talent=False
        print(converted_seeking_talent)
        venue = Venue(name= form['name'],
        city=form['city'],
        state=form['state'],
        address=form['address'],
        phone=form['phone'],
        genres= form.getlist('genres'),
        image_link=form['image_link'],
        facebook_link=form['facebook_link'],
        website_link=form['website_link'],
        seeking_talent=converted_seeking_talent,
        seeking_description=form['seeking_description'])
        db.session.add(venue)
        db.session.commit()
      
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
       flash('An error occurred. Venue ' + form['name'] + ' could not be listed.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!') 
        return render_template('pages/home.html')
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error=False
  name=''
  try:
    venueResultById = Venue.query.get(venue_id)
    name = venueResultById.name
    db.session.delete(venueResultById)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    if error:
      flash('An error occurred. Venue ' + name + ' could not be deleted.')
    else:
      flash('Venue ' + name + ' was successfully deleted.')
  return render_template('pages/home.html')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
 

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data=[]
  for artist in artists:
    body={}
    body['id']=artist.id
    body['name']=artist.name
    data.append(body)
 
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_phrase = request.form['search_term']
  artistResults = Artist.query.filter(
        Artist.name.ilike('%{}%'.format(search_phrase))).all()

  data = []
  for artist in artistResults:
        resultObject = {}
        resultObject['id'] = artist.id
        resultObject['name'] = artist.name
        resultObject['num_upcoming_shows'] = Show.query.filter(Show.artist_id==artist.id, Show.start_time>datetime.now()).count()
        data.append(resultObject)

  response = {}
  response['count'] = len(artistResults)
  response['data'] = data
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artistResultById = Artist.query.get(artist_id)
  
  past_show_data=[]
  future_show_data =[]
  future_shows = Show.query.filter_by(artist_id=artist_id).filter(Show.start_time > datetime.now()).all()
  past_shows = Show.query.filter_by(artist_id=artist_id).filter(Show.start_time <= datetime.now()).all()
  for show in future_shows:
    venue_id = show.venue_id
    body={}
    venue = Venue.query.get(venue_id)
    body['venue_id']=venue.id
    body['venue_name']=venue.name
    body['venue_image_link']=venue.image_link
    body['start_time']=str(show.start_time)
    future_show_data.append(body)   
  for show in past_shows:
    venue_id = show.venue_id
    body={}
    venue = Venue.query.get(venue_id)
    body['venue_id']=venue.id
    body['venue_name']=venue.name
    body['venue_image_link']=venue.image_link
    body['start_time']=str(show.start_time)
    past_show_data.append(body)   
  print(artistResultById.genres)
  convertedgenres = artistResultById.genres.replace('{', '').replace('}', '').split(',')
  print(convertedgenres)
  data =({
    "id": artist_id,
    "name": artistResultById.name, 
    "genres": convertedgenres,
    "city": artistResultById.city,
    "state": artistResultById.state,
    "phone": artistResultById.phone,
    "website": artistResultById.website_link,
    "facebook_link": artistResultById.facebook_link,
    "seeking_venue": artistResultById.seeking_venue,
    "seeking_description": artistResultById.seeking_description,
    "image_link": artistResultById.image_link,
    "past_shows":past_show_data,
    "upcoming_shows": future_show_data,
    "past_shows_count": len(past_show_data),
    "upcoming_shows_count":len(future_show_data) ,

  })
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  print(artist.genres)
  form.genres.data = artist.genres
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
   error = False
   try:
        form = request.form
        converted_seeking_venue=False
        if form.get("seeking_venue", False)=='y':
          print("if loop")
          converted_seeking_venue=True
        else :
          print("else  loop")
          converted_seeking_venue=False
        artist = Artist.query.get(artist_id)
        artist.name = form['name']
        artist.city=form['city']
        artist.state=form['state']
        artist.phone=form['phone']
        artist.genres=form.getlist('genres')
        artist.image_link=form['image_link']
        artist.facebook_link=form['facebook_link']
        artist.website_link=form['website_link']
        artist.seeking_venue=converted_seeking_venue
        artist.seeking_description=form['seeking_description']
        db.session.commit()
      
   except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
   finally:
        db.session.close()
   if error:
       flash('An error occurred. Artist ' + form['name'] + ' could not be edited.')
   else:
        flash('Artist ' + request.form['name'] + ' was successfully edited!') 
        return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  print(venue.genres)
  form.genres.data = venue.genres
  print(form.genres.data)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
        form = request.form
        converted_seeking_talent=False
        if form.get("seeking_talent", False)=='y':
          print("if loop")
          converted_seeking_talent=True
        else :
          print("else  loop")
          converted_seeking_talent=False
        venue = Venue.query.get(venue_id)
        venue.name=form['name']
        venue.city=form['city']
        venue.state=form['state']
        venue.address=form['address']
        venue.phone=form['phone']
        venue.genres=form.getlist('genres')
        venue.image_link=form['image_link']
        venue.facebook_link=form['facebook_link']
        venue.website_link=form['website_link']
        print("setting value")
        print(converted_seeking_talent)
        venue.seeking_talent=converted_seeking_talent
        venue.seeking_description=form['seeking_description']
        db.session.commit()
      
  except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
  finally:
        db.session.close()
  if error:
       flash('An error occurred. Venue ' + form['name'] + ' could not be edited.')
  else:
        flash('Venue ' + request.form['name'] + ' was successfully edited!') 
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        form = request.form
        converted_seeking_venue=False
        if form.get("seeking_venue", False)=='y':
          print("if loop")
          converted_seeking_venue=True
        else :
          print("else  loop")
          converted_seeking_venue=False
        artist = Artist(name= form['name'],
        city=form['city'],
        state=form['state'],
        phone=form['phone'],
        genres=form.getlist('genres'),
        image_link=form['image_link'],
        facebook_link=form['facebook_link'],
        website_link=form['website_link'],
        seeking_venue=converted_seeking_venue,
        seeking_description=form['seeking_description'])
        db.session.add(artist)
        db.session.commit()
      
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
       flash('An error occurred. Artist ' + form['name'] + ' could not be listed.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!') 
        return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  data=[]
  for show in shows:
    venue=Venue.query.get(show.venue_id)
    artist=Artist.query.get(show.artist_id)
    body={}
    body['venue_id']=venue.id
    body['venue_name']=venue.name
    body['artist_id']=artist.id
    body['artist_name']=artist.name
    body['artist_image_link']=artist.image_link
    body['start_time']=str(show.start_time)
    data.append(body)
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
        form = request.form
        show = Show(artist_id=form['artist_id'],
        venue_id=form['venue_id'],
        start_time=form['start_time'])
        db.session.add(show)
        db.session.commit()
      
  except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
  finally:
        db.session.close()
  if error:
       flash('An error occurred. Show could not be listed')
  else:
        flash('Show was successfully listed!') 
        return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
