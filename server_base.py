#!/usr/bin/env python

from flask import Flask
from flask import render_template, request, session, g, url_for, flash, get_flashed_messages, redirect, send_from_directory
import sqlite3
import json
import sys, os
from colorama import *
import sys
from threading import Thread
from time import sleep
from werkzeug.utils import secure_filename
from uuid import uuid4
from textwrap import dedent
from PIL import Image # needed to resize the image they upload
import re # Used to verify phone numbers
from resizeimage import resizeimage

# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

from passlib.hash import sha256_crypt
from contextlib import closing

f = open("badwords.txt")
bad_words = f.read().split('\n')
f.close()

def contains_bad_word( string ):

	words = string.split(" ")
	for word in words:
		if word in bad_words:
			return True
	else:
		return False

price_cap = 10000

debug = True

init( autoreset = True )
email_from = 'USCGA BearShop'

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def send_email( to_address, subject, message ):

	msg = MIMEText(message, 'html')
	msg["Subject"] = subject
	msg['From'] = email_from
	msg['To'] = to_address
	server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
	server.ehlo()
	server.login('uscga.bearshop@gmail.com', 'Go Coast Guard')
	server.sendmail(email_from, [to_address], msg.as_string())
	server.quit()

# ===========================================================================

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
DATABASE = 'database.db'
UPLOAD_FOLDER = 'uploads'
# PRIVATE_KEY = '$PRIVATEKEY_FILE'

SECRET_KEY = 'this_key_needs_to_be_used_for_session_variables'

# if DATABASE == '$DATABASE':
# 	error("This server has not yet been configured with a database file!")
# 	exit(-1)

# if CERTIFICATE == '$CERTIFICATE_FILE':
# 	error("This server has not yet been configured with a certificate!")
# 	exit(-1)

# if PRIVATE_KEY == '$PRIVATEKEY_FILE':
# 	error("This server has not yet been configured with a private key!")
# 	exit(-1)

app = Flask( __name__ )

app.config.from_object(__name__)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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

	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified from users where uuid = (?)', [session['uuid']])
	verified = cur.fetchone()[0]
	if not verified: 
		return redirect('verify')
	return redirect('products')

@app.route("/login", methods=["GET", "POST"])
def login():

	email = password = ""
	
	if request.method == "POST":

		cur = g.db.execute('select email, password, uuid from users')
		users = dict(( row[0], row[1] ) for row in cur.fetchall())

		email = request.form['email']
		password = request.form['password']

		if ( email == "" ):
			flash("You need to enter an e-mail address!")
		elif not email.endswith("uscga.edu"):
			flash("This does not look like a valid USCGA EDU e-mail address!")
		elif not email in users.iterkeys():
			flash('This e-mail is not in the database!')
		else:
			if ( password == "" ):
				flash("You need to enter a password!")
			elif not ( sha256_crypt.verify( request.form['password'], users[email] ) ):
				flash("Incorrect password!")
			else:
				session_login( request.form['email'] )
				return redirect( "verify" )

	return render_template( 'login.html', email=email, password = password )

@app.route("/register", methods=["GET", "POST"])
def register():

	cur = g.db.execute('select email from users')
	usernames = [row[0] for row in cur.fetchall() ]
	
	email = password = confirm = ""

	if request.method == "POST":
		email = request.form['email']
		password = request.form['password']
		confirm = request.form['confirm']
		if unicode(request.form['email']) in usernames:
			flash('This e-mail is already registered!')
		elif (request.form['password'] == ""):
			flash("You must supply a password!")
		elif request.form['password'] != request.form['confirm']:
			flash('Your passwords do not match!')

		else:

			# I use this for command-line submission...
			identifier = str(uuid4())

			cur = g.db.execute('insert into users (email, name, password, uuid, your_products, room, phone, verified) values ( ?, ?, ?, ?, ?, ?, ?, ? )', [ 
				               email, 
				               " ".join( [email.split(".")[0], email.split(".")[2].split("@")[0] ]),
				               sha256_crypt.encrypt( request.form['password']),
				               identifier, # a completely unique idenitifier
				               "", # They currently have no products being sold
				               "", # They can enter their room number later
				               "", # They can enter their phone number later
				               0 # verified? ...since they just registered, no!
				  ] )

			g.db.commit()

			session_login( request.form['email'] )
			send_verification_link()
			return redirect( "verify" )
	
	return render_template( 'register.html', email = email, password = password, confirm = confirm )


