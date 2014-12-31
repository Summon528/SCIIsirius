# encoding: utf-8
from base import *

def get_slide():
	slides = memcache.get("slides")
	if not slides:
		temp=[]
		index=0
		slides = Slide.all()
		for i in slides:
			temp=i.url
			index=i.index

		memcache.set("slides",(temp,index))
		return (temp,index)
	return slides

def get_stream():
	topfive = memcache.get("topfive")
	online = memcache.get("online")
	offline = memcache.get("offline")
	refresh_stream = memcache.get("refresh_stream")
	if not (topfive and online and offline ):

		stream = db.GqlQuery("SELECT * FROM Stream")
		online = []
		offline = []
		topfive = []
		now=0
		for i in stream:
			j = json.loads(urllib2.urlopen("https://api.twitch.tv/kraken/streams/%s" % i.twitch_id).read())
			if j['stream']:
				online.append(i)
				if j['stream']['channel']['logo'] != None:
					online[now].img = j['stream']['channel']['logo']
				else:
					online[now].img = "/picture/stream.png"
				now+=1
			else:
				offline.append(i)
		j = json.loads(urlfetch.fetch('https://api.twitch.tv/kraken/search/streams?limit=5&q="StarCraft+II:+Heart+of+the+Swarm"').content)
		for i in range(0,len(j['streams'])): 
			if j['streams'][i]['channel']['logo']:
				img =j['streams'][i]['channel']['logo']
			else:
				 img = "/picture/stream.png"
			topfive.append(Stream(name=j['streams'][i]['channel']['name'],
								  img = img,
								  twitch_id = j['streams'][i]['channel']['name']))

		refresh_stream = datetime.datetime.now() + timedelta(hours = 8)
		memcache.set(key="refresh_stream", value=refresh_stream, time=300)
		memcache.set(key="topfive", value=topfive, time=300)
		memcache.set(key="online", value=online, time=300)
		memcache.set(key="offline", value=offline, time=300)
	return (online,offline,topfive,refresh_stream)


def get_ladder(must = False):
	account = memcache.get("ladder")
	refresh_ladder = memcache.get("refresh_ladder")
	ladders_race={"ZERG":0,
				"PROTOSS":0,
				"TERRAN":0,
				"RANDOM":0,
				}
	ladders_rank=[0,0,0,0,0,0,0,0]
	if not account or must:
		accounts = db.GqlQuery("SELECT * FROM Account")
		account=[]
		for k in accounts:
			temp=[]
			if k.status>=3:
				j = json.loads(urlfetch.fetch(LADDERS_URL % (k.game_id,k.game_name)).content)
				if "currentSeason" in j:
					if j['currentSeason'] != [] :
						for i in j['currentSeason']:
							if i['ladder']!=[]:
								if i['ladder'][0]['matchMakingQueue'] == "HOTS_SOLO":
									account.append((k.username,k.game_name,
													RANK[i['ladder'][0]['league']],i['ladder'][0]['rank'],i['ladder'][0]['wins'],
													i['ladder'][0]['losses']*-1,RANKTW[i['ladder'][0]['league']],RACE[k.race]))
									ladders_rank[RANK[i['ladder'][0]['league']]]+=1
									ladders_race[k.race]+=1
									break
						else:
							account.append((k.username,k.game_name,0,None,0,0,u"無階",RACE[k.race]))
							ladders_rank[0]+=1
							ladders_race[k.race]+=1
					else:
						account.append((k.username,k.game_name,0,None,0,0,u"無階",RACE[k.race]))
						ladders_rank[0]+=1
						ladders_race[k.race]+=1
				else:
					account.append((k.username,k.game_name,-1,None,0,0,u"錯誤",RACE[k.race]))
					ladders_rank[0]+=1
					ladders_race[k.race]+=1
		account.sort(reverse=True, key=itemgetter(2,4,5)) 
		refresh_ladder = datetime.datetime.now() + timedelta(hours = 8)
		ladder=[account,ladders_rank,ladders_race]
		memcache.set(key="refresh_ladder", value=refresh_ladder, time=1900)		
		memcache.set(key="ladder", value=ladder,time = 1900)
	return (account,refresh_ladder)

