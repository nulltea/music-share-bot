import os
import urllib.request

import mongoengine as mdb
import redis
import telebot

from music_api import *;
from config import *

mdb_db = config["mongodb"]["db"];
mdb_login = config["mongodb"]["login"];
mdb_password = config["mongodb"]["password"];
mdb_host = f"mongodb+srv://{mdb_login}:{mdb_password}@cluster0-qvq1p.azure.mongodb.net/{mdb_db}?retryWrites=true&w=majority";
mdb.connect(db=mdb_db, host=mdb_host);
cache = redis.StrictRedis(host='localhost', port=6379, db=1)


class BotUser(mdb.Document):
	username = mdb.StringField(required=True, unique=True);
	chat_id = mdb.IntField(required=True, unique=True);
	first_name = mdb.StringField();
	last_name = mdb.StringField();
	profile_picture = mdb.ImageField();
	bio = mdb.StringField();
	genres = mdb.ListField();
	queue_sort_num = mdb.IntField()
	meta = {
		"indexes": ["username", "chat_id"],
		"ordering": ["-queue_sort_num"],
	}

	def __str__(self):
		return f"{self.first_name} {self.last_name}";

	def set_profile_info(self, message):
		profile_photos = telebot.apihelper.get_user_profile_photos(TOKEN, message.from_user.id);
		file_id = profile_photos['photos'][0][2]['file_id'];
		img_path = telebot.apihelper.get_file(TOKEN, file_id)["file_path"];
		img_url = f"https://api.telegram.org/file/bot{TOKEN}/{img_path}";
		urllib.request.urlretrieve(img_url, "tmp.png");
		with open("tmp.png", "rb") as img:
			self.profile_picture.put(img);
		os.remove("tmp.png");

	def generate_message(self):
		bio = "-" if self.bio is None or self.bio == "" else self.bio;
		preferences = "-" if self.genres is None or not any(self.genres) else ", ".join(self.genres);
		msgs = [f"Username: *{self.username}*",
		f"Full name: *{self.first_name} {self.last_name}*",
		f"Bio: *{bio}*",
		f"Music preferences: *{preferences}*"];
		return "\n".join(msgs);

	def get_edit_menu(self):
		menu = telebot.types.InlineKeyboardMarkup();
		firstname_button = telebot.types.InlineKeyboardButton(text="Change first name", callback_data=f"profile/firstname/{self.pk}");
		lastname_button = telebot.types.InlineKeyboardButton(text="Change last name", callback_data=f"profile/lastname/{self.pk}");
		bio_button = telebot.types.InlineKeyboardButton(text="Fill bio (optional)", callback_data=f"profile/bio/{self.pk}");
		preferences_button = telebot.types.InlineKeyboardButton(text="Set music preferences", callback_data=f"profile/genres/choose/{self.pk}");
		save_button = telebot.types.InlineKeyboardButton(text="Finish editing/checking", callback_data=f"profile/save/ask/{self.pk}");
		menu.row(firstname_button, lastname_button);
		menu.row(bio_button, preferences_button);
		menu.row(save_button);
		return menu;