@app.route("/send_verification_link")
def send_verification_link():
	
	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified from users where uuid = (?)', [session['uuid']])
	verified = cur.fetchone()[0]

	if ( session['logged_in'] ):

		email = session['email']
		cur = g.db.execute('select uuid, verified from users where email = (?)', [email])	

		identifier, verified = cur.fetchone()
		if ( verified == 1 ):
			flash("Your e-mail address has already been verified.")
			return redirect('products')
		else:
			
			send_email(	email, 
						'Your Registration Verification Code', 
						render_template("verification_email.html", identifier = identifier
					))

			# THIS IS ONLY FOR TESTING....
			send_email(	'johnhammond010@gmail.com', 
						'Your Registration Verification Code', 
						render_template("verification_email.html", identifier = identifier
					))

	flash("An e-mail has been sent!")
	return redirect("verify")


@app.route("/products")
def products():

	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified from users where uuid = (?)', [session['uuid']])
	verified = cur.fetchone()[0]
	if not verified: 
		return redirect('verify')
	cur = g.db.execute('select name, picture, price, uuid from products')
	products = [ [ row[0], row[1], row[2], row[3] ] for row in cur.fetchall()[::-1]]

	return render_template("products.html", products = products)

@app.route("/products/<uuid>")
def product(uuid):

	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified from users where uuid = (?)', [session['uuid']])
	verified = cur.fetchone()[0]
	if not verified: 
		return redirect('verify')

	cur = g.db.execute('select name, price, picture, description, seller, interested_people from products where uuid = (?)', [uuid] )
	name, price, picture, description, seller, interested_people = cur.fetchone()

	cur = g.db.execute('select uuid from users where name = (?)', [seller] )
	seller_uuid = cur.fetchone()[0]


	interested_people = [ person for person in interested_people.split('\n') if person ]

	return render_template('item.html', name=name, picture=picture, description=description, seller=seller, price=price, uuid=uuid, interested_people =interested_people, seller_uuid = seller_uuid)

@app.route("/remove_product/<uuid>")
def remove_product(uuid):

	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified from users where uuid = (?)', [session['uuid']])
	verified = cur.fetchone()[0]
	if not verified: 
		return redirect('verify')

	cur = g.db.execute('select seller from products where uuid = (?)', [uuid])
	product_seller = cur.fetchone()[0]
	
	if ( product_seller == session['name'] ):
		
		cur = g.db.execute('delete from products where uuid = (?)', [uuid])
		g.db.commit()
		cur = g.db.execute('select your_products from users where email = (?)', [session['email']])
		your_products = cur.fetchone()[0];
		your_products = your_products.replace(uuid,'')
		your_products = your_products.strip()
		print your_products
		cur = g.db.execute('update users set your_products = (?) where email = (?)', [
			your_products,
			session['email']
		])
		g.db.commit()

		flash("The product has been successfully removed.")
		return redirect("products")
	else:
		return "This product does not belong to you. Nice try, but no."

@app.route("/verify", methods=["GET", "POST"])
def verify():

	identifier = ""
	
	if not 'logged_in' in session: return redirect('login')
	else:
		cur = g.db.execute('select uuid, verified from users where email = (?)', [session['email']])
		uuid, verified = cur.fetchone()

		if ( verified ):
			# flash("Your e-mail address has already been verified.")
			return redirect('products')
		else:
			if ( request.method == "GET" ):
				identifier = request.args.get('identifier')
			if ( request.method == "POST" ):
				identifier = request.form['identifier']
			
			if ( identifier ):
				if ( identifier == uuid ):
					cur = g.db.execute("update users set verified = (?) where email = (?)", [
						1, 
						session['email']
					] );

					g.db.commit();
					return redirect('products')

				else:
					flash("Incorrect verification code.")

	return render_template( 'verify.html', identifier = identifier)

@app.route("/search")
def search():
	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified from users where uuid = (?)', [session['uuid']])
	verified = cur.fetchone()[0]
	if not verified: 
		return redirect('verify')
	return render_template("search.html")


