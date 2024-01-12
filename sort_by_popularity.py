import sys
import winsound

import bs4
import requests
import xmltodict

BASE_URL = "https://myanimelist.net/anime"
anime_info = {}


def add_info(db_id: str):
    page_response = requests.get(BASE_URL + "/" + db_id)
    while page_response.status_code != 200:
        winsound.MessageBeep(winsound.MB_ICONHAND)
        input("It looks like MAL is blocking our requests.\n" +
              "Visit MAL in a browser and press the button, " +
              "then press enter in this script to continue")
        page_response = requests.get(BASE_URL + "/" + db_id)

    is_tv_movie = ("myanimelist.net/topanime.php?type=tv" in page_response.text
        or "myanimelist.net/topanime.php?type=movie" in page_response.text)
    soup = bs4.BeautifulSoup(page_response.content, 'html.parser')
    jpn_title = soup.find(
        'h1', attrs={"class": "title-name"}).find('strong').get_text()
    eng_title_tag = soup.find('p', attrs={"class": "title-english"})
    if eng_title_tag is not None:
        eng_title = eng_title_tag.get_text()
    else:
        eng_title = None

    print("Processing " + BASE_URL + "/" + db_id + " [" +
          jpn_title + "] "
          + ("(" + eng_title + ")" if eng_title is not None else "")
          + (" {TV/Movie}" if is_tv_movie else ""))

    members = int(soup.find(
        'span', attrs={"class": "members"}).find(
            'strong').get_text().replace(',', ''))

    anime_info[db_id] = (jpn_title, eng_title, members, is_tv_movie)


def main():
    if len(sys.argv) == 1:
        print("You must provide the path of a valid MyAnimeList XML dump")
        sys.exit(1)
    mal_dump_path = ' '.join(sys.argv[1:])
    with open(mal_dump_path, encoding='utf8') as file:
        xml = xmltodict.parse(file.read())

    matched_db_ids = []
    for anime in xml["myanimelist"]["anime"]:
        if anime["my_status"] != "Plan to Watch":
            matched_db_ids.append(anime["series_animedb_id"])
    for matched_id in matched_db_ids:
        add_info(matched_id)

    all_lines = []
    tv_movie_only_lines = []
    sorted_by_popularity = sorted(
        anime_info.values(), key=lambda a: a[2], reverse=True)
    for jpn_title, eng_title, members, is_tv_movie in sorted_by_popularity:
        line = jpn_title
        if eng_title is not None:
            line += " (" + eng_title + ")"
        line += f" ～ {members}\n"
        all_lines.append(line)
        if is_tv_movie:
            tv_movie_only_lines.append(line)

    with open("result.txt", 'w', encoding='utf8') as file:
        file.writelines(all_lines)

    with open("result-tv-movie-only.txt", 'w', encoding='utf8') as file:
        file.writelines(tv_movie_only_lines)


if __name__ == "__main__":
    main()
