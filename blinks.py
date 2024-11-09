import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_registered_blinks():
    """Retrieves and filters registered blinks from the Dial registry.

    Returns:
        A list of dictionaries representing registered blinks,
        or an empty list if an error occurs.
    """
    
    headers = {
        'Content-type': 'application/json'
    }
    
    try:
        blink_list_url = 'https://registry.dial.to/v1/list'
        response = requests.get(blink_list_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])  
        return [x for x in results if 'registered' in x.get('tags', [])]
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching registered blinks: {e}")
        return []

async def get_resgitered_blink(blink_url: str) -> dict:
    headers = {
        'Content-type': 'application/json'
    }
    
    try:
        response = requests.get(blink_url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching registered blink: {e}")
        return {}

def append_to_markdown(filename, blink, anction_url):
    title = blink.get("title")
    description = blink.get("description")
    data = json.dumps(blink)
    
    new_content = f"""
## {title}
{description}

actionUrl: {anction_url}

```json
{data}
```
    """
    try:
        with open(filename, 'a', encoding='utf-8') as file:
            file.write('\n' + new_content)
        return True
    except IOError as e:
        print(f"Error appending to file: {e}")
        return False 
    
async def main():
    registered_blinks = await get_registered_blinks()
    file_path = './context/blinks/blinks.md'
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write('')
        
    for blink in registered_blinks:
        anction_url = blink.get('actionUrl')
        registered_blink = await get_resgitered_blink(anction_url)
        if isinstance(registered_blink, dict) and bool(registered_blink):
            disabled = registered_blink.get('disabled', False)
            if not disabled:
                append_to_markdown(file_path, registered_blink, anction_url)
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
