import string
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
    def __get_term_frequencies(self, text):
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
    # FUNCTION: remove_posting
    # SPECIFICATION: removes a document posting from a term and deletes the
    #                term if its postings list becomes empty
    #-------------------------------------------------------------------------
    def __remove_posting(self, term, docId):
        # Removing the posting from the term
        self.inverted_index.update_one(
            { "term": term },
            { "$pull": { "postings": { "docId": docId } }}
        )

        # Retrieving the term after removing the posting
        term_document = self.inverted_index.find_one({ "term": term })

        # Deleting the term if its postings list is empty
        if len(term_document["postings"]) == 0:
            self.inverted_index.delete_one({ "_id": term_document["_id"] })

    #-------------------------------------------------------------------------
    # FUNCTION: insert_document
    # SPECIFICATION: inserts a document and updates the inverted index
    #-------------------------------------------------------------------------
    def __insert_document(self, document):
        # Inserting the document into the documents collection
        self.documents.insert_one(document)
        docId = document["_id"]

        # TODO: We need to apply text transformation before adding it to the index
        # I will likely need a helper method from Josiah here where I pass the html
        transformed_text = document["html"]

        # Obtaining the term frequencies
        term_frequencies = list(self.__get_term_frequencies(transformed_text).items())

        # Updating the inverted index
        for term_and_frequency in term_frequencies:
            term = term_and_frequency[0]
            frequency = term_and_frequency[1]
            self.__add_posting(term, docId, frequency)

    #-------------------------------------------------------------------------
    # FUNCTION: delete_document
    # SPECIFICATION: deletes a document and removes all of its postings from
    #                the inverted index
    #-------------------------------------------------------------------------
    def __delete_document(self, docId):
        # Retrieving the document before deleting it
        document = self.documents.find_one({ "_id": docId })

        # TODO: Same as add_document, we need to apply text transformation, 
        # so we know what in the inverted index needs to be taken away
        transformed_text = document["html"]

        # Obtaining the terms contained in the document
        term_frequencies = list(self.__get_term_frequencies(transformed_text).items())
        terms = term_frequencies.keys()

        # Removing the document from every corresponding posting list
        for term in terms:
            self.inverted_index.update_one(
                { "term": term }, 
                { "$pull": { "postings": { "docId": docId } } 
            })

        # Deleting the document
        self.documents.delete_one({ "_id": docId })

    def store_page(self, url, facultyName, html):
        document = {
            "url": url,
            "facultyName": facultyName,
            "html": html
        }
        self.__insert_document(document)

storage = Storage(restart=True)
storage.store_page("some_url", "Bobby Bad", "This is a text document")