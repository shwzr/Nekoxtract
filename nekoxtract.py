from tkinter import messagebox, ttk
import tkinter as tk
import asyncio
import httpx
import re
import os

icon_path = "neko-sama.ico"

def on_submit():
    # Définir les variables globales pour l'URL et le type de vidéo (VF ou VOSTFR)
    global url, is_vostfr, is_vf
    url = url_entry.get()
    
    # Valider et formater l'URL pour s'assurer qu'elle est correcte et contient "www"
    if url.startswith("https://neko-sama.fr/"):
        url = url.replace("https://neko-sama.fr/", "https://www.neko-sama.fr/")
    elif url.startswith("www.neko-sama.fr/"):
        url = "https://" + url
    elif url.startswith("neko-sama.fr/"):
        url = "https://www." + url
    elif not url.startswith("https://www.neko-sama.fr/"):
        messagebox.showerror("Erreur", "L'URL doit commencer par 'https://www.neko-sama.fr/'")
        return

    # Supprimer le fichier "links.txt" s'il existe
    if os.path.exists("links.txt"):
        os.remove("links.txt")

    # Ajouter une gestion spéciale pour les liens "/info/"
    if "/anime/info/" in url:
        is_vostfr, is_vf = "_vostfr" in url, "_vf" in url
        url = url.replace("/anime/info/", "/anime/episode/")
        url = re.sub(r"_vostfr|_vf", "", url)
        url += "-01_vostfr" if is_vostfr else "-01_vf"

    # Extraire le numéro de l'épisode de l'URL
    episode_num_match = re.search(r"-(\d+)_", url)
    if not episode_num_match or not episode_num_match.group(1).isdigit():
        messagebox.showerror("Erreur", "Impossible de trouver le numéro de l'épisode dans l'URL spécifiée")
        return

    # Définir le type de vidéo en fonction de l'URL
    is_vostfr, is_vf = "_vostfr" in url, "_vf" in url
    if is_vostfr:
        url = re.sub(r"-(\d+)_vostfr", "-01_vostfr", url)
    elif is_vf:
        url = re.sub(r"-(\d+)_vf", "-01_vf", url)
    else:
        messagebox.showerror("Erreur", "Le lien doit être en VF ou VOSTFR.")
        return

    # Lancer la fonction principale avec asyncio
    asyncio.run(main())


async def fetch_episode_link(http_client, episode_num, url):
    # Génère l'URL pour l'épisode suivant en remplaçant le numéro dans l'URL de départ
    next_url = url.replace("01_vostfr" if is_vostfr else "01_vf", "{:02d}_vostfr" if is_vostfr else "{:02d}_vf").format(episode_num)
    
    # Envoie une requête GET à l'URL pour l'épisode suivant
    response = await http_client.get(next_url)
    
    # Vérifie si la réponse est 404 (page non trouvée)
    if response.status_code == 404:
        return None
    
    # Recherche un lien vers l'épisode sur la page
    match = re.search(r"(fusevideo.net|pstream.net)/e/(\w+)", response.text)
    if match:
        # Si un lien est trouvé, le retourne avec le numéro d'épisode correspondant
        return "Episode {} : https://{}/e/{}\n\n".format(episode_num, match.group(1), match.group(2))

async def main():
    # Crée un client HTTP asynchrone
    async with httpx.AsyncClient() as http_client:
        episode_num = 1
        links = []
        concurrent_requests = 20

        # Boucle jusqu'à ce qu'aucun nouveau lien ne soit trouvé
        while True:
            # Crée des tâches pour récupérer les liens des épisodes suivants de manière asynchrone
            tasks = [fetch_episode_link(http_client, episode_num + i, url) for i in range(concurrent_requests)]
            
            # Attend que toutes les tâches soient terminées et récupère les résultats
            results = await asyncio.gather(*tasks)

            found_new_links = False
            for result in results:
                if result is None:
                    continue
                found_new_links = True
                # Si un nouveau lien est trouvé, l'ajoute à la liste des liens avec le numéro d'épisode correspondant
                links.append(result)
                episode_num += 1

            if not found_new_links:
                # Si aucun nouveau lien n'est trouvé, sort de la boucle
                break

        # Affiche les liens dans la fenêtre de texte
        display_links(links)

        # Écrit les liens dans le fichier links.txt
        with open("links.txt", "w") as f:
            f.writelines(links)

        # Affiche une boîte de dialogue pour informer l'utilisateur que les liens ont été enregistrés dans le fichier
        messagebox.showinfo("Succès", "Les liens ont été enregistrés dans le fichier links.txt")

def display_links(links):
    # Efface le contenu de la fenêtre de texte
    url_text.delete(1.0, tk.END)
    # Ajoute chaque lien à la fenêtre de texte
    for link in links:
        url_text.insert(tk.END, link)

# Crée la fenêtre principale
window = tk.Tk()
window.title("Nekoxtract")
window.iconbitmap(default=icon_path)
window.resizable(0, 0)
window.configure(background="#F5F5F5")

# Crée les widgets
url_label = tk.Label(window, text="Entrez l'URL de départ :", font=("Helvetica", 14), fg="#333333", bg="#F5F5F5")
url_label.grid(row=0, column=0, padx=5, pady=5)

url_entry = ttk.Entry(window, width=30, font=("Helvetica", 14))
url_entry.grid(row=0, column=1, padx=5, pady=5)

submit_button = tk.Button(window, text="Extraire les liens", font=("Helvetica", 14), bg="#333333", fg="#FFFFFF", command=on_submit)
submit_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

clear_button = tk.Button(window, text="Clear", font=("Helvetica", 14), bg="#333333", fg="#FFFFFF", command=clear_entry)
clear_button.grid(row=1, column=1, padx=(50,5), pady=5)

url_text = tk.Text(window, width=50, height=20, font=("Helvetica", 14))
url_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

def show_info():
    tk.messagebox.showinfo("Infos", "Version: 1.1\nContact: Showzur#8509")

info_button = tk.Button(window, text="i", font=("Helvetica", 14), fg="#333333", bg="#F5F5F5", bd=0, command=show_info)
info_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

window.mainloop()
