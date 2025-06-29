import ollama
import requests

model = 'llama3.2'
from dnabarcoder.classification.classifyAgainstReferenceSet import classifyAgainstReferenceSet
import tempfile
import os
import multiprocessing
import json

# Tool Functions
def is_good_DNA_sequence(search_key):
    count_acgt = sum(1 for c in search_key.lower() if c in "acgt")
    return (count_acgt > 50)

def search_DNA(sequence):
    # sanitize the search keyword    
    sequence = ''.join([c if c.lower() in 'acgt' else ' ' for c in sequence])

    # Duong's DNA sequence identification
    dnabarcoder_out=tempfile.mkdtemp(prefix="dnabarcoder_output_")
    nproc=multiprocessing.cpu_count()
    classification_result=classifyAgainstReferenceSet(sequence,"data/references","id",dnabarcoder_out,nproc)    
    os.system("rm -r " + dnabarcoder_out)
    return classification_result["query"]

def search_SpeciesDescription(speciesname):
    # Duong's species description
    #load species_description_dict
	with open("data/dictionaries/species_description.json", 'r') as f:
		speciesdescriptiondict=json.load(f)
	speciesdescription={}	
	if speciesname in speciesdescriptiondict.keys():
		speciesdescription=speciesdescriptiondict[speciesname]
	return speciesdescription

def get_weather(city):
    url = "https://api.weather.gov/gridpoints/TOP/32,81/forecast"
    response = requests.get(url)
    return response.json()
    #return response.json()["properties"]["periods"][0]["temperature"]

tools = [
    {
        "type": "function",
        'function': {
            "name": "search_DNA",
            "description": "Identify the DNA sequence",
            'parameters': {
                'type': 'object',
                'properties': {
                    'sequence': {'type': 'string','description': 'The DNA sequence to be identified'},
                },
                'required': ['sequence'],
            },        
        },        
    },
	{
        "type": "function",
        'function': {
            "name": "search_SpeciesDescription",
            "description": "Query species description",
            'parameters': {
                'type': 'object',
                'properties': {
                    'sequence': {'type': 'string','description': 'The description of the current species'},
                },
                'required': ['speciesname'],
            },        
        },        
    },
    {
        "type": "function",
        'function': {
            "name": "get_weather",
            "description": "Get the weather for a given latitude and longitude",
            'parameters': {
                'type': 'object',
                'properties': {
                    'latitude': {'type': 'float','description': 'The latitude of the city'},
                    'longitude': {'type': 'float','description': 'The longitude of the city'},
                },
                'required': ['latitude', 'longitude'],
            },            
        }        
    }
]

# creating a generic function to call appropriate tool based on tool input
def process_tool_call(tool_name, tool_input):
    if tool_name == "get_weather":
        return get_weather(tool_input["latitude"], tool_input["longitude"])
    if tool_name == "search_DNA":
        return search_DNA(tool_input["sequence"])
    if tool_name == "search_SpeciesDescription":
        return search_SpeciesDescription(tool_input["speciesname"])	
  

def chatBot(user_message):
    print(f"\n{'='*50}\nUser Message: {user_message}\n{'='*50}")
    response = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': user_message}],
        tools=tools 
    )
    # print(response)

    if response["done_reason"] == "stop":
        tool_results = []
        for tool_call in response["message"]["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            tool_input = tool_call["function"]["arguments"]            
            tool_result = process_tool_call(tool_name, tool_input)
            print(f"Tool: {tool_name}, Input: {tool_input}, Result: {tool_result}")
            tool_results.append({"name": tool_name, "result": tool_result})

        # aggregate tool results for the next message
        tool_results_str = "; ".join([f"{item['name']}: {item['result']}" for item in tool_results])

        response = ollama.chat(
                model=model,
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", 
                     "content": f"as per results from tools API, current data is {str(tool_result)} , based ONLY on this data, please answer this {user_message}. Try to be as specific as possible."},
                    {"role": "tool", "content": tool_results_str },
                ],
                #tools=tools # type: ignore
                )
        #print(response)
    return response

#user_message = "What is the current weather in Cape Town? Also, what are my todos?"
#user_message = "Can you identify this sequence cgtaacaaggtttccgtaggtgaacctgcggaaggatcattagtgaatattagggtgtccaacttaacttggagcccgaccctcactttctaaccctgtgcatttgtcttgggtagtagcttgcgtcagcgagcgaatcccatttcacttacaaacacaaagtctatgaatgtaacaaatttataacaaaacaaaactttcaacaacggatctcttggctctcgcatcgatgaagaacgcagcgaaatgcgatacgtaatgtgaattgcagaattcagtgaatcatcgaatctttgaacgcaccttgcgctccatggtattccgtggagcatgcctgtttgagtgtcatgaattcttcaacccacctctttcttagtgaatcaggcggtgtttggattctgagcgctgctggcttcgcggcctagctcgctcgtaatgcattagcatccgcaatcgaacttcggattgactcggcgtaatagactattcgctgaggattctggtctctgactggagccgggtaagattaaagggagctactaatcctcatgtctatcttgagattagacctcaaatcaggtaggactacccgctgaacttaagcatatcaa"
#user_message = "Can you identify this sequence cgtaacaaggttt ?"
#user_message = "Which species this sequence cgtaacaaggtttccgtaggtgaacctgcggaaggatcattagtgaatattagggtgtccaacttaacttggagcccgaccctcactttctaaccctgtgcatttgtcttgggtagtagcttgcgtcagcgagcgaatcccatttcacttacaaacacaaagtctatgaatgtaacaaatttataacaaaacaaaactttcaacaacggatctcttggctctcgcatcgatgaagaacgcagcgaaatgcgatacgtaatgtgaattgcagaattcagtgaatcatcgaatctttgaacgcaccttgcgctccatggtattccgtggagcatgcctgtttgagtgtcatgaattcttcaacccacctctttcttagtgaatcaggcggtgtttggattctgagcgctgctggcttcgcggcctagctcgctcgtaatgcattagcatccgcaatcgaacttcggattgactcggcgtaatagactattcgctgaggattctggtctctgactggagccgggtaagattaaagggagctactaatcctcatgtctatcttgagattagacctcaaatcaggtaggactacccgctgaacttaagcatatcaa could belong to?"

#response = chatBot(user_message)
#print(f"\n{'='*50}\nAI response: {response['message']['content']}\n{'='*50}")
