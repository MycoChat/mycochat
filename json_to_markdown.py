""" json_to_markdown.py
This script converts a JSON file containing question, answers, and snippets into a Markdown format.
It removes any thinking sections from the answers and formats the output for readability.

Usage:
    python json_to_markdown.py <input_json_file> [output_markdown_file]
    
If an output file is specified, it will write the Markdown content to that file.
If no output file is specified, it will create a Markdown file with the same name as the input JSON file but with a .md extension.
Example: python json_to_markdown.py JOSS_Question_20.json
"""

import json
import sys
import re
from pathlib import Path

def remove_thinking_sections(text):
    """Remove <think>...</think> sections from text."""
    # Use regex to find and remove <think>...</think> blocks
    pattern = r'<think>.*?</think>'
    cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)
    # Clean up any extra whitespace that might be left
    cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)
    return cleaned_text.strip()

def json_to_markdown(json_file_path, output_file_path=None):
    """
    Convert a JSON file containing question, answers, and snippets to Markdown format.
    
    Args:
        json_file_path (str): Path to the input JSON file
        output_file_path (str, optional): Path for the output Markdown file. 
                                        If None, uses the same name with .md extension
    """
    
    # Read the JSON file
    if not Path(json_file_path).is_file():
        print(f"Error: File '{json_file_path}' not found.")
        return
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return
    except Exception as e:
        print(f"Error reading file '{json_file_path}': {e}")
        return
    
    # Determine output file path
    if output_file_path is None:
        output_file_path = Path(json_file_path).with_suffix('.md')
    
    # Generate Markdown content
    markdown_content = []
    
    # Title and Question
    # Extract index from file name (e.g., 20 from JOSS_Question_20.json)
    match = re.search(r'(\d+)', Path(json_file_path).stem)
    index = match.group(1) if match else "?"
    markdown_content.append(f"# Question {index}\n")
    markdown_content.append(f"**Question:** {data.get('question', 'No question provided')}\n")
    
    # Answers Section
    answers = data.get('answers', [])
    if answers:
        markdown_content.append(f"## Generated Answers ({len(answers)} responses)\n")
        
        for i, answer in enumerate(answers, 1):
            # Remove thinking sections from the answer
            cleaned_answer = remove_thinking_sections(answer)
            
            # Only add the answer if there's content left after removing thinking sections
            if cleaned_answer.strip():
                markdown_content.append(f"### Answer {i}\n")
                markdown_content.append(f"{cleaned_answer}\n")
                markdown_content.append("---\n")
    
    # Snippets Section
    snippets = data.get('snippets', [])
    if snippets:
        markdown_content.append(f"## Retrieved Research Snippets ({len(snippets)} sources)\n")
        
        for i, snippet in enumerate(snippets, 1):
            title = snippet.get('title', '_')
            authors = snippet.get('authors', '_')
            year = snippet.get('publication_year', '_')
            content = snippet.get('snippet', 'No content')

            markdown_content.append(f"**[{i}] {authors}**. ***{title}***. **{year}**\n")
            markdown_content.append(f"...{content}...\n\n")
        
    # Write to file
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        print(f"Markdown file successfully created: {output_file_path}")
        print(f"Note: Thinking sections (<think>...</think>) have been filtered out from answers.")
    except Exception as e:
        print(f"Error writing to file: {e}")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python json_to_markdown.py <input_json_file> [output_markdown_file]")
        print("Example: python json_to_markdown.py JOSS_Question_20.json")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    json_to_markdown(input_file, output_file)

if __name__ == "__main__":
    main()