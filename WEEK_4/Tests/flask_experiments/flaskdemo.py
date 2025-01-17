from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re
from nltk.stem import *
from nltk.tokenize import sent_tokenize, word_tokenize
import operator
import time

from flask import Flask, render_template, request

#Initialize Flask instance
app = Flask(__name__)

example_data = [
    {'name': 'Cat sleeping on a bed', 'source': 'cat.jpg'},
    {'name': 'Misty forest', 'source': 'forest.jpg'},
    {'name': 'Bonfire burning', 'source': 'fire.jpg'},
    {'name': 'Old library', 'source': 'library.jpg'},
    {'name': 'Sliced orange', 'source': 'orange.jpg'}
]


@app.route('/')
def hello_world():
   return "Add /engine to get to our search engine!"

#Function search() is associated with the address base URL + "/search"
@app.route('/search')
def search():

    #Get query from URL variable
    query = request.args.get('query')

    #Initialize list of matches
    matches = []

    #If query exists (i.e. is not None)
    if query:
        #Look at each entry in the example data
        for entry in example_data:
            #If an entry name contains the query, add the entry to matches
            if query.lower() in entry['name'].lower():
                matches.append(entry)

    #Render index.html with matches variable
    return render_template('index.html', matches=matches)


@app.route('/engine')
def engine():

