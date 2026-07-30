import os
import csv
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings # Or Nomic's official API client

# 1. Define structural markdown headers
headers_to_split_on = [
    ("#", "Section_l1"),
    ("##", "Section_l2"),
    ("###", "Section_l3"),
]

# 2. Initialize Stage 1: Header Splitter
markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=True # Keep header in breadcrump only
)

# 3. Initialize Stage 2: Sub-splitter for overly long sections
# We use from_tiktoken_encoder to ensure the chunk size is measured in exact tokens, not characters
recursive_splitter_500 = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", 
    chunk_size=500,       # Targets ~500 tokens per chunk for highly dense scientific text
    chunk_overlap=50,     # 10% overlap to avoid cutting sentences awkwardly at boundaries
    # CRITICAL SETTINGS BELOW:
    is_separator_regex=False,
    separators=["\n\n", "\n", " ", ""] 
)

recursive_splitter_1500 = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", 
    chunk_size=1500,       # Targets ~1500 tokens per chunk for highly dense scientific text
    chunk_overlap=150,     # 10% overlap to avoid cutting sentences awkwardly at boundaries
    # CRITICAL SETTINGS BELOW:
    is_separator_regex=False,
    separators=["\n\n", "\n", " ", ""] 
)

md_directory_curated = "/data/storage-llm/data/openaccess_parsed/md_curated_manual_jos/"
md_directory_raw = "/data/storage-llm/data/openaccess_parsed/md/"
db_directory = "/data/storage-llm/myco-chat/mycollm/db/aspergillus/"
embeddings = OllamaEmbeddings(model="nomic-embed-text", num_ctx=8192)
aspergillus_curated_500 = "aspergillus_500"
aspergillus_raw_500 = "aspergillus_500_raw"
aspergillus_curated_1500 = "aspergillus_1500"
aspergillus_raw_1500 = "aspergillus_1500_raw"

aspergillus_curated_500_no_table_heading = "aspergillus_500_no_table_heading"
aspergillus_curated_1500_no_table_heading = "aspergillus_1500_no_table_heading"

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

def create_breadcrumbs(metadata):
    title = metadata.get("title", "Unknown Document")
    section_l1 = metadata.get("Section_l1", "")
    section_l2 = metadata.get("Section_l2", "")
    section_l3 = metadata.get("Section_l3", "")
    
    breadcrumbs = f"Document: {title}"
    if section_l1: breadcrumbs += f" | Section: {section_l1}"
    if section_l2: breadcrumbs += f" | {section_l2}"
    if section_l3: breadcrumbs += f" | {section_l3}"
    
    return breadcrumbs

def create_breadcrumbs_light(metadata):
    title = metadata.get("title", "Unknown Document")
    section_l1 = metadata.get("Section_l1", "")
    section_l2 = metadata.get("Section_l2", "")
    section_l3 = metadata.get("Section_l3", "")
    
    breadcrumbs = f"Section: "
    if section_l3: breadcrumbs += f"{section_l3}"
    elif section_l2: breadcrumbs += f"{section_l2}"
    elif section_l1: breadcrumbs += f"{section_l1}"   
    else: breadcrumbs += f"{title}" 
    
    return breadcrumbs

def create_breadcrumbs_light_no_table_heading(metadata):
    #title = metadata.get("title", "Unknown Document")
    #section_l1 = metadata.get("Section_l1", "")
    section_l2 = metadata.get("Section_l2", "")
    section_l3 = metadata.get("Section_l3", "")
    
    breadcrumbs = ""
    if section_l3: breadcrumbs = section_l3
    elif section_l2: breadcrumbs = section_l2
    #elif section_l1: breadcrumbs = section_l1
    #else: breadcrumbs = title 
    #if breadcrumbs.startswith("Table "): return ""    
    return breadcrumbs

