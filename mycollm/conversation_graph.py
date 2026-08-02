from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from typing_extensions import List, TypedDict
from langchain_ollama.chat_models import ChatOllama

import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from mycobase.search_species import search_RelevantSpeciesDescription_json

MycoBase_metadata = {"title": "MycoBase","content_type": "database", "author": "Jos Houbraken & Duong Vu", "publication year": 2026}

system_prompt = (
    "You are a scientific assistant answering questions using ONLY the provided research-paper snippets.\n\n"
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

# system_prompt = (
#     "You're a scientific assistant. Given a user question "
#     "and some scientific research paper snippets, answer the user "
#     "question. If none of the paper snippets answer the question, "
#     "just say 'I found no answer based on the paper collection'."
#     "\n\nHere are research paper snippets: "
#     "{context}"
# )

def found_no_answer(response: str):
    return "I found no answer" in response

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

# Define state for application
class State(TypedDict):
    question: str
    db_context: List[Document]
    doc_context: List[Document]
    context: List[Document]
    answer: str


class PrioritizedGraph:
    def __init__(self, model: str, vector_store=None, with_searchSpecies=True):
        """
        Initialize the graph with parameterized LLM and data sources.
        """
        self.llm = ChatOllama(model=model)
        self.vector_store = vector_store
        
        # Compile the graph immediately upon initialization
        if with_searchSpecies: self.graph = self._build_graph()
        else: self.graph = self._build_chain()

    def _build_chain(self):          
        workflow = StateGraph(State)        
        workflow.add_node("retrieve_documents", self._retrieve_documents)
        workflow.add_node("generate_answer", self._generate_answer)        
        workflow.set_entry_point("retrieve_documents")
        workflow.add_edge("retrieve_documents", "generate_answer")
        workflow.add_edge("generate_answer", END)
        return workflow.compile()

    def _build_graph(self):
        # Initialize the graph
        workflow = StateGraph(State)

        # Add your nodes
        workflow.add_node("query_database", self._query_database)
        workflow.add_node("retrieve_documents", self._retrieve_documents)
        workflow.add_node("generate_answer", self._generate_answer)

        # Set the entry point
        workflow.set_entry_point("query_database")

        # Add the conditional routing after the DB check
        workflow.add_conditional_edges(
            "query_database",
            self._route_after_db,
            {
                "generate_answer": "generate_answer",
                "retrieve_documents": "retrieve_documents"
            }
        )

        # Connect the document retrieval fallback to the generator
        workflow.add_edge("retrieve_documents", "generate_answer")

        # End the graph after generating the answer
        # workflow.add_edge("generate_answer", END)
        workflow.add_conditional_edges(
            "generate_answer",
            self._route_after_generate_answer,
            {
                "retrieve_documents": "retrieve_documents",
                "END": END
            }
        )

        return workflow.compile()

    # --- Nodes and Routing (Instance Methods) ---
        
    def _route_after_db(self, state: State) -> str:
        # Check if the database provided a satisfactory answer
        if state.get("db_context") is not None:
            return "generate_answer"  # Skip documents, go straight to generation        
        print("Not found in Mycobase, searching paper collection")
        return "retrieve_documents"    # Fallback to documents

    def _route_after_generate_answer(self, state: State) -> str:        
        if state["db_context"] is not None and found_no_answer(state['answer'].content):
            print("Search paper collection")
            return "retrieve_documents"
        return "END"

    def _query_database(self, state: State):
        question = state["question"]       
        db_json = search_RelevantSpeciesDescription_json(question)
        db_result = convert_to_string(db_json) if db_json else None 

        if db_result: # and is_sufficient(self.llm, db_result, question): commented out because of inconsistent quality            
            print(f"Using Mycobase.")
            dict_doc = [Document(
                                page_content=db_result,
                                metadata=MycoBase_metadata)]
            return {"db_context": dict_doc, "context": dict_doc}        
        
        return {"db_context": None}

    def _retrieve_documents(self, state: State):        
        retrieved_docs = self.vector_store.similarity_search(state["question"], k=10)
        return {"db_context": None, "doc_context": retrieved_docs, "context": retrieved_docs}

    def _generate_answer(self, state: State):
        retrieved_docs = state["context"]    
        formatted_docs = "\n\n".join(doc.page_content for doc in retrieved_docs)
        messages = prompt.invoke({"question": state["question"], "context": formatted_docs})  	  
        response = self.llm.invoke(messages)    

        return {"answer": response}


    # --- Public API ---
    
    def run(self, question: str):
        """Helper method to invoke the compiled graph."""
        initial_state = {
            "question": question
        }
        return self.graph.invoke(initial_state)
    
    def invoke(self, initial_state):                
        return self.graph.invoke(initial_state)


SPECIES_KEY = "Species"
COLONY_DIAM_KEY = "Colony diam, 7 d (mm)"
EXTROLITES_KEY = "Extrolites"
SYNONYM_KEY = "Synonym"
ACCEPTED_KEY = "is accepted"

def convert_to_string(db_json):    
    """ Make it more readable for small llm's """

    if SPECIES_KEY in db_json:
        name = db_json[SPECIES_KEY]
        
        if COLONY_DIAM_KEY in db_json:
            db_json[f"Colony diagram of {name} after 7 days incubation (mm)"] = db_json.pop(COLONY_DIAM_KEY)

        if EXTROLITES_KEY in db_json:        
            db_json[f"Extrolites produced by {name}"] = db_json.pop(EXTROLITES_KEY)

        if SYNONYM_KEY in db_json:        
            db_json[f"Synonyms of {name}"] = db_json.pop(SYNONYM_KEY)

        if ACCEPTED_KEY in db_json:                 
            if db_json[ACCEPTED_KEY].lower() == "no": 
                db_json[ACCEPTED_KEY] = f"{name} is not an accepted species."
            else: db_json[ACCEPTED_KEY] = f"{name} is an accepted species."

    return str(db_json)  

# A small Pydantic model for the LLM judge node. Not usable for small llm's.
class SufficiencyCheck(BaseModel):
    is_sufficient: bool = Field(description="True if Context answers the question, False otherwise.")

def is_sufficient(llm, db_result, question):
    if not db_result:
        return False

    judge_llm = llm.with_structured_output(SufficiencyCheck)
    
    # prompt = ChatPromptTemplate.from_messages([
    #     ("system", "You are an auditor. Evaluate if the provided Context is sufficient to completely answer the User Question without needing extra documents. Respond with True or False."),
    #     ("user", "Question: {question}\nContext: {context}")
    # ])
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an auditor. Evaluate if the provided Context, which is a taxonomy species description is sufficient to answer the User Question. Respond with True or False."),
        ("user", "Question: {question}\nContext: {context}")
    ])
    
    chain = prompt | judge_llm
    result = chain.invoke({"question": question, "context": str(db_result)})
    
    return result.is_sufficient