import unittest
from urllib.parse import urlparse
import time
from .domain import *
from .scheduler import *


class DomainTest(unittest.TestCase):

    def test_domain(self):
        domain = Domain("xpto.com", 10)
        self.assertTrue(domain.is_accessible(),
                        "Ao iniciar um servidor, ele deve estar acessível")

        domain.accessed_now()
        self.assertTrue(not domain.is_accessible(
        ), "Como ele acabou de ser acessado, ele não pode estar acessivel")
        print("Verificando acesso a um dominio já requisitado (após espera)")
        print("aguardando 10 segundos...")
        time.sleep(10)
        self.assertTrue(domain.is_accessible(
        ), f"Após a espera do tempo limite entre requisições, o servidor deveria voltar a ficar acessível")


class SchedulerTest(unittest.TestCase):
    def setUp(self):
        arr_urls_seeds = []
        self.scheduler = Scheduler(str_usr_agent="xxbot",
                                   int_page_limit=10,
                                   int_depth_limit=3,
                                   arr_urls_seeds=arr_urls_seeds)

    def test_init(self):
        arr_str_urls_seeds = ["cnn.com",
                              "www.gq.com.au/", "www.huffingtonpost.com/"]
        arr_urls_seeds = [urlparse(str_url) for str_url in arr_str_urls_seeds]
        self.assertEqual(3, 3, "Nao foi adicionado as sementes solicitadas")

    def test_add_remove_pages(self):
        # tuplas url,profundidade a serem testadas
        urlProf = (urlparse("http://www.xpto.com.br/index.html"), 100000)
        urlTerra = (urlparse("http://www.terra.com.br/index.html"), 1)
        urlTerraRep = (urlparse("http://www.terra.com.br/index.html"), 1)
        urlUOL1 = (urlparse("http://www.uol.com.br/"), 1)
        urlUOL2 = (urlparse("http://www.uol.com.br/profMax.html"), 1)
        urlGlobo = (urlparse("http://www.globo.com.br/profMax.html"), 1)

        arr_urls = [urlProf, urlTerra, urlTerraRep, urlUOL1, urlUOL2, urlGlobo]

        # adiciona todas as paginas em ordem
        # "**" faz passar a url e a profundidade
        # como o primeiro e segundo parametro, respectivamente
        [self.scheduler.add_new_page(*url) for url in arr_urls]
        # verificação se adicionou a mesma URL duas vezes
        urls = set()
        for key, arr in self.scheduler.dic_url_per_domain.items():
            set_urls = set(arr)
            self.assertTrue(len(set_urls) == len(
                arr), "Existem URLs repetidas na fila!")

        u1 = self.scheduler.get_next_url()
        u2 = self.scheduler.get_next_url()
        u3 = self.scheduler.get_next_url()
        # ao obter a UOL, é considerado a primeira requição nela
        time_first_hit_UOL = datetime.now()

        print("Verificação da ordem das URLs...")
        arr_expected_order = [urlTerra[0], urlUOL1[0], urlGlobo[0]]
        arr_url_order = [u1[0], u2[0], u3[0]]
        for i, expected_url in enumerate(arr_expected_order):
            self.assertEqual(
                expected_url, arr_url_order[i], f"A URL {expected_url.geturl()} deveria ser a {i+1}ª a ser obtida e foi a {arr_url_order[i].geturl()}.")

        # resgata o quarto (UOL)
        print("Resgatando a segunda página do mesmo dominio...")
        u4 = self.scheduler.get_next_url()
        time_second_hit_UOL = datetime.now()
        time_wait = (time_second_hit_UOL - time_first_hit_UOL)
        time_wait_seconds = time_wait.seconds
        if(time_wait.microseconds > 500000):
            time_wait_seconds += 1
        print(f"Tempo esperado: {time_wait_seconds} segundos")
        self.assertTrue(time_wait_seconds >= Scheduler.TIME_LIMIT_BETWEEN_REQUESTS,
                        f"O tempo de espera entre as duas requisições do mesmo servidor não foi maior que {Scheduler.TIME_LIMIT_BETWEEN_REQUESTS} (foi {time_wait_seconds} segundos)")

    def test_can_fetch_page(self):
        obj_url_not_allowed = urlparse("https://www.globo.com/beta/dasdas")
        obj_url_allowed = urlparse("https://www.terra.com/index.html")

        bol_not_allowed = self.scheduler.can_fetch_page(obj_url_not_allowed)
        bol_allowed = self.scheduler.can_fetch_page(obj_url_allowed)

        obj_robot_not_allowed = self.scheduler.dic_robots_per_domain[obj_url_not_allowed.netloc]

        # verifica se, nas requisições, o robot retornou a resposta correta
        self.assertTrue(
            not bol_not_allowed, f"Não deveria ser permitida requisitar a url {obj_url_not_allowed.geturl()} segundo o robots.txt  do dominio {obj_url_not_allowed.netloc}, porém o método can_fetch_page retornou True")
        self.assertTrue(
            bol_allowed, f"Não deveria ser permitida requisitar a url {obj_url_allowed.geturl()} segundo o robots.txt do dominio {obj_url_allowed.netloc}, porém o método can_fetch_page retornou False")

        # verifica se foi adicionado a globo.com
        self.assertTrue(obj_url_allowed.netloc in self.scheduler.dic_robots_per_domain,
                        "Não foi adicionado o robot da globo.com em dic_robots_per_domain do escalonador")

        # verifica se foi usado o mesmo robot
        self.scheduler.can_fetch_page(obj_url_not_allowed)
        self.assertTrue(obj_robot_not_allowed == self.scheduler.dic_robots_per_domain[obj_url_not_allowed.netloc],
                        "Na segunda requisição de um mesmo dominio, você não pode criar um novo objeto RobotFileParser")

        self.assertTrue(
            bol_allowed, f"O mesmo robots.txt não pode ser requisitado duas vezes.")


if __name__ == "__main__":
    unittest.main()
