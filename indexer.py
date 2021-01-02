import utils
import os

class Indexer:

    def __init__(self, config):
        self.inverted_idx = {}
        self.postingDict = {}
        self.config = config

        self.indexers = [{} for i in range(28)]
        self.postings = [{} for i in range(28)]


    def add_new_doc(self, document):

        if len(document.term_doc_dictionary) == 0:
            return
        document_dictionary = document.term_doc_dictionary

        # Go over each term in the doc
        for term in document_dictionary.keys():
            try:
                idx = ord(term[0].lower()) - 97
                if 0 > idx or idx > 25: #Rule out specialists
                    idx = -1
                elif term.lower() != term and term.upper() != term:  #Rule out entities
                    idx = -2

                cur_indexer = self.indexers[idx]
                cur_posting = self.postings[idx]

                try:
                    cur_indexer[term] += 1
                except:
                    cur_indexer[term] = 1

                try:
                    cur_posting[term].append([document.to_post(document_dictionary[term])])
                except:
                    cur_posting[term] = [document.to_post(document_dictionary[term])]
            except:
                pass

    def post_indexing(self, max_n_docs_for_discard, min_n_docs_for_discard):
        before = 0

        for idx in range(-2, 26):
            cur_indexer = self.indexers[idx]
            before += len(cur_indexer)
            cur_posting = self.postings[idx]
            discard_terms = set()

            terms = list(cur_indexer)
            if idx != -2:
                for term in terms:
                    if term.isupper():
                        try:
                            cur_indexer[term.lower()] += cur_indexer[term]
                            cur_posting[term.lower()].extend(cur_posting[term])
                            discard_terms.add(term)
                        except:
                            pass

            cur_indexer = {key: cur_indexer[key] for key in terms if key not in discard_terms and
                           max_n_docs_for_discard > cur_indexer[key] > min_n_docs_for_discard}
            terms = list(cur_indexer)
            cur_posting = {key: cur_posting[key] for key in terms}

            self.inverted_idx.update(cur_indexer)
            self.postingDict.update(cur_posting)
            self.postings[idx] = {}
            self.indexers[idx] = {}

        return before, len(self.inverted_idx), len(self.postingDict)

    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def load_index(self, fn):
        """
        Loads a pre-computed index (or indices) so we can answer queries.
        Input:
            fn - file name of pickled index.
        """
        indexer = utils.load_obj(os.path.join(self.config.saveFilesDir, fn[:-4]))
        self.inverted_idx = indexer[0]
        self.postingDict = indexer[1]

        # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def save_index(self, fn):
        """
        Saves a pre-computed index (or indices) so we can save our work.
        Input:
              fn - file name of pickled index.
        """
        utils.save_obj([self.inverted_idx, self.postingDict], os.path.join(self.config.saveFilesDir, fn[:-4]))