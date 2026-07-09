import streamlit as st
import ast
import ollama
from typing import Dict, Callable

from mycollm.utils.retrieve import get_vectorstore, shorten_author_list, get_citations
from mycoid.tools.search_dna import search_DNA, is_good_DNA_sequence, dna_search_tool
from mycobase.tools.search_species import search_SpeciesDescription, species_search_tool
from mycollm.conversation_graph import PrioritizedGraph

version = "dev"
DB_COLLECTION_NAME = "aspergillus_500_no_table_heading"
#CHAT_MODEL = "llama3.2" 
CHAT_MODEL = "gemma2:2b"


available_functions: Dict[str, Callable] = {
    'search_DNA': search_DNA,
    'search_SpeciesDescription': search_SpeciesDescription,
}

def needs_RAG_in_addition_to_tool(tool_name: str) -> bool:
    """Check if the conversation requires RAG in addition to tools."""
    return tool_name not in [        
        'search_DNA',
    ]   

tools=[species_search_tool, dna_search_tool] 

tool_icon = """
<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#3d5047">
    <path d="M433-121q-63-2-119.5-15T214-170.5Q171-192 145.5-220T120-280q0 32 25.5 60t68.5 49.5q43 21.5 99.5 34.5T433-121Zm-50-205q-23-3-48-7.5t-49-11q-24-6.5-46-15.5t-40-19q18 10 40 19t46 15.5q24 6.5 49 11t48 7.5Zm97-274q88 0 178.5-25.5T760-679q-11-29-100.5-55T480-760q-91 0-178.5 25.5T200-679q15 29 104.5 54T480-600ZM120-280v-400q0-33 28.5-62t77.5-51q49-22 114.5-34.5T480-840q74 0 139.5 12.5T734-793q49 22 77.5 51t28.5 62q0 33-28.5 62T734-567q-49 22-114.5 34.5T480-520q-85 0-157-15t-123-44v101q34 31 82.5 48T383-406q17 2 27.5 14t10.5 29q0 16-11 27.5t-27 9.5q-47-5-97-18.5T200-379v99q12 23 72 43.5T434-206q17 2 27.5 15t10.5 30q0 17-11 29t-28 11q-63-2-119.5-15T214-170.5Q171-192 145.5-220T120-280Zm540 160q-75 0-127.5-52.5T480-300q0-75 52.5-127.5T660-480q75 0 127.5 52.5T840-300q0 26-7.5 50T812-204l80 80q11 11 11 28t-11 28q-11 11-28 11t-28-11l-80-80q-22 13-46 20.5t-50 7.5Zm0-80q42 0 71-29t29-71q0-42-29-71t-71-29q-42 0-71 29t-29 71q0 42 29 71t71 29Z"/>
</svg>
"""
AVATARS = {
    "user": None, #"🧑‍🔬",
    "assistant": None, #"🤖",    
    #"tool": ":material/database:", # "🛠️",
    "tool": tool_icon,
}
   
graph = PrioritizedGraph(model=CHAT_MODEL, vector_store=get_vectorstore(DB_COLLECTION_NAME))

def get_conversation_response(user_question):
    """Handle user input and generate a response."""

    if st.session_state.conversation is None:  
        st.session_state.conversation = graph
        st.session_state.messages = []        

    chat_history_str = ""
    for msg in st.session_state.messages:
        chat_history_str += f"{msg['role']}: {msg['content']}\n"
    
    input_data = {
        "question": user_question,
        "chat_history": chat_history_str		
    }
    
    response = st.session_state.conversation.invoke(input_data)    
    return response

def display_search_result(search_result):
    if isinstance(search_result, str):
        try:
            result_dict = ast.literal_eval(search_result)
        except Exception:
            result_dict = {"Result": search_result}
    else:
            result_dict = search_result

    st.sidebar.markdown(
            "\n".join([f"- **{k.capitalize()}**: {v}" for k, v in result_dict.items()])
    )

def format_search_result(search_result):    
    if isinstance(search_result, str):
        try:
            result_dict = ast.literal_eval(search_result)
            if result_dict:
                return (
                    "\n".join([f"- **{k.capitalize()}**: {v}" for k, v in result_dict.items()])
                )                
        except Exception:
            pass    

    return "No results found."

