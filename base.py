# encoding: utf-8
import webapp2
import jinja2
import os
import random
import hashlib
import hmac
import string
import requests
import requests.auth
import urllib
import urllib2
import json
import re
import imghdr
import time
import datetime
from datetime import timedelta
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.ext import deferred
from uuid import uuid4


RANK={
	"BRONZE":1,
	"SILVER":2,
	"GOLD":3,
	"PLATINUM":4,
	"DIAMOND":5,
	"MASTER":6,
	"GRANDMASTER":7,
}

RANKTW={
	"BRONZE":u"青銅",
	"SILVER":u"白銀",
	"GOLD":u"黃金",
	"PLATINUM":u"白金",
	"DIAMOND":u"鑽石",
	"MASTER":u"大師",
	"GRANDMASTER":u"宗師",
}

RACE={
	"ZERG":u"蟲族",
	"TERRAN":u"人類",
	"PROTOSS":u"神族",
	"RANDOM":u"隨機",
}

STATUS = {0:u"未驗證",1:u"未驗證",2:u"非隊員",3:u"隊員",4:u"文書",5:u"領隊",
          6:u"公關",7:u"人事",8:u"副隊長",9:u"隊長",10:u"網頁管理員",-1:u"怪胎"}


with open('secret.json') as data_file:    
    secret = json.load(data_file)

CLIENT_ID = secret['CLIENT_ID']
CLIENT_SECRET = secret['CLIENT_SECRET']
REDIRECT_URI = secret['REDIRECT_URI']
CLIENT_ID2 = secret['CLIENT_ID2']
CLIENT_SECRET2 = secret['CLIENT_SECRET2']
REDIRECT_URI2 = secret['REDIRECT_URI2']
SECRET = str(secret['SECRET'])
SECRET2 = str(secret['SECRET2'])
PROFILE_URI = secret['PROFILE_URI']
LADDERS_URL = secret['LADDERS_URL']


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render_error(self ,error):
		self.render_nav("error.html",error=str(error))

	def render(self ,template, logged_in=False, username="" , img_id = "",userstatus=-1 ,**kw):
		self.write(self.render_str(template, logged_in=logged_in, username=username, img_id=img_id,userstatus = userstatus , **kw))

	def render_nav(self, web, **kw):
		cookie=self.request.cookies.get("ukey" , "")
		if check_secure_val(cookie):
			ukey =  cookie.split('|')[0]
			ukey = db.Key(ukey)
			account =  db.get(ukey)
			self.render(web, logged_in =  True, username= account.username, img_id = account.key(),userstatus = account.status,**kw)
		else:
			self.render(web, logged_in = False,**kw)

	def get_status(self):
		cookie=self.request.cookies.get("ukey" , "")
		if check_secure_val(cookie):
			ukey =  cookie.split('|')[0]
			ukey = db.Key(ukey)
			account =  db.get(ukey)
			return account.status
		else:
			return -1

class Account(db.Model):
	image = db.BlobProperty()
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.EmailProperty(required =True)
	game_id = db.IntegerProperty (required = True, default=-1)
	status = db.IntegerProperty (required = True, default=0)
	game_name = db.StringProperty(required = True, default ="default")
	verify_id = db.StringProperty()
	intro = db.TextProperty()
	create = db.DateTimeProperty (auto_now_add = True)
	race = db.StringProperty()
	win = db.IntegerProperty(required=True, default=0)
	loss = db.IntegerProperty(required=True, default=0)


class Stream(db.Model):
	name = db.StringProperty(required = True)
	twitch_id = db.StringProperty(required=True)

class Forum (db.Model):
	title = db.StringProperty (required = True)
	content = db.TextProperty (required = True)
	create = db.DateTimeProperty (auto_now_add = True)
	modify = db.DateTimeProperty (auto_now = True)
	author = db.StringProperty(required = True)
	author_key = db.StringProperty (required = True)
	message = db.ListProperty (unicode, default=[],required = True)
	message_author = db.ListProperty (unicode, default=[],required = True)
	message_style = db.ListProperty (int, default=[],required = True)
	message_img = db.StringListProperty (default=[],required = True)
	message_time = db.ListProperty (datetime.datetime, default=[],required = True)

class Stra (db.Model):
	title = db.StringProperty (required = True)
	content = db.TextProperty (required = True)
	create = db.DateTimeProperty (auto_now_add = True)
	modify = db.DateTimeProperty (auto_now = True)
	author = db.StringProperty(required = True)
	author_key = db.StringProperty (required = True)
	message = db.ListProperty (unicode, default=[],required = True)
	message_author = db.ListProperty (unicode, default=[],required = True)
	message_style = db.ListProperty (int, default=[],required = True)
	message_img = db.StringListProperty (default=[],required = True)
	message_time = db.ListProperty (datetime.datetime, default=[],required = True)
	upload_files_key = db.ListProperty (str, default=[])
	upload_files_name = db.ListProperty (str, default=[])
	upload_files_displayname = db.ListProperty (unicode, default=[])
	
