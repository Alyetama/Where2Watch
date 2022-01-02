import html
import json
import re
from pathlib import Path

import requests
import streamlit as st
from justwatch import JustWatch

from config import providers_dict


@st.experimental_singleton
def stringfy_values(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


@st.experimental_singleton
def get_plot_trailer(movie_full_path):
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
        if name == 'trailer':
            if res['provider'] == 'youtube':
                res = f'https://www.youtube.com/watch?v={res["external_id"]}'
            else:
                res = None
        res_d.update({name: res})
    return res_d


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
        if x['provider_type'] in ['imdb:score', 'imdb:votes']
    ])

    col1, col2 = st.columns(2)

    poster = f'https://images.justwatch.com{res["items"][0]["poster"]}'.replace(
        '{profile}', 's332')
    col1.image(poster)

    res_d = get_plot_trailer(movie_full_path)
    plot = res_d['plot']['description']
    trailer = res_d['trailer']

    with col2:
        st.markdown(f'### Title: `{metdata["title"]}`')
        st.markdown(f'#### Release year: `{metdata["original_release_year"]}`')
        st.markdown(f'#### Type: `{metdata["object_type"].capitalize()}`')
        st.markdown(
            f'#### IMDb score: `{scoring[0]}` (`{stringfy_values(scoring[1])}`)'
        )
        st.markdown(f'#### Plot:')
        st.caption(plot)

        streams = []
        if subs:
            for sub in subs:
                curr = providers_dict[sub["package_short_name"]]
                streams.append(
                    f'[![{curr[0]}]({curr[1]})]({sub["urls"]["standard_web"]})'
                )
            st.markdown('#### Available on:\n' + ' '.join(streams))
        else:
            st.markdown('---\n#### ❌ Not available...\n---')

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
    #title-the-witcher > div:nth-child(1) > a:nth-child(1) {visibility: hidden;}
    #release-year-2019 > div:nth-child(1) > a:nth-child(1) {visibility: hidden;}
    #type-show > div:nth-child(1) > a:nth-child(1) {visibility: hidden;}
    #imdb-score-8-2-413-28k > div:nth-child(1) > a:nth-child(1) {visibility: hidden;}
    </style>""",
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    query = c1.text_input(label='', placeholder='Search...')

    if query:
        st.write('')
        main(query)
