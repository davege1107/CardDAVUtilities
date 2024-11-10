import requests
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

# iCloud Base URL
BASE_URL = "https://contacts.icloud.com/"

USERNAME = "xxxxxxxxx@icloud.com"
#iCloud Application Password, not a main iCloud/Apple password
PASSWORD = "yyyy-yyyy-yyyy-yyyy"

def discover_principal_url():
    """
    Discover the principal URL for the user.
    """
    headers = {
        "Depth": "0",
        "Content-Type": "application/xml",
    }
    body = """<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:">
      <d:prop>
        <d:current-user-principal/>
      </d:prop>
    </d:propfind>"""

    response = requests.request(
        "PROPFIND", BASE_URL, auth=(USERNAME, PASSWORD), headers=headers, data=body
    )

    if response.status_code not in [200, 207]:
        print(f"Failed to discover principal URL: {response.status_code}")
        print(response.content.decode("utf-8"))
        return None

    # Parse the response XML to extract the principal URL
    root = ET.fromstring(response.content)
    ns = {"d": "DAV:"}
    principal = root.find(".//d:current-user-principal/d:href", ns)
    if principal is not None:
        return BASE_URL + principal.text.strip("/")
    return None

def discover_addressbook_url(principal_url):
    """
    Discover the address book URL for the user.
    """
    headers = {
        "Depth": "0",
        "Content-Type": "application/xml",
    }
    body = """<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
      <d:prop>
        <card:addressbook-home-set/>
      </d:prop>
    </d:propfind>"""

    response = requests.request(
        "PROPFIND", principal_url, auth=(USERNAME, PASSWORD), headers=headers, data=body
    )

    if response.status_code not in [200, 207]:
        print(f"Failed to discover address book URL: {response.status_code}")
        print(response.content.decode("utf-8"))
        return None

    # Parse the response XML to extract the address book URL
    root = ET.fromstring(response.content)
    ns = {"d": "DAV:", "card": "urn:ietf:params:xml:ns:carddav"}
    addressbook = root.find(".//card:addressbook-home-set/d:href", ns)
    if addressbook is not None:
        return addressbook.text.strip("/")
    return None

def discover_addressbook_carddav_url(addressbook_url):
    if addressbook_url is not None:
        return addressbook_url + "/card/"
    return None

def get_adjusted_base_url(addressbook_carddav_url):
    
    # Parse the URL
    parsed_url = urlparse(addressbook_carddav_url)

    # Extract the scheme and netloc (without the port number)
    base_domain = f"{parsed_url.scheme}://{parsed_url.hostname}"

    print("Extracted Base Domain:", base_domain)
    return base_domain


def get_addressbook_carddav_urls():
    # Step 1: Discover the user principal URL
    principal_url = discover_principal_url()
    if not principal_url:
        print("Failed to discover principal URL.")
        exit(1)
    print(f"Discovered principal URL: {principal_url}")

    # Step 2: Discover the address book URL
    addressbook_url = discover_addressbook_url(principal_url)
    if not addressbook_url:
        print("Failed to discover address book URL.")
        exit(1)
    print(f"Discovered address book URL: {addressbook_url}")

    addressbook_carddav_url = discover_addressbook_carddav_url(addressbook_url)
    print(f"addressbook_carddav_url: {addressbook_carddav_url}")

    parsed_url = urlparse(addressbook_carddav_url)
    adjusted_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    print(f"adjusted_base_url: {adjusted_base_url}")

    adjusted_base_url = get_adjusted_base_url(addressbook_carddav_url)
    
    return (addressbook_carddav_url, adjusted_base_url)


    
if __name__ == "__main__":
    get_addressbook_carddav_urls()
