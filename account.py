# encoding: utf-8
import uuid
from base import *


STATUS = {0:u"未驗證",1:u"未驗證",2:u"非隊員",3:u"隊員",4:u"文書",5:u"領隊",
          6:u"公關",7:u"人事",8:u"副隊長",9:u"隊長",-1:u"怪胎",10:u"網站管理員"}


class signup(Handler):
	def get (self):
		self.response.headers['Content-Type'] = 'text/HTML'
		self.render_nav ("signup/signup_1.html", )
	def post(self):
		USER_RE=re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
		PASS_RE=re.compile(r"^.{3,20}$")
		EMAIL_RE=re.compile(r"^[\S]+@[\S]+\.[\S]+$" )
		username = self.request.get("username")
		email = self.request.get("email")
		password = self.request.get("password")
		verify = self.request.get("verify")
		intro = self.request.get("intro")
		image = self.request.get("image")
		error = "has-error"
		warning = "has-warning"
		chk_account=  Account.all().filter('username =', username).get()
		chk_email=  Account.all().filter('email =', email).get()
		if (USER_RE.match(username) and not chk_account ):
			user_ok=""
		else:
			user_ok=error
		if (PASS_RE.match(password)):
			pass_ok=warning
		else:
			pass_ok=error
		if (password == verify  and PASS_RE.match(verify)):
			verify_ok=warning
		else:
			verify_ok=error
		if (EMAIL_RE.match(email) and not chk_email):
			email_ok=""
		else:
			email_ok=error
		if imghdr.what (None, image):
			image_ok=warning
		elif image == "":
			image_ok=""
		else:
			image_ok=error


		if (not (email_ok or user_ok  or verify_ok != warning or pass_ok != warning or not (image_ok == warning or image_ok == ""))):
			HASH=make_pw_hash(username , password)
			url = make_verify_id()	
			message = mail.EmailMessage(sender="ClanSR天狼星戰隊 <SCIIClanSR@gmail.com>",
                            			subject="在此驗證你的信箱")

			message.to = "%s <%s>" % (username, email)
			message.body = u"""
			親愛的 %s:

			你所申請的帳號需要通過電子信箱驗證，請拜訪
			https://sciisirius.appspot.com/account/verify?id=%s 來驗證您的信箱並且繼續註冊程序。

			如果有任何問題記得回報我們。

			戰隊網編群敬上。
			""" % (username, url)

			message.send()
			if image:
				temp=Account  (username = username, password = HASH, email = email, intro = intro,
							   image = image, verify_id= url)
			else:
				temp=Account  (username = username, password = HASH, email = email, intro = intro,
							   verify_id= url)

			temp.put()
			self.render_nav ("/signup/signup_2.html")
		else:
			self.write(image)
			self.render_nav ("signup/signup_1.html", user_ok=user_ok, email_ok=email_ok, pass_ok=pass_ok,
						    verify_ok=verify_ok,username=username, email=email,
						    image_ok = image_ok, intro=intro, error=1)

		

class verify(Handler):
	def get (self):
		id = self.request.get ('id')
		if id == '0':
			self.render_error(404)
		else:
			account=  Account.all().filter('verify_id =', id).get()
		if account:
			setattr(account, 'status', 1)
			account.put()
			self.render_nav ("/signup/signup_3.html")
			self.response.set_cookie('ukey', make_secure_val2(str(account.key())) , path='/')
		else:
			self.render_error(404)
		

class connect(Handler):
	def  get(self):
		cookie=self.request.cookies.get("ukey" , "")
		if check_secure_val2(cookie):
			ukey =  cookie.split('|')[0]
			ukey = db.Key(ukey)
			account =  db.get(ukey)
			code = self.request.get("code")
			if account.status == 1:
				if code:
					r= json.load(urllib2.urlopen(r'https://kr.api.battle.net/sc2/profile/user?locale=ko_KR&access_token=%s' % get_token(code)))
					chk=  Account.all().filter('game_id =', r['characters'][0]['id']).get()
					if not chk:	
						setattr(account, 'game_name', r['characters'][0]['displayName'])
						setattr(account, 'race', r['characters'][0]['career']['primaryRace'])
						setattr(account, 'game_id', long(r['characters'][0]['id']))
						setattr(account, 'status', 2)
						setattr(account, 'verify_id', None)
						account.put()
						battletag = r['characters'][0]['name']
						self.render_nav("signup/signup_4.html" , tag = battletag)
						self.response.set_cookie('ukey', make_secure_val(str(account.key())) , path='/')
					else:
						self.render_error("ALREADY USED!!!")
   				else:
   					self.redirect(make_authorization_url())	
   			else:
   				self.render_error(403)
		else:
			self.render_error(403)



