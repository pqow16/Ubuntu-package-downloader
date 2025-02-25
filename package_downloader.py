import time
import os

import requests
from bs4 import BeautifulSoup

class UbuntuPackageDownloader:
    def __init__(self, 
            distribution, 
            architecture, 
            want_recommendations=False, 
            want_suggestions=False, 
            favorite_mirrors=[], 
            use_local_cache=True,
            request_delay=0.5,
            retry_delay=3.0):
        self.base_url = "https://packages.ubuntu.com"
        self.distribution = distribution
        self.architecture = architecture
        self.want_recommendations = want_recommendations
        self.want_suggestions = want_suggestions
        self.use_local_cache = use_local_cache
        self.request_delay = request_delay
        self.retry_delay = retry_delay
        
        self.warning_store = []
        
        self.visited_packages = set()
        self.packages_all = []
        self.package_page_map = {}
        self.package_arch_page_map = {}
        
        self.load_page_cache()
        self.load_arch_page_cache()
    
    def run(self, packages):
        self.rec_build_packages_all(packages)
        self.write_page_cache()

        #print("All packages:", self.packages_all)
        for package_name in self.packages_all:
            self.download_package(package_name)

        self.write_arch_page_cache()
        
        print("\n\n-------Warning:-------")
        for warning_msg in self.warning_store:
            print(warning_msg)
    
    def load_page_cache(self):
        if not self.use_local_cache:
            return
            
        print("Loading page cache")
        
        cache_dir_path = f"cache/{distribution}-{architecture}/page/"
        if not os.path.isdir(cache_dir_path):
            return
        
        filenames = next(os.walk(cache_dir_path))[2]
        for filename in filenames:
            package_name = ".".join(filename.split(".")[:-1])
            cache_path = cache_dir_path + filename
            with open(cache_path, "r", encoding='utf-8') as fh:
                soup = BeautifulSoup(fh, 'html.parser')
            
            self.package_page_map[package_name] = soup
        
    def load_arch_page_cache(self):
        if not self.use_local_cache:
            return
            
        print("Loading arch page cache")
        
        cache_dir_path = f"cache/{distribution}-{architecture}/arch-page/"
        if not os.path.isdir(cache_dir_path):
            return
        
        filenames = next(os.walk(cache_dir_path))[2]
        for filename in filenames:
            package_name = ".".join(filename.split(".")[:-1])
            cache_path = cache_dir_path + filename
            with open(cache_path, "r", encoding='utf-8') as fh:
                soup = BeautifulSoup(fh, 'html.parser')
            
            self.package_arch_page_map[package_name] = soup
        
    def write_page_cache(self):
        if not self.use_local_cache:
            return
        
        print("Writing page cache")
        
        cache_dir_path = f"cache/{distribution}-{architecture}/page/"
        os.makedirs(cache_dir_path, exist_ok=True)
        
        for package_name, soup in self.package_page_map.items():
            cache_path = cache_dir_path + f"{package_name}.html"
            if os.path.isfile(cache_path):
                continue
            
            with open(cache_path, "w", encoding='utf-8') as fh:
                fh.write(str(soup))

    def write_arch_page_cache(self):
        if not self.use_local_cache:
            return
        
        print("Writing arch page cache")
        
        cache_dir_path = f"cache/{distribution}-{architecture}/arch-page/"
        os.makedirs(cache_dir_path, exist_ok=True)
        
        for package_name, soup in self.package_arch_page_map.items():
            cache_path = cache_dir_path + f"{package_name}.html"
            if os.path.isfile(cache_path):
                continue
            
            with open(cache_path, "w", encoding='utf-8') as fh:
                fh.write(str(soup))

    
    def rec_build_packages_all(self, packages):
        # BFS
        
        for package_name in packages:
            self.packages_all.append(package_name)
            self.visited_packages.add(package_name)
        
        next_packages = []
        for package_name in packages:
            deps = self.get_package_dependencies(package_name)
            #print(package_name, deps)
            for dep in deps:
                if not dep in self.visited_packages and not dep in next_packages:
                    next_packages.append(dep)
                
        if next_packages:
            self.rec_build_packages_all(next_packages)
            
        return
        
    def get_package_dependencies(self, package_name):
        result = set()

        page = self.get_package_page(package_name)
        div_pdeps = page.find("div", {"id": "pdeps"})
        
        # Package has no dependency
        if not div_pdeps:
            return result
        
        # Find dependencies
        dep_ul = div_pdeps.findChild('ul', {"class": "uldep"}, recursive=False)
        if dep_ul:
            # recursive need to be True, because the HTML <li> doesn't end with </li>
            dep_lis = dep_ul.findChildren('li', recursive=True) # 
            for li in dep_lis:
                dep_a = li.findChild('dl').findChild('dt').findChild('a')
                dep_name = dep_a.text
                #dep_url = dep_a["href"]
                result.add(dep_name)
                
        # Find recommendations
        if self.want_recommendations:
            rec_ul = div_pdeps.findChild('ul', {"class": "ulrec"}, recursive=False)
            if rec_ul:
                # recursive need to be True, because the HTML <li> doesn't end with </li>
                rec_lis = rec_ul.findChildren('li', recursive=True)
                for li in rec_lis:
                    dep_dt = li.findChild('dl').findChild('dt')
                    dep_a = dep_dt.findChild('a')
                    
                    # Package unavailable
                    if not dep_a:
                        print(f"Unavailable rec package: {dep_dt.text}")
                        continue
                    
                    dep_name = dep_a.text
                    #dep_url = dep_a["href"]
                    result.add(dep_name)
        
        # Find suggestions
        if self.want_suggestions:
            sug_ul = div_pdeps.findChild('ul', {"class": "ulsug"}, recursive=False)
            if sug_ul:
                # recursive need to be True, because the HTML <li> doesn't end with </li>
                sug_lis = sug_ul.findChildren('li', recursive=True)
                for li in sug_lis:
                    dep_dt = li.findChild('dl').findChild('dt')
                    dep_a = dep_dt.findChild('a')
                    
                    # Package unavailable
                    if not dep_a:
                        print(f"Unavailable sug package: {dep_dt.text}")
                        continue
                    
                    dep_name = dep_a.text
                    #dep_url = dep_a["href"]
                    result.add(dep_name)

        return result
    
    def check_page_error(self, page):
        error_div = page.find("div", {"class": "perror"})
        if error_div:
            error_message = error_div.findChild('p').text
            print(f"Page error: {error_message}")
            raise AssertionError(f"Page error: {error_message}")
    
    def get_package_page(self, package_name):
        if package_name in self.package_page_map:
            return self.package_page_map[package_name]
        
        print(f"Visit page: {package_name}")
        
        url = self.base_url + f"/{self.distribution}/{package_name}"
        response = requests.get(url)
        time.sleep(self.request_delay)
        
        while response.status_code == 500:
            time.sleep(self.retry_delay)
            response = requests.get(url)
            print("500. Retry page")
            time.sleep(self.request_delay)
            
        if response.status_code != 200:
            print(f"Error fetching package page info: HTTP {response.status_code}")
            print(f"Error at package page {package_name}")
            with open('error.html', 'w') as file:
                file.write(response.text)
            raise AssertionError(f"Error at package {package_name}")


        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if page has error
        self.check_page_error(soup)
        
        self.package_page_map[package_name] = soup

        return soup

    def get_package_arch_page(self, package_name):
        if package_name in self.package_arch_page_map:
            return self.package_arch_page_map[package_name]
        
        page = self.get_package_page(package_name)
        div_pdownload = page.find("div", {"id": "pdownload"})
        if not div_pdownload:
            return None
        
        arch_a = div_pdownload.findChild("a", string="all")
        if not arch_a:
            arch_a = div_pdownload.findChild("a", string=self.architecture)
        
        if not arch_a:
            raise AssertionError(f"Cannot find package architecture a: [{package_name}, {self.architecture}]")

        arch_url = arch_a.get("href")
        if not arch_url:
            raise AssertionError(f"Cannot find package architecture href: [{package_name}, {self.architecture}]")

        arch_url = self.base_url + arch_url

        response = requests.get(arch_url)
        time.sleep(self.request_delay)

        while response.status_code == 500:
            time.sleep(self.retry_delay)
            response = requests.get(arch_url)
            print("500. Retry arch page")
            time.sleep(self.request_delay)

        if response.status_code != 200:
            print(f"Error fetching package arch info: HTTP {response.status_code}")
            print(f"Error at package arch [{package_name}, {self.architecture}]")
            raise AssertionError(f"Error at package arch [{package_name}, {self.architecture}]")
            
        soup = BeautifulSoup(response.content, 'html.parser')
        self.check_page_error(soup)
        
        self.package_arch_page_map[package_name] = soup
        
        return soup

    def download_package(self, package_name):
        download_url_map = {}

        arch_page = self.get_package_arch_page(package_name)
        
        if arch_page == None:
            message = f"Package '{package_name}' cannot be downloaded"
            print(message)
            self.warning_store.append(message)
            return 
        
        filename = arch_page.find("kbd").text
        download_path = f"download/{filename}"
        if os.path.isfile(download_path):
            #print(f"Skip downloaded package: {package_name}")
            return
            
        os.makedirs("download", exist_ok=True)
        print(f"Download package: {package_name}")
        
        div_content = arch_page.find("div", {"id": "content"})
        uls = div_content.findChildren("ul", recursive=True)
        
        # Build download_url_map first
        for ul in uls:
            lis = ul.findChildren("li", recursive=True)
            
            for li in lis:
                anchor = li.findChild("a")
                mirror_name = anchor.text
                mirror_url = anchor["href"]
                
                download_url_map[mirror_name] = mirror_url
        
        download_url = None
        for favorite_mirror in favorite_mirrors:
            if favorite_mirror in download_url_map:
                download_url = download_url_map[favorite_mirror]
                break
        
        if not download_url:
            key0 = list(download_url_map.keys())[0]
            download_url = download_url_map[key0]
            
        response = requests.get(download_url)
        time.sleep(self.request_delay)

        while response.status_code == 500:
            time.sleep(self.retry_delay)
            response = requests.get(download_url)
            print("500. Retry download")
            time.sleep(self.request_delay)

        if response.status_code != 200:
            raise AssertionError(f"Error at download_url [{package_name}, {self.architecture}, {download_url}]")
            
        with open(download_path, 'wb') as file:
            file.write(response.content)

        

if __name__ == "__main__":
    os.chdir(os.getcwd())
    
    import json
    with open("settings.json", "r") as fh:
        fc = fh.read()
        settings = json.loads(fc)
    distribution = settings["distribution"]
    architecture = settings["architecture"] 
    want_recommendations = settings["want_recommendations"]
    want_suggestions = settings["want_suggestions"]
    favorite_mirrors = settings["favorite_mirrors"]
    use_local_cache = settings["use_local_cache"]
    
    upd = UbuntuPackageDownloader(distribution=distribution,
        architecture=architecture,
        want_recommendations=want_recommendations,
        want_suggestions=want_suggestions,
        favorite_mirrors=favorite_mirrors,
        use_local_cache=use_local_cache)
        
    upd.run(settings["packages"])