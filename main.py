import sys
import requests
import json
import time
from pprint import pprint as print
import os
import argparse
import logging
from progress.bar import Bar

def cmdline_parser() :
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-d",
            "--debug",
            help="Print lots of debugging statements",
            action="store_const",
            dest="loglevel",
            const=logging.DEBUG,
            default=logging.WARNING,
     )  # mind the default value

    parser.add_argument(
        "-v",
        "--verbose",
        help="Be verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
     )

    parser.add_argument(
        "-q",
        "--quiet",
        help="Be quiet",
        action="store_const",
        dest="loglevel",
        const=logging.CRITICAL,
     )

    parser.add_argument("-t", "--token", help="mon token github", required=True)
    parser.add_argument("-c","--csv", help="fichier dans lequel je vais ecrire mon csv", default="Mon_Outil_Bg.csv")
    parser.add_argument("-C","--cache", help="fichier de cache", default="Cache.json")
    parser.add_argument("-o","--organisation", help="l'organisation dans lequel je veux chercher", required=True)
    parser.add_argument("-r","--repo", help="le repo dans lequel je veux chercher", required=True)
    # argparse : créer une interface en ligne de commande -> l'idée : run le code avec le token git sans le donner
    # Convention ajouter argument q v d
    # q : le programme est en silence
    # d : le programme affiche les informations à desination des dev en vue de résoudre l'erreur
    # v : le programme affichera toutes les informations utiles supplémentaires

    args = parser.parse_args()
    #parser les arguments et les stockers dans args
    logging.basicConfig(level=args.loglevel)
    #basic config : va passer quelle niveau d'alerte (logging python3)
    return args

TITRES = ["login", "name", "company", "location", "email", "hireable", "twitter_username", "blog"]

class Mon_client_github:
    def __init__(self, token, cache):
        self.token = token
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({'authorization': f'Bearer {token}'})

    def get_contributors(self, owner, repository, per_page=100):
        # define what is next page and then if next page -> go or break if not
        contributors = []
        page = 1
        while True:
            payload = {'per_page': per_page, 'page': page}
            r = self.session.get (f"https://api.github.com/repos/{owner}/{repository}/contributors", params=payload)
            if r.status_code > 299 :
                logging.error ("Erreur dans le repository ou owner")
                logging.info (str(r.json()["message"]))
                sys.exit(1)
                # sys.exit = 0 = tout s'est bien passé /// sys.exit =/= 0 = il y a une erreur sur cette boucle
            contributors.extend(r.json())
            page = page+1
            if len(r.json()) < per_page:
                break
        logging.info (f"J'ai trouvé {len(contributors)} contributeurs")
        return contributors

#Dans ce bloc là a été defini une fonction* qui permettent les choses ci-dessous :
#Ce bloc sert à se connecter à l'API de Github, récupérer les contributeurs du projet X owner X
#Dans le cas où le projet n'existe pas ou bien qu'il y a une faute dans le OWNER ou REPOSITORY, le programme affiche un message d'erreur

    def get_personal_data(self, login):
        cached_personal_data = self.get_from_cache(login)
        if cached_personal_data :
            return cached_personal_data
        t = self.session.get (f"https://api.github.com/users/{login}")
        #https://api.github.com/users/USERNAME donc login variable qui évolue
        if t.status_code > 299 :
            print("Erreur lors de la récupération du login " + login)
            print (str(t.json()["message"]))
            sys.exit(1)
        #time.sleep(1)  # attend 1sec par ittération, pour ne pas se faire rate limit
        personal_data = t.json()
        self.set_to_cache(login, personal_data)
        return personal_data

    def data_compilation(self, contributeurs):
        csv_final = [";".join(TITRES)]
        ligne = ""
        bar = Bar('Processing', max=len(contributeurs))
        for contributeur in contributeurs: #Si_le_type_de_user_est_bot_ne_pas_le_screener
            if contributeur ['type'] != "User":
                bar.next()
                continue
            login = contributeur['login']
            #info = mock_recuperer_les_contributeurs("/Users/aguingan/PycharmProjects/Arthur2.0/doc_git2")
            info = self.get_personal_data(login)
            for data in TITRES:
                if data not in info:
                    ligne += "" + ";"
                else:
                    ligne += str(info[data]) + ";"
            csv_final.append(ligne)
            ligne = ""
            bar.next()
        bar.finish()
        return csv_final

    def get_from_cache(self,login):
        #Ouvrir le fichier, lire le fichier, chercher les infos de login dans le fichier
        try:
            cache = self.load_cache()
            return(cache[login])
        except KeyError:
            logging.info("Je n'ai pas trouvé le login dans le cache")
            return()

    def load_cache(self):
        #try:
            if not os.path.isfile(self.cache):
                return {}
            file_descriptor = open(self.cache, "r")
            cache = json.load(file_descriptor)
            file_descriptor.close()
            return(cache)
        #except Exception:
        #    print("Je n'ai réussi à lire le cache load_cache")
         #   sys.exit(1)

    def set_to_cache(self,login, personnal_data) :
        cache = self.load_cache()
        cache [login] = personnal_data
        self.write_cache(cache)

    def write_cache (self,cache):
        try:
            file_descriptor = open(self.cache, "w")
            json.dump(cache, file_descriptor, indent=True)
            file_descriptor.close()
        except Exception:
            logging.critical("Je n'ai réussi à lire le cache write_cache")
            sys.exit(1)

#Dans ce bloc là a été defini une fonction* qui permettent les choses ci-dessous :
#Ce bloc sert à récupérer dans le repo choisi précédemment les infos sur le contributeur X
#Dans le cas où le login n'existe pas ou bien qu'il y a une faute dans son écriture, le programme affiche un message d'erreur



#Dans ce bloc là a été defini une fonction* qui permettent les choses ci-dessous :
#Ce bloc sert filtrer et ordonner les données que l'on a extraite précédémment du login X


def write_csv(mon_csv, path):
    try:
        file_descriptor = open(path,"w")
        file_descriptor.write("\n".join(mon_csv))
        file_descriptor.close()
    except Exception:
        logging.critical("Je n'ai pas réussi à écrire le dossier")
        sys.exit(1)

#Dans ce bloc là a été defini une fonction* qui permettent les choses ci-dessous :
#Compiler les données précédemment ordonnées et filtrées dans un fichier CSV que l'on créer

def mock_recuperer_les_contributeurs(file_name):
    file_descriptor = open(file_name)
    donne_contributeurs_mock = file_descriptor.read()
    donne_contributeurs_mock_json = json.loads(donne_contributeurs_mock)
    return donne_contributeurs_mock_json


def main():
    args = cmdline_parser()
    #print(f"mon token est:{args.mon_token}")
    #Dans ce bloc là a été defini une fonction* qui permettent les choses ci-dessous :
    #On a maqueté un fichier qui sort les mêmes données que Github pour ne pas se faire bloquer et pouvoir tester le code "pas en prod"

    mon_client_github = Mon_client_github(args.token, args.cache)
    # contributeurs = mock_recuperer_les_contributeurs("doc_git")
    contributeurs = mon_client_github.get_contributors(args.organisation, args.repo)
    #print(contributeurs)
    csv_final = mon_client_github.data_compilation(contributeurs)
    write_csv(csv_final, path=args.csv)
    # *fonction = une fraction de code qui peut être exécuté indépendamment du reste

if __name__ == "__main__":
    main()