class connect_again(Handler):
	def  get(self):
		code = self.request.get("code")
		cookie=self.request.cookies.get("ukey" , "")
		cookie = check_secure_val (cookie)
		account=db.get(cookie)
		if code:
			r= json.load(urllib2.urlopen(r'https://kr.api.battle.net/sc2/profile/user?locale=ko_KR&access_token=%s' % get_token2(code)))
			chk=  Account.all().filter('game_id =', r['characters'][0]['id'])
			flag= True
			for i in chk:
				if i.username!=account.username:
					flag = False
			if flag:
				setattr(account, 'game_name', r['characters'][0]['displayName'])
				setattr(account, 'game_id', r['characters'][0]['id'])
				account.put()
				memcache.delete("ladder")
				self.redirect("/account/profile?uid="+account.username)
			else:
				self.render_error("ALREADY USED!!!")
   		else:
   			self.redirect(make_authorization_url2())	


class login(Handler):
	def  get(self):
		self.render_nav ("/account/login.html")
		cookie = self.request.cookies.get("ukey" , "")
		if check_secure_val(cookie):
			self.redirect("/")
	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		remember = self.request.get("remember")
		account = db.GqlQuery ("SELECT * FROM Account WHERE username = :1" , username).get()
		if account:
			if (valid_pw(account.username, password, account.password)):
				if account.status >= 2:
					if remember=="on":
						self.response.set_cookie('ukey', make_secure_val(str(account.key())), expires= datetime.datetime(2050, 01, 01, 00, 00, 00, 000000) , path='/')
						self.redirect("/")
					else:
						self.response.set_cookie('ukey', make_secure_val(str(account.key())) , path='/')						
						self.redirect("/")
				else:
					self.render_nav ("/account/login.html", error = 2)
			else:
				self.render_nav ("/account/login.html", error=1)
		else:
			self.render_nav ("/account/login.html",  error=1)


class profile(Handler):
	def get(self):
		username = self.request.get("uid")
		account=  Account.all().filter('username =', username).get()
		if account:
			if (account.win+account.loss):
				rate = round(float(float(account.win)/float(account.loss+account.win)*100),2)
			else:
				rate = "NULL"
			jp = json.loads(urlfetch.fetch(PROFILE_URI % (account.game_id,account.game_name)).content)	
			jl = json.loads(urlfetch.fetch(LADDERS_URL % (account.game_id,account.game_name)).content)
			if not 'previousSeason' in jl:
				self.render_nav("/account/profile.html",
								profileuser = account.username,
								profile_img_id = account.key(),
								win = account.win,
								loss = account.loss,
								rate = rate,
								date = (account.create + timedelta(hours = 8)).strftime("%Y-%m-%d %H:%M"),
								intro = account.intro,
								status=STATUS[account.status],
								error = True)
			else:
				profilePath = jp['profilePath']
				displayName = jp['displayName']
				primaryRace = jp['career']['primaryRace']
				highest1v1Rank = jp['career']['highest1v1Rank']
				if jl['previousSeason'] != []:
					for i in jl['previousSeason']:
						if i['ladder'] != []:
							if i['ladder'][0]['matchMakingQueue'] == "HOTS_SOLO":
								previousSeasonleague = i['ladder'][0]['league']
								previousSeasonrank = i['ladder'][0]['rank']
								previousSeasonwins = i['ladder'][0]['wins']
								previousSeasonlosses = i['ladder'][0]['losses']
								break
					else:
						previousSeasonleague = "None"
						previousSeasonrank = "None"
						previousSeasonwins = "None"
						previousSeasonlosses = "None"
				else:
						previousSeasonleague = "None"
						previousSeasonrank = "None"
						previousSeasonwins = "None"
						previousSeasonlosses = "None"
				if jl['currentSeason'] != [] :
					for i in jl['currentSeason']:
						if i['ladder']!=[]:
							if i['ladder'][0]['matchMakingQueue'] == "HOTS_SOLO":
								Seasonleague = i['ladder'][0]['league']
								Seasonrank = i['ladder'][0]['rank']
								Seasonwins = i['ladder'][0]['wins']
								Seasonlosses = i['ladder'][0]['losses']
								break
					else:
						Seasonleague = "None"
						Seasonrank = "None"
						Seasonwins = "None"
						Seasonlosses = "None"
				else:
						Seasonleague = "None"
						Seasonrank = "None"
						Seasonwins = "None"
						Seasonlosses = "None"

				self.render_nav("/account/profile.html",
								profileuser = account.username,
								profile_img_id = account.key(),
								profilePath = profilePath,
								displayName = displayName,
								primaryRace = account.race,
								highest1v1Rank = highest1v1Rank,
								previousSeasonleague = previousSeasonleague,
								previousSeasonrank = previousSeasonrank,
								previousSeasonwins = previousSeasonwins,
								previousSeasonlosses = previousSeasonlosses,
								Seasonleague = Seasonleague,
								Seasonrank = Seasonrank,
								Seasonwins = Seasonwins,
								Seasonlosses = Seasonlosses,
								win = account.win,
								loss = account.loss,
								rate = rate,
								date = (account.create + timedelta(hours = 8)).strftime("%Y-%m-%d %H:%M"),
								intro = account.intro,
								status=STATUS[account.status])

		else:
			self.render_error(404)



