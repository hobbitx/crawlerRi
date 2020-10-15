from urllib import robotparser
from util.threads import synchronized
from collections import OrderedDict
from .domain import Domain
from time import sleep
from urllib.parse import urljoin


class Scheduler():
    # tempo (em segundos) entre as requisições
    TIME_LIMIT_BETWEEN_REQUESTS = 30

    def __init__(self, str_usr_agent, int_page_limit, int_depth_limit, arr_urls_seeds):
        """
            Inicializa o escalonador. Atributos:
                - `str_usr_agent`: Nome do `User agent`. Usualmente, é o nome do navegador, em nosso caso,  será o nome do coletor (usualmente, terminado em `bot`)
                - `int_page_limit`: Número de páginas a serem coletadas
                - `int_depth_limit`: Profundidade máxima a ser coletada
                - `int_page_count`: Quantidade de página já coletada
                - `dic_url_per_domain`: Fila de URLs por domínio (explicado anteriormente)
                - `set_discovered_urls`: Conjunto de URLs descobertas, ou seja, que foi extraída em algum HTML e já adicionadas na fila - mesmo se já ela foi retirada da fila. A URL armazenada deve ser uma string.
                - `dic_robots_per_domain`: Dicionário armazenando, para cada domínio, o objeto representando as regras obtidas no `robots.txt`
        """
        self.str_usr_agent = str_usr_agent
        self.int_page_limit = int_page_limit
        self.int_depth_limit = int_depth_limit
        self.int_page_count = 0
        
        self.dic_url_per_domain = OrderedDict()
        self.set_discovered_urls = set()
        self.dic_robots_per_domain = {}
        for url in arr_urls_seeds:
            self.add_new_page(url[0],url[1])

    @synchronized
    def count_fetched_page(self):
        """
            Contabiliza o número de paginas já coletadas
        """
        self.int_page_count += 1

    def has_finished_crawl(self):
        """
            Verifica se finalizou a coleta
        """
        if(self.int_page_count > self.int_page_limit):
            return True
        return False

    @synchronized
    def can_add_page(self, obj_url, int_depth):
        """
            Retorna verdadeiro caso  profundade for menor que a maxima
            e a url não foi descoberta ainda
        """
        return (int_depth < self.int_depth_limit) and (obj_url not in self.set_discovered_urls)

    @synchronized
    def add_new_page(self, obj_url, int_depth):
        """
            Adiciona uma nova página
            obj_url: Objeto da classe ParseResult com a URL a ser adicionada
            int_depth: Profundidade na qual foi coletada essa URL
        """
        if self.can_add_page(obj_url, int_depth):
            obj_domain = obj_url.netloc
            domain = Domain(obj_domain, Scheduler.TIME_LIMIT_BETWEEN_REQUESTS)

            if domain in self.dic_url_per_domain:
                urls = self.dic_url_per_domain[domain]
                if (obj_url, int_depth) in urls:
                    return False

                self.dic_url_per_domain[domain].append((obj_url, int_depth))
                return True

            self.dic_url_per_domain[domain] = [(obj_url, int_depth)]
            return True

        return False

    @synchronized
    def get_next_url(self):
        """
        Obtem uma nova URL por meio da fila. Essa URL é removida da fila.
        Logo após, caso o servidor não tenha mais URLs, o mesmo também é removido.
        """
        for domain, urls in self.dic_url_per_domain.items():
            if domain.is_accessible():
                domain.accessed_now()
                if len(urls[0]) > 0 :
                    url, depth = urls[0]
                    urls.pop(0)
                    if self.can_fetch_page(url):
                        if not urls:
                            self.dic_url_per_domain.pop(domain)
                        self.count_fetched_page()
                        return url, depth
        return None,None

    def can_fetch_page(self, obj_url):
        """
        Verifica, por meio do robots.txt se uma determinada URL pode ser coletada
        """
        if obj_url.netloc in self.dic_robots_per_domain:
            robot = self.dic_robots_per_domain[obj_url.netloc]
        else:    
            robot = robotparser.RobotFileParser()
            try:
                robot.set_url(urljoin(obj_url.geturl(),'robots.txt'))
                robot.read()
                self.dic_robots_per_domain[obj_url.netloc] = robot
            except:
                return False
        return robot.can_fetch(self.str_usr_agent,obj_url.geturl())
        
