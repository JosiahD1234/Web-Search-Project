import string
import math
from pymongo import MongoClient

class Storage:
    def __init__(self, restart=False):
        # Connecting to MongoDB
        self.client = MongoClient("mongodb://localhost:27017/")

        # Accessing the database and collections
        self.db = self.client["web-search-project"]
        self.documents = self.db["documents"]
        self.inverted_index = self.db["inverted_index"]

        # Clear the documents and inverted_index collections if restart flag is passed through
        if restart:
            self.documents.delete_many({})
            self.inverted_index.delete_many({})

    #-------------------------------------------------------------------------
    # FUNCTION: get_term_frequencies
    # SPECIFICATION: receives a text and returns the frequency of each term
    #-------------------------------------------------------------------------
    def get_term_frequencies(self, text):
        # TODO: Text normalization (lowercase and punctuation removal) may be removed
        # since text transformation would occur upstream

        # Converting text to lowercase
        lowercase_text = text.lower()

        # Removing punctuation
        unpunctuated_text = lowercase_text.translate(str.maketrans("", "", string.punctuation))

        # Splitting the text into terms
        terms = unpunctuated_text.split()

        # Returning the term frequencies
        res = {}
        for term in terms:
            res[term] = res.get(term, 0) + 1
        return res

    #-------------------------------------------------------------------------
    # FUNCTION: add_posting
    # SPECIFICATION: adds a posting to an existing term or creates a new term
    #-------------------------------------------------------------------------
    def __add_posting(self, term, docId, tf):
        # Searching for the term in the inverted index
        term_document = self.inverted_index.find_one({ "term": term })

        # Creating a new term if it does not exist
        if term_document is None:
            self.inverted_index.insert_one({
                "term": term,
                "postings": [
                    {
                        "docId": docId,
                        "tf": tf,
                    }
                ]
            })
        else:
            # Adding a posting if the term already exists
            self.inverted_index.update_one(
                { "_id": term_document["_id"] },
                { "$push": { 
                    "postings": {
                        "docId": docId,
                        "tf": tf
                    }
                }}
            )

    #-------------------------------------------------------------------------
    # FUNCTION: insert_document
    # SPECIFICATION: inserts a document and updates the inverted index
    #-------------------------------------------------------------------------
    def __insert_document(self, document):
        # TODO: We need to apply text transformation before adding it to the index
        # I will likely need a helper method from Josiah here where I pass the html
        transformed_text = document["html"]

        # Overwrite 
        document["content"] = document["html"]
        document.pop("html", None)

        # Inserting the document into the documents collection
        self.documents.insert_one(document)
        docId = document["_id"]

        # Obtaining the term frequencies
        term_frequencies = list(self.get_term_frequencies(transformed_text).items())

        # Updating the inverted index
        for term_and_frequency in term_frequencies:
            term = term_and_frequency[0]
            frequency = term_and_frequency[1]
            self.__add_posting(term, docId, frequency)

    #-------------------------------------------------------------------------
    # FUNCTION: store_page
    # SPECIFICATION: adds and indexes a faculty page document using internal Storage
    # methods. meant to be used within the Crawler
    #-------------------------------------------------------------------------
    def store_page(self, url, facultyName, html):
        document = {
            "url": url,
            "facultyName": facultyName,
            "html": html
        }
        self.__insert_document(document)

    def get_documents(self):
        return list(self.documents.find({}))

    def get_document(self, doc_id):
        return self.documents.find_one({ "_id": doc_id })

    def get_term_in_index(self, term):
        return self.inverted_index.find_one({ "term": term })

    #-------------------------------------------------------------------------
    # FUNCTION: apply_norms
    # SPECIFICATION: calculates the magnitude of a document based on all its terms
    # This is intended to be used for calculating the cosine similarity to normalize
    # the vector. This function must be called after crawling is completed
    #-------------------------------------------------------------------------
    def calculate_doc_norms(self):
        # Precompute idf for every term once (avoids a DB lookup per term per document)
        N = self.documents.count_documents({})
        idf = {}
        for entry in self.inverted_index.find({}):
            idf[entry["term"]] = math.log(N / len(entry["postings"]))

        documents = self.documents.find({})
        for document in documents:
            # TODO: Transform
            transformed_text = document["content"]
            term_frequencies = self.get_term_frequencies(transformed_text)

            norm = 0
            for term, frequency in term_frequencies.items():
                norm += ((1 + math.log(frequency)) * idf[term]) ** 2

            norm = math.sqrt(norm)
            self.documents.update_one({ "_id": document["_id"] }, { "$set": { "norm": norm }})

storage = Storage(restart=True)
storage.store_page("example_url", "John Doe", "John Doe loves beyblade")
storage.store_page("example_url", "Jane Doe", "Jane Doe loves pokemon cards")
storage.calculate_doc_norms()

print(storage.get_documents())