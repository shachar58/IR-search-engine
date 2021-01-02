from nltk.corpus import stopwords
from document import Document
import re
import time
from stemmer import Stemmer
class Parse:

    def __init__(self, with_stem=False):
        self.stemmer = Stemmer()
        self.with_stemmer = with_stem
        self.stop_words = stopwords.words('english')
        self.stop_words += ["i'm", "it's", 'they', "i've", 'you', 'u', 'we', 'rt', 'im', 'use', 'sure', 'https', 'www',
                            'p', 'igshid', 'wear', 't.co', 'covid', 'covid-19', 'people', 'new', 'amp',
                            'like', 'get']
        self.times = []
        self.timer = False

    def _is_number(self, number):
        return number.replace(',', '').replace('.', '', 1).replace('%', '', 1).replace('$', '', 1).replace('K', '', 1) \
            .replace('M', '', 1).replace('B', '', 1).isdigit()

    def _pre_parse(self, text):
        text = ' '.join([w for w in text.split(' ') if '…' not in w])
        whitespace = ' \t\n\r\v\f'
        ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
        ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        # punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
        punctuation = r"""!#$%&'*’+,-./<=>?@[\]^_{|}~"""
        printable = digits + ascii_lowercase + ascii_uppercase + punctuation + whitespace
        text = ''.join([x for x in text if x in printable])

        text = text.replace('\n', ' ')  # remove new lines
        text = re.sub(' +', ' ', text)  # Remove double spaces
        text = re.sub('-', " ", text)
        text = re.sub('’', "'", text)
        return text

    def _extract_entities(self, text):
        entities_terms = []
        subterm = ''

        for subtext in text.split(', '):
            sub_terms = subtext.replace('-', ' ').split(' ')
            for term in sub_terms:
                if not term.replace("'", '').isalnum(): #Not a word
                    if len(subterm.split(' ')) >= 2:
                        entities_terms.append(subterm)
                    subterm = ''
                elif term[0].isupper() and term[0].upper() == term[0]:
                    if subterm == '':
                        subterm = term.replace('-', ' ')
                    else:
                        subterm += ' ' + term.replace('-', ' ')
                else:
                    if len(subterm.split(' ')) >= 2:
                        entities_terms.append(subterm)
                    subterm = ''
            entities_terms.append(subterm)

        entities_terms = [term for term in entities_terms if term != '']
        return entities_terms

    def _number_transform(self, term):
        opt_term = term.replace('%', '', 1).replace('$', '', 1).replace('K', '', 1) \
            .replace('M', '', 1).replace('B', '', 1)
        replaced_term_optional = opt_term.replace(',', '')
        if not self._is_number(term.replace(',', '')):
            return term

        if float(replaced_term_optional) < 1000:
            number = round(float(replaced_term_optional), 3)
            if number == float(int(float(replaced_term_optional))):
                number = int(number)
            return term.replace(replaced_term_optional, str(number))

        elif float(replaced_term_optional) < 1000000:
            if term.isdigit() and len(term) == 4 and int(term) > 1500 and int(term) < 2100:  # Maybe an year
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
        else:
            return term

    def _url_transform(self, url):
        url_parts = url.split('/')[2:]

        addr = url_parts[0]
        addr_parts = addr.split('.')
        addr_parts = [addr_parts[0]] + ['.'.join(addr_parts[1:])] if addr_parts[0] == 'www' else ['.'.join(addr_parts)]

        parts = []
        parts += addr_parts

        for info in url_parts[1:]:
            for inf in info.split('?'):
                props = inf.split('&')
                for prop in props:
                    if '=' not in prop:
                        parts = parts + prop.split('-')

        parts = [p for p in parts if p != '' and len(p) != 1 and p.isalpha()]
        return parts

    def remove_punctuation(self, w):
        w_prev = ''
        while w_prev != w:
            w_prev = w
            w = re.sub('[-]+', ' ', w)
            w = re.sub('[..]+[...]+', '', w)
            w = re.sub('[’]+', "'", w)
            w = re.sub(r"^[!&'*+,.?<=>{}|~_]*|[!&'*+,.?<=>{}|~_]*$", '', w)
        return w

    def _splitHashtags(self, term_):
        for i in range(len(term_) - 1)[::-1]:
            if term_[i].isupper() and term_[i + 1].islower():
                term_ = term_[:i] + ' ' + term_[i:]
            if term_[i].isupper() and term_[i - 1].islower():
                term_ = term_[:i] + ' ' + term_[i:]
        return term_.split()

    def _hashtags_tag_parse(self, tokens):
        result_tokens = []
        rest_tokens = []
        for w in tokens:
            if w[0] == '#':
                for subw in w[1:].split('_'):
                    splited_hashtag = self._splitHashtags(subw)
                    result_tokens += [sub_hashtag.lower() for sub_hashtag in splited_hashtag]
                #result_tokens.append(w.replace('_', '').lower())
            elif w[0] == '@':
                 pass
                 #result_tokens.append(w)
            else:
                rest_tokens.append(w)
        return result_tokens, rest_tokens

    def _special_parse(self, tokens):
        parse_number_comma_tokens = []
        for w in tokens:
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
        return parse_number_comma_tokens

    def _remove_slashes(self, tokens):
        result_tokens = []

        for token in tokens:
            if len(token.split('/')) == 1:
                result_tokens.append(token)
                continue
            splited = token.split('/')
            if len(splited) == 2 and splited[0].isdigit() and splited[1].isdigit():
                result_tokens.append(token)
            else:
                result_tokens += splited
        return result_tokens

    def _apply(self, func, input):
        end_time, start_time = 0, 0
        if self.timer:
            start_time = time.perf_counter()
            result = func(input)
            end_time = time.perf_counter()
        else:
            result = func(input)

        self.times.append(end_time - start_time)
        return result

    def parse_sentence(self, text):
        self.timer = False
        self.times = []

        text = self._apply(self._pre_parse, text)
        entities = self._apply(self._extract_entities, text)

        tokens = text.split(' ')
        covid = [token for token in tokens if token.lower() == 'covid-19']
        removed_urls_tokens = [w for w in tokens if not w.startswith('https') or w.lower() != 'covid-19']
        tokens = self._apply(self._remove_slashes, removed_urls_tokens)

        remove_comma_terms = [self.remove_punctuation(term) for term in tokens]
        entities_terms = [self.remove_punctuation(term) for term in entities]

        fix_numbers_terms = [self._number_transform(w) for w in remove_comma_terms if w != '']

        parse_number_comma_tokens = self._apply(self._special_parse, fix_numbers_terms)

        parse_number_comma_tokens = [w for w in parse_number_comma_tokens if w.lower() not in self.stop_words]

        hashtags_tag_parsed, rest_tokens = self._apply(self._hashtags_tag_parse, parse_number_comma_tokens)

        capital_tokens = [token.upper() for token in rest_tokens if token.lower() != token]
        rest_tokens = [token for token in rest_tokens if token.lower() == token] + capital_tokens

        if self.with_stemmer:
            rest_tokens = [self.stemmer.stem_term(token) for token in rest_tokens]
        total_tokens = rest_tokens + entities_terms + hashtags_tag_parsed + covid
        total_tokens = [token for token in total_tokens if token != '' or len(token) == 1]

        return total_tokens

    def _parse_urls(self, urls):
        try:
            urls = urls.replace('null', 'None')
            urls_tokens = [self._url_transform(w) for w in eval(urls).values() if
                           w != '' and w is not None and 'twitter.com' not in w]
            urls_tokens = [item.split('-') for sublist in urls_tokens for item in sublist]
            urls_tokens = [item for sublist in urls_tokens for item in sublist]
            urls_tokens = [w for w in urls_tokens if w.lower() not in self.stop_words]
            if self.with_stemmer:
                urls_tokens = [self.stemmer.stem_term(token) for token in urls_tokens]
        except:
            urls_tokens = []
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
            tokenized_text = self.parse_sentence(full_text) + self._parse_urls(url)
            discard_terms = [token for token in tokenized_text if token.isdigit() or (token.isalnum() and not token.isalpha())]
            tokenized_text = [token for token in tokenized_text if token not in discard_terms]
        except:
            tokenized_text = []

        doc_length = len(tokenized_text)  # after text operations.

        for term in tokenized_text:
            try:
                term_dict[term] += 1
            except:
                term_dict[term] = 1

        document = Document(tweet_id, tweet_date, full_text, url, retweet_text=None, retweet_url=None,
                            quote_text=quote_text, quote_url=quote_url, term_doc_dictionary=term_dict,
                            doc_length=doc_length)
        return document