class logout(Handler):
	def get(self):
		self.response.headers.add_header('Set-Cookie', str('ukey= ;  Path=/') )
		time.sleep(1)
		self.redirect("/")

		
class image(Handler):
	def get(self):	
		self.response.headers['Content-Type'] = 'image'	
		img_id = self.request.get ('img_id')
		account = db.get(img_id)
		image = memcache.get('img_%s'% img_id)
		if not image:
			if account.image:
				image = (account.image)
				image = images.Image(image)
				image.resize(width=40, height=40)
				image = image.execute_transforms(output_encoding=images.PNG)
			else:
				self.redirect("../picture/default.jpg")
			memcache.set('img_%s'% img_id, image)
		self.write(image)

class image_53(Handler):
	def get(self):	
		self.response.headers['Content-Type'] = 'image'	
		img_id = self.request.get ('img_id')
		account = db.get(img_id)
		image = memcache.get('img_64_%s'% img_id)
		if not image:
			if account.image:
				image = (account.image)
				image = images.Image(image)
				image.resize(width=53, height=53)
				image = image.execute_transforms(output_encoding=images.PNG)
			else:
				self.redirect("../picture/default.jpg")
			memcache.set('img_%s'% img_id, image)
		self.write(image)

class image_org(Handler):
	def get(self):
		self.response.headers['Content-Type'] = 'image'	
		img_id = self.request.get ('img_id')
		account = db.get(img_id)
		if account.image:
			image = (account.image)
			image = images.Image(image)
			image.resize(width=80, height=80)
			image = image.execute_transforms(output_encoding=images.PNG)
			self.write(image)
		else:
			self.redirect("../picture/default.jpg")

