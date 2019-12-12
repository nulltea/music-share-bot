
import mongoengine as mdb;
import redis;

db_connection_string = "mongodb://localhost:27017/";
cache_connection_string = "redis://localhost:6379";

mdb.connect("botdb");
cache = redis.from_url(cache_connection_string, db=0)
#Documents

class MusicTrack(Document):
	track_id = mdb.StringField(required=True, unique=True);
	track_urls = mdb.DictField();
	artist = mdb.StringField();
	description = mdb.StringField();
	queue_sort_num = mdb.IntField()
	is_used = mdb.BooleanField(default=False);
	comment = mdb.StringField();
	meta = {
		"indexes" : ["track_id"],
		"ordering": ["-queue_sort_num"],
	}

	def add_link(self, link):
		if "apple" in link:
			if track_id == None: self.track_id = link.split('/')[-2];
			self.track_urls["apple_music"] = link;
		if "spotify" in link:
			self.track_urls["spotify"] = link;
		if "deezer" in link:
			self.track_urls["deezer"] = link;
		if "soundcloud" in link:
			self.track_urls["soundcloud"] = link;
		if "youtube" in link:
			self.track_urls["youtube"] = link;

class MusicLibrary:
	def add_track(self, music_track):
		track_url = music_track.track_urls["apple_music"];
		music_track.track_id = track_url.split('/')[-2];
		music_track.save();

	def edit_track(self, trac, new_data):
		self.music_collection.update_one(query, { "$set": new_data });

	def delete_track(self, args):
		self.music_collection.delete_one({"track_url": args});

	def view_tracks(self):
		return MusicTrack.objects(is_used=False);

	def check_existance(self, query = {}):
		query["is_used"] = False;
		return self.music_collection.count(query) > 0;

	def get_new_track(self, artist = None):
		if not self.check_existance(): return None; 
		track = self.music_collection.find({ "is_used": False })[0];
		self.music_collection.update_one({"track_id": track["track_id"]}, { "$set": { "is_used": True }});
		return track;

	def get_by_artist(self, artist):
		if not self.check_existance({"artist": artist}): return None; 
		track = self.music_collection.find({ "is_used": False, "artist": artist })[0];
		self.music_collection.update_one({"track_id": track["track_id"]}, { "$set": { "is_used": True }});
		return track;

	def get_by_id(self, id):
		return self.music_collection.find({"track_id": id})[0];

	def rate_track(self, track_id, comment):
		self.music_collection.update_one({ "track_id": track_id }, { "$set": {"comment": comment} });

class ChatsInfo:
	database_client = pymongo.MongoClient(db_connection_string)
	bot_database = database_client["botdb"]
	chats_collection = bot_database["chats"]

	def __init__(self):
		super().__init__()

	def upsert_chat(self, data):
		if self.chats_collection.count({"username": data["username"]}) > 0:
			self.chats_collection.update_one({"username": data["username"]}, { "$set": data });
		else: self.chats_collection.insert_one(data["username"]);

	def get_chat_id(self, username):
		return self.chats_collection.find({"username": username})[0]["chat_id"];

	def set_last_track(self, username, last_track_id):
		user = self.chats_collection.find({"username": username})[0];
		user["last_track"] = last_track_id;
		self.upsert_chat(user);

	def get_last_track(self, username):
		user = self.chats_collection.find({"username": username})[0];
		if "last_track" in user: 
			return user["last_track"];
		else: return {"artist": None};