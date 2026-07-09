#*************************************************************************************************
# how to run:
# python openaccess_conversation_freestyle.py < TEXT_FILE_CONTAINTING_QUESTIONS > RESULT_FILE
# e.g.
# python openaccess_conversation_freestyle.py < Aspergillus_questions_by_Jos.txt > out/JOSS_Questions.txt
#
# without the > and <, you would have to type the questions manually and see the answers in the console.
#
#*************************************************************************************************
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict

from .retrieve import get_vectorstore, shorten_author_list, get_citations, retrieve_documents

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="OpenAccess Conversation Freestyle")
    parser.add_argument("--model", type=str, default="llama3.2", help="Model name for ChatOllama")    
    parser.add_argument("--k", type=str, default="10", help="Retrieval size (number of document chunks to retrieve)")    
    return parser.parse_args()


#DB_COLLECTION_NAME = "aspergillus_500"  # Name of the vector store collection for Aspergillus curated 500 database    
#DB_COLLECTION_NAME = "aspergillus_500_light_breadcrumbs"  # lightweight version of the collection with breadcrumbs instead of full document titles   
DB_COLLECTION_NAME = "aspergillus_500_no_table_heading"  # lightweight version of the collection with breadcrumbs instead of full document titles   
#DB_COLLECTION_NAME = "aspergillus_curated_500_db"  # old version ww/o breadcrumbs

CHAT_MODEL = "llama3.2"   
#CHAT_MODEL = "gemma2:2b"   # doesn't follow instructions
#CHAT_MODEL = "gemma4:e4b" #very bad, it know nothing about conventions in taxonomy text

vector_store = get_vectorstore(DB_COLLECTION_NAME)  # Load the vector store for Aspergillus curated 500 database
llm = ChatOllama(model=CHAT_MODEL)
k = 10  # Default retrieval size

system_prompt = (
    "You are a scientific assistant answering questions about fungal taxonomy "
    "using ONLY the provided research-paper snippets.\n\n"
    "Rules:\n"
    "1. Base your answer solely on the snippets below. Do NOT use prior or external "
    "knowledge, and do not rely on what you may already know.\n"
    "2. Do not guess or invent anything. Every species name, number, and reference "
    "in your answer must appear in the snippets. If a detail is not in the snippets, "
    "do not state it.\n"
    "3. If the snippets do not contain enough information to answer the question, "
    "reply with exactly this sentence and nothing else: "
    "'I found no answer based on the paper collection'.\n"
    "4. Answer only what is asked, concisely and precisely.\n\n"
    "Snippets:\n{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

def format_docs_with_id(docs: List[Document]) -> str:
    formatted = [
        f"Article Title: {doc.metadata['title']}\nArticle Snippet: {doc.page_content}"
        for i, doc in enumerate(docs)
    ]
    return "\n\n" + "\n\n".join(formatted)

# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    dict_context: str
    answer: str

# Define application steps
def retrieve(state: State):
    #retrieved_docs = vector_store.similarity_search(state["question"], k=10)      
    retrieved_docs = retrieve_documents(vector_store, state["question"], k=10)      
    return {"context": retrieved_docs}

def generate(state: State):
    retrieved_docs = state["context"]
    dict_context = state.get("dict_context", "")
    
    if dict_context!="":
        dict_doc = Document(
        					page_content=dict_context,
        					metadata={"title": "MycoChat's database","content_type": "database", "author": "Jos Houbraken & Duong Vu", "publication year": "2026"})
        retrieved_docs.append(dict_doc)

    formatted_docs = "\n\n".join(doc.page_content for doc in retrieved_docs)
    messages = prompt.invoke({"question": state["question"], "context": formatted_docs})  	  
    response = llm.invoke(messages)    
    return {"answer": response}

def get_conversation_graph():
    # Create a state graph for the application
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    return graph_builder.compile()

def handle_question(graph, question: str):
    """Invoke the graph with a user question and display the result."""    
    
    result = graph.invoke({"question": question})        
    print(f"Answer: {result['answer'].content}")    

    print('Sources:')    
    citations = get_citations(result['context'])
    for citation in citations:     
        print(f" {shorten_author_list(citation['author'])}, {citation['title']}, {citation['publication year']}")     

def get_response(graph, question: str):    
    result = graph.invoke({"question": question})            
    return {"answer": result['answer'].content, "sources": get_citations(result['context'])}
    
import sys
def compile_and_test():        
    graph = get_conversation_graph()

    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    question = sys.argv[1] if len(sys.argv) > 1 else "Which mycotoxin is produced by Penicillium nordicum?"
    question = "Is Aspergillus welwitschiae an accepted species?"
    question = "Which extrolites are produced by Aspergillus mulundensis?"
    question = "Which extrolites are produced by Penicillium robsamsonii?"

    print(f"\n{'='*50}\nQuestion: {question}\n{'='*50}")
    for i in range(n):
        print("-"*50)
        handle_question(graph, question)

if __name__ == "__main__":
    # args = parse_args()
    # llm = ChatOllama(model=args.model)  # Use the model argument
    # k = int(args.k)
    # graph = get_conversation_graph()

    # i = 0
    # for question in sys.stdin:
    #     question = question.strip()
    #     if not question:
    #         continue        
    #     print(f"\n{'='*50}")
    #     i += 1
    #     print(f"\nQuestion {i}: {question}")
    #     response = get_response(graph, question)
    #     print(f"\nAnswer: {response['answer']}")
    #     print("\nSources:")
    #     for source in response["sources"]:
    #         print(f" - {source['author']}, {source['title']}, {source['year']}")
    
    compile_and_test()