def get_announce():
	announces = memcache.get("announces")
	if not announces:
		announces = db.GqlQuery ("SELECT * FROM Announce order by create desc limit 5")
		memcache.set("announces",announces)
	return announces

def get_event():
	events = memcache.get("events")
	now = datetime.datetime.now()
	now += timedelta(hours = 8)
	gap = 1
	if memcache.get("events_refresh"):
		gap = (now - memcache.get("events_refresh") ).days
	if not events or gap!=0:
		events = Event.all()
		today = str(now.year)+'-'+str(now.month)+'-'+str(now.day)
		events = events.filter("date >=", today)
		events.order("date")
		memcache.set("events",events)
		memcache.set("events_refresh",now)
	return events


def get_forum_one(forum_id):
	forum = memcache.get("forum_%s" % forum_id)
	if not forum:
		forum = Forum.get_by_id(long(forum_id))
		memcache.set("forum_%s" % forum_id, forum)
	return forum

def get_stra_one(stra_id):
	stra = memcache.get("stra_%s" % stra_id)
	if not stra:
		stra = Stra.get_by_id(long(stra_id))
		memcache.set("stra_%s" % stra_id, stra)
	return stra

class index(Handler):

	def get(self):
		now = datetime.datetime.now()
		now += timedelta(hours = 8)
		announces = get_announce()
		events = get_event()
		(slides,index) = get_slide() 
		deferred.defer(get_ladder)
		self.render_nav ("index.html", announces = announces, events = events , slides = slides,index = index)

		

class announce(Handler):
	def get(self):
		ann_id = self.request.get ("ann_id")
		page = self.request.get ("page")
		if ann_id:
			announce = Announce.get_by_id(long(ann_id))
			self.render_nav("announce_show.html", announce=announce)
		elif page:
			announces = Announce.all()
			announces.order("-create")
			count=0
			for i in announces:
				count+=1
			count = ((count-1)/10)+1
			announce = []
			for i in announces.run(offset=(int(page)-1)*10,limit = 10):
				temp=[]
				temp.append(i.title)
				temp.append((i.create+ timedelta(hours = 8)).strftime("%Y-%m-%d %H:%M"))
				temp.append((i.modify+ timedelta(hours = 8)).strftime("%Y-%m-%d %H:%M"))
				temp.append(i.key().id())
				temp.append(i.key())
				announce.append(temp)
			self.render_nav ("announce.html", announce = announce, page = int (page) , count = count)
		else:
			self.redirect("/announce?page=1")



class forum(Handler):
	def get(self):
		forum_id = self.request.get ("forum_id")
		page = self.request.get ("page")
		if forum_id:
			forum = get_forum_one(forum_id)
			self.render_nav("forum_show.html", forum=forum)
		elif page:
			forums = Forum.all()
			forums.order("-modify")
			count=0
			for i in forums:
				count+=1
			count = ((count-1)/10)+1
			forum = []
			for i in forums.run(offset=(int(page)-1)*10,limit = 10):
				temp=[]
				temp.append(i.title)
				temp.append((i.create+ timedelta(hours = 8)).strftime("%Y-%m-%d %H:%M"))
				temp.append((i.modify+ timedelta(hours = 8)).strftime("%Y-%m-%d %H:%M"))
				temp.append(i.key().id())
				temp.append(i.key())
				temp.append(i.author)
				forum.append(temp)
			self.render_nav ("forum.html", forum = forum, page = int (page) , count = count)
		else:
			self.redirect("/forum?page=1")

	def post(self):
		if self.get_status()>=3:
			forum_key = self.request.get("forum_key")
			forum = db.get(forum_key)
			if forum:
				cookie = self.request.cookies.get("ukey","")
				cookie = check_secure_val(cookie)
				account=db.get(cookie)
				author = account.game_name+"("+account.username+")"
				message = self.request.get("message")
				flag=True
				for i in message:
					if i!="　" and not i.isspace():
						flag=False
						break
				if len(message)>50:
					self.render_nav("forum_show.html", forum=forum,message=message, error=1)
				elif message==""  or flag:
					self.render_nav("forum_show.html", forum=forum, error=2)
				else:
					message = message.replace(' ',"%[$s-p-a-c-e$]%")
					message = cgi.escape (message)
					message = message.replace("%[$s-p-a-c-e$]%","&nbsp")
					forum.message.append(message)
					forum.message_author.append(author)
					forum.message_time.append(datetime.datetime.now() + timedelta(hours = 8))
					forum.message_img.append(str(account.key()))
					forum.message_style.append(int(self.request.get("style")))
					forum.put()
					memcache.delete("forum_%s" %  str(forum.key().id()))
					self.redirect("/forum?forum_id=%s" % str(forum.key().id()))
			else:
				self.render_error(404)
		else:
			self.render_error(403)