def load_one_file(file_path, metadata, vector_store, recursive_splitter, 
                  add_to_vectorstore=True, output_chunks=False):
    """Load a single file, chunk it, and add to the vector store."""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Stage 1: Header Split
    section_docs = markdown_splitter.split_text(text)
    
    # Stage 2: Token-based Sub-split for long blocks
    final_chunks = recursive_splitter.split_documents(section_docs)
    
    # Enrich with metadata and breadcrumbs
    for chunk in final_chunks:
        chunk.metadata.update(metadata)
        #breadcrumbs = create_breadcrumbs(chunk.metadata)            
        #breadcrumbs = create_breadcrumbs_light(chunk.metadata)            
        breadcrumbs = create_breadcrumbs_light_no_table_heading(chunk.metadata)      
        if breadcrumbs != "":
            chunk.page_content = f"[{breadcrumbs}]\n{chunk.page_content}"
        if output_chunks: print(chunk.page_content)        
    
    # Add to vector store, by default, only page_content gets digested for embeddings, metadata is stored separately
    if add_to_vectorstore:
        try:
            vector_store.add_documents(final_chunks)
        except Exception as e:            
            for chunk in final_chunks:
                try:
                    vector_store.add_documents([chunk])
                except Exception as e:
                    print(f"Failed to add chunk: {chunk.page_content[:100]}... with error: {e}")

def get_vector_store(collection_name):
    """Retrieve an existing vector store by collection name."""
    return Chroma(
        collection_name=collection_name,
        persist_directory=db_directory + collection_name,
        embedding_function=embeddings
    )

def create_db(csv_path, md_dir, collection_name, recursive_splitter, remove_existing=False):    
    """Load file names from CSV, chunk curated version of the file and add to vector store."""            
    print(f"Creating vector store for collection: {collection_name} at {db_directory}")
    print(f"using markdown directory: {md_dir}")
    print(f"using CSV metadata file: {csv_path}")

    vector_store = get_vector_store(collection_name)
    if remove_existing:    
        vector_store.delete_collection()
        vector_store = get_vector_store(collection_name)
        print("Existing collection deleted. Starting fresh.")
    elif vector_store._collection.count():
        print(f"Collection {collection_name} is NOT empty. Change parameter and run again if you really want to overwrite it.")
    else:
        print(f"Proceeding to add data.")

    count = 0
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            base_filename = row[0].strip()                
            
            file_path = f"{md_dir}{base_filename}.md"                  
            if os.path.exists(file_path):
                load_one_file(file_path, create_metadata(row), vector_store, recursive_splitter)                
                print(f"Processed file: {file_path}")
                count += 1  
            else:
                print(f"File not found for {base_filename}")
    print(f"Total files processed: {count}")


def test_chunking_results():
    load_one_file(
        #file_path="/data/storage-llm/data/openaccess_parsed/md_curated_manual_jos/sim102Art1.pdf.md",
        #file_path="/data/storage-llm/data/openaccess_parsed/md_curated_manual_jos/Vol84Art1_Aspergillus-section-Nidulantes--formerly-Emericella---Polyp_2016_Studies-in-.pdf.md",
        file_path="/data/storage-llm/data/openaccess_parsed/md_curated_manual_jos/Visagie et al 2016 Persoonia 36 247-280.pdf.md",
        #file_path="/data/storage-llm/data/openaccess_parsed/md_curated_manual_jos/Visagie et al 2013 Persoonia 31 42-62.pdf.md",
        metadata={"title": "Test Document 1", "author": "Author A", "publication year": 2024, "journal": "Journal X"},
        vector_store=get_vector_store(aspergillus_curated_500),
        recursive_splitter=recursive_splitter_500,
        add_to_vectorstore=False,
        output_chunks=True
    )

if __name__ == "__main__":
    #test_chunking_results()

    csv_path = "/data/storage-llm/data/openaccess_Duong/Aspergillus_openaccess_metadata.csv"    
    
    # DONE Create db from raw markdown files
    # create_db(csv_path, md_directory_raw, aspergillus_raw_1500, recursive_splitter_1500, remove_existing=True)    
    # create_db(csv_path, md_directory_raw, aspergillus_raw_500, recursive_splitter_500, remove_existing=True)
    
    # DONE Create db from curated markdown files
    # create_db(csv_path, md_directory_curated, aspergillus_curated_500, recursive_splitter_500, remove_existing=True)    
    # create_db(csv_path, md_directory_curated, aspergillus_curated_1500, recursive_splitter_1500, remove_existing=True)  


    #create_db(csv_path, md_directory_curated, "aspergillus_500_light_breadcrumbs", recursive_splitter_500, remove_existing=True)     

    #DONE
    #create_db(csv_path, md_directory_curated, aspergillus_curated_500_no_table_heading, recursive_splitter_500, remove_existing=True)     
    create_db(csv_path, md_directory_curated, aspergillus_curated_1500, recursive_splitter_1500, remove_existing=True)  
        
    