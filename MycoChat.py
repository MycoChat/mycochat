import streamlit as st
import ast
import os

from mycollm.db.retrieve import get_vectorstore, shorten_author_list, get_citations
from mycoid.tools.search_dna import search_DNA, is_good_DNA_sequence
from mycobase.search_species import search_SpeciesDescription
from mycollm.conversation_graph import PrioritizedGraph, found_no_answer

version = "r20260730"
DB_COLLECTION_NAME = "r20260729"
CHAT_MODEL = "gemma2:2b" #"llama3.2"

icon_image = "https://avatars.githubusercontent.com/u/24915122"

tool_icon = """
<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#3d5047">
    <path d="M433-121q-63-2-119.5-15T214-170.5Q171-192 145.5-220T120-280q0 32 25.5 60t68.5 49.5q43 21.5 99.5 34.5T433-121Zm-50-205q-23-3-48-7.5t-49-11q-24-6.5-46-15.5t-40-19q18 10 40 19t46 15.5q24 6.5 49 11t48 7.5Zm97-274q88 0 178.5-25.5T760-679q-11-29-100.5-55T480-760q-91 0-178.5 25.5T200-679q15 29 104.5 54T480-600ZM120-280v-400q0-33 28.5-62t77.5-51q49-22 114.5-34.5T480-840q74 0 139.5 12.5T734-793q49 22 77.5 51t28.5 62q0 33-28.5 62T734-567q-49 22-114.5 34.5T480-520q-85 0-157-15t-123-44v101q34 31 82.5 48T383-406q17 2 27.5 14t10.5 29q0 16-11 27.5t-27 9.5q-47-5-97-18.5T200-379v99q12 23 72 43.5T434-206q17 2 27.5 15t10.5 30q0 17-11 29t-28 11q-63-2-119.5-15T214-170.5Q171-192 145.5-220T120-280Zm540 160q-75 0-127.5-52.5T480-300q0-75 52.5-127.5T660-480q75 0 127.5 52.5T840-300q0 26-7.5 50T812-204l80 80q11 11 11 28t-11 28q-11 11-28 11t-28-11l-80-80q-22 13-46 20.5t-50 7.5Zm0-80q42 0 71-29t29-71q0-42-29-71t-71-29q-42 0-71 29t-29 71q0 42 29 71t71 29Z"/>
</svg>
"""

bot_icon = """
<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#b14a10">
    <path d="M160-360q-50 0-85-35t-35-85q0-50 35-85t85-35v-80q0-33 23.5-56.5T240-760h120q0-50 35-85t85-35q50 0 85 35t35 85h120q33 0 56.5 23.5T800-680v80q50 0 85 35t35 85q0 50-35 85t-85 35v160q0 33-23.5 56.5T720-120H240q-33 0-56.5-23.5T160-200v-160Zm242.5-97.5Q420-475 420-500t-17.5-42.5Q385-560 360-560t-42.5 17.5Q300-525 300-500t17.5 42.5Q335-440 360-440t42.5-17.5Zm240 0Q660-475 660-500t-17.5-42.5Q625-560 600-560t-42.5 17.5Q540-525 540-500t17.5 42.5Q575-440 600-440t42.5-17.5ZM320-280h320v-80H320v80Zm-80 80h480v-480H240v480Zm240-240Z"/>
</svg>
"""

AVATARS = {
    "user": None, #"🧑‍🔬",
    #"assistant": bot_icon, 
    "assistant": None, #"🤖",    
    #"tool": ":material/database:", # "🛠️",
    "tool": tool_icon,
}
   
graph = PrioritizedGraph(model=CHAT_MODEL, vector_store=get_vectorstore(DB_COLLECTION_NAME))

def get_conversation_response(user_question):
    """Handle user input and generate a response."""

    if st.session_state.conversation is None:  
        st.session_state.conversation = graph

    chat_history_str = ""
    if "messages" in st.session_state:
        for msg in st.session_state.messages:
            chat_history_str += f"{msg['role']}: {msg['content']}\n"
    
    input_data = {
        "question": user_question,
        "chat_history": chat_history_str		
    }
    
    response = st.session_state.conversation.invoke(input_data)    
    return response

