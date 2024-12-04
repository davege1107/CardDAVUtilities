import requests
from xml.etree import ElementTree as ET

# CardDAV server details
CARD_DAV_URL = "https://carddav.aol.com/dav/xxxxxx@aol.com/Contacts/"
USERNAME = "xxxxxx@aol.com"
#This is an Application Password, not you main password
PASSWORD = "16-digits application password"  # Replace with your app-specific password


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

def delete_contact(contact_url):
    """
    Delete a single contact from the CardDAV server.
    """
    # Construct the full URL for the contact
    if contact_url.startswith("/"):
        contact_full_url = "https://carddav.aol.com" + contact_url
    elif contact_url.startswith("http"):
        contact_full_url = contact_url
    else:
        contact_full_url = CARD_DAV_URL.rstrip("/") + "/" + contact_url.lstrip("/")

    print(f"Deleting contact: {contact_full_url}")
    response = requests.delete(contact_full_url, auth=(USERNAME, PASSWORD))

    if response.status_code in [200, 204]:
        print(f"Successfully deleted contact: {contact_url}")
    else:
        print(f"Failed to delete contact {contact_url}: {response.status_code}")
        print(f"Response Content: {response.content.decode('utf-8')}")

def fetch_and_delete_contacts():
    """
    Fetch the list of contacts from the CardDAV server and delete them all.
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

    print(f"Found {len(contacts)} contacts to delete.")
    for contact_url in contacts:
        delete_contact(contact_url)

if __name__ == "__main__":
    fetch_and_delete_contacts()
