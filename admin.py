# encoding: utf-8
from base import *

class admin(Handler):
	def get(self):
		status = self.get_status()
		self.render_nav("/admin/admin.html", status=STATUS[status])

class list(Handler):
	def get(self):
		status = self.get_status()
		if status>=7:
			accounts =  db.GqlQuery ("SELECT * FROM Account order by status desc")
			self.render_nav("/admin/list.html", accounts = accounts, success=False)
		else:
			self.render_error(403)


	def post(self):
		status = self.get_status()
		if status>=7:
			accounts =  db.GqlQuery ("SELECT * FROM Account")
			for i in accounts:
				key = str(i.key())
				account=db.get(key)
				if self.request.get(key):
					setattr(account, 'status', int(self.request.get(key)))
				account.put()
			time.sleep(1)
			accounts =  db.GqlQuery ("SELECT * FROM Account order by status desc")
			self.render_nav("/admin/list.html", accounts = accounts, success=True)
		else:
			self.render_error(403)
		

class stream(Handler):
	def get(self):
		status = self.get_status()
		if status>=4 :
			streams = db.GqlQuery ("SELECT * FROM Stream")
			self.render_nav("/admin/stream.html", streams = streams)
		else:
			self.render_error(403)

		
	def post(self):
		status = self.get_status()
		if status>=4 :
			twitch_key = self.request.get("twitch_key")
			if not twitch_key:
				twitch_id = self.request.get("twitch_id")
				name = self.request.get("name")
				j = json.loads(urlfetch.fetch("https://api.twitch.tv/kraken/streams/%s" % twitch_id).content)
				chk_id=  Stream.all().filter('twitch_id =', twitch_id).get()
				j = j.get('error',"Good")
				if j=="Good" and name and not chk_id:		
					if not chk_id:
						temp = Stream (name = name , twitch_id = twitch_id)
						temp.put()
						time.sleep(1)
						streams = db.GqlQuery ("SELECT * FROM Stream")
						memcache.delete("online")
						self.render_nav("/admin/stream.html", streams = streams)	
				else:
					streams = db.GqlQuery ("SELECT * FROM Stream")
					self.render_nav("/admin/stream.html", streams = streams, message = "error")
			else:	
				stream = db.get(twitch_key)
				stream.delete()
				time.sleep(1)
				streams = db.GqlQuery ("SELECT * FROM Stream")
				memcache.delete("online")
				self.render_nav("/admin/stream.html", streams = streams, message = "success")
		else:
			self.render_error(403)

		
class new_forum(Handler):
	def get(self):
		status = self.get_status()
		if status>=3 :
			self.render_nav("/admin/forum_new.html")
		else:
			self.render_error(403)
	def post(self):
		status = self.get_status()
		if status>=3 :
			title = self.request.get("title")
			content = self.request.get ("content")
			if title and content:
				content = get_things_clean(content,status)
				cookie=check_secure_val(self.request.cookies.get("ukey" , ""))
				account = db.get(cookie)
				author = account.game_name+"("+account.username+")"
				Forum (title = title, content = content , author = author , author_key=str(account.key())).put()
				self.render_nav ("/admin/forum_success.html")
				memcache.delete("forums")
			else:
				self.render_nav("/admin/forum_new.html",title = title, content=content, error=True)
		else:
			self.render_error(403)


