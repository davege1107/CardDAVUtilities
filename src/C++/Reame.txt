To run under Linux:

1. Install libcurl : sudo apt install libcurl4-openssl-dev
2. Install tinyxml2: sudo apt install libtinyxml2-dev
3. Compile g++ -std=c++17 -o getGoogleContactsLinux getGoogleContactsLinux.cpp -lcurl -ltinyxml2
4. Run  ./getGoogleContactsLinux