class MusicTrack(mdb.Document):
	track_id = mdb.StringField(required=True, unique=True);
	track_urls = mdb.DictField();
	main_artist = mdb.StringField();
	artists = mdb.ListField();
	album = mdb.StringField();
	genres = mdb.ListField();
	cover_image = mdb.ImageField();
	description = mdb.StringField();
	publisher = mdb.ReferenceField(BotUser);
	queue_sort_num = mdb.IntField()
	available = mdb.BooleanField(default=False);
	seen_by = mdb.ListField();
	comments = mdb.DictField();
	likes = mdb.ListField();
	dislikes = mdb.ListField();
	meta = {
		"indexes": ["track_id"],
		"ordering": ["-queue_sort_num"],
	}

	def add_link(self, link):
		is_set_info = len(self.track_urls) <= 1;
		if "apple" in link:
			self.track_urls["Apple Music"] = link;
			if self.track_id is None:
				self.track_id = link.split('/')[-2];
			if is_set_info:
				track_info = Spotify.query_track_info(self.track_id);
		elif "spotify" in link:
			query = self.track_urls["Spotify"] = link;
			if is_set_info:
				track_info = Spotify.query_track_info(link);
		elif "deezer" in link:
			self.track_urls["Deezer"] = link;
			if is_set_info:
				track_info = Deezer.query_track_info(link);
		elif "soundcloud" in link:
			self.track_urls["SoundCloud"] = link;
			# if self.track_id is None:
			# 	self.track_id = link.split('/')[-1];
			if is_set_info:
				track_info = SoundCloud.query_track_info(link);
		elif "youtube" in link:
			self.track_urls["Youtube"] = link;
			if is_set_info:
				track_info = YouTube.query_track_info(link);
		elif "play.google" in link:
			self.track_urls["Play Music"] = link;
			self.track_id = link.split('t=')[-1].replace("_", " ");
			if is_set_info:
				track_info = Spotify.query_track_info(self.track_id);
		else:
			track_info = Spotify.query_track_info(link);
		if is_set_info and track_info:
			self.set_track_info(track_info);
		self.set_other_links(self.track_id, self.artists[0]);

	def add_comment(self, user, comment):
		self.comment[user] = comment;

	def set_track_info(self, track_info):
		self.track_id = track_info["track_id"];
		self.album = track_info["album"];
		self.main_artist = track_info["artists"][0];
		self.artists = track_info["artists"];
		self.genres = track_info["genres"];
		urllib.request.urlretrieve(track_info["cover_url"], "tmp.png");
		with open("tmp.png", "rb") as img:
			self.cover_image.put(img);
		os.remove("tmp.png");

	def set_other_links(self, track_id, artist):
		if "Spotify" not in self.track_urls:
			track_info = Spotify.query_track_info(f"{artist} {track_id}");
			if track_info:
				self.track_urls["Spotify"] = track_info["track_url"];
		if "Deezer" not in self.track_urls:
			track_info = Deezer.query_track_info(f"{artist} {track_id}");
			if track_info:
				self.track_urls["Deezer"] = track_info["track_url"];
		if "SoundCloud" not in self.track_urls:
			track_info = SoundCloud.query_track_info(f"{artist} {track_id}");
			if track_info:
				self.track_urls["SoundCloud"] = track_info["track_url"];
		if "YouTube" not in self.track_urls:
			pass;

	def generate_message(self):
		artists = ", ".join(self.artists);
		genres = "-" if self.genres is None or not any(self.genres) else ", ".join(self.genres);
		description = "-" if self.description is None or self.description == "" else self.description;
		seen_by = "-" if self.seen_by is None or not any(self.seen_by) else ", ".join([str(user) for user in self.seen_by]);
		msgs = [f"Track Id: *{self.track_id}*",
		f"Artists: *{artists}*",
		f"Album: *{self.album}*",
		f"Genres: *{genres}*",
		f"Discription: *{description}*",
		f"Seen by: *{seen_by}*"];
		return "\n".join(msgs);

	def get_edit_menu(self):
		menu = telebot.types.InlineKeyboardMarkup();
		prefix = "Add" if any(self.artists) else "Set";
		artist_button = telebot.types.InlineKeyboardButton(text=f"{prefix} artists", callback_data=f"crud/artist/{self.pk}");
		prefix = "Set" if self.album is None or self.album == "" else "Edit";
		album_button = telebot.types.InlineKeyboardButton(text=f"{prefix} album", callback_data=f"crud/album/{self.pk}");
		prefix = "Add" if any(self.genres) else "Set";
		genres_button = telebot.types.InlineKeyboardButton(text=f"{prefix} genres", callback_data=f"crud/genres/choose/{self.pk}");
		prefix = "Set" if self.description is None or self.description == "" else "Edit";
		description_button = telebot.types.InlineKeyboardButton(text=f"{prefix} description", callback_data=f"crud/description/{self.pk}");
		link_button = telebot.types.InlineKeyboardButton(text="Add link", callback_data=f"crud/link/menu/{self.pk}");
		del_button = telebot.types.InlineKeyboardButton(text="Remove from collection", callback_data=f"crud/delete/ask/{self.pk}");
		if not self.available:
			publish_button = telebot.types.InlineKeyboardButton(text="Publish to shared collection", callback_data=f"crud/publish/{self.pk}");
		menu.row(artist_button, album_button);
		menu.row(genres_button, description_button);
		menu.row(link_button);
		menu.row(del_button);
		if not self.available:
			menu.row(publish_button);
		return menu;