@app.route("/edit/<uuid>",  methods=["GET", "POST"])
def edit(uuid):
	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified from users where uuid = (?)', [session['uuid']])
	verified = cur.fetchone()[0]
	if not verified: 
		return redirect('verify')

	if ( request.method == "GET" ):

		
		cur = g.db.execute('select name, price, picture, description, seller from products where uuid = (?)', [uuid] )
		name, price, picture, description, seller = cur.fetchone()

		return render_template('edit.html', name=name, picture=picture, description=description, seller=seller, price=price[1:], uuid=uuid)
	
	if ( request.method == "POST" ):
		
		name = request.form['name']
		# uuid = request.form['uuid']
		picture = request.form['picture']
		cur = g.db.execute('select seller from products where uuid = (?)', [uuid])
		product_seller = cur.fetchone()[0]
		
		if ( product_seller == session['name'] ):
			# picture = request.form['picture']
			price = request.form['price']
			name = request.form['name']
			description = request.form['description']

			if (contains_bad_word(price.lower()) or \
				contains_bad_word(description.lower()) or \
				contains_bad_word(name.lower())
			):
				flash("Detected a bad word. Not accepting that.")
				return redirect(url_for('edit', uuid=uuid))

			if ( name == "" ):
				flash("Please enter a name of the product!")
				return redirect(url_for('edit', uuid=uuid))

			elif ( price == "" ):
				flash("Please enter the price of the product in dollars!")
				return redirect(url_for('edit', uuid=uuid))
			elif ( description == "" ):
					flash("Please enter a description of your product!")
					return redirect(url_for('edit', uuid=uuid))
			elif ( '.' in price ):
				if ( price[-3] != '.' ):
					flash("That does not look like a valid price!")
					return redirect(url_for('edit', uuid=uuid))
			try:
				price_number = round(float(price),2)
				warning(str(price_number))
				if (price_number != abs(price_number)):
					flash("That does not look like a valid price!")
					return redirect(url_for('edit', uuid=uuid))
				elif ( price_number >= price_cap ):
					flash("Please enter a cost less than $" + str(price_cap))
					return redirect(url_for('edit', uuid=uuid))
				else:
					# We should be good to process the form
					price_number = '$' + format(price_number, '.2f')

					if 'picture' not in request.files:
						pass # They don't have to update the picture
					else:
						file = request.files['picture']

						if file and allowed_file(file.filename):
							filename = secure_filename(str(uuid4()) + "." + file.filename.split('.')[-1])
							save_location = os.path.join(app.config['UPLOAD_FOLDER'], filename)
							file.save(save_location)
							p = Image.open(save_location)
							try:
								p = resizeimage.resize_cover(p, (350, 350))
							except:
								pass
							p.save(save_location)
							# return redirect(url_for('uploaded_file', filename=filename))
							picture = (url_for('uploaded_file', filename=filename))

						cur = g.db.execute("update products set name = (?), picture = (?), description = (?), price = (?) where uuid = (?)", [
									name,
									str(picture),
									description, 
									price_number,
									uuid
								] );
						g.db.commit()
			except:
				# print price
				flash("That does not look like a valid price!")
				return redirect(url_for('edit', uuid=uuid))

		else:
			flash("This is not your own product!")
			return redirect(request.referrer)

	return redirect(url_for('product', uuid=uuid))


@app.route("/profile/<uuid>", methods= ["GET", "POST"])
def profile(uuid):
	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified, room, phone from users where uuid = (?)', [session['uuid']])
	verified, room, phone = cur.fetchone()
	if not verified: 
		return redirect('verify')

	cur = g.db.execute('select email, your_products from users where uuid = (?)', [uuid])
	email, your_products = cur.fetchone()
	name = " ".join( [email.split(".")[0], email.split(".")[2].split("@")[0] ])
	your_products = your_products.split(" ")
	products = []
	for product in your_products:
		cur = g.db.execute('select name from products where uuid = (?)', [product])
		product_name = cur.fetchone()
		if product_name != None: 
			product_name = product_name[0]
			products.append( [product_name, product] )

	if ( request.method == "POST" ):

		if uuid == session['uuid']:

			phone = room = ""
			phone = request.form['phone']
			room = request.form['room']
			name = session['name']

			if ( not re.search('\d\d\d-\d\d\d-\d\d\d\d', phone) ):
				flash("Please enter the phone number in the form: ###-###-####")
				return render_template("profile.html", name = name, products = products, phone = phone, room = room )
			elif ( not re.search('.\d\d\d', room)):
				flash("Please enter a proper room number, #### or E###.")
				return render_template("profile.html", name = name, products = products, phone = phone, room = room )
			else:
				flash("Your profile has been saved successfully!")
				cur = g.db.execute('update users set room = (?), phone = (?) where uuid = (?)', [
					room,
					phone,
					session['uuid']
					])

				g.db.commit()

				return render_template("profile.html", name = name, products = products, phone = phone, room = room )

	return render_template("profile.html", name = name, products = products, room = room, phone = phone )

@app.route("/show_interest/<seller>/<uuid>")
def show_interest(seller, uuid):
	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified, room, phone from users where uuid = (?)', [session['uuid']])
	verified, room, phone = cur.fetchone()
	if not verified: 
		return redirect('verify')

	cur = g.db.execute('select interested_people, name from products where uuid = (?)', [uuid])
	interested_people, product_name = cur.fetchone();
	interested_people += '\n' + session['name']
	interested_people = interested_people.strip()
	cur = g.db.execute('update products set interested_people = (?) where uuid = (?)', [
		interested_people,
		uuid
	])
	g.db.commit()


	cur = g.db.execute('select email from users where name = (?)', [seller])
	sellers_email = cur.fetchone()[0]

	send_email(	sellers_email, 
		'Someone is interested in your product!', 
		render_template("interest_email.html", 
				name = session['name'], 
				product_name = product_name,
				room = room,
				phone = phone,
				email = session['email']
	))


	flash("You showed interest in this product! An e-mail has been sent to notify the seller.")
	return redirect( request.referrer )


