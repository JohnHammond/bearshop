#!/usr/bin/env python

from flask import Flask
from flask import render_template, request, session, g, url_for, flash, get_flashed_messages, redirect
import sqlite3
import json
import sys, os
from colorama import *
import sys
from threading import Thread
from time import sleep

from uuid import uuid4


from passlib.hash import sha256_crypt
from contextlib import closing


debug = True

init( autoreset = True )

if (debug):

	def success( string ):
		print Fore.GREEN + Style.BRIGHT + "[+] " + string

	def error( string ):
		sys.stderr.write( Fore.RED + Style.BRIGHT + "[-] " + string + "\n" )

	def warning( string ):
		print Fore.YELLOW + "[!] " + string

else:
	def success( string ): pass
	def error( string ): pass
	def warning( string ): pass

# ===========================================================================

DATABASE = '/tmp/bears.db'
CERTIFICATE = 'certificate.crt'
PRIVATE_KEY = 'privateKey.key'

SECRET_KEY = 'this_key_needs_to_be_used_for_session_variables'

if DATABASE == '$DATABASE':
	error("This server has not yet been configured with a database file!")
	exit(-1)

if CERTIFICATE == '$CERTIFICATE_FILE':
	error("This server has not yet been configured with a certificate!")
	exit(-1)

if PRIVATE_KEY == '$PRIVATEKEY_FILE':
	error("This server has not yet been configured with a private key!")
	exit(-1)

app = Flask( __name__ )

app.config.from_object(__name__)

def init_db():
	with closing(connect_db()) as db:
	    with app.open_resource('schema.sql', mode='r') as f:
	        db.cursor().executescript(f.read())
	    db.commit()

def connect_db():
	return sqlite3.connect( app.config['DATABASE'] )

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# --------------------------------------------------------------------

@app.route("/")
def index():

	if not ( session['logged_in'] ):
		return redirect('login')

@app.route("/login", methods=["GET", "POST"])
def login():

	error = ""
	if request.method == "POST":

		cur = g.db.execute('select email, password from users')
		# username, password_hash
		users = dict(( row[0], row[1] ) for row in cur.fetchall())
		
		print "You POSTed", users

		if not request.form['email'] in users.iterkeys():
			flash('This e-mail is not in the database!')
		else:

			if not ( sha256_crypt.verify( request.form['password'], users[request.form['username']] ) ):
				flash("Incorrect password!")
			else:
				
				session_login( request.form['email'] )

				return redirect( "about" )

	return render_template( 'login.html' )


@app.route("/register", methods=["GET", "POST"])
def register():

	cur = g.db.execute('select email from users')
	
	usernames = [row[0] for row in cur.fetchall() ]

	error = ""
	if request.method == "POST":

		if unicode(request.form['email']) in usernames:
			flash('This e-mail is already registered!')
		elif (request.form['password'] == ""):
			flash("You must supply a password!")
		elif request.form['password'] != request.form['confirm']:
			flash('Your passwords do not match!')
		else:

			# I use this for command-line submission...
			identifier = str(uuid4())

			cur = g.db.execute('insert into users (email, password, uuid) values ( ?, ?, ? )', [ 
				               request.form['email'], 
				               sha256_crypt.encrypt( request.form['password']),
				               identifier # and a completely unique idenitifier
				  ] )

			g.db.commit()

			flash("Hello " + request.form['username'] + ", you have successfully registered!")
			session_login( request.form['email'] )
			return redirect( "challenges" )

	return render_template( 'register.html', error = error )


# @app.route("/scoreboard")
# def scoreboard(): 

# 	cur = g.db.execute('select username, score from users order by score desc, last_submission asc')	
# 	response = cur.fetchall()
	
# 	users = [ { "username": row[0], "score": row[1] } for row in response]
	
# 	return render("scoreboard.html", users = users )

# @app.route("/logout")
# def logout():

# 	session_logout()
# 	return redirect("about")

# @app.route("/")
# @app.route("/about")
# def about(): return render("about.html", app_about=configuration['app_about'])

# @app.route("/challenges")
# def challenges_page(): 

# 	if not ( session['logged_in'] ):
# 		return render("login.html", error = "You must log in to be able to see the challenges!")	
# 	try:
# 		cur = g.db.execute('select uuid from users where username =?',
# 				[ session['username'],] )

# 		uuid = cur.fetchone()[0]
# 	except Exception as e:
# 		print error(e.message)
# 		uuid = ''

# 	return render("challenges.html", challenges = configuration['services'], url=request.url_root, session_value = uuid )

# @app.route("/check_answer", methods=["GET", "POST"])
# def check_answer(): 

# 	global correct_answers

# 	if request.method == "POST":
# 		if request.form['answer'] in session['solved_challenges']:

# 			return json.dumps({'correct': -1});

# 		if ( request.form['answer'] in correct_answers.keys() ):

# 			flag = request.form['answer']

# 			new_score = int(session['score']) + correct_answers[flag]
# 			cur = g.db.execute("update users set score = (?), last_submission = (SELECT strftime('%s')) where username = (?)", [
# 					new_score, 
# 					session['username']
# 				] );

# 			session['solved_challenges'].append( request.form['answer'] ) 
# 			session['score'] = new_score
# 			g.db.commit();

# 			return json.dumps({'correct': 1, 'new_score': new_score});
# 		else:
# 			return json.dumps({'correct': 0});

# @app.route("/submit", methods=[ "POST" ])
# def submit(): 

# 	global correct_answers

# 	if request.method == "POST":

# 		if ( request.form['flag'] in correct_answers.keys() ):

# 			flag = request.form['flag']

# 			cur = g.db.execute('select score, solved_challenges from users where uuid = (?)',
# 				[ request.form['uuid'], ])


# 			current_score, solved_challenges = cur.fetchone()

# 			solved_challenges = solved_challenges.split()

# 			if ( flag in solved_challenges ):
# 				return 'You already submitted this flag!\n'

# 			print solved_challenges

# 			new_score = current_score + correct_answers[flag]
# 			solved_challenges.append( flag + " " )
# 			cur = g.db.execute("update users set score = (?), last_submission = (SELECT strftime('%s')), solved_challenges = (?) where uuid = (?)", [
# 					new_score, 
# 					' '.join(solved_challenges),
# 					request.form['uuid']
# 				] );

# 			# session['solved_challenges'].append( request.form['flag'] ) 
# 			session['score'] = new_score
# 			g.db.commit();

# 			# return json.dumps({'correct': 1, 'new_score': new_score});
# 			return 'Correct!\n';
# 		else:
# 			# return json.dumps({'correct': 0});
# 			return 'Incorrect!\n';

def session_login( username ):
	
	flash("You were successfully logged in!")

	# cur = g.db.execute('select solved_challenges, score from users where username = (?)',
	# 		[username])	

	# solved_challenges, score = cur.fetchone()

	session['logged_in'] = True
	# session['username'] = username
	# session['score'] = score
	# session['solved_challenges'] = []

def session_logout():

	flash("You have been successfully logged out.")

	session['logged_in'] = False
	# session.pop('username')
	# session.pop('score')

if ( __name__ == "__main__" ):
	context = (CERTIFICATE, PRIVATE_KEY)
	app.run( host="0.0.0.0", debug=True, ssl_context=context, threaded=True)