#Get query from URL variable
    query = request.args.get('query')

    matches = []

    # ### 1 READING IN FILES AND PREPARING INITIAL DATA
    # # 1a Splitting textstring into separate articles
    def readandcut(file_path):
        with open(file_path, "r") as file:
            text = file.read()

        text = str(text)

        cuttext = text.split("</article>")
        cuttext = cuttext[:-1]
        return text, cuttext

    # 1b Splitting 100 documents into lines
    def linesplitter_and_cleaner(document):

        #making a list of lines of the document
        doc_lines = document.splitlines()

        #removing lines that are empty
        for line in doc_lines:
            if len(line) < 1:
                doc_lines.remove(line)

        return doc_lines

    # 1c default file_path used
    file_path = "enwiki-20181001-corpus.100-articles.txt"

    # 1d executing readandcut() function and saving full 
    # string into "text" and split articles into "documents"
    text, documents = readandcut(file_path)
    print("checking print() statement!")
    print(text[300:])

    ### 2 CODE FOR USER INTERACTION AND INTERFACE MESSAGES 
    # 2a Welcome message
    def welcome():

        welcome_message = "Welcome to HALM search engine!"

        print()
        print("*"*len(welcome_message))
        print(welcome_message)
        print("*"*len(welcome_message))
        print()

    # 2b Goodbye message
    def goodbye():
            
        quit_message = "Quitting program. Thank you for using the HALM Search Engine!"
        
        print()
        print("*"*len(quit_message))
        print(quit_message)
        print("*"*len(quit_message))
        print()

    # 2c User chooses a search mode – "boolean" or "tfv"
    def choose_bool_or_tfv_or_stems():

        answer = ""
        while True:
            answer = input("Choose 'boolean', 'tfv' or 'stems' search: ")
            if answer == "boolean":
                    print("Use only lower-case unless using the AND, OR and AND NOT commands in 'boolean' mode")
                    return answer
            elif answer == "tfv":
                    print('If you want to search for bigrams write query inside quotes (" ")') 
                    return answer
            else:
                return answer

    # 2d User inputs a query to search for – 
    # !! – perhaps this function should be renamed. interface() does not tell
    # what is really happening
    def interface(bool_or_tfv_or_stems):
        
        while True:
            print()
            print("'q' = Quit; 'm' = Choose mode")
            # input_query = input("Input your query: ")

            # changed this line to grab query contents from html text_input
            input_query = query

            # following 5 lines of code added for Stemmer functionality
            additional_tokens = input_query
            additional_tokens = find_related_tokens_from_stem(input_query) # comment out this line to disable Stemmer functionality
        
            # pause code for 2 seconds to see added tokens by Stemmer
            #time.sleep(2)
            print()

            if input_query == "q":
                break
            elif input_query == "m":
                bool_or_tfv_or_stems = choose_bool_or_tfv_or_stems()
            elif bool_or_tfv_or_stems == "boolean":
                search_bool(input_query, bool_or_tfv_or_stems)
            elif bool_or_tfv_or_stems == "tfv":
                search_tfv(input_query, bool_or_tfv_or_stems)
            elif bool_or_tfv_or_stems == "stems":
                search_stems(input_query, bool_or_tfv_or_stems, additional_tokens)

    # 2e Search in articles and outputs results
    # perhaps this function can be split into 2 - logic and representational  –
    # anyways print_output() function name currently is not exactly precise to 
    # what is happening - maybe search_and_print_results()
    def print_output(hits_list, bool_or_tfv_or_stems):
            print("\nThere are/is ", len(hits_list), " hit(s).\n")
            time.sleep(1)
            print("-"*30)
            for i, doc_idx in enumerate(hits_list):

                    #tfv gives tuples, so to make the code work, it has to be split into score and the index
                    if type(doc_idx) == tuple:
                            score = doc_idx[0]
                            doc_idx = doc_idx[1]

                    doc_lines = linesplitter_and_cleaner(documents[doc_idx])
                    article_name = doc_lines[0]
                    first_line = doc_lines[1]

                    #Deletes the article name tag from the article_name
                    article_name = re.sub(r'<article name="(.*?)">', r'\1', article_name)

                    if bool_or_tfv_or_stems == "tfv":
                            print("Article: {:s}\nScore: {:f}\nContent: {:s}...".format(article_name, score, first_line[:100]))
                    elif bool_or_tfv_or_stems == "boolean":
                            print("Article: {:s}\nContent: {:s}...".format(article_name, first_line[:100]))
                    elif bool_or_tfv_or_stems == "stems":
                            print("Article: {:s}\nContent: {:s}...".format(article_name, first_line[:100]))
                    print("-"*30)

                    #Ask if print 10 more or stop printing
                    if i % 10 == 0 and i > 1:
                            stop_or_continue = input("\nWould you like more results (Y / N)? ")
                            if stop_or_continue == "N" or stop_or_continue == "n":
                                    break
                            
                            
    ### 3 LOGIC CODE TO MAKE ALL WORK – MATRICES, VECTORS, MULTIGRAMS, etc
    # 3a A code snippet from Week1 CSC notebook – "A simple query-parser"
    # slightly modified to use only capital AND, OR, NOT as boolean operators
    d = {"AND": "&",
        "OR": "|",
        "NOT": "1 -",
        "(": "(",
        ")": ")"}

    def rewrite_token(t):
        return d.get(t, 'td_matrix[t2i["{:s}"]]'.format(t)) # rewrites tokens

    def rewrite_query(query): # rewrite every token in the query
        if type(query) != "NoneType":
            return " ".join(rewrite_token(t) for t in query.split())
        else:
            return "dog"
    # 3b Code to prepare results for the "stems" type query
    def search_stems(input_query, bool_or_tfv_or_stems, additional_tokens): # search the stems

        cv = CountVectorizer(lowercase=True, binary=True, token_pattern=r'[A-Za-z0-9_À-ÿ\-]+\b')
        sparse_matrix = cv.fit_transform(documents)
        dense_matrix = sparse_matrix.todense()
        td_matrix = dense_matrix.T
        t2i = cv.vocabulary_

        try:
            # this IF block added for Stemmer functionality
            if type(additional_tokens) is list:
                hits_list = []
                for token in additional_tokens:
                    hits_matrix = eval(rewrite_query(token))
                    hits_list.append(list(hits_matrix.nonzero()[1]))
                hits_list = list(set([item for items in hits_list for item in items]))
                # print("hits_list from IF: ", hits_list)
            else:
                hits_matrix = eval(rewrite_query(input_query))
                hits_list = list(hits_matrix.nonzero()[1])
                # print("hits_list from ELSE: ", hits_list)

            print("Additional tokens from Stemmer: ", additional_tokens)
            print_output(hits_list, bool_or_tfv_or_stems)            
            print()

        except KeyError:
            print("Query not found in the documents.")
        print()

    def search_bool(input_query, bool_or_tfv): # search the query
    #token_pattern=r'[A-Za-z0-9_À-ÿ\-]+\b',
        cv = CountVectorizer(lowercase=True, binary=True, token_pattern=r'[A-Za-z0-9_À-ÿ\-]+\b', ngram_range=(1, 2))
        sparse_matrix = cv.fit_transform(documents)
        dense_matrix = sparse_matrix.todense()
        td_matrix = dense_matrix.T
        t2i = cv.vocabulary_

        try:
            
            hits_matrix = eval(rewrite_query(input_query))
            hits_list = list(hits_matrix.nonzero()[1])

            print_output(hits_list, bool_or_tfv)

            """
            for i, doc_idx in enumerate(hits_list):
                
                doc_lines = linesplitter_and_cleaner(documents[doc_idx])

                article_name = doc_lines[0]
                first_line = doc_lines[1]

                #Delete the article name tag from the article_name
                article_name = re.sub(r'<article name="(.*?)">', r'\1', article_name)
                
                print("Article: {:s}\n\nContent: {:s}\n\n".format(article_name, first_line))
                print("-"*30)
            """   
                
            print()
        except KeyError:
            print("Query not found in the documents.")
        except SyntaxError:
            print("'AND', 'AND NOT', and 'OR' are commands. Use lowercase, e.g. 'and', 'not', or 'or'")
        print() 
                

    # 3c Code to prepare results for the "tfv" type query
    def search_tfv(input_query, bool_or_tfv_or_stems):
        #if input is in quotes, use bigrams only (c. Multi-word phrases)
        try:
            if input_query.startswith('"') and input_query.endswith('"'):
                input_query = input_query[1:-1] # remove the quotes
                try:
                    gv = TfidfVectorizer(lowercase=True, ngram_range=(2, 2), sublinear_tf=True, use_idf=True, norm="l2")
                except IndexError:
                    gv = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True, use_idf=True, norm="l2")
            else:
                gv = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True, use_idf=True, norm="l2")
        
            g_matrix = gv.fit_transform(documents).T.tocsr()

        # Vectorize query string
            query_vec = gv.transform([ input_query ]).tocsc()

        # Cosine similarity
            hits = np.dot(query_vec, g_matrix)

        # Rank hits
            ranked_scores_and_doc_ids = \
                sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]),
                    reverse=True)
        except IndexError:
            print("Query not found in the documents.")
            print()
            return
        # Output result
        try:

            print_output(ranked_scores_and_doc_ids, bool_or_tfv_or_stems)
            
            #print("Your query '{:s}' matches the following documents:".format(input_query))
            #print()
            

        except KeyError:
            print("Query not found in the documents.")
        except SyntaxError:
            print("'AND', 'NOT', and 'OR' are commands. Use lowercase, e.g. 'and', 'not', or 'or'")
        print()
        
    # 3d tokenize the text from the file, 
    # create token_to_stem_dict and stem_to_tokens_dict 
    def stemming(file_path): 

        stemmer = PorterStemmer()
        # words = word_tokenize(text[:3000])
        words = word_tokenize(text)

        # loop over all tokens and save one_to_one 'token':'stem' pair in a dict
        token_to_stem_dict = {}
        for i in words:
            if i.lower() not in token_to_stem_dict:
                token_to_stem_dict[i.lower()] = stemmer.stem(i)
        
        # loop over 'token':'stem' pairs in dict and reverse order to 'stem': ['token1', 'token2', 'token3', etc]
        stem_to_tokens_dict = {}    
        for key, value in token_to_stem_dict.items():
            if value not in stem_to_tokens_dict:
                stem_to_tokens_dict[value] = [key]
            else:
                stem_to_tokens_dict[value].append(key)

        # print("stem_to_tokens_dict: ", stem_to_tokens_dict)
        return token_to_stem_dict, stem_to_tokens_dict

    token_to_stem_dict, stem_to_tokens_dict = stemming(file_path)

    # 3e find_related_tokens_from_stem – and return a list of words for search
    def find_related_tokens_from_stem(token):
        try:
            stem = token_to_stem_dict[token]
            list_of_words_to_look_for = stem_to_tokens_dict[stem]
        # print(list_of_words_to_look_for)
            return list_of_words_to_look_for
        except KeyError: # error handling if query not in text
            return [token]
        print()


        # #Render index.html with matches variable
        # return render_template('index.html', matches=matches)


    bool_or_tfv_or_stems = 'boolean'
    interface(bool_or_tfv_or_stems)
    
    #Render index.html with matches variable
    return render_template('index.html', matches=matches)