def get_dna_search_response(user_question, search_result):
    """Handle DNA search input and generate a response."""    

    result = str(search_result)
    response = ollama.chat(
                model=CHAT_MODEL,
                messages=[
                    {"role": "user", "content": user_question},
                    {"role": "assistant", 
                     "content": f"as per results from tools API, current data is {result} , based ONLY on this data, please answer this {user_question}. Try to be as specific as possible."},
                    {"role": "tool", "content": result },
                ],
                tools=tools # type: ignore
                )

    return response['message']['content']

def compose_sources(sources):    
    print(sources)
    citations = get_citations(sources)    
    print(citations)    
    s = "\n- ".join(
        f"{shorten_author_list(citation['author'])}, {citation['title']}, {citation['publication year']}"
        for citation in citations)
    return "\n\n**Sources**:\n- " + s if s else ""

def init_session_state():
    if "conversation" not in st.session_state:
        st.session_state.conversation = None      
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "search_result" not in st.session_state:
        st.session_state.search_result = None

def render_page():
    st.set_page_config(page_title="MycoChat", page_icon=":book:")
    col1, col2 = st.columns([5, 1])  # Adjust the ratio as needed    
    with col1:
        st.markdown("<h1 style='color:#3d5047;'>MycoChat</h1>", unsafe_allow_html=True)
        st.markdown(f"Version: {version}. DB: {DB_COLLECTION_NAME}. Model: {CHAT_MODEL}.")    
    with col2:
        st.image("https://avatars.githubusercontent.com/u/24915122", width=120)  

    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=AVATARS.get(message["role"], "🙂")):
            st.markdown(message["content"])

def register_message(role, content):
    """display a message and register it in the session state."""    
    with st.chat_message(role, avatar=AVATARS[role]):
        st.markdown(content)
    st.session_state.messages.append({"role": role, "content": content})

def handle_search(search_key):      
    if is_good_DNA_sequence(search_key):      
        user_question = "Identify DNA sequence."              
        search_result = str(search_DNA(search_key))                    
    else:
        user_question = f"Species search: {search_key}"          #Aspergillus flavus
        search_result = str(search_SpeciesDescription(search_key))

    register_message("user", user_question)
    response = format_search_result(search_result)
    register_message("tool", response)       

def try_using_tools(question):
    analysis = ollama.chat(
        model= CHAT_MODEL,
        messages=[{'role': 'user', 'content': question}],
        tools=tools,
    )
    
    if not analysis.message.tool_calls:
        print("No tool calls found in the response.")
        return None    
    
    for tool in analysis.message.tool_calls:
        if function_to_call := available_functions.get(tool.function.name):
            print('Calling function:', tool.function.name)
            print('Arguments:', tool.function.arguments)
            results = function_to_call(**tool.function.arguments)
            print('Function output:', results)
            return (results, needs_RAG_in_addition_to_tool(tool.function.name))
        else:
            print('Function', tool.function.name, 'not found')
            return (None, True)

def handle_user_question(user_question):
    """Handle user input and generate a response."""

    register_message("user", user_question)    
    
    result = get_conversation_response(user_question)
    answer = result['answer'].content
    hasNoRagAnswer = 'I found no answer' in answer
    if hasNoRagAnswer:
        RAG_response = answer            
    else:
        sources = compose_sources(result['context'])
        RAG_response = f"{answer}\n\n{sources}"    
    
    register_message("assistant", RAG_response)    

def main():
    init_session_state()
    render_page()    

    st.sidebar.image(tool_icon, width=24)
    st.sidebar.markdown("**DNA/Species search**")
    search_key = st.sidebar.text_input("Enter a DNA sequence or species name here", key="sidebar_input", placeholder="Search key")
    search_button = st.sidebar.button("Go", key="sidebar_button")        
    
    if user_question := st.chat_input("Ask a question"):        
        handle_user_question(user_question)

    if (search_button and search_key.strip()):
        handle_search(search_key.strip())

if __name__ == "__main__":
    main()
