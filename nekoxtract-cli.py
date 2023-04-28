import os
import re
import asyncio
import httpx

if os.path.exists("links.txt"):
    os.remove("links.txt")

url = input("Entrez l'URL de départ : ")
if not url.startswith("https://www.neko-sama.fr/"):
    print("L'URL doit commencer par 'https://www.neko-sama.fr/'")
    exit()

# Ajout pour gérer les liens /info/
if "/anime/info/" in url:
    is_vostfr, is_vf = "_vostfr" in url, "_vf" in url
    url = url.replace("/anime/info/", "/anime/episode/")
    url = re.sub(r"_vostfr|_vf", "", url)
    url += "-01_vostfr" if is_vostfr else "-01_vf"

episode_num_match = re.search(r"-(\d+)_", url)
if not episode_num_match or not episode_num_match.group(1).isdigit():
    print("Impossible de trouver le numéro de l'épisode dans l'URL spécifiée")
    exit()

is_vostfr, is_vf = "_vostfr" in url, "_vf" in url
if is_vostfr:
    url = re.sub(r"-(\d+)_vostfr", "-01_vostfr", url)
elif is_vf:
    url = re.sub(r"-(\d+)_vf", "-01_vf", url)
else:
    print("Le lien doit être en VF ou VOSTFR.")
    exit()

async def fetch_episode_link(http_client, episode_num, url):
    next_url = url.replace("01_vostfr" if is_vostfr else "01_vf", "{:02d}_vostfr" if is_vostfr else "{:02d}_vf").format(episode_num)
    response = await http_client.get(next_url)
    if response.status_code == 404:
        return None
    match = re.search(r"(fusevideo.net|pstream.net)/e/(\w+)", response.text)
    if match:
        return "Episode {} : https://{}/e/{}\n\n".format(episode_num, match.group(1), match.group(2))

async def main():
    async with httpx.AsyncClient() as http_client:
        episode_num = 1
        links = []

        # Modifier cette valeur pour contrôler le nombre de requêtes simultanées
        concurrent_requests = 20

        while True:
            tasks = [fetch_episode_link(http_client, episode_num + i, url) for i in range(concurrent_requests)]
            results = await asyncio.gather(*tasks)

            found_new_links = False
            for result in results:
                if result is None:
                    continue
                found_new_links = True
                links.append(result)
                episode_num += 1

            if not found_new_links:
                break

        with open("links.txt", "w") as f:
            f.writelines(links)

        print("Les liens ont été enregistrés dans le fichier links.txt")

asyncio.run(main())