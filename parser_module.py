from nltk.corpus import stopwords
from document import Document
import re
import spacy
from stemmer import Stemmer
import sys
import time

nlp = spacy.load("en_core_web_sm")


class Parse:

    def __init__(self, with_stemmer=False, include_urls=False, include_quote=False):
        self.stemmer = Stemmer()
        self.with_stemmer = with_stemmer
        self.include_urls = include_urls
        self.include_quote = include_quote
        self.stop_words = stopwords.words('english')
        self.stop_words += ["i'm", "it's", 'they', "i've", 'you', 'u', 'we', 'rt', 'im', 'use', 'sure', ]

    def _is_number(self, number):
        return number.replace(',', '').replace('.', '', 1).replace('%', '', 1).replace('$', '', 1).replace('K', '', 1) \
            .replace('M', '', 1).replace('B', '', 1).isdigit()

    def _number_transform(self, term):
        opt_term = term.replace('%', '', 1).replace('$', '', 1).replace('K', '', 1) \
            .replace('M', '', 1).replace('B', '', 1)
        replaced_term_optional = opt_term.replace(',', '')
        if not self._is_number(replaced_term_optional):
            return term

        if float(replaced_term_optional) < 1000:
            number = round(float(replaced_term_optional), 3)
            if number == float(int(float(replaced_term_optional))):
                number = int(number)
            return term.replace(replaced_term_optional, str(number))

        elif float(replaced_term_optional) < 1000000:
            if term.isdigit() and len(term) == 4:  # Maybe an year
                return term
            else:
                number = round(float(replaced_term_optional) / 1000, 3)
                if number == float(float(replaced_term_optional) // 1000):
                    number = int(number)
                return term.replace(opt_term, str(number) + 'K')
        elif float(replaced_term_optional) < 1000 * 1000 * 1000:
            number = round(float(replaced_term_optional) / 1000000, 3)
            if number == float(float(replaced_term_optional) // 1000000):
                number = int(number)
            return term.replace(opt_term, str(number) + 'M')
        elif float(replaced_term_optional) < 1000 * 1000 * 1000 * 1000:
            number = round(float(replaced_term_optional) / 1000000, 3)
            if number == float(float(replaced_term_optional) // 1000000):
                number = int(number)
            return term.replace(opt_term, str(number) + 'B')

    def _url_transform(self, url):
        parts = []

        url_parts = url.split('/')
        parts.append(url_parts[0][:-1])

        addr = url_parts[2]
        addr_parts = addr.split('.')
        addr_parts = [addr_parts[0]] + ['.'.join(addr_parts[1:])] if addr_parts[0] == 'www' else ['.'.join(addr_parts)]

        parts = parts + addr_parts + url_parts[3:-1]

        info = url_parts[-1].split('?')

        if len(info) == 1:
            parts = parts + info
        elif len(info) == 3:
            assert 1 == 0
        else:
            parts.append(info[0])

            props = info[1].split('&')
            for prop in props:
                parts = parts + prop.split('=')

        parts = [p for p in parts if p != '']
        return parts

    def _splitHashtags(self, term_):
        for i in range(len(term_) - 1)[::-1]:
            if term_[i].isupper() and term_[i + 1].islower():
                term_ = term_[:i] + ' ' + term_[i:]
            if term_[i].isupper() and term_[i - 1].islower():
                term_ = term_[:i] + ' ' + term_[i:]
        return term_.split()

    def _pre_parse(self, text):
        text = ' '.join([w for w in text.split(' ') if '…' not in w])
        whitespace = ' \t\n\r\v\f'
        ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
        ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        # punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
        punctuation = r"""!#$%&'*+,-./<=>?@[\]^_{|}~"""
        printable = digits + ascii_lowercase + ascii_uppercase + punctuation + whitespace
        text = ''.join([x for x in text if x in printable])

        text = text.replace('\n', ' ')  # remove new lines
        text = re.sub(' +', ' ', text)  # Remove double spaces
        return text

    def parse_sentence(self, text):
        """
        This function tokenize, remove stop words and apply lower case for every word within the text
        :param text:
        :return:
        """

        # print('Text:', text)
        timer = True
        times = []

        if timer:
            start_time = time.perf_counter()

        text = self._pre_parse(text)
        temp_text_tokens = text.split(' ')


        if timer:
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        removed_urls_tokens = [w for w in temp_text_tokens if not w.startswith('https')]

        if timer:
            start_time = time.perf_counter()

        text_tokens = []
        for token in removed_urls_tokens:
            if len(token.split('/')) == 1:
                text_tokens.append(token)
                continue
            splited = token.split('/')
            if len(splited) == 2 and splited[0].isdigit() and splited[1].isdigit():
                text_tokens.append(token)
            else:
                text_tokens += splited

        if timer:
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        # print('After cleaning slashes', text_tokens)

        if timer:
            start_time = time.perf_counter()


        remove_comma_terms = []
        for w in text_tokens:
            w = re.sub('[,]*$', '', w)
            w = re.sub('[.]*$', '', w)
            w = re.sub('^[,]*', '', w)
            w = re.sub('^[.]*', '', w)
            w = re.sub('[:]*$', '', w)
            w = re.sub('[-]*', ' ', w)
            w = re.sub('[?]*$', '', w)
            w = re.sub('[!]*$', '', w)
            if w != '':
                remove_comma_terms.append(w)


        if timer:
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        # print('After remove comma:', remove_comma_terms)

        if timer:
            start_time = time.perf_counter()


        fix_numbers_terms = [self._number_transform(w) for w in remove_comma_terms]

        if timer:
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        if timer:
            start_time = time.perf_counter()


        parse_number_comma_tokens = []
        for w in fix_numbers_terms:
            n_new_text_tokens = len(parse_number_comma_tokens) - 1
            if (w.lower() == 'percent' or w.lower() == 'percentage') and len(parse_number_comma_tokens) != 0 and \
                    self._is_number(parse_number_comma_tokens[n_new_text_tokens]):
                parse_number_comma_tokens[n_new_text_tokens] = parse_number_comma_tokens[n_new_text_tokens] + '%'
            elif (w.lower() == 'dollar' or w.lower() == 'dollars') and len(parse_number_comma_tokens) != 0 and \
                    self._is_number(parse_number_comma_tokens[n_new_text_tokens]):
                parse_number_comma_tokens[n_new_text_tokens] = parse_number_comma_tokens[n_new_text_tokens] + '$'
            elif w.lower() == 'thousand' and len(parse_number_comma_tokens) != 0 and \
                    self._is_number(parse_number_comma_tokens[n_new_text_tokens]):
                parse_number_comma_tokens[n_new_text_tokens] = parse_number_comma_tokens[n_new_text_tokens] + 'K'
            elif (w.lower() == 'million' or w.lower() == 'mill') and len(parse_number_comma_tokens) != 0 and \
                    self._is_number(parse_number_comma_tokens[n_new_text_tokens]):
                parse_number_comma_tokens[n_new_text_tokens] = parse_number_comma_tokens[n_new_text_tokens] + 'M'
            elif w.lower() == 'billion' and len(parse_number_comma_tokens) != 0 and \
                    self._is_number(parse_number_comma_tokens[n_new_text_tokens]):
                parse_number_comma_tokens[n_new_text_tokens] = parse_number_comma_tokens[n_new_text_tokens] + 'B'
            elif len(w.split('/')) == 2 and w.split('/')[0].isdigit() and len(parse_number_comma_tokens) != 0 and \
                    w.split('/')[1].isdigit() and self._is_number(parse_number_comma_tokens[n_new_text_tokens]):
                parse_number_comma_tokens[n_new_text_tokens] = parse_number_comma_tokens[n_new_text_tokens] + ' ' + w
            else:
                parse_number_comma_tokens.append(w)

        if timer:
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        # print('After numbers comma:', parse_number_comma_tokens)

        if timer:
            start_time = time.perf_counter()


        text_tokens_without_stopwords = []
        rest_tokens = []
        for w in parse_number_comma_tokens:
            if w.lower() in self.stop_words:
                continue
            if w[0] == '#':
                for subw in w[1:].split('_'):
                    splited_hashtag = self._splitHashtags(subw)
                    text_tokens_without_stopwords += [sub_hashtag.lower() for sub_hashtag in splited_hashtag]
                text_tokens_without_stopwords.append(w.replace('_', '').lower())
            elif w[0] == '@':
                text_tokens_without_stopwords.append(w)
            else:
                rest_tokens.append(w)


        if timer:
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        if timer:
            start_time = time.perf_counter()

        entities = nlp(' '.join(rest_tokens))
        entities = [entity.text for entity in entities.ents if entity.label_ in ['PERSON', 'ORG', 'GPE', 'NORP', 'FAC']]

        if timer:
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        if timer:
            start_time = time.perf_counter()

        rest_tokens = [token for token in rest_tokens if token not in entities]
        capital_tokens = [token for token in rest_tokens if token.lower() != token]
        rest_tokens = [token for token in rest_tokens if token.lower() == token]

        if timer:
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        if self.with_stemmer:
            rest_tokens = [self.stemmer.stem_term(token) for token in rest_tokens]
        total_tokens = rest_tokens + entities + text_tokens_without_stopwords + capital_tokens
        # print('After:', total_tokens)
        # print('------------------------------------------------------------------------------------------')
        return times, total_tokens

    def _parse_urls(self, urls):
        urls = urls.replace('null', 'None')
        urls_tokens = [self._url_transform(w) for w in eval(urls).values() if
                       w != '' and w != None and 'twitter.com' not in w]
        urls_tokens = [item for sublist in urls_tokens for item in sublist]
        return urls_tokens

    def parse_doc(self, doc_as_list):
        """
        This function takes a tweet document as list and break it into different fields
        :param doc_as_list: list re-preseting the tweet.
        :return: Document object with corresponding fields.
        """

        tweet_id = doc_as_list[0]
        tweet_date = doc_as_list[1]
        full_text = doc_as_list[2]
        url = doc_as_list[3]
        quote_text = doc_as_list[8]
        quote_url = doc_as_list[9]
        term_dict = {}

        try:
            times, tokenized_text = self.parse_sentence(full_text)
        except:
            print(full_text)
            print(sys.exc_info()[0])
            tokenized_text = []
            times = [0] * 7

        if self.include_urls:
            tokenized_text += self._parse_urls(url)

        if self.include_quote and quote_text is not None:
            tokenized_text += self.parse_sentence(quote_text)

        if self.include_quote and self.include_urls and quote_url is not None:
            tokenized_text += self._parse_urls(quote_url)

        doc_length = len(tokenized_text)  # after text operations.

        for term in tokenized_text:
            if term not in term_dict.keys():
                term_dict[term] = 1
            else:
                term_dict[term] += 1

        document = Document(tweet_id, tweet_date, full_text, url, retweet_text=None, retweet_url=None,
                            quote_text=quote_text, quote_url=quote_url, term_doc_dictionary=term_dict,
                            doc_length=doc_length)
        return times, document
