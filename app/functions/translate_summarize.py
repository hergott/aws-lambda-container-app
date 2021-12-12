from time import time
import logging
import os
import re

import boto3

from functions.WebPageRead import WebPageRead
from functions.RSS_Fetch import RSS_Fetch
# from get_page_text import get_page_text


def html5_template():
    top = '''<html lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>Web Page Translate & Summarize</title>
    <link href="default.css" rel="stylesheet" type="text/css">
  </head>
  <body>'''

    bottom = '''</body>
</html>'''

    return top, bottom


def format_summary(story):
    nl = '<br />'*2
    bullet_point_char = '&#8226;'
    tab_char = '&#9;'

    t = story['title'] + nl
    t = t+story['date'] + nl
    t = t+story['link'] + nl*2
    t = t+'Publisher Summary:' + nl
    t = t+story['publisher_summary'] + nl*2

    if story['ai_summary'] is not None:
        t = t+'AI Summary:' + nl
        for a in story['ai_summary']:
            t = t+bullet_point_char+tab_char+a+nl
    else:
        t = t+'AI summarization failed.'

    t = t + nl*6

    return t


def polish_text(txt):
    replacements = [('==References==', ''),
                    ('==External links==', ''), ('..',
                                                 '.'), ('. .', '.'), (' . .', '.'),
                    (',.', '.'), (' )', ')'), ('( ', '('), (' .', '.'), ('<br />', ''), ('&#8226;', ''), ('&#9;', '')]

    for r in replacements:
        txt = txt.replace(r[0], r[1])

    txt = re.sub(' +', ' ', txt)

    return txt


def translate_summarize(rss_url, translator, summarizer, max_chars=25000):
    tic = time()

    bucket_name = 'web-translation-summarization'
    blob_name_txt = 'summaries.txt'
    blob_name_html = 'summaries.html'

    # profile_name = 'mjh'
    session = boto3.Session(region_name='us-west-1')

    s3 = session.resource('s3')

    obj = s3.Object(bucket_name=bucket_name, key=blob_name_txt)
    download_txt_bytes = obj.get()['Body'].read()

    download_txt = str(download_txt_bytes, 'utf-8')

    if len(download_txt) > 50000:
        download_txt = download_txt[:50000]

    rss_fetch = RSS_Fetch(rss_url)

    # print(rss_fetch)
    # print(rss_fetch.feed)
    # print(rss_fetch.stories)
    # print(len(rss_fetch.stories))
    # print(rss_fetch.story_links)

    selected_story = None

    rejected_links = ['informationen']

    for i, sel in enumerate(rss_fetch.stories):

        reject_link = False

        for rl in rejected_links:
            if rl in sel['link']:
                reject_link = True

        if not reject_link and sel['link'] not in download_txt:
            selected_story = i
            break

    if selected_story is None:
        logging.info('No stories match criteria.')
        return None

    s = rss_fetch.stories[selected_story]

    story = dict()

    story['title'] = translator.translate(s['title'])
    story['date'] = s['published']
    story['link'] = s['link']
    story['publisher_summary'] = translator.translate(s['summary'])[:-2]

    wpr = WebPageRead(s['link'])
    foreign = wpr.page_text

    if len(foreign) > max_chars:
        foreign = foreign[:max_chars]

    english = translator.translate(foreign, exclude=True)

    # # this can give duplicate results in AI summary
    # english = story['publisher_summary']+'. '+english

    story['title'] = polish_text(story['title'])
    story['publisher_summary'] = polish_text(story['publisher_summary'])
    english = polish_text(english)

    print(english)

    logging.info('Translation done.')

    if english.count('%') > 50:
        print('Encoding error translating foreign to English.')
        return None

    # ~375 is max
    block_length = 150

    summarizer.set_block_length(block_length)

    ai_summary = summarizer.summarize(english)

    for i, s in enumerate(ai_summary):
        ai_summary[i] = polish_text(ai_summary[i])

    story['ai_summary'] = ai_summary

    top, bottom = html5_template()

    upload_str = format_summary(story) + download_txt

    upload_obj_txt = s3.Object(bucket_name=bucket_name, key=blob_name_txt)

    result = upload_obj_txt.put(Body=upload_str)  # .encode('ascii'))

    res = result.get('ResponseMetadata')
    if res.get('HTTPStatusCode') == 200:
        print('Text File Uploaded Successfully')
    else:
        print('Text  File Not Uploaded')

    upload_str_html = top+upload_str+bottom

    upload_obj_html = s3.Object(bucket_name=bucket_name, key=blob_name_html)

    # .encode('ascii'))
    result = upload_obj_html.put(Body=upload_str_html, ContentType='text/html')

    res = result.get('ResponseMetadata')
    if res.get('HTTPStatusCode') == 200:
        print('HTML File Uploaded Successfully')
    else:
        print('HTML File Not Uploaded')

    toc = time()
    print(f'\nelapsed time: {round(toc-tic,2)} seconds\n')

    return story
