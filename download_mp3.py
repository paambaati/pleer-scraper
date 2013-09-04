#!/usr/bin/python
#ganesh.prasannah

"""Simple script that scrapes pleer's search results page for MP3s
and lets you download them.
"""

__author__ = ['GP']
__version__ = ['1.0']

import sys
import requests
from tabulate import tabulate
from BeautifulSoup import BeautifulSoup

PLEER_API_URL = 'http://pleer.com/site_api/files/get_url'
TABLE_HEADERS = ['#', 'Artist', 'Track Title', 'Bitrate', 'Size']


def call_pleer_api(song_id):
    post_data = {'action': 'download', 'id': song_id}
    response = requests.post(PLEER_API_URL, params=post_data)
    return response.json()


def show_progressbar(current_value, max_value):
    percentage = (float(current_value) / float(max_value)) * 100.0
    sys.stdout.write('{0} of {1} bytes read. {2:.2f}% completed.'
                     .format(current_value, max_value, percentage))
    sys.stdout.flush()
    sys.stdout.write('\r')
    sys.stdout.flush()


def download_file(url, local_filename):
    response = requests.get(url, stream=True)
    file_size = int(response.headers.get('content-length'))
    bytes_read = 0
    with open(local_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                show_progressbar(bytes_read, file_size)
                f.write(chunk)
                f.flush()
                bytes_read += len(chunk)
    show_progressbar(file_size, file_size)


def get_tracks(search_string, page):
    loop_counter = 0
    total_pages = 1
    screen_output = []
    song_ids = []
    url = 'http://pleer.com/search?q={0}&target=tracks&page={1}'
    url = url.format(search_string, page)
    page_content = requests.get(url)
    raw_html = page_content.text
    soup = BeautifulSoup(raw_html)
    results_pages = soup.find('ul', {'class': 'pagination'})
    if results_pages:
        total_pages = int(results_pages.get('end'))
        print(('Displaying page {0} of {1}'.format(page, total_pages)))
    results = soup.findAll('div', {'class': 'playlist'})
    for song_listing in results:
        songs = song_listing.findChildren('li')
        for song in songs:
            loop_counter += 1
            artist = song.get('singer')
            title = song.get('song')
            bitrate = song.get('rate')
            filesize = song.get('size')
            song_ids.append(str(song.get('link')))
            screen_output.append([str(loop_counter),
                                 artist, title, bitrate, filesize])
    print((tabulate(screen_output, headers=TABLE_HEADERS, tablefmt='orgtbl')))
    return song_ids, total_pages, screen_output


def display_results(search_string, page=1):
    song_ids, total_pages, screen_output = get_tracks(search_string, page)
    user_prompt = "Enter the song # you'd like to download, or press [Enter]{0}"
    if page < total_pages:
        user_prompt = user_prompt.format(' for next page. Enter 0 to quit. ')
    else:
        user_prompt = user_prompt.format(' to quit. ')
    user_choice = raw_input(user_prompt)
    if user_choice and int(user_choice) > 0:
        user_choice = int(user_choice) - 1
        song_id = song_ids[user_choice]
        api_response = call_pleer_api(song_id)
        download_url = str(api_response['track_link'])
        print('Link found! Downloading..')
        file_name = u'{0} - {1}.mp3'.format(
                    screen_output[user_choice][1].rstrip(),
                    screen_output[user_choice][2].rstrip())
        download_file(download_url, file_name)
        print(('\nFile saved as \'{0}\''.format(file_name)))
    else:
        while not user_choice:
            page += 1
            if page > total_pages:
                sys.exit(1)
            display_results(search_string, page)


if __name__ == "__main__":
    search_string = raw_input('What are you looking for? ')
    print('Searching..')
    search_string = search_string.replace(' ', '+')
    try:
        display_results(search_string)
    except requests.exceptions.ConnectionError:
        print("""[ERROR] Not able to reach pleer.com! Possible reasons could\
        be the lack of an internet connection, an aggressive firewall, a proxy
        or aliens. Probably aliens.""")
