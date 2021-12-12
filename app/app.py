from functions.Translator import Translator
from functions.Summarizer import Summarizer

from functions.translate_summarize import translate_summarize

import json


def handler(event, context):

    de = 'https://www.deutschland.de/de/feed-news/rss.xml'
    feed_url = de

    repetitions = 1

    t5_version = 't5-base'

    translator = Translator()
    summarizer = Summarizer(t5_version=t5_version)

    for _ in range(repetitions):
        res = translate_summarize(
            feed_url, translator=translator, summarizer=summarizer, max_chars=25000)

        print(res)

    return {'headers': {'Content-Type': 'application/json'}, 'statusCode': 200, 'body': json.dumps({"message": res, "event": event})}

# handler(event='', context='')
