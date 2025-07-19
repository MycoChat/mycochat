#*************************************************************************************************
# how to run:
# python openaccess_conversation_freestyle.py < TEXT_FILE_CONTAINTING_QUESTIONS > RESULT_FILE
# e.g.
# python openaccess_conversation_freestyle.py < Aspergillus_questions_by_Jos.txt > out/JOSS_Questions.txt
#
# without the > and <, you would have to type the questions manually and see the answers in the console.
#
#*************************************************************************************************
from unittest import result

from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from typing_extensions import List

from openaccess_db import get_vectorstore, shorten_author_list, get_citations, retrieve_documents_and_rank, retrieve_documents

vector_store = get_vectorstore()
LLMs = ["llama3.2", "gemma2:2b", "qwen2.5:3b", "deepseek-r1"]
k = 10  # Default retrieval size
AnswersPerQuestion = 2  # Default number of answers per question, should be 5

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

    # print('Sources:')    
    # citations = get_citations(result['context'])
    # for citation in citations:     
    #     print(f" {shorten_author_list(citation['author'])}, {citation['title']}, {citation['publication year']}")     

def get_response(graph, question: str):    
    result = graph.invoke({"question": question})            
    return {"answer": result['answer'].content, "sources": get_citations(result['context'])}

def process_one_question(question: str):    
    print(f"\n{'='*50}\nQuestion: {question}\n{'='*50}")

    retrieved_docs = retrieve_documents(vector_store, question, k=10)              
    print(f"\n{'='*50}\nRetrieved snippets:\n{'='*50}")
    print(format_retrieved_docs(retrieved_docs))

    print(f"\n{'='*50}\nAnswers:\n{'='*50}")
    formatted_docs = "\n\n".join(doc.page_content for doc in retrieved_docs)
    for llm_name in LLMs:
        llm = ChatOllama(model=llm_name)        
        message = prompt.invoke({"question": question, "context": formatted_docs})
        for i in range(AnswersPerQuestion):
            response = llm.invoke(message)
            print(f"{llm_name}:\n {response.content}\n{'-'*50}\n")

def format_retrieved_docs(docs: List[Document]) -> str:
    return "\n".join(f"Article Title: {doc.metadata['title']}\nArticle Snippet: {doc.page_content}\n{'-'*50}\n" for doc in docs)

    
import sys
def compile_and_test():        
 
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    question = sys.argv[1] if len(sys.argv) > 1 else "What plants were found in Canary Island?"

    print(f"\n{'='*50}\nQuestion: {question}\n{'='*50}")
    for i in range(n):
        print("-"*50)
 

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
    
    process_one_question("What is Aspergillus ustus?")