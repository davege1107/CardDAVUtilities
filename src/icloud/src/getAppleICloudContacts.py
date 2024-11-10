import os
import requests
from xml.etree import ElementTree as ET
from discoverICloudCardDAVURLs import get_addressbook_carddav_urls

card_dav_url = ""
adjusted_base_url = ""

USERNAME = "xxxxxxxxx@icloud.com"
#Application Password, not a main iCloud/Apple password
PASSWORD = "yyyy-yyyy-yyyy-yyyy"
OUTPUT_DIR = "./icloud_contacts"
COMBINED_FILE = os.path.join(OUTPUT_DIR, "contacts_combined.vcf")

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def clean_vcard(content):
    """
    Normalize line endings in vCard content.
    - Replace '\r\n' or '\r' with '\n'.
    - Remove any extra blank lines.
    """
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]  # Remove blank lines
    return "\n".join(cleaned_lines)

def fetch_contacts_list():
    """
    Fetch the list of contact URLs from the address book.
    """
    headers = {
        "Depth": "1",
        "Content-Type": "application/xml",
    }
    body = """<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
      <d:prop>
        <d:getetag/>
        <d:displayname/>
        <d:resourcetype/>
      </d:prop>
    </d:propfind>"""

    response = requests.request(
        "PROPFIND", card_dav_url, auth=(USERNAME, PASSWORD), headers=headers, data=body
    )

    if response.status_code not in [200, 207]:
        print(f"Failed to fetch contacts list: {response.status_code}")
        print(response.content.decode("utf-8"))
        return []

    # Debug: Print the raw response
    print("Raw contacts list response:")
    print(response.content.decode("utf-8"))

    # Parse the response XML to extract hrefs
    root = ET.fromstring(response.content)
    ns = {"d": "DAV:"}
    hrefs = []

    for response in root.findall("d:response", ns):
        href = response.find("d:href", ns)
        if href is not None:
            hrefs.append(href.text)

    return hrefs

def fetch_contact(href):
    """
    Fetch a single contact's data and save it.
    """
    # Check if href already contains the full path
    if href.startswith("http"):
        full_url = href  # Use href directly if it's a full URL
    elif href.startswith("/"):
        print("adjusted_base_url111 = " + str(adjusted_base_url))
        full_url = adjusted_base_url + href  # Prepend domain for absolute paths
    else:
        full_url = card_dav_url.rstrip("/") + "/" + href  # Construct full URL for relative paths

    print(f"Fetching contact from URL: {full_url}")  # Debug the URL

    response = requests.get(full_url, auth=(USERNAME, PASSWORD))

    if response.status_code == 200:
        vcard_content = clean_vcard(response.content.decode("utf-8"))
        save_contact(href.split("/")[-1], vcard_content)
        append_to_combined_file(vcard_content)
    else:
        print(f"Failed to fetch contact {href}: {response.status_code}")
        print(response.content.decode("utf-8"))

def save_contact(filename, content):
    """
    Save the vCard data to a file.
    """
    filepath = os.path.join(OUTPUT_DIR, filename + ".vcf")
    with open(filepath, "w", encoding="utf-8") as vcf_file:
        vcf_file.write(content)
    print(f"Saved contact to {filepath}")

def append_to_combined_file(content):
    """
    Append the vCard data to the combined file.
    """
    with open(COMBINED_FILE, "a", encoding="utf-8") as combined_vcf:
        combined_vcf.write(content + "\n")  # Add newline between contacts
    print(f"Appended contact to combined file: {COMBINED_FILE}")

if __name__ == "__main__":

    card_dav_url, adjusted_base_url = get_addressbook_carddav_urls()

    print(adjusted_base_url)

  
    # Clear the combined file before appending new contacts
    with open(COMBINED_FILE, "w", encoding="utf-8") as combined_vcf:
        combined_vcf.write("")  # Start with an empty file

    # Fetch the list of contacts
    hrefs = fetch_contacts_list()
    print(f"Found {len(hrefs)} contacts.")

    for href in hrefs:
        fetch_contact(href)
