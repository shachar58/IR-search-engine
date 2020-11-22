from reader import ReadFile
from configuration import ConfigClass
from parser_module import Parse
from indexer import Indexer
from searcher import Searcher
import utils
import time
import sys
import os
import multiprocessing

def run_engine():
    """

    :return:
    """
    number_of_documents = 0
    timer = True
    config = ConfigClass()
    r = ReadFile(corpus_path=config.get__corpusPath())
    p = Parse() #p = Parse(with_stemmer=True)
    indexer = Indexer(config)

    data_dir = 'Data' + os.sep + 'Data'
    npy_dirs = [root for root, dirs, files in os.walk(data_dir)]
    for dir_path in npy_dirs:
        files = [os.path.join(dir_path, fname) for fname in os.listdir(dir_path) if fname.endswith('.parquet')]
        for file in files:
            tweets = r.read_file(file_name=file)
            start_time = time.perf_counter()
            documents_list = multiprocessing.Pool(12).map(p.parse_doc, tweets)
            end_time = time.perf_counter()
            avg_time_per_tweet = (end_time - start_time) / len(tweets)
            print(f'Parsed {len(tweets)} tweets, Elapsed time: {end_time - start_time:0.4f} seconds, average per tweet: {avg_time_per_tweet:0.8f} seconds')

            start_time = time.perf_counter()
            for parsed_document in documents_list:
                indexer.add_new_doc(parsed_document)
            end_time = time.perf_counter()
            print(f'Indexing {len(documents_list)} tweets, Elapsed time: {end_time - start_time:0.4f} seconds')
    print('Finished parsing and indexing. Starting to export files')
    utils.save_obj(indexer.inverted_idx, "inverted_idx")
    utils.save_obj(indexer.postingDict, "posting")


def load_index():
    print('Load inverted index')
    inverted_index = utils.load_obj("inverted_idx")
    return inverted_index


def search_and_rank_query(query, inverted_index, k):
    p = Parse()
    query_as_list = p.parse_sentence(query)
    searcher = Searcher(inverted_index)
    relevant_docs = searcher.relevant_docs_from_posting(query_as_list)
    ranked_docs = searcher.ranker.rank_relevant_doc(relevant_docs)
    return searcher.ranker.retrieve_top_k(ranked_docs, k)


def main():
    run_engine()
    query = input("Please enter a query: ")
    k = int(input("Please enter number of docs to retrieve: "))
    inverted_index = load_index()
    for doc_tuple in search_and_rank_query(query, inverted_index, k):
        print('tweet id: {}, score (unique common words with query): {}'.format(doc_tuple[0], doc_tuple[1]))
