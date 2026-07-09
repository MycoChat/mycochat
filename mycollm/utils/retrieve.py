from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from typing_extensions import List
from langchain_core.documents import Document
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

db_directory = "/data/storage-llm/myco-chat/mycollm/db/aspergillus/"
embeddings_model = "nomic-embed-text"

def get_vectorstore(collection_name): 
    # Load existing vectorstore or create if not exists      
    vector_store = Chroma(
            collection_name=collection_name,
            persist_directory=db_directory + collection_name,
            embedding_function=OllamaEmbeddings(model=embeddings_model)
        )
    return vector_store

def retrieve_documents(vector_store, query: str, k: int = 10) -> List[Document]:
    """Retrieve documents from the vector store based on a query."""    
    return vector_store.similarity_search(query, k=k)

def shorten_author_list(author: str) -> str:
    """Shorten the author list to a maximum of 3 authors."""
    authors = author.split(", ")
    if len(authors) > 3:
        return ", ".join(authors[:3]) + " et al."
    return author

def get_citations(docs: List[Document]):
    """Extract sources from documents."""
    citations = []
    files = set()
    for doc in docs:
        source = doc.metadata["title"]
        if source not in files:
            files.add(source)
            citations.append(doc.metadata)
    return citations

#-----------------------------------------------------------------------
# test functions
#-------------------------------------------------------------------------
def test_retrieve_documents():
    #vector_store = get_vectorstore("aspergillus_curated_500_db")
    vector_store = get_vectorstore("aspergillus_500_no_table_heading")
    query = "which extrolites are produced by Penicillium robsamsonii?"
    docs = retrieve_documents(vector_store, query, k=5)
    for doc in docs:
        print(f"Title: {doc.metadata['title']}, Author: {doc.metadata['author']}, Year: {doc.metadata['publication year']}")
        print(f"Content: {doc.page_content}")  
        print("-" * 80)  

if __name__ == "__main__":
    #csv_file = "openaccess_metadata.csv"
    #load_data(csv_file)

    #print("Openaccess db fully loaded. Checking database...")
    #check_db()

    # testonly read one file to check its content
    # read_one_file("../data/openaccess_Duong/Studies_in_Mycology/Vol93Art1_Taxonomy_of_Aspergillus_section_Flavi_and_their_production_of_aflatoxins,_ochratoxins_and_other_mycotoxins.pdf")

    #vector_store = get_vectorstore()
    #retrieve_documents_and_rank(vector_store, "What is an extrolite?") #very weird snippets. should look into why this happens
    print("hello world")    
    test_retrieve_documents()
