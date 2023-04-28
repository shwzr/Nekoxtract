from tkinter import messagebox, ttk
import tkinter as tk
import asyncio
import httpx
import re
import os

icon_path = "neko-sama.ico"

def on_submit():
    global url, is_vostfr, is_vf
    url = url_entry.get()
    if url.startswith("https://neko-sama.fr/"):
        url = url.replace("https://neko-sama.fr/", "https://www.neko-sama.fr/")
    elif url.startswith("www.neko-sama.fr/"):
        url = "https://" + url
    elif url.startswith("neko-sama.fr/"):
        url = "https://www." + url
    elif not url.startswith("https://www.neko-sama.fr/"):
        messagebox.showerror("Erreur", "L'URL doit commencer par 'https://www.neko-sama.fr/'")
        return

    if os.path.exists("links.txt"):
        os.remove("links.txt")

    # Ajout pour gérer les liens /info/
    if "/anime/info/" in url:
        is_vostfr, is_vf = "_vostfr" in url, "_vf" in url
        url = url.replace("/anime/info/", "/anime/episode/")
        url = re.sub(r"_vostfr|_vf", "", url)
        url += "-01_vostfr" if is_vostfr else "-01_vf"

    

    episode_num_match = re.search(r"-(\d+)_", url)
    if not episode_num_match or not episode_num_match.group(1).isdigit():
        messagebox.showerror("Erreur", "Impossible de trouver le numéro de l'épisode dans l'URL spécifiée")
        return

    is_vostfr, is_vf = "_vostfr" in url, "_vf" in url
    if is_vostfr:
        url = re.sub(r"-(\d+)_vostfr", "-01_vostfr", url)
    elif is_vf:
        url = re.sub(r"-(\d+)_vf", "-01_vf", url)
    else:
        messagebox.showerror("Erreur", "Le lien doit être en VF ou VOSTFR.")
        return

    asyncio.run(main())


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

        # Affichez les liens dans l'espace de texte
        display_links(links)

        # Écrivez les liens dans le fichier links.txt
        with open("links.txt", "w") as f:
            f.writelines(links)

        messagebox.showinfo("Succès", "Les liens ont été enregistrés dans le fichier links.txt")

def display_links(links):
    url_text.delete(1.0, tk.END)
    for link in links:
        url_text.insert(tk.END, link)        

# Créez la fenêtre principale
window = tk.Tk()
window.title("Nekoxtract")
window.iconbitmap(default=icon_path)
window.resizable(0, 0)
window.configure(background="#F5F5F5")

# Créez les widgets
url_label = tk.Label(window, text="Entrez l'URL de départ :", font=("Helvetica", 14), fg="#333333", bg="#F5F5F5")
url_label.grid(row=0, column=0, padx=5, pady=5)

url_entry = ttk.Entry(window, width=30, font=("Helvetica", 14))
url_entry.grid(row=0, column=1, padx=5, pady=5)

submit_button = tk.Button(window, text="Extraire les liens", font=("Helvetica", 14), bg="#333333", fg="#FFFFFF", command=on_submit)
submit_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

url_text = tk.Text(window, width=50, height=20, font=("Helvetica", 14))
url_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

def show_info():
    tk.messagebox.showinfo("Infos", "Version: 1.1\nContact: Showzur#8509")

info_button = tk.Button(window, text="i", font=("Helvetica", 14), fg="#333333", bg="#F5F5F5", bd=0, command=show_info)
info_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

window.mainloop()
