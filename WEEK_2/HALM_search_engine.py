from sklearn.feature_extraction.text import CountVectorizer

d = {"AND": "&",
     "OR": "|",
     "NOT": "1 -",
     "(": "(",
     ")": ")"}

documents = ["This is a silly example",
             "A better example",
             "Nothing to see here",
             "This is a great and long example"]

def rewrite_token(t):
    return d.get(t, 'td_matrix[t2i["{:s}"]]'.format(t)) # Can you figure out what happens here?

def rewrite_query(query): # rewrite every token in the query
    return " ".join(rewrite_token(t) for t in query.split())

def search(input_query):
    print("Searching...\n\n")
    print("Commands 'AND', 'NOT', and 'OR' always upper case!")
    
    cv = CountVectorizer(lowercase=True, binary=True)
    sparse_matrix = cv.fit_transform(documents)
    dense_matrix = sparse_matrix.todense()
    td_matrix = dense_matrix.T
    t2i = cv.vocabulary_

    print("Query: '" + input_query + "'")

    try:
        print("Rewritten:", rewrite_query(input_query))
        print("Matching:", eval(rewrite_query(input_query))) # Eval runs the string as a Python command
        print()
    except KeyError:
        print("Query not found in the documents.")
    except SyntaxError:
        print("'AND', 'NOT', and 'OR' are commands. Use lowercase, e.g. 'and', 'not', or 'or'")
    print()

def interface():
    print("Welcome to HALM search engine!\n")

    while True:
    
        print("'q'= Quit")
        input_query = input("Input your query: ")

        if input_query == "q":
            break
        else:
            search(input_query)

import re

def readandcut(file_path):
    with open(file_path, "r") as file:
        text = file.read()

   
    text = str(text)

    
    cuttext = re.split(r"<", text)
    cuttext.pop(0)
    return cuttext


file_path = "/GitHub/KIK-LG211_HALM/WEEK_2/enwiki-20181001-corpus.100-articles.txt"
cuttext = readandcut(file_path)

print(cuttext[0])

            
def main():
    interface()

main()

