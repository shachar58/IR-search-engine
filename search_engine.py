from reader import ReadFile
from configuration import ConfigClass
from parser_module import Parse
from indexer import Indexer
from searcher import Searcher
import utils
import time
import sys

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

    documents_list = r.read_file(file_name='Data/Data/date=07-08-2020/covid19_07-08.snappy.parquet')

    # Iterate over every document in the file
    start_time = time.perf_counter()
    n_doc_lst = len(documents_list)
    total_times = [0, 0, 0, 0, 0, 0, 0, 0]
    for idx, document in enumerate(documents_list):
        # parse the document
        times, parsed_document = p.parse_doc(document)
        number_of_documents += 1
        # index the document data
        indexer.add_new_doc(parsed_document)
        end_time = time.perf_counter()

        # pre_parse, slashes, comma, numbers, perc/dollars/KMB, stop_words@#, entities, rest
        for t in range(len(times)):
            total_times[t] = total_times[t] * idx + times[t]
            total_times[t] = round(total_times[t] / (idx + 1), 6)


        avg_time_per_tweet = round((end_time - start_time) / (idx + 1), 3)
        estimate_time = int(((n_doc_lst - idx) * avg_time_per_tweet) / 60)
        # sys.stdout.write('\r' + str(idx) + '/' + str(n_doc_lst) + ', avg. per tweet:' + str(avg_time_per_tweet)
        #                  + ' seconds, estimated end time: ' + str(estimate_time) + 'mins')

        sys.stdout.write('\r' + str(idx) + '/' + str(n_doc_lst)
                         + ', avg. per tweet:' + str(avg_time_per_tweet)
                         + ' seconds, pre_parse:' + str(total_times[0])
                         + ' seconds, slashes:' + str(total_times[1])
                         + ' seconds, comma:' + str(total_times[2])
                         + ' seconds, numbers:' + str(total_times[3])
                         + ' seconds, perc/dollars/KMB:' + str(total_times[4])
                         + ' seconds, stop_words@#:' + str(total_times[5])
                         + ' seconds, entities:' + str(total_times[6])
                         + ' seconds, rest:' + str(total_times[7])
                         + ' seconds, estimated end time: ' + str(estimate_time) + 'mins')


    end_time = time.perf_counter()
    if timer:
        print(f'Elapsed parsing time: {end_time - start_time:0.4f} seconds')
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
