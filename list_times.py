# Warning: This script requires that your list page is FULLY scrolled to the
#          bottom before saving as HTML. It also requires that the "more"
#          button has been pressed on every list entry. The following
#          JavaScript can do that for you (scroll to the bottom FIRST):
#              var moreButtons = document.getElementsByClassName("more");
#              for (let i = 0; i < moreButtons.length; i++) {
#                  moreButtons[i].children[0].click();
#              }
import re
import sys
from dataclasses import dataclass

import bs4

RE_PER_EPISODE = re.compile(
    r"\((\d+) hours?, (\d+) minutes?, and (\d+) seconds? per episode\)"
)
RE_PROGRESS = re.compile(r"(\d+|-)(?: / (\d+|-))?")


@dataclass
class Anime:
    name: str
    seconds_per_ep: int
    episode_count: int
    watched_episodes: int


if len(sys.argv) < 2:
    print("You must provide the path to the list HTML export")
    sys.exit(1)

with open(sys.argv[1], encoding="utf8") as file:
    soup = bs4.BeautifulSoup(file, "html.parser")

names = [x.get_text(' ', True) for x in soup.select(".title > a")[1:]]
more_sections = [x.get_text(' ', True) for x in soup.select(".borderRBL")]
progress_labels = [x.get_text(' ', True) for x in soup.select(".progress")[1:]]

all_anime: list[Anime] = []

for name, more, prog in zip(names, more_sections, progress_labels):
    per_ep_match = RE_PER_EPISODE.search(more)
    assert per_ep_match is not None
    seconds = (
        int(per_ep_match[1]) * 60 * 60
        + int(per_ep_match[2]) * 60
        + int(per_ep_match[3])
    )

    prog_match = RE_PROGRESS.search(prog)
    assert prog_match is not None
    if prog_match[1] == '-':
        watched = 0
    else:
        watched = int(prog_match[1])

    if prog_match[2] == '-':
        total = 0
    elif prog_match[2] is None:
        total = watched
    else:
        total = int(prog_match[2])

    all_anime.append(Anime(name, seconds, total, watched))

total_watched = 0
total_unwatched = 0
grand_total_seconds = 0

for anime in all_anime:
    total_watched += anime.watched_episodes * anime.seconds_per_ep
    total_unwatched += max(
        (anime.episode_count - anime.watched_episodes) * anime.seconds_per_ep,
        0
    )
    grand_total_seconds += anime.episode_count * anime.seconds_per_ep

watched_days, remainder = divmod(total_watched, 86400)
watched_hours, remainder = divmod(remainder, 3600)
watched_minutes, watched_seconds = divmod(remainder, 60)

unwatched_days, remainder = divmod(total_unwatched, 86400)
unwatched_hours, remainder = divmod(remainder, 3600)
unwatched_minutes, unwatched_seconds = divmod(remainder, 60)

total_days, remainder = divmod(grand_total_seconds, 86400)
total_hours, remainder = divmod(remainder, 3600)
total_minutes, total_seconds = divmod(remainder, 60)

print(
    f"Watched       : {watched_days:02} day{'s'[:watched_days ^ 1]}, "
    f"{watched_hours:02} hour{'s'[:watched_hours ^ 1]}, "
    f"{watched_minutes:02} minute{'s'[:watched_minutes ^ 1]} and "
    f"{watched_seconds:02} second{'s'[:watched_seconds ^ 1]}"
)
print(
    f"Plan to Watch : {unwatched_days:02} day{'s'[:unwatched_days ^ 1]}, "
    f"{unwatched_hours:02} hour{'s'[:unwatched_hours ^ 1]}, "
    f"{unwatched_minutes:02} minute{'s'[:unwatched_minutes ^ 1]} and "
    f"{unwatched_seconds:02} second{'s'[:unwatched_seconds ^ 1]}"
)
print(f"{total_watched / grand_total_seconds * 100:.2f}% watched")
print(
    f"\nTotal         : {total_days:02} day{'s'[:total_days ^ 1]}, "
    f"{total_hours:02} hour{'s'[:total_hours ^ 1]}, "
    f"{total_minutes:02} minute{'s'[:total_minutes ^ 1]} and "
    f"{total_seconds:02} second{'s'[:total_seconds ^ 1]}"
)
input("Press Enter to continue...")

anime_with_time: list[tuple[Anime, int]] = []
for anime in all_anime:
    anime_with_time.append((anime, max(
        (anime.episode_count - anime.watched_episodes) * anime.seconds_per_ep,
        0
    )))
anime_with_time.sort(key=lambda x: x[1])
anime_with_time = [a for a in anime_with_time if a[1] > 0]

print("\n\nShortest Titles to Watch:")
for index, (anime, unwatched) in enumerate(anime_with_time):
    if unwatched == 0:
        continue
    unwatched_hours, remainder = divmod(unwatched, 3600)
    unwatched_minutes, unwatched_seconds = divmod(remainder, 60)
    print(
        f"{index + 1:03}. {anime.name} ("
        f"{unwatched_hours:02} hour{'s'[:unwatched_hours ^ 1]}, "
        f"{unwatched_minutes:02} minute{'s'[:unwatched_minutes ^ 1]} and "
        f"{unwatched_seconds:02} second{'s'[:unwatched_seconds ^ 1]})"
    )
