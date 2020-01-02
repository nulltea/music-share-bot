
import os;
import urllib.request;

import mongoengine as mdb;
import redis;

import spotify;

cache_connection_string = "redis://localhost:6379";

mdb.connect(db='music-share-bot-db', host='mongodb+srv://admin:admin@cluster0-qvq1p.azure.mongodb.net/music-share-bot-db?retryWrites=true&w=majority');
cache = redis.from_url(cache_connection_string, db=0)


class MusicTrack(mdb.Document):
	track_id = mdb.StringField(required=True, unique=True);
	track_urls = mdb.DictField();
	main_artist = mdb.StringField();
	artists = mdb.ListField();
	album = mdb.StringField();
	genres = mdb.ListField();
	cover_image = mdb.ImageField();
	description = mdb.StringField();
	queue_sort_num = mdb.IntField()
	is_used = mdb.BooleanField(default=False);
	comment = mdb.StringField();
	meta = {
		"indexes": ["track_id"],
		"ordering": ["-queue_sort_num"],
	}

	def add_link(self, link):
		query = link;
		if "apple" in link:
			if self.track_id is None:
				query = self.track_id = link.split('/')[-2];
			self.track_urls["apple_music"] = link;
		elif "spotify" in link:
			query = self.track_urls["spotify"] = link;
		elif "deezer" in link:
			self.track_urls["deezer"] = link;
		elif "soundcloud" in link:
			self.track_urls["soundcloud"] = link;
		elif "youtube" in link:
			self.track_urls["youtube"] = link;

		if len(self.track_urls) <= 1:
			try:
				self.set_track_info(query);
			except:
				pass;

	def set_track_info(self, track_id):
		track_info = spotify.query_track_info(track_id);
		self.track_id = track_info["track_id"];
		self.album = track_info["album"];
		self.main_artist = track_info["artists"][0];
		self.artists = track_info["artists"];
		self.genres = track_info["genres"];
		urllib.request.urlretrieve(track_info["cover_url"], "tmp.png");
		with open("tmp.png", "rb") as img:
			self.cover_image.put(img);
		os.remove("tmp.png");

	def generate_message(self):
		artists = ", ".join(self.artists);
		genres = ", ".join(self.genres);
		description = "-" if self.description is None or self.description == "" else self.description;
		msgs = [f"Track Id: *{self.track_id}*",
		f"Artists: *{artists}*",
		f"Album: *{self.album}*",
		f"Genres: *{genres}*",
		f"Discription: *{description}*"];
		return "\n".join(msgs);


class ChatsInfo:
	def __init__(self):
		super().__init__()

	def upsert_chat(self, data):
		pass;

	def get_chat_id(self, username):
		pass;

	def set_last_track(self, username, last_track_id):
		pass;

	def get_last_track(self, username):
		pass;