class stra(Handler):
	def get(self):
		stra_id = self.request.get ("stra_id")
		page = self.request.get ("page")
		if stra_id:
			stra = get_stra_one(stra_id)
			self.render_nav("stra_show.html", stra=stra)
		elif page:
			stras = Stra.all()
			stras.order("-modify")
			count=0
			for i in stras:
				count+=1
			count = ((count-1)/10)+1
			stra = []
			for i in stras.run(offset=(int(page)-1)*10,limit = 10):
				temp=[]
				temp.append(i.title)
				temp.append((i.create+ timedelta(hours = 8)).strftime("%Y-%m-%d %H:%M"))
				temp.append((i.modify+ timedelta(hours = 8)).strftime("%Y-%m-%d %H:%M"))
				temp.append(i.key().id())
				temp.append(i.key())
				temp.append(i.author)
				stra.append(temp)
			self.render_nav ("stra.html", stra = stra, page = int (page) , count = count)
		else:
			self.redirect("/stra?page=1")

	def post(self):
		if self.get_status()>=3:
			stra_key = self.request.get("stra_key")
			stra = db.get(stra_key)
			if stra:
				cookie = self.request.cookies.get("ukey","")
				cookie = check_secure_val(cookie)
				account=db.get(cookie)
				author = account.game_name+"("+account.username+")"
				message = self.request.get("message")
				flag=True
				for i in message:
					if i!="　" and not i.isspace():
						flag=False
						break
				if len(message)>50:
					self.render_nav("stra_show.html", stra=stra,message=message, error=1)
				elif message==""  or flag:
					self.render_nav("stra_show.html", stra=stra, error=2)
				else:
					message = message.replace(' ',"%[$s-p-a-c-e$]%")
					message = cgi.escape (message)
					message = message.replace("%[$s-p-a-c-e$]%","&nbsp")
					stra.message.append(message)
					stra.message_author.append(author)
					stra.message_time.append(datetime.datetime.now() + timedelta(hours = 8))
					stra.message_img.append(str(account.key()))
					stra.message_style.append(int(self.request.get("style")))
					stra.put()
					memcache.delete("stra_%s" %  str(stra.key().id()))
					self.redirect("/stra?stra_id=%s" % str(stra.key().id()))
			else:
				self.render_error(404)
		else:
			self.render_error(403)


class event(Handler):
	def get(self):
		events = Event.all()
		events.filter("date >=", (datetime.datetime.now()+ timedelta(hours = 8)-timedelta(days = 7)).strftime("%Y-%m-%d"))
		events.order("date")
		self.render_nav ("event.html", events = events)




class list(Handler):
	def get(self):
		accounts =  db.GqlQuery ("SELECT * FROM Account order by status desc")
		self.render_nav("list.html", accounts = accounts)

class stream(Handler):
	def get(self):
		stream_id =  self.request.get("stream_id","clansr")
		(online,offline,topfive,refresh_stream) = get_stream()
		j = json.loads(urlfetch.fetch('https://api.twitch.tv/kraken/streams/%s' % stream_id).content)
		if j['stream']:
			title = j['stream']['channel']['status']
		else:
			title = "This Channel is offline"

		self.render_nav ("stream.html", stream_id=stream_id, online=online, refresh_stream = refresh_stream,
										offline=offline, topfive = topfive, title=title)

class calendar(Handler):
	def get(self):
		events = Event.all()
		self.render_nav("calendar.html" , events = events)


