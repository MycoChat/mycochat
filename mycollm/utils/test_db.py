
from create_db import get_vector_store
from mycollm.db.retrieve import retrieve_documents

aspergillus_curated_500 = "aspergillus_500"
aspergillus_raw_500 = "aspergillus_500_raw"
aspergillus_curated_1500 = "aspergillus_1500"
aspergillus_raw_1500 = "aspergillus_1500_raw"

#-----------------------------------------------------------------------
# test functions
#-------------------------------------------------------------------------

def check_db():
    vector_store = get_vector_store(aspergillus_curated_500)
    print(f"Collection name: {vector_store._collection_name}")
    print(f"Number of documents in the collection: {vector_store._collection.count()}")    

    vector_store = get_vector_store(aspergillus_raw_500)
    print(f"Collection name: {vector_store._collection_name}")
    print(f"Number of documents in the collection: {vector_store._collection.count()}")    

    vector_store = get_vector_store(aspergillus_curated_1500)
    print(f"Collection name: {vector_store._collection_name}")
    print(f"Number of documents in the collection: {vector_store._collection.count()}")    

    vector_store = get_vector_store(aspergillus_raw_1500)
    print(f"Collection name: {vector_store._collection_name}")
    print(f"Number of documents in the collection: {vector_store._collection.count()}")  

def test_retrieve_documents(query = "How are xerophilic fungi defined?"):
    #vector_store = get_vector_store("aspergillus_500_no_table_heading")  # Use the appropriate collection name
    #vector_store = get_vector_store("aspergillus_500_light_breadcrumbs")
    #vector_store = get_vector_store("aspergillus_curated_500_db")
    #docs = retrieve_documents(vector_store, query)    
    print(f"Query: {query}")
    results = vector_store.similarity_search_with_relevance_scores(query, k=10)
    for result in results:
        doc, score = result
        print(f"Score: {score}, Title: {doc.metadata['title']}, Author: {doc.metadata['author']}, Year: {doc.metadata['publication year']}")
        print(f"Content: {doc.page_content}")  # Print first 200 characters of content
        print("-" * 80)
    # for doc in docs:
    #     print(f"Title: {doc.metadata['title']}, Author: {doc.metadata['author']}, Year: {doc.metadata['publication year']}")
    #     print(f"Content: {doc.page_content}")  # Print first 200 characters of content
    #     print("-" * 80)

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

vector_store = Chroma(
        collection_name="r20260729",
        persist_directory="/data/storage-llm/myco-chat/mycollm/db/aspergillus/r20260729",
        embedding_function=OllamaEmbeddings(model="nomic-embed-text", num_ctx=8192)
    )

# DONE making a copy of aspergillus_500_no_table_heading to release
# vector_store._collection.modify(name="r20260729")
#test_retrieve_documents("Which 14 species are able to produce aflatoxin B1, B2, G1 and G2?") 

#if __name__ == "__main__":   
    #ok
    
    #test_retrieve_documents("Which mycotoxin is produced by Penicillium nordicum?")        
    #test_retrieve_documents("Is Aspergillus welwitschiae an accepted species?")
    #test_retrieve_documents("Which extrolites are produced by Aspergillus mulundensis?")
    
    #test_retrieve_documents("What is the colony diameter on YES of Penicillium alogum?")
    

    # --------------------- still wrong    
    #test_retrieve_documents("which extrolites are produced by Penicillium robsamsonii?")
    #test_retrieve_documents("Which five species are named after the royal family?")
    #test_retrieve_documents("List the synonyms of A. alliaceus") 
    #test_retrieve_documents("Which 14 species are able to produce aflatoxin B1, B2, G1 and G2?") 
    #test_retrieve_documents("Which Aspergillus section Nidulantes grows at 50 °C?") #---------------------

    # vector_store = get_vector_store("aspergillus_curated_500_db")
    # print(f"Collection name: {vector_store._collection_name}")
    # print(f"Number of documents in the collection: {vector_store._collection.count()}") 
    #test_retrieve_documents("Who are you?")