class modify_forum(Handler):
	def get(self):
		cookie = self.request.cookies.get("ukey","")
		cookie = check_secure_val(cookie)
		forum_id = self.request.get("forum_id")
		forum = db.get(forum_id)
		status = self.get_status()
		if forum:
			if forum.author_key == cookie or status==10:
				self.render_nav("/admin/forum_new.html",title = forum.title, content=forum.content, forum_id = forum_id)
			else:
				self.render_error(404)
		else:
			self.render_error(403)


	def post(self):
		status = self.get_status()
		cookie = self.request.cookies.get("ukey","")
		cookie = check_secure_val(cookie)
		forum_id = self.request.get ("forum_id")
		forum = db.get(forum_id)
		if (forum.author_key == cookie and status >=3) or status==10:
			title = self.request.get("title")
			content = self.request.get ("content")
			delete = self.request.get("delete")
			if delete:
				forum.delete()
				self.render_nav ("/admin/forum_success.html")
			else:
				if title and content:
					content = get_things_clean(content,status)
					setattr(forum, 'content', content)
					setattr(forum, 'title', title)
					forum.put()
					memcache.delete("forum_%s" % db.Key(forum_id).id())
					self.render_nav ("/admin/forum_success.html")
				else:
					self.render_nav("/admin/forum_new.html",title = title, content=content, error=True)	
		else:
			self.render_error(403)


class new_stra(Handler):
	def get(self):
		status = self.get_status()
		if status>=3 :
			upload_url = blobstore.create_upload_url('/admin/stra/upload',max_bytes_per_blob=8388608)
			self.render_nav("/admin/stra_new.html",upload_url = upload_url)
		else:
			self.render_error(403)

