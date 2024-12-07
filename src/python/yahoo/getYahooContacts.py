import os
import requests
from xml.etree import ElementTree as ET

# Replace xxxxxxxxx@yahoo.com by your actual Yahoo email address
# You can use also other Yahoo domains like
# yahoo.ca, yahoo.jp, yahoo.in, yahoo.co.uk, yahoo.co.il, myyahoo.com, currently.com, att.net
USERNAME = "xxxxxxxxx@yahoo.com" # or xxxxxx@yahoo.co.uk or xxxxxx@currently.com etc.

#This is "Application Password", not a main Yahoo Account password
PASSWORD = "application_password_16_digits"  # Replace with your application-specific password

# CardDAV server details. It is not a base URL, but Address Book URL
CARD_DAV_URL = f"https://carddav.address.yahoo.com/dav/{USERNAME}/Contacts/"


# Directory to save the contacts
OUTPUT_DIR = "./contacts_yahoo"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "yahoo_contacts.vcf")

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

def clean_vcard(vcard_data):
    """
    Remove empty lines from the vCard data.
    """
    lines = vcard_data.splitlines()
    cleaned_lines = [line for line in lines if line.strip()]  # Remove empty or whitespace-only lines
    return "\n".join(cleaned_lines)

def fetch_contacts():
    """
    Fetch the list of contacts from the CardDAV server.
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
        return []

    # Parse the response XML
    root = ET.fromstring(response.content)
    ns = {"d": "DAV:"}
    contacts = []

    # Extract hrefs for .vcf files
    for response in root.findall("d:response", ns):
        href = response.find("d:href", ns)
        if href is not None and href.text.endswith(".vcf"):
            contacts.append(href.text)

    return contacts

def fetch_contact_data(contact_url):
    """
    Fetch the data for a single contact and return it as text.
    """
    if contact_url.startswith("/"):
        contact_full_url = "https://carddav.address.yahoo.com" + contact_url
    elif contact_url.startswith("http"):
        contact_full_url = contact_url
    else:
        contact_full_url = CARD_DAV_URL.rstrip("/") + "/" + contact_url.lstrip("/")

    print(f"Fetching contact: {contact_full_url}")
    response = requests.get(contact_full_url, auth=(USERNAME, PASSWORD))

    if response.status_code == 200:
        return clean_vcard(response.text)  # Clean the vCard data
    else:
        print(f"Failed to fetch contact {contact_url}: {response.status_code}")
        print(response.content.decode("utf-8"))
        return None

def save_contacts_to_file(contacts, output_file):
    """
    Save all contact data into a single VCF file.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        for contact_url in contacts:
            contact_data = fetch_contact_data(contact_url)
            if contact_data:
                f.write(contact_data)
                f.write("\n")  # Ensure each contact is separated by a newline

    print(f"Contacts saved to {output_file}")

if __name__ == "__main__":
    # Fetch the list of contacts
    contacts = fetch_contacts()
    print(f"Found {len(contacts)} contacts.")

    # Save all contacts into a single file
    save_contacts_to_file(contacts, OUTPUT_FILE)
