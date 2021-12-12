from bs4 import BeautifulSoup
import sys
import requests
import re


class WebPageRead:

    def __init__(self, page_url):
        self.page_url = page_url
        print(page_url)
        print(f'Parsing link: {self.page_url}')

        try:
            response = requests.get(self.page_url)

        except Exception as e:
            error_type, error_obj, error_info = sys.exc_info()
            print('ERROR FOR LINK:', self.page_url)
            print(error_type, 'Line:', error_info.tb_lineno)

        parser = 'html.parser'
        encoding = 'utf-8'
        self.html_parse = BeautifulSoup(
            response.content, parser, from_encoding=encoding)

        paragraph_blacklist = ['©']

        print(f'Getting paragraphs.')

        paragraphs = self.html_parse.find_all("p")

        print(f'There are {len(paragraphs)} paragraphs.')

        p_text = []

        for p in paragraphs:
            txt = p.get_text()

            ignore = False

            for b in paragraph_blacklist:
                if b in txt:
                    ignore = True
                    break

            if not ignore:
                txt = self.clean_text(txt)
                p_text.append(txt)

        p_text = ' '.join(p_text)

        self.page_text = re.sub(' +', ' ', p_text)

        return None

    def clean_text(self, txt):
        txt = txt.replace('<span>', '')
        txt = txt.replace('</span>', '')
        txt = txt.replace('(dpa)', '')
        txt = txt.replace('</a>', '')
        txt = txt.replace('+++', '')
        txt = txt.replace('\xa0', '')
        txt = txt.strip()

        return txt
