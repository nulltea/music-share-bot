import spotipy;
import spotipy.util as util;

scope = 'user-read-private user-read-playback-state user-modify-playback-state'
token = util.prompt_for_user_token("o3wg05pdhtx9646uma9legdfz", scope=scope, client_id="4226537ad7374fb7a4f0c3243cb255b3", client_secret="46b838d339c248bba55f15721430eaca", redirect_uri="http://example.com/callback/");

spotipy = spotipy.Spotify(auth=token);


def get_track_info(track_id):
	result = spotipy.track(track_id);
	album = spotipy.album(result["album"]['id']);
	album_name = album["name"];
	artists = [artist["name"] for artist in album["artists"]]
	main_artist = spotipy.artist(album["artists"][0]["id"]);
	genres = main_artist["genres"];
	cover_image = album["images"][0]["url"];
	return {
		"track_id": result["name"],
		"album": album_name,
		"artists": artists,
		"genres": genres,
		"cover_url": cover_image
	};


def query_track_info(track_query):
	if "http" in track_query:
		return get_track_info(track_query);
	result = spotipy.search(track_query);
	track_id = result["tracks"]["items"][0]["id"];
	return get_track_info(track_id);
