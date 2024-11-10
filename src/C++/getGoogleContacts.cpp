// GoogleContactsCardDAV.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include "curl.h"
#include <direct.h>
#include <cerrno>
#include "tinyxml2.h"

#define CURL_STATICLIB

// CardDAV server details
const std::string CARD_DAV_URL = "https://www.google.com/carddav/v1/principals/xxxxxxxxx@gmail.com/lists/default/";
const std::string USERNAME = "xxxxxxxxx@gmail.com";
const std::string PASSWORD = "16-digits-application-password";
const std::string OUTPUT_DIR = "x:\\google_contacts";
const std::string COMBINED_FILE = OUTPUT_DIR + "\\contacts_combined.vcf";

// Function to handle HTTP response data
size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
    size_t totalSize = size * nmemb;
    userp->append((char*)contents, totalSize);
    return totalSize;
}

// Function to make HTTP requests
std::string makeHttpRequest(const std::string& url, const std::string& method, const std::string& body = "") {
    CURL* curl = curl_easy_init();
    if (!curl) {
        std::cerr << "Failed to initialize cURL." << std::endl;
        return "";
    }

    std::string response;
    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/xml");
    headers = curl_slist_append(headers, "Depth: 1");

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_USERPWD, (USERNAME + ":" + PASSWORD).c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

    if (method == "PROPFIND") {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PROPFIND");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body.c_str());
    }

    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
        std::cerr << "cURL error: " << curl_easy_strerror(res) << std::endl;
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    return response;
}

// Function to fetch contacts list
std::vector<std::string> fetchContactsList() {
    const std::string requestBody = R"(<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
      <d:prop>
        <d:getetag/>
        <d:href/>
      </d:prop>
    </d:propfind>)";

    std::string response = makeHttpRequest(CARD_DAV_URL, "PROPFIND", requestBody);
    if (response.empty()) {
        std::cerr << "Failed to fetch contacts list." << std::endl;
        return {};
    }

    // Print raw response for debugging
    std::cout << "Raw XML Response:\n" << response << std::endl;

    // Parse the XML response
    tinyxml2::XMLDocument doc;
    if (doc.Parse(response.c_str()) != tinyxml2::XML_SUCCESS) {
        std::cerr << "Failed to parse XML response." << std::endl;
        return {};
    }

    std::vector<std::string> hrefs;
    tinyxml2::XMLElement* root = doc.FirstChildElement("d:multistatus");
    if (root) {
        for (tinyxml2::XMLElement* response = root->FirstChildElement("d:response"); response; response = response->NextSiblingElement("d:response")) {
            tinyxml2::XMLElement* propstat = response->FirstChildElement("d:propstat");
            while (propstat) {
                tinyxml2::XMLElement* status = propstat->FirstChildElement("d:status");
                if (status && std::string(status->GetText()).find("HTTP/1.1 200 OK") != std::string::npos) {
                    tinyxml2::XMLElement* prop = propstat->FirstChildElement("d:prop");
                    if (prop) {
                        tinyxml2::XMLElement* href = response->FirstChildElement("d:href");
                        if (href && href->GetText()) {
                            hrefs.push_back(href->GetText());
                        }
                    }
                }
                propstat = propstat->NextSiblingElement("d:propstat");
            }
        }
    }

    return hrefs;
}
// Function to clean vCard content
std::string cleanVCard(const std::string& content) {
    std::string cleanedContent;
    for (char c : content) {
        if (c != '\r') {
            cleanedContent += c;
        }
    }
    return cleanedContent;
}

// Function to fetch and save contact
void fetchAndSaveContact(const std::string& href, std::ofstream& combinedFile) {
    std::string contactUrl = "https://www.google.com" + href;
    std::string response = makeHttpRequest(contactUrl, "GET");
    if (!response.empty()) {
        std::string cleanedContent = cleanVCard(response);
        combinedFile << cleanedContent << "\n";
        std::cout << "Fetched and saved contact: " << href << std::endl;
    }
    else {
        std::cerr << "Failed to fetch contact: " << href << std::endl;
    }
}

int main() {
    // Ensure output directory exists
    if (_mkdir(OUTPUT_DIR.c_str()) == -1 && errno != EEXIST) {
        std::cerr << "Failed to create output directory." << std::endl;
        return 1;
    }

    // Fetch contact list
    std::vector<std::string> contacts = fetchContactsList();
    std::cout << "Found " << contacts.size() << " contacts." << std::endl;

    // Open combined file
    std::ofstream combinedFile(COMBINED_FILE, std::ios::out | std::ios::trunc);
    if (!combinedFile.is_open()) {
        std::cerr << "Failed to create combined file." << std::endl;
        return 1;
    }

    // Fetch and save each contact
    for (const std::string& href : contacts) {
        fetchAndSaveContact(href, combinedFile);
    }

    combinedFile.close();
    std::cout << "All contacts saved to: " << COMBINED_FILE << std::endl;

    return 0;
}
