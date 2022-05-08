import base64
import requests
import datetime
import asyncio
import sys
import time
import json
from stealth_login import StealthLogin

# constant values used to query Pandora GQL API
OPERATION_NAME = "ThumbedUpTracks"
OPERATION_HASH = "8679089a5fe9b7cf8d9f9b88788756d4d4e5a6ee9caadfa4812767a37347eac6"

class Downloader:
    def __init__(self, email, password):
        self.session = requests.session()
        self.stealth_login = StealthLogin(email, password)

    def load_auth_details(self, cookies, response_json):
        """Set the session cookies gathered with StealthLogin that are required to access the /getFeedback endpoint"""
        required_cookie_names = ["at"]

        for cookie in cookies:
            cookie_name = cookie.get("name")
            if cookie_name in required_cookie_names:
                self.session.cookies.set_cookie(requests.cookies.create_cookie(name=cookie_name, value=cookie.get("value"), domain="www.pandora.com"))

        return response_json.get("authToken"), response_json.get("webname")

    def get_amount_songs(self, auth_token):
        """Visit Pandora song API to determine the total amount of liked songs"""
        headers = {
            'accept': 'application/json',
            'x-apollo-operation-id': OPERATION_HASH,
            'x-apollo-operation-name': OPERATION_NAME,
            'x-apollo-cache-fetch-strategy': 'NETWORK_ONLY',
            'x-apollo-expire-timeout': '0',
            'x-apollo-expire-after-read': 'false',
            'x-apollo-prefetch': 'false',
            'x-apollo-cache-do-not-store': 'false',
            'user-agent': 'Mozilla/5.0 (Linux; Android 7.1.2; SM-G935F Build/N2G48H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/68.0.3440.70 Mobile Safari/537.36 Pandora/2203.1',
            'apollographql-client-name': 'com.pandora.android',
            'apollographql-client-version': '2203.1',
            'x-authtoken': auth_token,
            'content-type': 'application/json; charset=utf-8',
        }
        data = {
            "operationName": "ThumbedUpTracks",
            "variables": {
                "limit": 1
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": OPERATION_HASH
                }
            }
        }

        songs_url = "https://www.pandora.com/api/v1/graphql/graphql"
        songs_json = self.session.post(songs_url, headers=headers, json=data).json()
        song_total = songs_json.get("data").get("feedbacks").get("totalCount")

        if song_total is not None:
            print(f"Total Liked Songs: {song_total}\n")
            return song_total

        print("Error Getting Amount of Liked Songs, Exiting")
        sys.exit()

    def fetch_songs(self, auth_token, start_index, page_size):
        """Fetch a range of liked songs"""
        headers = {
            'accept': 'application/json',
            'x-apollo-operation-id': OPERATION_HASH,
            'x-apollo-operation-name': OPERATION_NAME,
            'x-apollo-cache-fetch-strategy': 'NETWORK_ONLY',
            'x-apollo-expire-timeout': '0',
            'x-apollo-expire-after-read': 'false',
            'x-apollo-prefetch': 'false',
            'x-apollo-cache-do-not-store': 'false',
            'user-agent': 'Mozilla/5.0 (Linux; Android 7.1.2; SM-G935F Build/N2G48H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/68.0.3440.70 Mobile Safari/537.36 Pandora/2203.1',
            'apollographql-client-name': 'com.pandora.android',
            'apollographql-client-version': '2203.1',
            'x-authtoken': auth_token,
            'content-type': 'application/json; charset=utf-8',
        }
        encoded_cursor = f"{start_index}|DESC|DATE_MODIFIED".encode("utf-8")
        cursor = base64.b64encode(encoded_cursor).decode("utf-8")
        data = {
            "operationName": OPERATION_NAME,
            "variables": {
                "limit": page_size,
                "cursor": cursor,
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": OPERATION_HASH
                }
            }
        }

        print(f"Fetching Songs from {start_index} to {start_index + page_size}...")
        songs_url = "https://www.pandora.com/api/v1/graphql/graphql"
        songs_json = self.session.post(songs_url, headers=headers, json=data).json()
        songs = songs_json.get("data").get("feedbacks").get("items")

        if songs is not None:
            return songs

        print("Error Fetching Songs, Exiting")
        sys.exit()

    @staticmethod
    def parse_songs(parsed_songs, songs_batch):
        """Append and extract various information for a 'batch' of liked songs"""
        for song in songs_batch:
            try:
                song = song["target"]
                song_and_artist = {
                    "title": song["name"],
                    "artist": song["artist"]["name"],
                    "album": song["album"]["name"],
                    "track_length": song["duration"]
                }
                parsed_songs.append(song_and_artist)
            except KeyError:
                print("** Error Parsing Song, Skipping")

        return parsed_songs

    def compile_liked_songs(self, auth_token, song_count):
        """Fetch information for all liked songs"""
        parsed_songs = []
        fetched_songs = 0
        fetch_amount = 50

        while fetched_songs < song_count:
            if song_count - fetched_songs < 50:
                fetch_amount = song_count - fetched_songs

            songs = self.fetch_songs(auth_token, fetched_songs, fetch_amount)
            parsed_songs = self.parse_songs(parsed_songs, songs)

            fetched_songs += len(songs)
            time.sleep(0.75)

        return parsed_songs

    @staticmethod
    def format_songs(song_list):
        """Generate a string with each song in 'TITLE ARTIST' format"""
        output_string = ""
        for song in song_list:
            output_string += f"{song['title']} {song['artist']}\n"

        return output_string

    def output_songs(self, song_list, webname):
        """Write detailed and formatted songs to file system"""
        current_time = datetime.datetime.today().strftime("%Y-%m-%d %H.%M.%S")
        songs_json_filename = f"{webname} {current_time}.json"
        songs_txt_filename = f"formatted_songs {current_time}.txt"
        formatted_songs = self.format_songs(song_list)

        with open(songs_json_filename, "w", encoding="utf-8") as f:
            json.dump(song_list, f)

        with open(songs_txt_filename, "w", encoding="utf-8") as f:
            f.write(formatted_songs)

        print(f"\nWrote Songs (JSON) to {songs_json_filename}")
        print(f"Wrote Songs (TXT) to {songs_txt_filename}")

    def download_likes(self):
        """Main method encompassing all functionailty for downloading song information"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.stealth_login.initiate_browser())

        cookies, login_response_json = loop.run_until_complete(self.stealth_login.fetch_login_data())
        auth_token, webname = self.load_auth_details(cookies, login_response_json)
        song_count = self.get_amount_songs(auth_token)

        parsed_songs = self.compile_liked_songs(auth_token, song_count)
        self.output_songs(parsed_songs, webname)


if __name__ == "__main__":
    email = "YOUREMAIL"
    password = "YOURPASSWORD"

    downloader = Downloader(email, password)
    downloader.download_likes()