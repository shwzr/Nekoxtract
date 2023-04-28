# Importation des modules nécessaires
import os
import re
import asyncio
import httpx

# Vérification de l'existence du fichier "links.txt" et suppression s'il existe déjà
if os.path.exists("links.txt"):
    os.remove("links.txt")

# Demande de l'URL de départ à l'utilisateur
url = input("Entrez l'URL de départ : ")

# Vérification que l'URL commence bien par "https://www.neko-sama.fr/"
if not url.startswith("https://www.neko-sama.fr/"):
    print("L'URL doit commencer par 'https://www.neko-sama.fr/'")
    exit()

# Ajout pour gérer les liens /info/
if "/anime/info/" in url:
    # Vérification si l'URL est en VF ou VOSTFR
    is_vostfr, is_vf = "_vostfr" in url, "_vf" in url
    # Remplacement de "/anime/info/" par "/anime/episode/"
    url = url.replace("/anime/info/", "/anime/episode/")
    # Suppression de "_vostfr" ou "_vf" dans l'URL
    url = re.sub(r"_vostfr|_vf", "", url)
    # Ajout du numéro de l'épisode et de la langue
    url += "-01_vostfr" if is_vostfr else "-01_vf"

# Recherche du numéro de l'épisode dans l'URL
episode_num_match = re.search(r"-(\d+)_", url)
if not episode_num_match or not episode_num_match.group(1).isdigit():
    print("Impossible de trouver le numéro de l'épisode dans l'URL spécifiée")
    exit()

# Vérification si l'URL est en VF ou VOSTFR
is_vostfr, is_vf = "_vostfr" in url, "_vf" in url

# Remplacement du numéro de l'épisode par "01" dans l'URL
if is_vostfr:
    url = re.sub(r"-(\d+)_vostfr", "-01_vostfr", url)
elif is_vf:
    url = re.sub(r"-(\d+)_vf", "-01_vf", url)
else:
    print("Le lien doit être en VF ou VOSTFR.")
    exit()
    
# Fonction pour récupérer le lien de l'épisode
async def fetch_episode_link(http_client, episode_num, url):
    # Génération de l'URL de l'épisode en fonction de l'épisode en cours de récupération
    next_url = url.replace("01_vostfr" if is_vostfr else "01_vf", "{:02d}_vostfr" if is_vostfr else "{:02d}_vf").format(episode_num)
    # Récupération de la page de l'épisode
    response = await http_client.get(next_url)
    # Vérification si la page de l'épisode existe
    if response.status_code == 404:
        return None
    # Recherche du lien de l'épisode dans le code HTML de la page de l'épisode
    match = re.search(r"(fusevideo.net|pstream.net)/e/(\w+)", response.text)
    if match:
        # Retour du lien de l'épisode
        return "Episode {} : https://{}/e/{}\n\n".format(episode_num, match.group(1), match.group(2))

# Fonction principale
async def main():
    # Création du client HTTP
    async with httpx.AsyncClient() as http_client:
        # Initialisation du numéro de l'épisode à 1
        episode_num = 1
        # Initialisation de la liste des liens
        links = []

        # Modifier cette valeur pour contrôler le nombre de requêtes simultanées
        concurrent_requests = 20

        while True:
            # Création des tâches pour récupérer les liens des épisodes
            tasks = [fetch_episode_link(http_client, episode_num + i, url) for i in range(concurrent_requests)]
            # Récupération des résultats de toutes les tâches
            results = await asyncio.gather(*tasks)

            # Vérification si de nouveaux liens ont été trouvés
            found_new_links = False
            for result in results:
                if result is None:
                    continue
                found_new_links = True
                links.append(result)
                episode_num += 1

            # Sortie de la boucle si aucun nouveau lien n'a été trouvé
            if not found_new_links:
                break

        # Écriture des liens dans le fichier "links.txt"
        with open("links.txt", "w") as f:
            f.writelines(links)

        # Affichage d'un message indiquant que les liens ont été enregistrés dans le fichier "links.txt"
        print("Les liens ont été enregistrés dans le fichier links.txt")

# Lancement de la fonction principale
asyncio.run(main())