class upload_stra(Handler,blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		status = self.get_status()
		if status>=3 :
			title = self.request.get("title")
			content = self.request.get ("content")
			if title and content:
				stra_id = self.request.get("stra_id")
				if not stra_id:
					upload_files = self.get_uploads('file')
					filename=[]
					hidden_filename=[]
					file_key=[]
					for i in range(0,len(upload_files)):
						afilename=self.request.get ("filename%d"%i)
						ahidden_filename=self.request.get ("hidden_filename%d"%i)
						if afilename:
							filename.append(afilename)
						else:
							filename.append(ahidden_filename)
						hidden_filename.append(self.request.get ("hidden_filename%d"%i))
						blob_info = upload_files[i]
						file_key.append(str(blob_info.key()))
					content = get_things_clean(content,status)
					cookie=check_secure_val(self.request.cookies.get("ukey" , ""))
					account = db.get(cookie)
					author = account.game_name+"("+account.username+")"
					Stra (title = title, content = content , author = author , author_key=str(account.key()),
						  upload_files_displayname = filename, upload_files_name = hidden_filename,
						   upload_files_key = file_key).put()
					self.render_nav ("/admin/stra_success.html")
					memcache.delete("stras")
				else:
					delete = self.request.get("delete")
					cookie = self.request.cookies.get("ukey","")
					cookie = check_secure_val(cookie)
					stra = db.get(stra_id)
					if stra.author_key == cookie or status==10:
						if delete:
							for i in stra.upload_files_key:
								blobstore.delete(i)
							stra.delete()
							self.render_nav ("/admin/stra_success.html")
						else:
							if title and content:
								content = get_things_clean(content,status)
								setattr(stra, 'content', content)
								setattr(stra, 'title', title)
								upload_files = self.get_uploads('file')
								del_blob_index=[]
								for i in range(0,len(stra.upload_files_key)):
									blob_key = self.request.get("del_blob%d" % i)
									if blob_key:
										blobstore.delete(blob_key)
										del_blob_index.append(i)
								stra.upload_files_key = [i for j, i in enumerate(stra.upload_files_key) if j not in del_blob_index]
								stra.upload_files_name = [i for j, i in enumerate(stra.upload_files_name) if j not in del_blob_index]
								stra.upload_files_displayname = [i for j, i in enumerate(stra.upload_files_displayname) if j not in del_blob_index]
								upload_files = self.get_uploads('file')
								for i in range(0,len(upload_files)):
									afilename=self.request.get ("filename%d"%i)
									ahidden_filename=self.request.get ("hidden_filename%d"%i)
									if afilename:
										stra.upload_files_dispalyname.append(afilename)
									else:
										stra.upload_files_displayname.append(ahidden_filename)
									stra.upload_files_name.append(self.request.get ("hidden_filename%d"%i))
									blob_info = upload_files[i]
									stra.upload_files_key.append(str(blob_info.key()))
								stra.put()
								memcache.delete("stra_%s" % db.Key(stra_id).id())
								self.render_nav ("/admin/stra_success.html")
							else:
								upload_url = blobstore.create_upload_url('/admin/stra/upload',max_bytes_per_blob=8388608)
								self.render_nav("/admin/stra_new.html",title = title, content=content, error=True, upload_files=stra.upload_files, upload_url  = upload_url)	
					else:
						render_error(403)
			else:
				upload_url = blobstore.create_upload_url('/admin/stra/upload',max_bytes_per_blob=8388608)
				self.render_nav("/admin/stra_new.html",title = title, content=content, error=True, upload_url  = upload_url)	
		else:
			self.render_error(403)


class modify_stra(Handler):
	def get(self):
		cookie = self.request.cookies.get("ukey","")
		cookie = check_secure_val(cookie)
		stra_id = self.request.get("stra_id")
		status = self.get_status()
		stra = db.get(stra_id)
		if stra:
			if stra.author_key == cookie or status==10:
				upload_url = blobstore.create_upload_url('/admin/stra/upload',max_bytes_per_blob=8388608)
				self.render_nav("/admin/stra_new.html",title = stra.title, content=stra.content,
					upload_files_key=stra.upload_files_key,upload_files_name=stra.upload_files_name,upload_files_displayname=stra.upload_files_displayname,
					 stra_id = stra_id, upload_url = upload_url)
			else:
				self.render_error(403)
		else:
			self.render_error(403)


class new_announce(Handler):
	def get(self):
		status = self.get_status()
		if status>=4 :
			self.render_nav("/admin/announce_new.html")
		else:
			self.render_error(403)
	def post(self):
		status = self.get_status()
		if status>=4 :
			title = self.request.get("title")
			content = self.request.get ("content")
			if title and content:
				content = get_things_clean(content,status)
				Announce (title = title, content = content).put()
				self.render_nav ("/admin/announce_success.html")
				memcache.delete("announces")
			else:
				self.render_nav("/admin/announce_new.html",title = title, content=content, error=True)
		else:
			self.render_error(403)
		

class announce(Handler):
	def get(self):
		status = self.get_status()
		if status>=4 :
			page = self.request.get ("page")
			if page:
				announces = Announce.all()
				announces.order("-create")
				count=0
				for i in announces:
					count+=1
				count = (count/10)+1
				self.render_nav ("/admin/announce.html", announces = announces, page = int (page) , count = count)
			else:
				self.render_error(404)
		else:
			self.render_error(403)

class modify_announce(Handler):
	def get(self):
		status = self.get_status()
		if status>=4 :
			ann_id = self.request.get("ann_id")
			announce = db.get(ann_id)
			if announce:
				self.render_nav("/admin/announce_new.html",title = announce.title, content=announce.content, ann_id = ann_id)
			else:
				self.render_error(404)
		else:
			self.render_error(403)


	def post(self):
		status = self.get_status()
		if status>=4 :
			title = self.request.get("title")
			content = self.request.get ("content")
			ann_id = self.request.get ("ann_id")
			if title and content:
				content = get_things_clean(content,status)
				announce = db.get(ann_id)
				setattr(announce, 'content', content)
				setattr(announce, 'title', title)
				announce.put()
				self.render_nav ("/admin/announce_success.html")
			else:
				self.render_nav("/admin/announce_new.html",title = title, content=content, error=True)
		else:
			self.render_error(403)

class notfound(Handler):
	def get(self):
		self.render_error(404)



class new_event(Handler):
	def get(self):
		status = self.get_status()
		if status>6:
			self.render_nav("/admin/event_new.html", event_map=u"第一張圖               之後敗方選圖 圖庫是當賽季天梯圖 可重複選圖 不可連續同圖")
		else:
			self.render_error(403)
	def post(self):
		status = self.get_status()
		if status>=6 :
			opponent = self.request.get("opponent")
			date = self.request.get ("date")
			time = self.request.get("time")
			style = self.request.get("style")
			channel = self.request.get ("channel")
			event_map = self.request.get("event_map") 
			other= self.request.get("other")
			rank = self.request.get("rank")
			TIME_RE=re.compile(r"^[0-2]{1}[0-9]{1}\:[0-6]{1}[0-9]{1}$")
			DATE_RE=re.compile(r"^20[0-9]{2}-[0-1]{1}[0-9]{1}-[0-3]{1}[0-9]{1}$")
			other = get_things_clean(other,status)
			if DATE_RE.match(date) and TIME_RE.match(time) and opponent and style and event_map and rank:
				Event (opponent = opponent, date = date , time = time , style=style , channel=channel, event_map = event_map, rank = rank, other = other).put()
				self.render_nav ("/admin/event_success.html")
			else:
				self.render_nav("/admin/event_new.html",opponent = opponent, date = date , time = time , style=style , rank = rank,
										channel=channel, event_map = event_map, other = other , error = True)
		else:
			self.render_error(403)



class modify_event(Handler):
	def get(self):
		status = self.get_status()
		if status>=6 :
			event_id = self.request.get("event_id")
			event = Event.get_by_id(long(event_id))
			if event:
				self.render_nav("/admin/event_new.html",opponent = event.opponent, date = event.date , time = event.time , style=event.style , rank = event.rank,event_id = event_id,
										channel=event.channel, event_map = event.event_map, other = event.other , regp=event.regp,error = False)
			else:
				self.render_error(404)
		else:
			self.render_error(403)

	def post(self):
		status = self.get_status()
		if status>=6 :
			opponent = self.request.get("opponent")
			date = self.request.get ("date")
			time = self.request.get("time")
			style = self.request.get("style")
			channel = self.request.get ("channel")
			event_map = self.request.get("event_map") 
			other= self.request.get("other")
			rank = self.request.get("rank")
			event_id = self.request.get("event_id")
			a1,a2,a3,a4,a5 = self.request.get("a1"),self.request.get("a2"),self.request.get("a3"),self.request.get("a4"),self.request.get("a5")
			b1,b2,b3 = self.request.get("b1"),self.request.get("b2"),self.request.get("b3"),
			TIME_RE=re.compile(r"^[0-2]{1}[0-9]{1}\:[0-6]{1}[0-9]{1}$")
			DATE_RE=re.compile(r"^20[0-9]{2}-[0-1]{1}[0-9]{1}-[0-3]{1}[0-9]{1}$")
			other = get_things_clean(other,status)
			if DATE_RE.match(date) and TIME_RE.match(time) and opponent and style and event_map and rank:
				event = Event.get_by_id(long(event_id))
				setattr(event, 'opponent', opponent)
				setattr(event, 'date', date)
				setattr(event, 'time', time)
				setattr(event, 'style', style)
				setattr(event, 'channel', channel)
				setattr(event, 'event_map', event_map)
				setattr(event, 'other', other)
				setattr(event, 'rank', rank)
				s1 = '1.'+a1+' 2.'+a2+' 3.'+a3+' 4.'+a4+' 5.'+a5
				s2 = '1.'+b1+' 2.'+b2+' 3.'+b3
				setattr(event, 'a', s1)
				setattr(event, 'b', s2)
				event.put()
				self.render_nav ("/admin/event_success.html")
			else:
				self.render_nav("/admin/event_new.html",opponent = opponent, date = date , time = time , style=style , rank = rank, regp=event.regp,
										event_id = event_id,channel=channel, event_map = event_map, other = other , error = True)
		else:
			self.render_error(403)

class score_event(Handler):
	def get(self):
		status = self.get_status()
		if status>=4 :
			event_id = self.request.get("event_id")
			event = Event.get_by_id(long(event_id))
			if event and event.finished==False:
				self.render_nav("/admin/event_score.html", event = event, event_id = event_id)
			elif event.finished==True:
				self.render_error(403)
			else:
				self.render_error(404)
		else:
			self.render_error(403)

	def post(self):
		status = self.get_status()
		if status>=4:
			detail_score=""
			player={}
			s1=0
			s2=0
			flag = False
			for i in range(1,10):
				p1 = self.request.get("%sp1" % str(i))
				if p1!="None":
					flag = True
					detail_score+=p1
					win = self.request.get("win%s" % str(i))
					p2 = self.request.get("%sp2" % str(i))
					if win=='0':
						player.setdefault(p1,[p1,0,0])
						player[p1][1]+=1
						detail_score+=' > '+p2
						s1+=1
					else:
						player.setdefault(p1,[p1,0,0])
						player[p1][2]+=1
						detail_score+=' < '+p2
						s2+=1
					race = self.request.get("race%s" % str(i))
					detail_score+=' '+race+'<br>'
			if flag:
				for i in player:
					accounts = Account.all()
					single = accounts.filter("game_name =",player[i][0]).get()
					single.win+=player[i][1]
					single.loss+=player[i][2]
					single.put()
			event_id = self.request.get("event_id")
			event = Event.get_by_id(int(event_id))
			event.detail_score = detail_score
			event.score = str(s1)+':'+str(s2)
			event.finished = True
			event.put()
			self.render_nav("/admin/event_score_success.html")
		else:
			self.render_error(403)

class slide(Handler):
	def get(self):
		status = self.get_status()
		if status>=4 :
			temp=[]
			slides = Slide.all()
			index = 0
			for i in slides:
				index = i.index
				temp = i.url
			self.render_nav("/admin/slide.html" , slides = temp , index = index)
		else:
			self.render_error(403)
	def post(self):
		status = self.get_status()
		if status>=4 :
			slide_index = self.request.get("slide_index")	
			if not slide_index:
				url = self.request.get("url")
				index = self.request.get("index")
				if index=="":
					index=0
				slides = Slide.all()
				cnt = 0
				for i in slides:
					cnt+=1
				temp=[]
				if cnt==1:
					for i in slides:
						temp=i.url
						i.index = int(index)
						if url != "":
							i.url.append(url)
						i.put()
				else:
					Slide(url=[url]).put()
			else:
				slides = Slide.all()
				for i in slides:
					temp=i.url
					index = i.index
					del i.url[int(slide_index)]
					i.put()
			time.sleep(2)
			self.render_nav("/admin/slide.html", success = True ,slides = temp, index= index)
			memcache.delete("slides")
		else:
			self.render_error(403)

class ServeHandler(Handler,blobstore_handlers.BlobstoreDownloadHandler):
	def get(self, blob_key):
		blob_key = str(urllib.unquote(blob_key))
		name=self.request.get("name")
		if not blobstore.get(blob_key):
			self.render_error(404)
		else:
			self.send_blob(blobstore.BlobInfo.get(blob_key), save_as=name)

application = webapp2.WSGIApplication([
    (r'/admin/',admin),
    (r'/admin/list',list),
    (r'/admin/stream',stream),
    (r'/admin/event/new',new_event),
    (r'/admin/event/score',score_event),
    (r'/admin/announce',announce),
    (r'/admin/event/modify',modify_event),
    (r'/admin/announce/modify',modify_announce),
    (r'/admin/forum/modify',modify_forum),
    (r'/admin/forum/new',new_forum),
    (r'/admin/stra/modify',modify_stra),
    (r'/admin/stra/new',new_stra),
    (r'/admin/stra/upload',upload_stra),
    (r'/admin/serve/([^/]+)?', ServeHandler),
    (r'/admin/announce/new',new_announce),
    (r'/admin/slide',slide),
    (r'/admin/.*',notfound)
], debug=True)
