import telebot

from data_storage import MusicTrack


def add_feed_actions(self):
	self.action_dictionary["feed"]["comment"]["add"] = self.comment_action;
	self.action_dictionary["feed"]["upvote"] = self.upvote;
	self.action_dictionary["feed"]["downvote"] = self.downvote;


def generate_post_message(self, track):
	artists = ", ".join(track.artists);
	genres = None if track.genres is None or not any(track.genres) else ", ".join(track.genres);
	description = None if track.description is None or track.description == "" else track.description;
	msgs = [f"Track Id: *{track.track_id}*"];
	if artists:
		msgs.append(f"Artists: *{artists}*");
	msgs.append(f"Album: *{track.album}*");
	if genres:
		msgs.append(f"Genres: *{genres}*");
	if description:
		msgs.append(f"Discription: *{description}*");
	return "\n".join(msgs);


def get_post_menu(track):
	menu = telebot.types.InlineKeyboardMarkup();
	button_row = [];
	for service in ["Spotify", "Apple Music", "Deezer"]:
		if service in track.track_urls:
			button_row.append(telebot.types.InlineKeyboardButton(text=service, url=track.track_urls[service]));
	menu.row(*button_row);
	button_row = [];
	for service in ["SoundCloud", "Youtube", "Play Music"]:
		if service in track.track_urls:
			button_row.append(telebot.types.InlineKeyboardButton(text=service, url=track.track_urls[service]));
	menu.row(*button_row);
	menu.row(
		telebot.types.InlineKeyboardButton(text="\U0001F44D", callback_data=f"feed/upvote/{track.pk}"),
		telebot.types.InlineKeyboardButton(text="\U0001F44E", callback_data=f"feed/downvote/{track.pk}")
	);
	menu.add(telebot.types.InlineKeyboardButton(text="Comment", callback_data=f"feed/comment/add/{track.pk}"));
	return menu;


def request_music(self, message):
	user = self.get_user(message);
	queried_tracks = MusicTrack.objects(available=True, seen_by__nin=[user], publisher__ne=user);
	if queried_tracks.count() == 0:
		self.bot.send_message(message.chat.id, "Sorry, I have nothing to offer you. "
											"I'll send your friends a request, so keep calm and hang on for a while...");
	# TODO request
	else:
		music_track = queried_tracks.first();
		music_track.seen_by.append(user);
		music_track.save();
		self.bot.send_photo(
			message.chat.id,
			music_track.cover_image,
			self.generate_post_message(music_track),
			reply_markup=get_post_menu(music_track),
			parse_mode='Markdown'
		);


def comment_action(self, call, track):
	self.bot.send_message(
		call.message.chat.id,
		"Hope you like it, what do you think?",
		reply_markup=telebot.types.ForceReply()
	);
	self.bot.register_next_step_handler(call.message, self.comment_callback, track);


def comment_callback(self, message, track):
	user = self.get_user(message);
	track.comments[user.username] = message.text;
	self.notify_publisher(track, message, from_user=user);


def notify_publisher(self, track, message, from_user):
	self.bot.send_message(
		track.publisher.chat_id,
		f"*{from_user.first_name} {from_user.last_name}* just commented track (*{track.track_id}*) you added:",
		parse_mode='Markdown'
	);
	self.bot.forward_message(track.publisher.chat_id, message.chat.id, message.message_id);


def upvote(self, track, message):
	pass;


def downvote(self, track, message):
	pass;