@app.route("/sell", methods=["GET", "POST"])
def sell():
	
	if not 'logged_in' in session: return redirect('login')
	cur = g.db.execute('select verified from users where uuid = (?)', [session['uuid']])
	verified = cur.fetchone()[0]
	if not verified: 
		return redirect('verify')

	name = picture = description = price = ""

	if ( request.method == "POST" ):
		
		name = request.form['name']
		price = request.form['price']
		description = request.form['description']
		if 	( contains_bad_word(price.lower()) or \
				contains_bad_word(description.lower()) or \
				contains_bad_word(name.lower())
		):
			flash("Detected a bad word. Not accepting that.")
			return render_template("sell.html", name=name, price = price, description = description)

		if ( name == "" ):
			flash("Please enter a name of the product!")
			return render_template("sell.html", name=name, price = price, description = description)
		elif ( price == "" ):
			flash("Please enter the price of the product in dollars!")
			return render_template("sell.html", name=name, price = price, description = description)
		elif ( description == "" ):
				flash("Please enter a description of your product!")
				return render_template("sell.html", name=name, price = price, description = description)
		elif ( '.' in price ):
			if ( price[-3] != '.' ):
				flash("That does not look like a valid price!")
				return render_template("sell.html", name=name, price = price, description = description)
		try:
			price_number = round(float(price),2)
			warning(str(price_number))
		except:
			print price
			flash("That does not look like a valid price!")
			return render_template("sell.html", name=name, price = price, description = description)

		if (price_number != abs(price_number)):
			flash("That does not look like a valid price!")
			return render_template("sell.html", name=name, price = price, description = description)
		elif ( price_number >= price_cap ):
			flash("Please enter a cost less than $" + str(price_cap))
			return render_template("sell.html", name=name, price = price, description = description)

		else:
			# We should be good to process the form
			price_number = '$' + format(price_number, '.2f')

			if 'picture' not in request.files:
				pass # We make it optional for them to upload files, remember?
			else:
				file = request.files['picture']

				if file and allowed_file(file.filename):
					filename = secure_filename(str(uuid4()) + "." + file.filename.split('.')[-1])
					save_location = os.path.join(app.config['UPLOAD_FOLDER'], filename)
					file.save(save_location)
					p = Image.open(save_location)
					try:
						p = resizeimage.resize_cover(p, (350, 350))
					except:
						pass
					p.save(save_location)
					# return redirect(url_for('uploaded_file', filename=filename))
					picture = (url_for('uploaded_file', filename=filename))

			uuid = str(uuid4())
			cur = g.db.execute('insert into products (name, picture, description, price, seller, interested_people, uuid) values ( ?, ?, ?, ?, ?, ?, ? )', [ 
		               name,
		               str(picture),
		               description, 
		               price_number, # Since you are just selling this product, no one is interested yet!
		               session['name'],
		               "",
		               uuid
				  ] );

			g.db.commit()
			cur = g.db.execute('select your_products from users where email = (?)', [session['email']])
			your_products = cur.fetchone()[0];
			your_products += ' ' + uuid
			your_products = your_products.strip()
			print your_products
			cur = g.db.execute('update users set your_products = (?) where email = (?)', [
				your_products,
				session['email']
			])
			g.db.commit()

			return redirect('products')

	return render_template("sell.html", name=name, price = price, description = description)

@app.route("/log_out", methods=["GET", "POST"])
def log_out():
	session_logout()
	return redirect('login')

def session_login( email ):

	flash("You have been successfully logged in!")

	session['logged_in'] = True
	session['email'] = email
	cur = g.db.execute('select uuid from users where email = (?)', [session['email']])
	uuid = cur.fetchone()
	if uuid != None: uuid = uuid[0];
	session['uuid'] = uuid
	session['name'] = " ".join( [email.split(".")[0], email.split(".")[2].split("@")[0] ])

def session_logout():

	flash("You have been successfully logged out.")

	session.pop('logged_in')
	session.pop('email')
	session.pop('uuid')
	session.pop('name')

	

if ( __name__ == "__main__" ):
	# context = (CERTIFICATE, PRIVATE_KEY)
	# app.run( host="0.0.0.0", debug=False, ssl_context=context, port = 444, threaded=True )


	app.run( host="0.0.0.0", debug=True, port=2001, threaded = True )
	
