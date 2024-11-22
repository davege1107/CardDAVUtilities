# Yahoo dropped support of CardDAV/CalDAV for some or all of its accounts around November 18 2024

import os
import re
import requests
from xml.etree import ElementTree as ET

# CardDAV server details
#Replace xxxxxxxxx@yahoo.com by your actual Yahoo email address
CARD_DAV_URL = "https://carddav.address.yahoo.com/dav/xxxxxxxxx@yahoo.com/Contacts/"
USERNAME = "xxxxxxxxx@yahoo.com"
#This is "Application Password", not a main Yahoo Account password
PASSWORD = "application_password_16_digits"
OUTPUT_DIR = "./yahoo_contacts"  # Directory to save .vcf files

# XML body for the PROPFIND request
PROPFIND_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:getetag/>
    <d:resourcetype/>
    <d:displayname/>
  </d:prop>
</d:propfind>
"""

# Ensure the output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def sanitize_filename(filename):
    """
    Replace forbidden characters in filenames with underscores.
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized

def clean_vcard(vcard_content):
    """
    Clean and normalize vCard content.
    - Replace unwanted characters like '\r' with '\n'.
    - Strip trailing/leading whitespace on each line.
    """
    # Replace \r\n or \r with \n and strip extra whitespace
    lines = vcard_content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned_lines)

def save_contact(filename, content):
    """
    Save the cleaned vCard content to a sanitized filename and append it to the merged file.
    """
    # Sanitize the filename
    sanitized_filename = sanitize_filename(filename)
    cleaned_content = clean_vcard(content)

    # Save individual vCard file
    filepath = os.path.join(OUTPUT_DIR, sanitized_filename)
    with open(filepath, "w", encoding="utf-8") as vcf_file:
        vcf_file.write(cleaned_content)
    print(f"Saved contact to {filepath}")

    # Append to merged file
    with open(os.path.join(OUTPUT_DIR, "contacts_merged.vcf"), "a", encoding="utf-8") as merged_file:
        merged_file.write(cleaned_content + "\n")  # Ensure a newline between contacts


def merge_contacts():
    """
    Create a single merged file from all vCard files in the directory.
    """
    merged_filename = os.path.join(OUTPUT_DIR, "contacts_merged.vcf")
    with open(merged_filename, "w", encoding="utf-8") as merged_file:
        print(f"Creating merged vCard file: {merged_filename}")

    # Fetch and save contacts
    fetch_contacts()
    print(f"All contacts merged into {merged_filename}")

def fetch_and_save_contact(contact_url):
    """
    Fetch and save a single contact from the CardDAV server.
    """
    # Construct the full URL for the contact
    if contact_url.startswith("/"):
        contact_full_url = "https://carddav.address.yahoo.com" + contact_url
    elif contact_url.startswith("http"):
        contact_full_url = contact_url
    else:
        contact_full_url = CARD_DAV_URL.rstrip("/") + "/" + contact_url.lstrip("/")

    print(f"Fetching contact: {contact_full_url}")
    response = requests.get(contact_full_url, auth=(USERNAME, PASSWORD))

    if response.status_code == 200:
        vcard_content = response.content.decode("utf-8")
        save_contact(contact_url.split("/")[-1], vcard_content)
    else:
        print(f"Failed to fetch contact {contact_url}: {response.status_code}")
        print(f"Response Content: {response.content.decode('utf-8')}")

def fetch_contacts():
    """
    Fetch the list of contacts from the CardDAV server and save them.
    """
    headers = {
        "Depth": "1",
        "Content-Type": "application/xml",
    }

    print("Fetching contact list from CardDAV server...")
    response = requests.request(
        "PROPFIND",
        CARD_DAV_URL,
        auth=(USERNAME, PASSWORD),
        headers=headers,
        data=PROPFIND_BODY,
    )

    if response.status_code not in [200, 207]:
        print(f"Error fetching contacts: {response.status_code}")
        print(response.content.decode("utf-8"))
        return

    # Parse the response XML
    root = ET.fromstring(response.content)
    ns = {"d": "DAV:"}
    contacts = []

    # Extract hrefs for .vcf files
    for response in root.findall("d:response", ns):
        href = response.find("d:href", ns)
        if href is not None and href.text.endswith(".vcf"):
            contacts.append(href.text)

    print(f"Found {len(contacts)} contacts.")
    for contact_url in contacts:
        fetch_and_save_contact(contact_url)

if __name__ == "__main__":
    fetch_contacts()
