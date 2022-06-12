import html
import json
import os
import re

import requests
import streamlit as st
import urllib.parse
from dotenv import load_dotenv
from justwatch import JustWatch


def stringfy_values(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


def get_plot(movie_full_path):
    url = 'https://www.justwatch.com' + movie_full_path
    resp = requests.get(url)
    regex_patterns = [('plot', 'description', r'"description":.+?(?=")'),
                      ('trailer', 'external_id',
                       r'"provider":"youtube","external_id":".+?(?=")')]
    res_d = {}
    for name, key, pattern in regex_patterns:
        regex = re.compile(pattern)
        match = regex.search(resp.text)
        res = json.loads(html.unescape('{' + match.group(0) + '"}'))
        res_d.update({name: res})
    return res_d


def get_trailer(title, year, key):
    q = urllib.parse.quote(f'{title} trailer {year}'.encode('utf8'))
    data = {'key': key, 'part': 'snippet', 'maxResults': 1, 'q': q}
    params = '&'.join([f'{k}={v}' for k, v in data.items()])
    url = f'https://youtube.googleapis.com/youtube/v3/search?{params}'
    resp = requests.get(url, headers={'Accept': 'application/json'})
    if resp.status_code == 200:
        video_id = resp.json()['items'][0]['id']['videoId']
        video_url = 'https://www.youtube.com/watch?v=' + video_id
        return video_url


def main(query):
    just_watch = JustWatch(country='US')
    res = just_watch.search_for_item(query=query)
    movie_full_path = res['items'][0]['full_path']

    subs = []
    with_ads = []

    for x in res['items'][0]['offers']:
        if x['monetization_type'] == 'flatrate' and x[
                'package_short_name'] in providers_dict.keys():
            if x not in subs:
                subs.append(x)
        elif x['monetization_type'] == 'ads':
            if x not in with_ads:
                with_ads.append(x)

    subs_ = []
    for x in subs:
        if not any(x in subs_ for x in subs):
            subs_.append(x)
    subs = subs_

    metdata = res['items'][0]

    scoring = sorted([
        x['value'] for x in res['items'][0]['scoring']
        if 'imdb' in x['provider_type']
    ])

    col1, col2 = st.columns(2)

    poster = f'https://images.justwatch.com{res["items"][0]["poster"]}'.replace(
        '{profile}', 's332')
    col1.image(poster)

    res_d = get_plot(movie_full_path)
    try:
        plot = res_d['plot']['description']
    except ValueError:
        plot = None

    if os.getenv('YOUTUBE_API_TOKEN'):
        trailer = get_trailer(metdata['title'],
                              metdata['original_release_year'],
                              os.environ['YOUTUBE_API_TOKEN'])
    else:
        trailer = None

    with col2:
        st.subheader(f'Title: `{metdata["title"]}`')
        st.subheader(f'Release year: `{metdata["original_release_year"]}`')
        st.subheader(f'Type: `{metdata["object_type"].capitalize()}`')
        if scoring:
            str_val = stringfy_values(scoring[1])
            st.subheader(f'IMDb score: `{scoring[0]}` (`{str_val}`)')

        if plot:
            st.subheader(f'Plot:')
            st.caption(plot)

        streams = []
        if subs:
            for sub in subs:
                curr = providers_dict[sub["package_short_name"]]
                streams.append(
                    f'[![{curr[0]}]({curr[1]})]({sub["urls"]["standard_web"]})'
                )
            st.subheader('Available on:\n' + ' '.join(streams))
        else:
            st.markdown('---\n❌ Not available...\n---')

    tc1, tc2 = st.columns([10, 1])
    if trailer:
        with st.expander('Trailer'):
            st.video(trailer)


if __name__ == '__main__':
    st.set_page_config(
        page_title='Where2Watch',
        page_icon="🍿",
        layout="centered",
        initial_sidebar_state="expanded",
    )

    st.markdown("""<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .css-e370rw {visibility: hidden;}
    .css-15zrgzn {visibility: hidden;}
    .css-e16nr0p31 {visibility: hidden;}
    </style>""",
                unsafe_allow_html=True)

    st.title('🍿 Where2Watch')

    load_dotenv()

    with open('providers.json') as j:
        providers_dict = json.load(j)

    c1, c2, c3 = st.columns(3)

    query = c1.text_input(label='', placeholder='Search...')

    if query:
        st.write('')
        main(query)
