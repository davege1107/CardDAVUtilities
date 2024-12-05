import os
import requests
from xml.etree import ElementTree as ET

# Base URL for CardDAV server
BASE_URL = "https://carddav.mail.com"
USERNAME = "xxxxxx@mail.com"
PASSWORD = "my strong password"  # Replace with your account password or app-specific password

# Directory to save the contacts
OUTPUT_DIR = "./contacts_mail.com"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "mail.com_contacts.vcf")

# XML body for the PROPFIND request
PROPFIND_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<d:propfind xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
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

def discover_address_book_url():
    """
    Discover the address book URL dynamically using the well-known path.
    """
    headers = {
        "Depth": "0",
        "Content-Type": "application/xml",
    }

    print(f"Discovering address book URL from {BASE_URL}/.well-known/carddav...")
    response = requests.request(
        "PROPFIND",
        f"{BASE_URL}/.well-known/carddav",
        auth=(USERNAME, PASSWORD),
        headers=headers,
        data=PROPFIND_BODY,
    )

    if response.status_code not in [200, 207]:
        print(f"Error discovering address book URL: {response.status_code}")
        print(response.content.decode("utf-8"))
        return None

    # Parse the response XML to extract the address book URL
    root = ET.fromstring(response.content)
    ns = {"d": "DAV:", "card": "urn:ietf:params:xml:ns:carddav"}
    addressbook_url = root.find(".//card:addressbook-home-set/d:href", ns)

    if addressbook_url is not None:
        relative_url = addressbook_url.text.strip("/")
        absolute_url = f"{BASE_URL.rstrip('/')}/{relative_url}"
        print(f"Discovered address book URL: {absolute_url}")
        return absolute_url
    else:
        print("Failed to discover address book URL.")
        return None

def clean_vcard(vcard_data):
    """
    Remove empty lines from the vCard data.
    """
    lines = vcard_data.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip() and not line.startswith("PRODID")] # Remove empty or whitespace-only lines and PRODID property

    return "\n".join(cleaned_lines)

def resolve_url(base_url, href):
    """
    Resolve a URL by checking if it is absolute or relative.
    """
    if href.startswith("http"):
        return href  # Already absolute
    elif href.startswith("/"):
        return BASE_URL.rstrip("/") + href  # Relative to the base domain
    else:
        return base_url.rstrip("/") + "/" + href.lstrip("/")  # Relative to the current directory

def fetch_contacts_recursive(current_url, visited_urls):
    """
    Fetch the list of contacts and directories from the CardDAV server.
    """
    if current_url in visited_urls:
        print(f"Skipping already visited URL: {current_url}")
        return []

    visited_urls.add(current_url)

    headers = {
        "Depth": "1",  # Use finite depth as required by the server
        "Content-Type": "application/xml",
    }

    print(f"Fetching contact list from {current_url}...")
    response = requests.request(
        "PROPFIND",
        current_url,
        auth=(USERNAME, PASSWORD),
        headers=headers,
        data=PROPFIND_BODY,
    )

    if response.status_code not in [200, 207]:
        print(f"Error fetching contacts: {response.status_code}")
        print(response.content.decode("utf-8"))
        return []

    # Debug: Print the raw response for inspection
    print("Raw PROPFIND response:")
    print(response.content.decode("utf-8"))

    # Parse the response XML
    root = ET.fromstring(response.content)
    ns = {"d": "DAV:"}
    contacts = []

    # Extract hrefs for .vcf files and directories
    for response in root.findall("d:response", ns):
        href = response.find("d:href", ns)
        resource_type = response.find("d:propstat/d:prop/d:resourcetype", ns)
        if href is not None:
            href_text = href.text.strip()
            absolute_url = resolve_url(current_url, href_text)
            if resource_type is None or resource_type.find("d:collection", ns) is None:
                # Consider non-collection resources as contacts
                contacts.append(absolute_url)
            elif resource_type is not None and resource_type.find("d:collection", ns) is not None:
                # Recursively fetch contacts in nested directories
                contacts.extend(fetch_contacts_recursive(absolute_url, visited_urls))

    return contacts

def fetch_contact_data(contact_url):
    """
    Fetch the data for a single contact and return it as text.
    """
    print(f"Fetching contact: {contact_url}")
    response = requests.get(contact_url, auth=(USERNAME, PASSWORD))

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
    # Discover the address book URL
    address_book_url = discover_address_book_url()
    if not address_book_url:
        print("Failed to discover address book URL. Exiting.")
        exit(1)

    # Fetch the list of contacts
    visited_urls = set()
    contacts = fetch_contacts_recursive(address_book_url, visited_urls)
    print(f"Found {len(contacts)} contacts.")

    # Save all contacts into a single file
    save_contacts_to_file(contacts, OUTPUT_FILE)