def format_search_result(search_result):    
    print (f"format {st.session_state.species_search_key}")
    if isinstance(search_result, str):
        try:
            result_dict = ast.literal_eval(search_result)            
            if result_dict:
                return (
                    "\n".join([f"- **{k.capitalize()}**: {v}" for k, v in result_dict.items()]),
                    True
                )                
        except Exception:
            pass    

    st.session_state.species_search_key = None
    return ("No results found.", False)

def compose_sources(sources):        
    #print(sources)    
    citations = get_citations(sources)    
    if (len(citations) == 0): 
        return ""
    heading =  "Sources" if len(citations) > 1 else "Source"
    #print(citations)    
    s = "\n- ".join(
        f"{shorten_author_list(citation['author'])}, {citation['title']}, {citation['publication year']}"
        for citation in citations)
    return f"\n\n**{heading}**:\n- " + s

def init_session_state():
    if "conversation" not in st.session_state:
        st.session_state.conversation = None      
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "search_result" not in st.session_state:
        st.session_state.search_result = None
    if "species_search_key" not in st.session_state:
        st.session_state.species_search_key = None  

def render_page():
    st.set_page_config(page_title="MycoChat", page_icon=icon_image)
    col1, col2 = st.columns([5, 1])  # Adjust the ratio as needed    
    with col1:
        st.markdown("<h1 style='color:#3d5047;'>MycoChat</h1>", unsafe_allow_html=True)
        st.caption(f"Version: {version}. DB: {DB_COLLECTION_NAME}. Model: {CHAT_MODEL}.")            
    with col2:        
        st.image("https://avatars.githubusercontent.com/u/24915122", width=120)  

    st.markdown('Enter a DNA sequence or a species name to look up in MycoID or MycoBase, or a question to ask MycoLLM.')
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=AVATARS.get(message["role"], "🙂")):
            st.markdown(message["content"])    

def get_image_path(species_name):
    image_path = f"mycobase/data/images/{species_name} Mycochat.jpg"
    if os.path.exists(image_path): return image_path
    return None

def register_message(role, content):
    """display a message and register it in the session state."""    

    st.session_state.messages.append({"role": role, "content": content})

    with st.chat_message(role, avatar=AVATARS[role]):
        st.markdown(content)
        if role == "tool" and st.session_state.species_search_key != None:        
            image_path = get_image_path(st.session_state.species_search_key)
            if image_path != None:
                st.image(image_path, use_container_width=True)
            st.session_state.species_search_key = None

def standardize(search_key: str): #Aspergillus flavus
    key = search_key.strip()
    if key[0].islower(): key = key[0].upper() + key[1:]
    if key.startswith('A.'): key = 'Aspergillus' + key[2:]
    return key 

def handle_search(search_key):      
    
    if is_good_DNA_sequence(search_key):      
        user_question = f"DNA search: {search_key[:60]}..."
        search_result = str(search_DNA(search_key))                    
    else:
        std_search_key = standardize(search_key)
        st.session_state.species_search_key = std_search_key 
        user_question = f"Species search: {std_search_key}"          
        search_result = str(search_SpeciesDescription(std_search_key))

    register_message("user", user_question)
    response = format_search_result(search_result)
    register_message("tool", response)       

def handle_user_question(user_question):
    """Handle user input and generate a response."""

    # try DNA search
    if is_good_DNA_sequence(user_question):
        register_message("user", f"DNA search: {user_question[:60]}...")
        search_result = str(search_DNA(user_question)) 
        (response, found) = format_search_result(search_result)        
        register_message("tool", response) 
        return

    #try species search
    if len(user_question) < 80:
        std_search_key = standardize(user_question)        
        search_result = str(search_SpeciesDescription(std_search_key))    
        (response, found) = format_search_result(search_result)
        if found:
            st.session_state.species_search_key = std_search_key 
            register_message("user", f"Species search: {std_search_key}")
            register_message("tool", response)
            return

    #try paper collection    
    register_message("user", user_question)
    result = get_conversation_response(user_question)
    answer = result['answer'].content        
    if found_no_answer(answer):
        RAG_response = answer            
    else:
        sources = compose_sources(result['context'])
        RAG_response = f"{answer}\n\n{sources}"
    
    register_message("assistant", RAG_response)             

def main():
    init_session_state()
    render_page()    
    if user_question := st.chat_input("Ask a question"):        
        handle_user_question(user_question)


if __name__ == "__main__":
    main()
