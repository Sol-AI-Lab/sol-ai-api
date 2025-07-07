import requests
import json
import logging
import csv
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_error_to_csv(url, status_code, message):
    filename = 'error_log.csv'
    file_exists = os.path.isfile(filename)

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(['Nº', 'URL', 'Status Code', 'Message', 'Request Date'])

        if file_exists:
            with open(filename, mode='r') as f:
                row_count = sum(1 for row in f)
                next_number = row_count
        else:
            next_number = 1

        writer.writerow([next_number, url, status_code, message, current_time])


async def get_registered_blinks():
    """Retrieves and filters registered blinks from the Dial registry.

    Returns:
        A list of dictionaries representing registered blinks,
        or an empty list if an error occurs.
    """
    headers = {
        'Content-type': 'application/json',
    }

    try:
        blink_list_url = 'https://registry.dial.to/v1/list'
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(blink_list_url)
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
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(blink_url)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        status_code = None
        url = None
        message = ''

        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            try:
                message = str(e)
            except ValueError:
                message = e.response.text

        if hasattr(e, 'request') and e.request is not None:
            url = e.request.url

        error_message = (
            f"Error fetching registered blink: \n\n"
            f"Status Code: {status_code} \n\n"
            f"URL: {url} \n\n"
            f"Message: {message} \n\n"
        )
        print(error_message)

        if any([url, status_code, message]):
            write_error_to_csv(url, status_code, message)

        return {}


def write_to_csv(filename, rows):
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['title', 'description', 'action_url'])  # Header
        for row in rows:
            writer.writerow(row)


async def main():
    registered_blinks = await get_registered_blinks()
    csv_filename = './context/blinks/blinks.csv'

    # Clear existing CSV if it exists
    if os.path.isfile(csv_filename):
        os.remove(csv_filename)

    rows_to_write = []

    for blink in registered_blinks:
        action_url = blink.get('actionUrl')
        registered_blink = await get_resgitered_blink(action_url)
        if isinstance(registered_blink, dict) and bool(registered_blink):
            if not registered_blink.get('disabled', False):
                title = (registered_blink.get("title") or "").strip()
                description = (registered_blink.get("description") or "").strip()
                rows_to_write.append([title, description, action_url])

    write_to_csv(csv_filename, rows_to_write)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
