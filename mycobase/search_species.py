import json
from pathlib import Path

script_dir = Path(__file__).resolve().parent
SPECIES_DESCRIPTION_FILE = script_dir / "data" / "species_description.json"

def search_SpeciesDescription(speciesname):
	"""
	Query species description
	
	Args:
        speciesname (str): The name of the species to be queried
		
    Returns:
        dict: The description of the species
	"""
    # Duong's species description
    #load species_description_dict
	with open(SPECIES_DESCRIPTION_FILE, 'r') as f:
		speciesdescriptiondict=json.load(f)
	speciesdescription={}	
	if speciesname in speciesdescriptiondict.keys():
		speciesdescription=speciesdescriptiondict[speciesname]
	return speciesdescription

def is_accepted(speciesname):
	"""
	check if the species name is accepted
	
	Args:
        speciesname (str): The name of the species to be checked
		
    Returns:
        a boolean value: True if the name is accepted; otherwise False
	"""
    # Duong's species description
    #load species_description_dict
	with open(SPECIES_DESCRIPTION_FILE, 'r') as f:
		speciesdescriptiondict=json.load(f)	
	if speciesname in speciesdescriptiondict.keys():
		return True
	return False

def search_RelevantSpeciesDescription(user_question):
	"""
	Query species description based on user question
	
	Args:
        user_question (str): The question to be queried
		
    Returns:
        dict: The description of the species
	"""
    # Duong's species description
    #load species_description_dict
	# with open(SPECIES_DESCRIPTION_FILE, 'r') as f:
	# 	speciesdescriptiondict=json.load(f)
	# speciesdescription_text=""	
	# for speciesname in speciesdescriptiondict.keys():
	# 	if speciesname in user_question:
	# 		speciesdescription_text=str(speciesdescriptiondict[speciesname])
	# 		break
	# return speciesdescription_text
	json_result=search_RelevantSpeciesDescription_json(user_question)
	if json_result: return str(json_result)
	else: return ""

def search_RelevantSpeciesDescription_json(user_question):
	"""
	Query species description based on user question
	
	Args:
        user_question (str): The question to be queried
		
    Returns:
        dict: The description of the species
	"""
    # Duong's species description
    #load species_description_dict
	with open(SPECIES_DESCRIPTION_FILE, 'r') as f:
		speciesdescriptiondict=json.load(f)
	
	for speciesname in speciesdescriptiondict.keys():
		if speciesname in user_question:
			return speciesdescriptiondict[speciesname]
			
	return None

species_search_tool = {
        "type": "function",
        'function': {
            "name": "search_SpeciesDescription",
            "description": "Query species description",
            'parameters': {
                'type': 'object',
                'properties': {
                    'speciesname': {'type': 'string','description': 'The name of the species to be queried'},
                },
                'required': ['speciesname'],
            },        
        },        
    }