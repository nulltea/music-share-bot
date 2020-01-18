import deezer
import sclib
import spotipy
import spotipy.util as util
import youtube_api

from config import config;


class SpotifyApi:
	token = util.prompt_for_user_token(
		username=config["spotify"]["username"],
		scope=config["spotify"]["scope"],
		client_id=config["spotify"]["client_id"],
		client_secret=config["spotify"]["client_secret"],
		redirect_uri=config["spotify"]["redirect_uri"]
	);
	spotipy = spotipy.Spotify(auth=token);

	def get_track_info(self, track_id):
		result = self.spotipy.track(track_id);
		album = self.spotipy.album(result["album"]['id']);
		album_name = album["name"];
		artists = [artist["name"] for artist in album["artists"]]
		main_artist = self.spotipy.artist(album["artists"][0]["id"]);
		genres = main_artist["genres"];
		cover_image = album["images"][0]["url"];
		return {
			"track_id": result["name"],
			"track_url": result["external_urls"]["spotify"],
			"album": album_name,
			"artists": artists,
			"genres": genres,
			"cover_url": cover_image
		};

	def query_track_info(self, track_query):
		if "http" in track_query:
			return self.get_track_info(track_query);
		result = self.spotipy.search(track_query);
		try:
			track_id = result["tracks"]["items"][0]["id"];
		except:
			return;
		return self.get_track_info(track_id);


Spotify = SpotifyApi();


class DeezerApi:
	deezer_client = deezer.Client(
		app_id=config["deezer"]["application_id"],
		app_secret=config["deezer"]["app_secret"]
	);

	def get_track_info(self, track):
		artists = [track.artist.name]
		genres = [];
		return {
			"track_id": track.title,
			"track_url": track.link,
			"album": track.album.title,
			"artists": artists,
			"genres": genres,
			"cover_url": track.album.cover_big
		};

	def query_track_info(self, track_query):
		try:
			track = self.deezer_client.search(track_query)[0];
		except:
			return;
		return self.get_track_info(track);


Deezer = DeezerApi();


class SoundCloudApi:
	soundcloud = sclib.SoundcloudAPI();

	def get_track_info(self, track):
		artists = [track.artist]
		genres = [track.genre];
		return {
			"track_id": track.title,
			"track_url": track.permalink_url,
			"album": track.album,
			"artists": artists,
			"genres": genres,
			"cover_url": track.artwork_url
		};

	def query_track_info(self, track_query):
		try:
			track = self.soundcloud.resolve(track_query);
		except:
			return;
		return self.get_track_info(track);


SoundCloud = SoundCloudApi();


class YouTubeApi:
	youtube = youtube_api.YouTubeDataAPI(key=config["youtube"]["api_key"]);

	def get_track_info(self, track):
		artist = track["channel_title"].replace(" - Topic", "");
		artists = [artist];
		track_id = track["video_title"];
		cover_url = track["video_thumbnail"];
		genres = [];
		try:
			spotify_data = Spotify.query_track_info(f"{artist} {track_id}");
		except:
			pass;
		if spotify_data:
			return spotify_data;
		return {
			"track_id": track_id,
			"track_url": "",
			"album": "",
			"artists": artists,
			"genres": genres,
			"cover_url": cover_url
		};

	def query_track_info(self, track_query):
		try:
			track = self.youtube.search(track_query)[0];
		except:
			return;
		return self.get_track_info(track);


YouTube = YouTubeApi();
