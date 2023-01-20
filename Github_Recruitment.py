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


    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    return args

TITRES = ["login", "name", "company", "location", "email", "hireable", "twitter_username", "blog"]

class Mon_client_github:
    def __init__(self, token, cache):
        self.token = token
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({'authorization': f'Bearer {token}'})

    def get_contributors(self, owner, repository, per_page=100):
        contributors = []
        page = 1
        while True:
            payload = {'per_page': per_page, 'page': page}
            r = self.session.get (f"https://api.github.com/repos/{owner}/{repository}/contributors", params=payload)
            if r.status_code > 299 :
                logging.error ("Erreur dans le repository ou owner")
                logging.info (str(r.json()["message"]))
                sys.exit(1)
            contributors.extend(r.json())
            page = page+1
            if len(r.json()) < per_page:
                break
        logging.info (f"J'ai trouvé {len(contributors)} contributeurs")
        return contributors

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
        personal_data = t.json()
        self.set_to_cache(login, personal_data)
        return personal_data

    def data_compilation(self, contributeurs):
        csv_final = [";".join(TITRES)]
        ligne = ""
        bar = Bar('Processing', max=len(contributeurs))
        for contributeur in contributeurs:
            if contributeur ['type'] != "User":
                bar.next()
                continue
            login = contributeur['login']
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
        try:
            cache = self.load_cache()
            return(cache[login])
        except KeyError:
            logging.info("Je n'ai pas trouvé le login dans le cache")
            return()

    def load_cache(self):
            if not os.path.isfile(self.cache):
                return {}
            file_descriptor = open(self.cache, "r")
            cache = json.load(file_descriptor)
            file_descriptor.close()
            return(cache)

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


def write_csv(mon_csv, path):
    try:
        file_descriptor = open(path,"w")
        file_descriptor.write("\n".join(mon_csv))
        file_descriptor.close()
    except Exception:
        logging.critical("Je n'ai pas réussi à écrire le dossier")
        sys.exit(1)


def mock_recuperer_les_contributeurs(file_name):
    file_descriptor = open(file_name)
    donne_contributeurs_mock = file_descriptor.read()
    donne_contributeurs_mock_json = json.loads(donne_contributeurs_mock)
    return donne_contributeurs_mock_json


def main():
    args = cmdline_parser()


    mon_client_github = Mon_client_github(args.token, args.cache)
    contributeurs = mon_client_github.get_contributors(args.organisation, args.repo)
    csv_final = mon_client_github.data_compilation(contributeurs)
    write_csv(csv_final, path=args.csv)

if __name__ == "__main__":
    main()







