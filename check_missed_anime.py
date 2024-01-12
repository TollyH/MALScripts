import re
import sys
import winsound

import bs4
import requests

BASE_URL = "https://myanimelist.net/anime"
resolved = []
final_lines = []


def add_info(
        soup: bs4.BeautifulSoup, match_type: str, db_id: str, level: int):
    final_lines.append('    ' * level)
    final_lines[-1] += soup.find(
        'h1', attrs={"class": "title-name"}).find('strong').get_text()

    eng_title = soup.find('p', attrs={"class": "title-english"})
    if eng_title is not None:
        final_lines[-1] += " | " + eng_title.get_text()

    final_lines[-1] += f" ({match_type}) [{db_id}]\n"


def find_missing_anime(
        db_id: str, match_type: str, matched_db_ids: list[str], level: int):
    if db_id in resolved:
        return

    resolved.append(db_id)

    page_response = requests.get(BASE_URL + "/" + db_id)
    while page_response.status_code != 200:
        winsound.MessageBeep(winsound.MB_ICONHAND)
        input("It looks like MAL is blocking our requests.\n" +
              "Visit MAL in a browser and press the button, " +
              "then press enter in this script to continue")
        page_response = requests.get(BASE_URL + "/" + db_id)

    soup = bs4.BeautifulSoup(page_response.content, 'html.parser')

    print("Processing " + BASE_URL + "/" + db_id + " [" + soup.find(
        'h1', attrs={"class": "title-name"}).find('strong').get_text() + "]")

    found_missing = False

    if level != 0:
        add_info(soup, match_type, db_id, level)

    related_anime_table = soup.find(
        'table', attrs={"class": "anime_detail_related_anime"})
    if related_anime_table is None:
        return
    related_anime_rows = related_anime_table.find_all('tr')
    if related_anime_rows is None:
        return
    for row in related_anime_rows:
        relation_type = row.find_all('td')[0].get_text().strip(':')
        if relation_type != "Character":
            anime_link_tags = row.find_all('td')[1].find_all('a')
            for link_tag in anime_link_tags:
                url = link_tag.get('href')
                try:
                    related_id = re.findall(r"/(\d+?)/", url)[0]
                except IndexError:
                    print("Invalid URL in table: " + url)
                    continue
                if "/anime/" in url and related_id not in matched_db_ids:
                    if level == 0 and not found_missing:
                        found_missing = True
                        add_info(soup, match_type, db_id, level)
                    find_missing_anime(
                        related_id, relation_type, matched_db_ids, level + 1)


def main():
    if len(sys.argv) == 1:
        print("You must provide the path of a valid MyAnimeList XML dump")
        sys.exit(1)
    mal_dump_path = ' '.join(sys.argv[1:])
    with open(mal_dump_path, encoding='utf8') as file:
        rawxml = file.read()

    matched_db_ids = re.findall(
        r"<series_animedb_id>(\d+?)</series_animedb_id>", rawxml)
    for matched_id in matched_db_ids:
        find_missing_anime(matched_id, "Watched", matched_db_ids, 0)

    with open("result.txt", 'w', encoding='utf8') as file:
        file.writelines(final_lines)


if __name__ == "__main__":
    main()
