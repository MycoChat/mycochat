#script to load OpenAccess data into a vector store

from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from typing_extensions import List
from langchain_core.documents import Document
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import csv

db_location = "./open_access_with_ranking_db"
collection_name = "first_collection"
pdf_directories = [
                   "../data/openaccess_Duong/Adv_Food_Mycology/", 
                   "../data/openaccess_Duong/Ant_Leeuwenhoek/",
                   "../data/openaccess_Duong/Food_Research_International/",
                   "../data/openaccess_Duong/Fung_Divers/",
                   "../data/openaccess_Duong/IMAFungus/",
                   "../data/openaccess_Duong/Int_J_Food_Microbiol/",
                   "../data/openaccess_Duong/JMC/",
                   "../data/openaccess_Duong/Lab_Manual_Westerdijk/",
                   "../data/openaccess_Duong/Others/", 
                   "../data/openaccess_Duong/Persoonia/", 
                   "../data/openaccess_Duong/Studies_in_Mycology/",
                   "../data/openaccess_Duong/Theses/",
                   "../data/openaccess_Duong/Trans_Br_Mycol_Soc/"]

embeddings_model = "nomic-embed-text"

def get_vectorstore():  
    # Load existing vectorstore or create if not exists      
    vector_store = Chroma(
            collection_name=collection_name,
            persist_directory=db_location,
            embedding_function=OllamaEmbeddings(model=embeddings_model)
        )
    return vector_store

def rerank(doc: Document, score: float) -> float:
    """Rank the document based on its metadata and score."""
    rank = doc.metadata.get("rank", 0)
    year = doc.metadata.get("year", 0)
    return score + rank + (year / 10000.0)

def retrieve_documents(vector_store, query: str, k: int = 10) -> List[Document]:
    """Retrieve documents from the vector store based on a query."""    
    return vector_store.similarity_search(query, k=k)


def retrieve_documents_and_rank(vector_store, query: str, k: int = 10) -> List[Document]:
    """Retrieve documents from the vector store based on a query."""    
    results = vector_store.similarity_search_with_relevance_scores(query, k=k)
    for doc, score in results:
        print(f"{doc}\n{score}\n\n")
    ranks = [rerank(doc, score) for doc, score in results]
    docs = [doc for doc, _ in results]
    sorted_docs = sorted(zip(ranks, docs), reverse=True)
    print("\n\nSorted documents based on rank:\n")
    for rank, doc in sorted_docs:
        print(f"{doc}\n{rank}\n\n")
    ranked_docs = [doc for _, doc in sorted_docs]
    return ranked_docs

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

def test_csv(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try: 
                loader = None
                for pdf_directory in pdf_directories:
                    if os.path.exists(pdf_directory + row[0]):
                        loader = UnstructuredPDFLoader(file_path=pdf_directory + row[0])
                        break
                if not loader:
                    print(f"Error file not found {row[0]}")
                    continue
                #print("Loading file: " + pdf_directory + row[0])
                #data = loader.load()
                #text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                #chunks = text_splitter.split_documents(data)
                #journal = row[4] if len(row) > 4 else "Unknown Journal"
                #print(f'"Processing {row[0]} with title "{row[1]}", author "{row[2]}", year "{row[3]}", journal "{journal}", len: {len(chunks)} chunks"')                
            except Exception as e:      
                print(f"Error processing {row[0]}: {e}")

def check_db():
    vector_store = get_vectorstore()
    print(f"Collection name: {vector_store._collection_name}")
    print(f"Number of documents in the collection: {vector_store._collection.count()}")    

def load_data(csv_path):    
    """Load data from CSV and add to vector store. for testing purposes."""

    vector_store = get_vectorstore()
    
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try: 
                loader = None
                for pdf_directory in pdf_directories:
                    if os.path.exists(pdf_directory + row[0]):
                        loader = UnstructuredPDFLoader(file_path=pdf_directory + row[0])
                        break
                if not loader:
                    print(f"Error file not found {row[0]}")
                    continue
                
                data = loader.load()
                title = row[1].strip()
                author = row[2].strip()
                year = int(row[3].strip())
                journal = row[4].strip()
                rank = int(row[5].strip())
                #print(f'"Processing {row[0]} with title "{title}", author "{author}", year "{year}", journal "{journal}", rank {rank}"')
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                chunks = text_splitter.split_documents(data)        
                for chunk in chunks:
                    del(chunk.metadata['source'])
                    chunk.metadata['title'] = title
                    chunk.metadata['author'] = author
                    chunk.metadata['publication year'] = year
                    chunk.metadata['journal'] = journal
                    chunk.metadata['rank'] = rank                            
                vector_store.add_documents(chunks)
                print("Added " + row[0])    
                
            except Exception as e:      
                print(f"Error processing {row[0]}: {e}")

def read_one_file(file_path):
    """Read a single file and return its content. for testing purposes."""
    try:
        loader = UnstructuredPDFLoader(file_path=file_path)
        data = loader.load()
        print(data)
        # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        # chunks = text_splitter.split_documents(data)
        # return chunks
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

if __name__ == "__main__":
    #csv_file = "openaccess_metadata.csv"
    #load_data(csv_file)

    #print("Openaccess db fully loaded. Checking database...")
    #check_db()

    # testonly read one file to check its content
    #read_one_file("../data/openaccess_Duong/Studies_in_Mycology/Vol93Art1_Taxonomy_of_Aspergillus_section_Flavi_and_their_production_of_aflatoxins,_ochratoxins_and_other_mycotoxins.pdf")

    vector_store = get_vectorstore()
    retrieve_documents_and_rank(vector_store, "What is an extrolite?") #very weird snippets. should look into why this happens

    