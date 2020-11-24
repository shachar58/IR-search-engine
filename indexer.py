class Indexer:

    def __init__(self, config):
        self.inverted_idx = {}
        self.postingDict = {}
        self.config = config

    def add_new_doc(self, document):
        """
        This function perform indexing process for a document object.
        Saved information is captures via two dictionaries ('inverted index' and 'posting')
        :param document: a document need to be indexed.
        :return: -
        """

        document_dictionary = document.term_doc_dictionary
        uniques = []
        max_tf = 0
        tf = {}
        # Go over each term in the doc
        for term in document_dictionary.keys():
            #TODO: improve inv index algo
            #TODO: chunk indexing
            document.tf[term] += 1  # tf count in doc
            try:
                # Update inverted index and posting
                if term not in self.inverted_idx.keys():
                    self.inverted_idx[term] = 1
                    self.postingDict[term] = []
                    uniques.append(term)
                else:
                    self.inverted_idx[term] += 1    # inverted_idx=DF
                    uniques.remove(term)
                    if self.inverted_idx[term] > max_tf:
                        document.max_tf = self.inverted_idx[term]
                document.unique_terms = uniques
                self.postingDict[term].append(document)     # postingDict[term] = list of documents it appears

            except:
                print('problem with the following key {}'.format(term[0]))
