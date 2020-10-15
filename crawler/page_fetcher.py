from bs4 import BeautifulSoup
from threading import Thread
from urllib import error
import requests
from urllib.parse import urlparse, urljoin


class PageFetcher(Thread):
    def __init__(self, obj_scheduler):
        self.obj_scheduler = obj_scheduler

    def request_url(self, obj_url):
        """
            Faz a requisição e retorna o conteúdo em binário da URL passada como parametro

            obj_url: Instancia da classe ParseResult com a URL a ser requisitada.
        """
        try:
            headers = {'user-agent': self.obj_scheduler.str_usr_agent}
            response = requests.get(obj_url.geturl(), headers=headers)
            if "text/html" in response.headers['Content-Type'] :
                return response.content
            return None
        except error.HTTPError as exception:
            print(exception)
            return None
    def discover_links(self, obj_url, int_depth, bin_str_content):
        """
        Retorna os links do conteúdo bin_str_content da página já requisitada obj_url
        """
        soup = BeautifulSoup(bin_str_content, features="lxml")
        for link in soup.select("body a"):
            if link.has_attr("href"):
                obj_new_url = urlparse(urljoin(obj_url.geturl(),link["href"]))
                if obj_url.netloc == obj_new_url.netloc:
                    int_new_depth = int_depth+1
                else:
                    int_new_depth = 0
                yield obj_new_url, int_new_depth
            else:
                yield ("", 0)

    def crawl_new_url(self):
        """
            Coleta uma nova URL, obtendo-a do escalonador
        """
        
        obj_url,int_depth = self.obj_scheduler.get_next_url()
        
        if obj_url is None:
            pass
        else:
            result = self.request_url(obj_url)
            #print(result.decode("utf-8"))
            
            with open("pages.txt","a",encoding="utf-8") as file:
                file.write(obj_url.geturl()+"\n")
            for url_link, depth in self.discover_links(obj_url,int_depth,result):
                if isinstance(url_link, str):
                    pass
                else:
                    self.obj_scheduler.add_new_page(url_link,depth)
            
        
        

    def run(self):
        """
            Executa coleta enquanto houver páginas a serem coletadas
        """
        while not self.obj_scheduler.has_finished_crawl():
            self.crawl_new_url()