class event_show(Handler):
	def get(self):
		event_id = self.request.get ("event_id")
		if event_id:
			cookie = self.request.cookies.get("ukey","")
			if check_secure_val(cookie) :
				ukey =  cookie.split('|')[0]
				ukey = db.Key(ukey)
				account =  db.get(ukey)
				if  account.status>=3:
					event = Event.get_by_id(long(event_id))
					self.render_nav("event_show.html", event = event,  account = account ,member = True)
				else:
					event = Event.get_by_id(long(event_id))
					self.render_nav("event_show.html", event = event, member = False)
			else:
				event = Event.get_by_id(long(event_id))
				self.render_nav("event_show.html", event = event, member = False)

		else:
			self.render_error(404)

	def post(self):
		cookie = self.request.cookies.get("ukey","")
		ukey = check_secure_val(cookie)
		if ukey:
			account=db.get(ukey)
			if account.status>=3:
				key = self.request.get("key")
				event = db.get(key)
				num=self.request.get("num")
				race=self.request.get("race")
				other=self.request.get("other")
				if not account.username in event.regn:
					s = account.game_name+'|'+num+'|'+race+'|'+other
					event.regn.append(account.username)
					event.regp.append(s)
					event.put()
					self.render_nav("event_reg_success.html")
				else:
					for i in event.regp:
						if i.split('|')[0]==account.game_name:
							event.regp[event.regp.index(i)]='|'+account.game_name+u"|取消報名"
					event.regn.remove(account.username)
					event.put()
					self.render_nav("event_reg_success.html")
			else:
				self.render_error(403)
		else:
			self.render_error(403)

class rank(Handler):
	def get(self):
		accounts = db.GqlQuery("SELECT * FROM Account where win!=0 order by win desc ")
		account=[]
		for i in accounts:
			temp=[]
			temp.append(i.game_name)
			temp.append(i.username)
			temp.append(i.win)
			temp.append(i.loss)
			temp.append(str(round((i.win/float(i.loss+i.win))*100,2))+'%')
			temp.append(RACE[i.race])
			account.append(temp)
		self.render_nav("rank.html", account = account)

class ladder_rank(Handler):
	def get(self):
		go = self.request.get("p")
		if go=="bot":
			get_ladder(True)
		if memcache.get("ladder") or go=="go":
			(ladder,refresh_ladder)=get_ladder()
			self.render_nav("ladder_rank.html", ladder = ladder, refresh_ladder=refresh_ladder)
		else:
			self.render_nav("ladder_rank_loading.html")
		

class about(Handler):
	def get(self):
		p=self.request.get("p")
		if p=="success":
			self.render_nav("about.html", success=True)
		else:
			self.render_nav("about.html")
	def post(self):
		cookie=self.request.cookies.get("ukey" ,None)
		cookie=check_secure_val(cookie)
		if cookie:
			user = db.get(cookie)
			email=user.email
			name=user.username+'_'+user.game_name
		else:
			email=email=self.request.get("email")
			name="Guest"
		title=self.request.get("title")
		content=self.request.get("content")
		message = mail.EmailMessage(sender="%s <sciiclansr@gmail.com>" % (name),
                        			subject="%s" %(title)) 
		message.to = u"ClanSR天狼星戰 <sciiclansr@gmail.com>"
		message.html = u'來自：<a href="mailto:%s">%s</a><br>%s' % (email,email,content)
		message.send()
		self.redirect("/about?p=success")


class joinus_form(Handler):
	"""docstring for joinus_form"""
	def get(self):
		self.render_nav("joinus_form.html")

class joinus(Handler):
	"""docstring for joinus"""
	def get(self):
		self.render_nav("joinus.html")
		

class notfound(Handler):
	def get(self):
		self.render_error(404)



application = webapp2.WSGIApplication([
    ('/',index),
    ('/calendar',calendar),
    ('/announce',announce),
    ('/event_show',event_show),
    ('/list',list),
    ('/stream',stream),
    ('/rank',rank),
    ('/ladder_rank',ladder_rank),
    ('/event',event),
    ('/about',about),
    ('/forum',forum),
    ('/stra',stra),
    ('/joinus_form',joinus_form),
    ('/joinus',joinus),
    ('/.*',notfound)
], debug=True)