class Announce (db.Model):
	title = db.StringProperty (required = True)
	content = db.TextProperty (required = True)
	create = db.DateTimeProperty (auto_now_add = True)
	modify = db.DateTimeProperty (auto_now = True)

class Slide(db.Model):
	url = db.ListProperty(unicode , required=True, default=[])
	index = db.IntegerProperty(required = True, default=0)

class Event(db.Model):
	opponent = db.StringProperty(required = True)
	date = db.StringProperty(required = True)
	time = db.StringProperty (required = True)
	style = db.StringProperty (required = True)
	channel = db.StringProperty()
	event_map = db.StringProperty()
	rank = db.StringProperty()	
	other = db.TextProperty()
	a = db.StringProperty()
	b = db.StringProperty()
	regn = db.ListProperty (unicode,indexed=True, default=[],required = True)
	regp = db.ListProperty(unicode,indexed=True, default=[],required = True)
	detail_score = db.TextProperty()
	score = db.StringProperty()
	finished = db.BooleanProperty(required = True, default = False)


def hash_str(s):
	return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
	return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):
	val = h.split('|')[0]
	if h == make_secure_val(val):
		return val

def get_things_clean (s,status):
	if status==10:
		return s
	else:
		attrs = {
			'a': ['href','target','download'],
			'img': ['src', 'style','class'],
			'table' : ['class'],
			'blockquote' : ['cite'],
			'ol' : ['start'],
			'*' : ['style']

		}
		tags = ['a','img','span','p','blockquote', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5','h6','ul','ol','li','table','tr','td','tbody','hr','br','small']
		styles = ['color', 'background-color' , 'font-family', 'font-style','text-decoration', 'font-weight' , 'float','line-height','text-align','border-spacing','border-color']
		return bleach.clean(s, tags, attrs, styles)

def make_salt():
	return ''.join(random.choice(string.letters) for x in xrange(64))

def make_verify_id():
	return ''.join(random.choice(string.letters) for x in xrange(10))

def make_pw_hash(name, pw, salt=""):
	if not salt:
		salt = make_salt()
	h = hmac.new(SECRET,(str(name) + str(pw) + str(salt))).hexdigest()
	return '%s|%s' % (h, salt)

def valid_pw(name, pw, h):
	salt = h.split('|')[1]
	if h==make_pw_hash(name,pw,salt):
		return True

def hash_str(s):
	return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
	return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):
	val = h.split('|')[0]
	if h == make_secure_val(val):
		return val

def hash_str2(s):
	return hmac.new(SECRET2,s).hexdigest()

def make_secure_val2(s):
	return "%s|%s" % (s, hash_str2(s))


def check_secure_val2(h):
	val = h.split('|')[0]
	if h == make_secure_val2(val):
		return val

def make_authorization_url():
	state = str(uuid4())
	params = {"client_id": CLIENT_ID,
		"redirect_uri": REDIRECT_URI,
		"state": state,
		"scope":"sc2.profile",
		"response_type": "code",
		}  
	url = "https://kr.battle.net/oauth/authorize?" + urllib.urlencode(params)
	return url

def make_authorization_url2():
	state = str(uuid4())
	params = {"client_id": CLIENT_ID2,
		"redirect_uri": REDIRECT_URI2,
		"state": state,
		"scope":"sc2.profile",
		"response_type": "code",
		}  
	url = "https://kr.battle.net/oauth/authorize?" + urllib.urlencode(params)
	return url


def get_token(code):
	client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
	post_data = {
		"redirect_uri": REDIRECT_URI,
		"grant_type": "authorization_code",
		"code": code
		}
	response = requests.post("https://kr.battle.net/oauth/token",
		 auth=client_auth,
		 data=post_data)
	token_json = response.json()
	return token_json['access_token']


def get_token2(code):
	client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID2, CLIENT_SECRET2)
	post_data = {
		"redirect_uri": REDIRECT_URI2,
		"grant_type": "authorization_code",
		"code": code
		}
	response = requests.post("https://kr.battle.net/oauth/token",
		 auth=client_auth,
		 data=post_data)
	token_json = response.json()
	return token_json['access_token']

template_dir = os.path.join(os.path.dirname(__name__), 'Templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
			             autoescape = True)