#script to test chunking strategies

from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from typing_extensions import List
from langchain_core.documents import Document
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_classic.retrievers.multi_vector import MultiVectorRetriever
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
import csv
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from unstructured.partition.md import partition_md

md_directory_curated = "/data/storage-llm/data/openaccess_parsed/md_curated_manual_jos/"
md_directory_raw = "/data/storage-llm/data/openaccess_parsed/md/"
db_directory = "/data/storage-llm/myco-chat/mycollm/db/"

# vector store collection names
embeddings_model = "nomic-embed-text"
embeddings = OllamaEmbeddings(model=embeddings_model, num_ctx=8192)

vectorstore_aspergillus_500_curated = Chroma(
    collection_name="aspergillus_curated_500_db",
    persist_directory=db_directory + "aspergillus_curated_500_db",
    embedding_function=embeddings
)

vectorstore_aspergillus_500_raw = Chroma(
    collection_name="aspergillus_raw_500_db",
    persist_directory=db_directory + "aspergillus_raw_500_db",
    embedding_function = embeddings
)

vectorstore_aspergillus_1500_curated = Chroma(
    collection_name="aspergillus_curated_1500_db",
    persist_directory=db_directory + "aspergillus_curated_1500_db",
    embedding_function = embeddings
)

vectorstore_aspergillus_1500_raw = Chroma(
    collection_name="aspergillus_raw_1500_db",
    persist_directory=db_directory + "aspergillus_raw_1500_db",
    embedding_function = embeddings
)

# *********************************************************
# functions to load data into vector store
# *********************************************************

def create_metadata(row):
    metadata = {
        "title": row[1].strip(),
        "author": row[2].strip(),
        "publication year": int(row[3].strip()),
        "journal": row[4].strip(),
    }
    return metadata

def chunk_to_snippet(chunk, metadata):
    """Convert a chunk to a Document with metadata."""
    if "Table" in str(type(chunk)):        
        text = chunk.metadata.text_as_html
        metadata["content_type"] = "Table"
    else:
        text = chunk.text
        metadata["content_type"] = "Text"
    if hasattr(chunk.metadata, 'page_number'):
        metadata["page_number"] = chunk.metadata.page_number

    return Document(
        page_content=text,
        metadata=metadata
    ) 

def test_chunking_md(file_path, max_characters=1500):
    """test chunking for curated markdown files to see if the structure is preserved."""
    combine_text_under_n_chars = max_characters // 2
    new_after_n_chars = 9 * max_characters // 10
    overlap = 200

    chunks = partition_md(
        filename=file_path,
        infer_table_structure=True,  # to handle tables
        strategy="hi_res",  # to use high-resolution strategy
        extract_image_block_types=["Image"],  # to extract images
        extract_image_block_to_payload=True,  # to extract images
        chunking_strategy="by_title",  # chunking by title
        max_characters=max_characters,  # upper limit for chunk size
        combine_text_under_n_chars=combine_text_under_n_chars,  # combine text under this limit
        new_after_n_chars=new_after_n_chars,  # new text starts after this limit
        overlap=overlap,  # Specify the overlap size in characters
    )
    print(len(chunks), "chunks created for", file_path)
    # for chunk in chunks:    
    #     if "Table" in str(type(chunk)):        
    #         print(chunk.metadata.text_as_html)
    #     else:
    #         print(chunk.text)
    #     print("-" * 80)


def load_one_file(file_path, metadata, vector_store, max_characters):
    """Load a single file, chunk curated version of the file and add to vector store."""
    # chunking parameters    
    combine_text_under_n_chars = max_characters // 2
    new_after_n_chars = 9 * max_characters // 10
    overlap = 200

    chunks = partition_md(
                    filename=file_path,
                    infer_table_structure=True,  # to handle tables
                    strategy="hi_res",  # to use high-resolution strategy
                    extract_image_block_types=["Image"],  # to extract images
                    extract_image_block_to_payload=True,  # to extract images
                    chunking_strategy="by_title",  # chunking by title
                    max_characters=max_characters,  # upper limit for chunk size
                    combine_text_under_n_chars=combine_text_under_n_chars,  # combine text under this limit
                    new_after_n_chars=new_after_n_chars,  # new text starts after this limit
                    overlap=overlap,  # Specify the overlap size in characters
                )    
    snippets = [chunk_to_snippet(chunk, metadata.copy()) for chunk in chunks]
    print(str(max_characters) + ": Loaded " + file_path + " with " + str(len(snippets)) + " snippets")
    start = 0
    while start < len(snippets):
        end = min(start + 100, len(snippets))  # Add in batches of 100
        batch = snippets[start:end]
        try:
            vector_store.add_documents(batch)
        except Exception as e:            
            for snippet in batch:
                try:
                    vector_store.add_documents([snippet])
                except Exception as e:
                    print(len(snippet.page_content))
                    print(str(snippet))  
                    print("==========================================")
        start = end        
    print("Added " + file_path)

def load_data(csv_path, md_dir, vector_store, max_characters):    
    """Load file names from CSV, chunk curated version of the file and add to vector store."""        
    count = 0
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            base_filename = row[0].strip()                
            
            file_path = f"{md_dir}{base_filename}.md"                  
            if os.path.exists(file_path):
                load_one_file(file_path, create_metadata(row), vector_store, max_characters)                
                count += 1  
            else:
                print(f"File not found for {base_filename}")
    print(f"Total files processed: {count}")

def creating_Aspergillus_DBs():    
    cvs = "/data/storage-llm/data/openaccess_Duong/Aspergillus_openaccess_metadata.csv"
    print("================ 500 curated ====================")
    load_data(cvs, md_directory_curated, vectorstore_aspergillus_500_curated, 500)

    print("================ 1500 curated ====================")    
    load_data(cvs, md_directory_curated, vectorstore_aspergillus_1500_curated, 1500)


    print("================ 500 raw ====================")
    load_data(cvs, md_directory_raw, vectorstore_aspergillus_500_raw, 500)
     
    print("================ 1500 raw ====================")
    load_data(cvs, md_directory_raw, vectorstore_aspergillus_1500_raw, 1500)

if __name__ == "__main__":
    #creating_Aspergillus_DBs()    
    print("Done creating Aspergillus DB's")
    cvs = "/data/storage-llm/data/openaccess_Duong/Aspergillus_openaccess_metadata.csv"
    print("================ 500 curated ====================")
    load_data(cvs, md_directory_curated, vectorstore_aspergillus_500_curated, 500)
