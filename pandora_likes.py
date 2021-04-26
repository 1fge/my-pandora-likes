import requests
import datetime
import asyncio
import sys
import time
import json
from stealth_login import StealthLogin

class Downloader:
    def __init__(self, email, password):
        self.session = requests.session()
        self.stealth_login = StealthLogin(email, password)

    def load_auth_details(self, cookies, response_json):
        """Set the session cookies gathered with StealthLogin that are required to access the /getFeedback endpoint"""
        required_cookie_names = ["csrftoken", "at"]

        for cookie in cookies:
            cookie_name = cookie.get("name")
            if cookie_name in required_cookie_names:
                self.session.cookies.set_cookie(requests.cookies.create_cookie(name=cookie_name, value=cookie.get("value"), domain="www.pandora.com"))

        return self.session.cookies.get("csrftoken"), response_json.get("authToken"), response_json.get("webname")

    def get_amount_songs(self, auth_token, csrf_token, webname):
        """Visit Pandora song API to determine the total amount of liked songs"""
        headers = {
            'origin': 'https://www.pandora.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3542.0 Safari/537.36',
            'x-csrftoken': csrf_token,
            'content-type': 'application/json',
            'accept': 'application/json, text/plain, */*',
            'x-authtoken': auth_token,
            'referer': f'https://www.pandora.com/profile/thumbs/{webname}',
            'authority': 'www.pandora.com',
        }
        data = {
            'pageSize':1,
            'startIndex':0,
            'webname':webname
        }

        songs_url = "https://www.pandora.com/api/v1/station/getFeedback"
        songs_json = self.session.post(songs_url, headers=headers, json=data).json()
        song_total = songs_json.get("total")

        if song_total is not None:
            print(f"Total Liked Songs: {song_total}\n")
            return song_total

        print("Error Getting Amount of Liked Songs, Exiting")
        sys.exit()

    def fetch_songs(self, auth_token, csrf_token, webname, start_index, page_size):
        """Fetch a range of liked songs"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "X-AuthToken": auth_token,
            "X-CsrfToken": csrf_token,
            "Origin": "https://www.pandora.com",
            "Connection": "keep-alive",
            "Referer": "https://www.pandora.com",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "TE": "Trailers",
        }
        data = {
            "pageSize": page_size,
            "startIndex": start_index,
            "webname": webname
        }

        print(f"Fetching Songs from {start_index} to {start_index + page_size}...")
        songs_url = "https://www.pandora.com/api/v1/station/getFeedback"
        songs_json = self.session.post(songs_url, headers=headers, json=data).json()
        songs = songs_json.get("feedback")

        if songs is not None:
            return songs

        print("Error Fetching Songs, Exiting")
        sys.exit()

    @staticmethod
    def parse_songs(parsed_songs, songs_batch):
        """Append and extract various information for a 'batch' of liked songs"""
        for song in songs_batch:
            try:
                song_and_artist = {
                    "title": song["songTitle"],
                    "artist": song["artistName"],
                    "album": song["albumTitle"],
                    "date_liked": song["feedbackDateCreated"],
                    "from_station": song["stationName"],
                    "track_length": song["trackLength"]
                }
                parsed_songs.append(song_and_artist)
            except KeyError:
                print("** Error Parsing Song, Skipping")

        return parsed_songs

    def compile_liked_songs(self, auth_token, csrf_token, song_count, webname):
        """Fetch information for all liked songs"""
        parsed_songs = []
        fetched_songs = 0
        fetch_amount = 100

        while fetched_songs < song_count:
            if song_count - fetched_songs < 100:
                fetch_amount = song_count - fetched_songs

            songs = self.fetch_songs(auth_token, csrf_token, webname, fetched_songs, fetch_amount)
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
        csrf_token, auth_token, webname = self.load_auth_details(cookies, login_response_json)
        song_count = self.get_amount_songs(auth_token, csrf_token, webname)

        parsed_songs = self.compile_liked_songs(auth_token, csrf_token, song_count, webname)
        self.output_songs(parsed_songs, webname)


if __name__ == "__main__":
    email = "YOUREMAIL"
    password = "YOURPASSWORD"

    downloader = Downloader(email, password)
    downloader.download_likes()