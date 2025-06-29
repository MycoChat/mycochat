import json

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
	with open("data/dictionaries/species_description.json", 'r') as f:
		speciesdescriptiondict=json.load(f)
	speciesdescription={}	
	if speciesname in speciesdescriptiondict.keys():
		speciesdescription=speciesdescriptiondict[speciesname]
	return speciesdescription

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