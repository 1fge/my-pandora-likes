import requests
import datetime
import sys
import time
import json

class Downloader:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.session()

    def get_csrf_token(self):
        """Generate a CSRF token used to log in."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "TE": "Trailers",
        }

        sign_in_url = "https://www.pandora.com/account/sign-in"
        self.session.get(sign_in_url, headers=headers)

        csrf_token = self.session.cookies.get_dict().get("csrftoken")
        if csrf_token is not None:
            return csrf_token

        print("Error getting CSRF, Exiting")
        sys.exit()

    def login(self, csrf):
        """Login to Pandora and return the webname and auth token."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "X-CsrfToken": csrf,
            "Origin": "https://www.pandora.com",
            "Connection": "keep-alive",
            "Referer": "https://www.pandora.com/account/sign-in",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "TE": "Trailers",
        }
        data = {
            "existingAuthToken": None,
            "username": self.email,
            "password": self.password,
            "keepLoggedIn": True
        }

        response_json = self.session.post('https://www.pandora.com/api/v1/auth/login', headers=headers, json=data).json()
        auth_token = response_json.get("authToken")
        webname = response_json.get("webname")

        if auth_token is None or webname is None:
            print("Unable to Login... Check Email and Password")
            sys.exit()

        print("Successfully Logged In!")
        return auth_token, webname

    def get_amount_songs(self, auth_token, csrf_token, webname):
        """Visit Pandora song API to determine the total amount of liked songs"""
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
            "pageSize": 1,
            "startIndex": 0,
            "webname": webname
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
            song_and_artist = {
                "title": song["songTitle"],
                "artist": song["artistName"],
                "album": song["albumTitle"],
                "date_liked": song["feedbackDateCreated"],
                "from_station": song["stationName"],
                "track_length": song["trackLength"]
            }
            parsed_songs.append(song_and_artist)
        return parsed_songs

    def compile_liked_songs(self, auth_token, csrf_token, song_count, webname):
        """Fetch information for all liked songs"""
        parsed_songs = []
        fetched_songs = 0
        fetch_amount = 100

        while fetched_songs < song_count:
            if song_count - fetched_songs < 100:
                fetch_amount = song_count-fetched_songs

            songs = self.fetch_songs(auth_token, csrf_token, webname, fetched_songs, fetch_amount)
            parsed_songs = self.parse_songs(parsed_songs, songs)

            fetched_songs += len(songs)
            time.sleep(1.25)

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

        with open(songs_json_filename, "w", encoding="utf-8") as f:
            json.dump(song_list, f)

        formatted_songs = self.format_songs(song_list)
        songs_txt_filename = f"formatted_songs {current_time}.txt"

        with open(songs_txt_filename, "w", encoding="utf-8") as f:
            f.write(formatted_songs)

    def download_likes(self):
        """Main method encompassing all functionailty for downloading song information"""
        csrf_token = self.get_csrf_token()
        auth_token, webname = self.login(csrf_token)
        song_count = self.get_amount_songs(auth_token, csrf_token, webname)

        parsed_songs = self.compile_liked_songs(auth_token, csrf_token, song_count, webname)
        self.output_songs(parsed_songs, webname)


if __name__ == "__main__":
    email = "YOUREMAIL"
    password = "YOURPASSWORD"

    downloader = Downloader(email, password)
    downloader.download_likes()