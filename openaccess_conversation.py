#*************************************************************************************************
# how to run:
# python openaccess_conversation.py < TEXT_FILE_CONTAINTING_QUESTIONS > RESULT_FILE
# e.g.
# python openaccess_conversation.py < Aspergillus_questions_by_Jos.txt > out/JOSS_Questions.txt
#
# without the > and <, you would have to type the questions manually and see the answers in the console.
#
#*************************************************************************************************
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from pydantic import BaseModel, Field

from openaccess_db import get_vectorstore

vector_store = get_vectorstore()
llm = ChatOllama(model="llama3.2")

system_prompt = (
    "You're a helpful AI assistant. Given a user question "
    "and some scientific research paper snippets, answer the user "
    "question. If none of the papers answer the question, "
    "just say 'I found no answer based on the paper collection'."
    "\n\nHere are research paper: "
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

class CitedAnswer(BaseModel):
    """Answer the user question based only on the given sources, and cite the sources used."""

    answer: str = Field(
        ...,
        description="The answer to the user question, which is based only on the given sources.",
    )
    citations: List[int] = Field(
        ...,
        description="Source IDs of the SPECIFIC articles which justify the answer.",
    )

def format_docs_with_id(docs: List[Document]) -> str:
    formatted = [
        f"Source ID: {i}\nArticle Title: {doc.metadata['title']}\nArticle Snippet: {doc.page_content}"
        for i, doc in enumerate(docs)
    ]
    return "\n\n" + "\n\n".join(formatted)

# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: CitedAnswer

# Define application steps
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])  
    #print(len(retrieved_docs))  
    return {"context": retrieved_docs}

def generate(state: State):
    formatted_docs = format_docs_with_id(state["context"])
    messages = prompt.invoke({"question": state["question"], "context": formatted_docs})
    raw_response = llm.invoke(messages)
    #print("RAW LLM OUTPUT:", raw_response)
    structured_llm = llm.with_structured_output(CitedAnswer)
    response = structured_llm.invoke(messages)
    #print("PARSE RESPONSE:", response)
    return {"answer": response}

def get_conversation_graph():
    # Create a state graph for the application
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    return graph_builder.compile()

def handle_question(graph, question: str):
    """Invoke the graph with a user question and display the result."""    
    try:
        result = graph.invoke({"question": question})        
        print(f"Answer: {result['answer'].answer}")
        print('Sources:')
    except Exception as e:
        print(f"Error processing question : {e}")  
        return
    
    citation_set = set()
    for citation in result["answer"].citations:     
        try:
            source = result["context"][citation].metadata["source"]
                #print(f" Citation: {citation} Document Source: {source}")
            if source in citation_set:
                continue
            citation_set.add(source)
            c = result["context"][citation]                
            print(f" {c.metadata['author']}, {c.metadata['title']}, {c.metadata['year']}")
        except Exception as e:  
            print(f"Error printing : {e} \n Citation: {citation}")  

def get_response(graph, question: str):
    while True:        
        try:
            result = graph.invoke({"question": question})        
            answer = result['answer'].answer
            sources = []
            citation_set = set()
            for citation in result["answer"].citations: 
                if citation < 0 or citation >= len(result["context"]):
                    continue
                source = result["context"][citation].metadata["source"]
                if source in citation_set:
                    continue
                citation_set.add(source)
                sources.append(result["context"][citation].metadata)

            return {"answer": answer, "sources": sources}
        except Exception as e:
            print('.') 
            continue                 

import sys
def compile_and_test():        
    graph = get_conversation_graph()

    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    question = sys.argv[1] if len(sys.argv) > 1 else "What plants were found in Canary Island?"

    print(f"\n{'='*50}\nQuestion: {question}\n{'='*50}")
    for i in range(n):
        print("-"*50)
        handle_question(graph, question)
        #handle_question(graph, "What is CANARIOMYCES NOTABILIS?")            
        #handle_question(graph, "What is Aspergillus ustus?")    
        #handle_question(graph, "What does calidus mean in Latin?")

Jos_questions = [
    "Which species produce aflatoxin B?",
    "Which Penicillium species can produce penicillin?",
    "What is an extrolite?",
    "Is the name Eurotium still in use?",
    "What is the type of Talaromyces?",
    "How many species are accepted in Talaromyces?",
    "Give all accepted Aspergillus species starting with a 'a'",
    "Which species belong to Aspergillus section Nigri?",
    "Can you list all accepted species in section Nigri?",
    "Why is Aspergillus section Flavi an important group of fungi?",
    "What Penicillium classification was proposed in Pitt (1979)?",
    "What is the preferred barcode for Penicillium identification?",
    "Is Penicillium brevicompactum safe to use?",
    "Can you give a species description of Penicillium roqueforti?",
    "What colour of conidia does Penicillium nalgiovense have?",
    "What is the reverse color of Penicillium discolor?",
    "From which substrates can Penicillium polonicum be isolated?",
    "Give me the five most important publications in Aspergillus taxonomy",
    "How do Penicillium series Viridicata species differ from each other?",
    "Give an overview of the history of Penicillium taxonomy."
]

if __name__ == "__main__":
    i = 0
    for question in sys.stdin:
        question = question.strip()
        if not question:
            continue        
        print(f"\n{'='*50}")
        i += 1
        print(f"\nQuestion {i}: {question}")
        response = get_response(get_conversation_graph(), question)
        print(f"\nAnswer: {response['answer']}")
        print("Sources:")
        for source in response["sources"]:
            print(f" - {source['author']}, {source['title']}, {source['year']}")
    
    #compile_and_test()