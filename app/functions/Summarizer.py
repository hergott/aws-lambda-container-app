# from transformers import T5Tokenizer, TFT5ForConditionalGeneration
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import os

from transformers.file_utils import TORCH_ONNX_DICT_INPUTS_MINIMUM_VERSION


class Summarizer:

    def __init__(self, t5_version='t5-small') -> None:
        # Available  versions:
        # t5-small
        # T5-base = 220 million parameters
        # T5-large = 770 million parameters
        # T5–3B = 3 billion parameters
        # T5–11B = 11 billion parameters

        self.set_block_length

        t5_version = t5_version.lower().strip()
        if t5_version == 't5-small':
            t5_directory = 't5-small'
        elif t5_version == 't5-base':
            t5_directory = 't5-base'
        elif t5_version == 't5-large':
            t5_directory = 't5-large'
        else:
            raise ValueError(
                'This app can only use "t5-small", "t5-base", or "t5-large."')

        cwd = os.getcwd()

        lambda_tmp_dir = os.path.abspath(os.path.join(cwd, 'tmp'))

        os.environ['TRANSFORMERS_CACHE'] = lambda_tmp_dir
        os.environ['HF_HOME'] = lambda_tmp_dir
        os.environ['XDG_CACHE_HOME'] = lambda_tmp_dir

        path_name = os.path.abspath(
            os.path.join(cwd, 'pretrained-models', t5_directory))

        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            t5_version, cache_dir=path_name)
        self.tokenizer = AutoTokenizer.from_pretrained(
            t5_version, cache_dir=path_name)

    def set_block_length(self, block_length=375):
        self.block_length = block_length

    def find_token_separators(self, str, separator=' '):
        separators = []
        index = 0

        while index < len(str):
            index = str.find(separator, index)

            if index > -1:
                separators.append(index)
                index = index+1
            else:
                break

        return separators

    def create_text_blocks(self, text_in, min_block_words=40, max_blocks=10):

        spaces = text_in.count(' ')

        if spaces < min_block_words:
            return None

        if spaces < self.block_length:
            text_blocks = [text_in]
            return text_blocks

        sentences = text_in.split('. ')

        sentences = [s.strip() for s in sentences]

        n_sentences = len(sentences)

        current_sentence = 0
        current_block = 0
        current_block_tokens = 0

        text_blocks = []
        sentence_list = []

        while current_sentence < n_sentences and current_block < max_blocks:

            spaces = self.find_token_separators(sentences[current_sentence])

            if len(spaces) < 1:
                current_sentence = current_sentence+1
                continue

            if (current_block_tokens+len(spaces)+1) > self.block_length:

                txt = ''
                for s in sentence_list:
                    txt = txt+' '+sentences[s]+'.'

                text_blocks.append(txt)

                sentence_list = []
                current_block_tokens = 0
                current_block = current_block+1

                continue

            else:
                sentence_list.append(current_sentence)
                current_block_tokens = current_block_tokens+len(spaces)+1
                current_sentence = current_sentence+1

            if current_sentence == n_sentences:
                txt = ''
                for s in sentence_list:
                    txt = txt+' '+sentences[s]+'.'

                spaces = self.find_token_separators(txt)
                if len(spaces) >= min_block_words:
                    text_blocks.append(txt)

                break

        # for t in text_blocks:
        #     print(t)
        #     print('\r\r\r')

        #     spaces = self.find_token_separators(t)
        #     print(len(spaces))

        return text_blocks

    def strip_tags(self, summarizations):
        delete_tokens = ['<pad>', '<extra_id_0>',
                         ',<extra_id_1>', '</s>', ',<extra_id_2>', ',<extra_id_3>', ',<extra_id_4>', '<extra_id_1>', '<extra_id_2>', '<extra_id_3>', '<extra_id_4>', '<extra_id_5>', '<extra_id_6>', '<extra_id_7>', '<extra_id_8>', '<extra_id_9>']

        for i, s in enumerate(summarizations):
            for d in delete_tokens:
                summarizations[i] = summarizations[i].replace(d, '')

            if summarizations[i][-1] != '.':
                summarizations[i] = summarizations[i]+'.'

        return summarizations

    def summarize(self, text_in, summary_min_length=10, summary_max_length=50):
        text_blocks = self.create_text_blocks(text_in)

        if text_blocks is None:
            return ['ERROR: Insufficient text for summarization.']

        summarizations = []

        for txt in text_blocks:

            print(txt)

            tokens_input = self.tokenizer.encode(
                txt, return_tensors="pt", max_length=512, truncation=True)

            print(
                f'block length: {txt.count(" ")}, tensor length: {tokens_input.size()}')

            summary_ids = self.model.generate(tokens_input, max_length=summary_max_length, min_length=summary_min_length,
                                              num_beams=30, early_stopping=False, do_sample=False, use_cache=True)
            #  , length_penalty=0.5 , num_beams=12, early_stopping=False, do_sample=False, use_cache=True, num_beam_groups=3, diversity_penalty=1.5)

            summary = []

            for si in summary_ids:
                summary.append(self.tokenizer.decode(si))

            summarizations.append(summary[0].strip())

        self.strip_tags(summarizations)

        return summarizations
