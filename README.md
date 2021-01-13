# My Pandora Likes
Unfortunaltely, Pandora offers no easy way to export your liked songs. `My Pandora Likes` solves this problem by using Pandora's API to fetch all of a user's liked songs, along with various information for each song.

## Installation
**Make sure you are using Python >=3.6**

To Install Files:
```bash
git clone https://github.com/1fge/my-pandora-likes
```
To Install Required Modules:
```bash
pip install -r requirements.txt
```



## Usage
Once you have installed Python along with all of the dependencies from `requirements.txt`, you'll need to open `pandora_likes.py` in a text editor.

At the bottom of the file, replace the variables `email` and `password` with your Pandora email and password. Then, start the program.
```bash
python pandora_likes.py
```
Next, the program will attempt to login with your provided credentials. As long as no errors are encountered, two files will be created in your working directory. The first is a .txt file containing the song name and artist on each line. The second is a JSON file containing the song name, artist, album, date liked, station liked on, and the song's run time.

If you run into any problems, feel free to create an issue. Furthermore, your contribution is encouraged, so feel free to make a pull request if you think something can be improved. Enjoy!
## TODO
- [ ] Implement a CLI
- [ ] Upload to PyPI
- [ ] Consider fetching likes from user's public profile to eliminate need for password
