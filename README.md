Ubuntu package downloader
===

Description
---
Download .deb packages and dependencies from packages.ubuntu.com. Then you can port those packages to the isolated Ubuntu system. 
Should work in most OS which can run Python.


Requirements
---
Python (Tested with 3.9.10)
    - requests
    - beautifulsoup4


Usage
---
1. Edit settings.json for you liking
2. Execute package_downloader.py
    - Windows: py package_downloader.py
    - Linux: python3 package_downloader.py
3. Downloaded files will be store in .download/


Settings
---
packages
: The packages you want to download.

distribution
: Target Ubuntu distribution
    - focal (for 20.04 LTS)
    - focal-updates
    - jammy (for 22.04.1 LTS)
    - jammy-updates
    - noble (for 24.04 LTS)
    - etc...
    
architecture
: Target architecture
    - amd64
    - arm64
    - armhf
    - etc...
    
favorite_mirrors
: The program will use download mirror listed here first. If none, then program will use the first available one.

want_recommendations
: Whether you want to download the "recommends" packages

want_suggestions
: Whether you want to download the "suggests" packages

use_local_cache
: Save the queried results into .cache/, to improve speed for next time

request_delay
: The delay time after each query request. Larger to reduce server burden

retry_delay
: The delay time after each Internal Server Error response. Larger to reduce server burden


Follow up
---
1. Use dpkg-scanpackages to setup local APT repository
2. apt update