class img_config(Handler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/HTML'
		cookie = self.request.cookies.get("ukey" , "")
		cookie = check_secure_val(cookie)
		if cookie:
			account = db.get(cookie)
			if account:
				self.render_nav("/account/img_config.html")
			else:
				self.render_error(404)
		else:
			self.render_error(403)

	def post(self):
		cookie = self.request.cookies.get("ukey" , "")
		cookie = check_secure_val(cookie)
		if cookie:
			account = db.get(cookie)
			if account:
				image = self.request.get("image")
				if imghdr.what (None, image) :
					account.image=str(image)
					account.put()
					memcache.delete("img_%s" % cookie)
					self.redirect("/account/profile?uid=%s" % account.username)
				elif image == "":
					account.image=None
					account.put()
					memcache.delete("img_%s" % cookie)
					self.redirect("/account/profile?uid=%s" % account.username)
				else:
					self.render_nav("/account/img_config.html", error=1)				
			else:
				self.render_error(404)
		else:
			self.render_error(403)


class intro_config(Handler):
	def get(self):
		cookie = self.request.cookies.get("ukey" , "")
		cookie = check_secure_val(cookie)
		if cookie:
			account = db.get(cookie)
			if account:
				self.render_nav("/account/intro_config.html",intro = account.intro)
			else:
				self.render_error(404)
		else:
			self.render_error(403)

	def post(self):
		cookie = self.request.cookies.get("ukey" , "")
		cookie = check_secure_val(cookie)
		if cookie:
			account = db.get(cookie)
			if account:
				intro = self.request.get("intro")
				if intro != "":
					account.intro=intro
					account.put()
					self.redirect("/account/profile?uid=%s" % account.username)
				else:
					self.render_nav("/account/intro_config.html", error=1)				
			else:
				self.render_error(404)
		else:
			self.render_error(403)

class race_config(Handler):
	def get(self):
		cookie = self.request.cookies.get("ukey" , "")
		cookie = check_secure_val(cookie)
		if cookie:
			account = db.get(cookie)
			if account:
				self.render_nav("/account/race_config.html",race = account.race)
			else:
				self.render_error(404)
		else:
			self.render_error(403)

	def post(self):
		cookie = self.request.cookies.get("ukey" , "")
		cookie = check_secure_val(cookie)
		if cookie:
			account = db.get(cookie)
			if account:
				race = self.request.get("race")
				if race != "":
					account.race=race
					account.put()
					self.redirect("/account/profile?uid=%s" % account.username)
				else:
					self.render_nav("/account/race_config.html", error=1)				
			else:
				self.render_error(404)
		else:
			self.render_error(403)


class pass_config(Handler):
	def get(self):
		cookie = self.request.cookies.get("ukey" , "")
		cookie = check_secure_val(cookie)
		if cookie:
			account = db.get(cookie)
			if account:
				self.render_nav("/account/pass_config.html")
			else:
				self.render_error(404)
		else:
			self.render_error(403)

	def post(self):
		cookie = self.request.cookies.get("ukey" , "")
		cookie = check_secure_val(cookie)
		if cookie:
			account = db.get(cookie)
			if account:
				password = self.request.get("password")
				new = self.request.get("new")
				verify = self.request.get("verify")
				PASS_RE=re.compile(r"^.{3,20}$")
				if valid_pw(account.username, password, account.password) and new == verify and PASS_RE.match(new):
					HASH=make_pw_hash(account.username,new)
					setattr(account, 'password', HASH)
					account.put()
					self.redirect("/account/profile?uid=%s" % account.username)
				else:
					self.render_nav("/account/pass_config.html", error=1)				
			else:
				self.render_error(404)
		else:
			self.render_error(403)

class stupid(Handler):
	def get(self):
		self.render_nav("/account/stupid.html")
	def post(self):
		email = self.request.get("email")
		account = db.GqlQuery("SELECT * FROM Account WHERE email = :1", email).get()
		if not account or account.status<2:
			self.render_nav("/account/stupid.html", error=1)
		else:
			verify_id = str(uuid.uuid4())
			account.verify_id = verify_id
			account.put()
			message = mail.EmailMessage(sender="ClanSR天狼星戰隊 <SCIIClanSR@gmail.com>",
	                            			subject="Reset Your password")
			message.to = "%s<%s>" % (account.username,email)
			message.html = u"""
				Dear %s:<br>
				<br>
				We were told that you forgot your password. Don't feel embarrass 
				because you are not the first one.<br>
				<br>
				goto the link and reset your password: <a href=https://sciisirius,appspot.com/account/stupid_reset?code=%s>https://sciisirius,appspot.com/account/stupid_reset?code=%s</a><br>
				<br>
				如果有任何問題記得回報我們。<br>
				<br>
				戰隊網編群敬上。
				""" % (account.username,verify_id,verify_id)	
			message.send()
			self.render_nav("/account/stupid_success.html")

class stupid_reset(Handler):
	def get(self):
		code = self.request.get("code")
		self.render_nav("/account/stupid_reset.html", code = code)
	def post(self):
		PASS_RE=re.compile(r"^.{3,20}$")
		code = self.request.get("code")
		password = self.request.get("password")
		verify = self.request.get("verify")
		account = db.GqlQuery("SELECT * FROM Account WHERE verify_id = :1", code).get()
		if account:
			if account.status>2:
				if (PASS_RE.match(password) and  password == verify ):
					account.password=make_pw_hash( account.username,password)
					account.put()
					self.redirect("/account/login")
				else:
					self.render_nav("/account/stupid_reset.html", error=1)
			else:
				self.render_error(403)
		else:
			self.render_error(404)

class notfound(Handler):
	def get(self):
		self.render_error(404)

		

application = webapp2.WSGIApplication([
    (r'/account/signup',signup),
    (r'/account/verify',verify),
    (r'/account/connect',connect),
    (r'/account/login',login),
    (r'/account/logout',logout),
    (r'/account/img',image),
    (r'/account/img_org',image_org),
    (r'/account/img_53',image_53),
    (r'/account/profile',profile),
    (r'/account/img_config',img_config),
    (r'/account/intro_config',intro_config),
    (r'/account/connect_again',connect_again),
    (r'/account/pass_config',pass_config),
    (r'/account/race_config',race_config),
    (r'/account/stupid/',stupid),
    (r'/account/stupid_reset/',stupid_reset),
    (r'/account/.*',notfound),
    
], debug=True)
