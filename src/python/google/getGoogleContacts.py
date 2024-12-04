import os
import requests
from xml.etree import ElementTree as ET

# CardDAV server details
# Base URL for CardDAV server
BASE_URL = "https://www.google.com/carddav/v1/principals"
#Replace xxxxxx@gmail.com by your actual Gmail email address
USERNAME = "xxxxxx@gmail.com"
#Enable 2FA and generate Application Password. You can't use your main Google password
PASSWORD = "16-character Application password"
OUTPUT_DIR = "./contacts_google"  # Directory to save .vcf files

# Construct the CardDAV URL
CARD_DAV_URL = f"{BASE_URL}/{USERNAME}/lists/default/"

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

def save_contact(filename, content, combined_file):
    """
    Save the cleaned vCard data to a combined .vcf file and optionally save individual files.
    """
    cleaned_content = clean_vcard(content)  # Clean the content before saving

    # Add contact to the combined file
    with open(combined_file, "a", encoding="utf-8") as combined_vcf:
        combined_vcf.write(cleaned_content + "\n")  # Add a newline between contacts
    print(f"Added contact {filename} to combined file: {combined_file}")

    # Optionally save as individual file (commented out but kept for reference)
    # filepath = os.path.join(OUTPUT_DIR, filename + ".vcf")
    # with open(filepath, "w", encoding="utf-8") as vcf_file:
    #     vcf_file.write(cleaned_content)
    # print(f"Saved contact to {filepath}")

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
        "PROPFIND", CARD_DAV_URL, auth=(USERNAME, PASSWORD), headers=headers, data=body
    )

    if response.status_code not in [200, 207]:
        print(f"Failed to fetch contacts list: {response.status_code}")
        print(response.content.decode("utf-8"))
        return []

    # Parse the response XML to extract hrefs
    root = ET.fromstring(response.content)
    ns = {"d": "DAV:"}
    hrefs = []

    for response in root.findall("d:response", ns):
        href = response.find("d:href", ns)
        if href is not None:
            hrefs.append(href.text)

    return hrefs

def fetch_contact(href, combined_file):
    """
    Fetch a single contact and add it to the combined file.
    """
    url = "https://www.google.com" + href
    response = requests.get(url, auth=(USERNAME, PASSWORD))

    if response.status_code == 200:
        vcard_content = response.content.decode("utf-8")
        filename = href.split("/")[-1]
        save_contact(filename, vcard_content, combined_file)
    else:
        print(f"Failed to fetch contact {href}: {response.status_code}")
        print(response.content.decode("utf-8"))

if __name__ == "__main__":
    combined_file_path = os.path.join(OUTPUT_DIR, "contacts_combined.vcf")

    # Create or clear the combined file
    with open(combined_file_path, "w", encoding="utf-8") as combined_vcf:
        combined_vcf.write("")  # Start with an empty file

    hrefs = fetch_contacts_list()
    print(f"Found {len(hrefs)} contacts.")
    for href in hrefs:
        fetch_contact(href, combined_file_path)
