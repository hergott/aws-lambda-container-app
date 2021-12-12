from transformers import MarianMTModel, MarianTokenizer
import os


class Translator:

    def __init__(self,  language='de-en') -> None:
        cwd = os.getcwd()

        lambda_tmp_dir = os.path.abspath(os.path.join(cwd, 'tmp'))

        os.environ['TRANSFORMERS_CACHE'] = lambda_tmp_dir
        os.environ['HF_HOME'] = lambda_tmp_dir
        os.environ['XDG_CACHE_HOME'] = lambda_tmp_dir

        path_name = os.path.abspath(
            os.path.join(cwd, 'pretrained-models', language))

        model_name = f'Helsinki-NLP/opus-mt-{language}'

        self.model = MarianMTModel.from_pretrained(
            model_name, cache_dir=path_name)
        self.tokenizer = MarianTokenizer.from_pretrained(
            model_name, cache_dir=path_name)

    def translate(self, src_text, max_sentences=100, exclude=False):

        if isinstance(src_text, list):
            src_text = ' '.join(src_text)

        src_text = self.clean_text(src_text, exclude)

        src_text = src_text.split('.')

        src_text = [s+"." for s in src_text]

        if len(src_text) > max_sentences:
            src_text = src_text[:max_sentences]
        else:
            src_text = src_text

        out = []

        for s in src_text:

            translated = self.model.generate(
                **self.tokenizer(s, return_tensors="pt", padding=True))

            result = [self.tokenizer.decode(t, skip_special_tokens=True)
                      for t in translated]

            out.append(result[0])

        return ' '.join(out)

    def clean_text(self, txt, exclude=False):
        replace = [('\\', ''), ("'", "\'"), ('"', '\"'), ('\r', ''),
                   ('\n', ''), ('\xa0', ' '), ('  ', ' ')]

        reject = ['+++']

        if exclude:
            for r in reject:
                if r in txt:
                    txt = ''
                    break

        for r in replace:
            txt = txt.replace(r[0], r[1])

        return txt
