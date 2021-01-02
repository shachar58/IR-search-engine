import pandas as pd
from reader import ReadFile
from configuration import ConfigClass
from parser_module import Parse
from indexer import Indexer
from searcher import Searcher
import utils
import multiprocessing
import sys
from time import perf_counter
import os

# DO NOT CHANGE THE CLASS NAME
class SearchEngine:

    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation, but you must have a parser and an indexer.
    def __init__(self, config=None):
        self._config = config
        self._parser = Parse()
        self._indexer = Indexer(self._config)
        self.reader = ReadFile(config.get__corpusPath())
        self._model = None
        self.number_of_docs = 0

    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def build_index_from_parquet(self, fn):
        """
        Reads parquet file and passes it to the parser, then indexer.
        Input:
            fn - path to parquet file
        Output:
            No output, just modifies the internal _indexer object.
        """
        start = perf_counter()
        documents_list = self.reader.read_file(fn)
        documents_list = multiprocessing.Pool().map(self._parser.parse_doc, documents_list)
        self.number_of_docs += len(documents_list)
        [self._indexer.add_new_doc(parsed_document) for parsed_document in documents_list]
        end = perf_counter()
        sys.stdout.write(
            '\rParsed: ' + str(self.number_of_docs) + ', Avg: ' + str((end - start) / len(documents_list)))

    def run_engine(self):
        data_dir = self._config.get__corpusPath()
        npy_dirs = [dirs for root, dirs, files in os.walk(data_dir)]
        npy_dirs = [item for sublist in npy_dirs for item in sublist]
        for dirr in npy_dirs:
            files = [os.path.join(dirr, file) for file in os.listdir(os.path.join(data_dir, dirr)) if file.endswith('.parquet')]
            for file in files:
                self.build_index_from_parquet(file)
        start = perf_counter()
        before, after, after_ = self._indexer.post_indexing(27000, 7.5)
        end = perf_counter()
        print('\nPost indexing:', str(end - start), ', Terms before:', before, ', Terms after:', after, " ", after_)
        self._indexer.save_index('new_indexer.pkl')


    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def load_index(self, fn):
        """
        Loads a pre-computed index (or indices) so we can answer queries.
        Input:
            fn - file name of pickled index.
        """
        self._indexer.load_index(fn)

    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def load_precomputed_model(self):
        """
        Loads a pre-computed model (or models) so we can answer queries.
        This is where you would load models like word2vec, LSI, LDA, etc. and 
        assign to self._model, which is passed on to the searcher at query time.
        """
        pass

        # DO NOT MODIFY THIS SIGNATURE
        # You can change the internal implementation as you see fit.

    def search(self, query):
        """ 
        Executes a query over an existing index and returns the number of 
        relevant docs and an ordered list of search results.
        Input:
            query - string.
        Output:
            A tuple containing the number of relevant search results, and 
            a list of tweet_ids where the first element is the most relavant 
            and the last is the least relevant result.
        """
        searcher = Searcher(self._parser, self._indexer, model=self._model)
        return searcher.search(query)

def main():
    config = ConfigClass()
    se = SearchEngine(config)
    se.run_engine()