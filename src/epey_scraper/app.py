#!/usr/bin/env python3

import concurrent.futures
from datetime import datetime

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from simple_term_menu import TerminalMenu
from tqdm import tqdm

MAIN_URL = "https://www.epey.com/"

now = datetime.now()
dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")


def scrape(product):
    product_url = MAIN_URL + product
    r = httpx.get(product_url)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def scrape_page(product, n):
    page_url = MAIN_URL + product + "/" + str(n)
    r = httpx.get(page_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("div", {"class": "listele table"})
    items = table.find_all("ul", {"class": "metin row"})
    items_list = []
    for item in items:
        # if "Reklam" in item:
        #     pass
        # else:
        item_specs = item.find_all("li")
        item_specs_list = []
        item_name = item_specs[0].find("a", {"class": "urunadi"}).getText()
        item_link = item_specs[0].a["href"]
        try:
            item_price = float(
                item_specs[1].a.text.split()[0].replace(".", "").replace(",", ".")
            )
        except (AttributeError, ValueError) as e:
            item_price = None
        try:
            item_score = int(item_specs[-1].div["data-text"])
        except TypeError:
            item_score = None
        item_specs_list.extend([item_name, item_price])
        other_specs_count = (len(item_specs) - 2) * -1
        for i in range(other_specs_count, -1):
            item_specs_list.append(item_specs[i].getText())
        item_specs_list.extend([item_score, item_link])
        items_list.append(item_specs_list)
    return items_list


def scrape_item_cell_names(product):
    soup = scrape(product)
    table = soup.find("div", {"class": "listele table"})
    items = table.find("ul", {"class": "baslik row"}).find_all("li")
    cell_names_list = [item.getText() for item in items]
    cell_names_list.append("Link")
    return cell_names_list


def get_page_count(product):
    soup = scrape(product)
    page_count = (
        soup.find("a", class_="son")["onclick"]
        .split(";")[0]
        .replace("sayfa(", "")
        .replace(")", "")
    )
    return int(page_count)


def scrape_multi_pages(product):
    page_count = get_page_count(product)
    multi_list = []
    with tqdm(total=page_count) as pbar:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_page = {
                executor.submit(scrape_page, product, n): n
                for n in range(1, page_count + 1)
            }
            for future in concurrent.futures.as_completed(future_to_page):
                multi_list.append(future.result())
                pbar.update(1)
    return multi_list


def make_dataframe(product):
    headers = scrape_item_cell_names(product)
    full_list = []
    for page in scrape_multi_pages(product):
        for i in page:
            full_list.append(i)
    return pd.DataFrame(full_list, columns=headers)


def menu():
    options = [
        "Anakart",
        "Fotoğraf makinesi",
        "Ekran kartı",
        "İşlemci",
        "Oyun konsolu",
        "Laptop",
        "Monitör",
        "Motosiklet",
        "RAM",
        "Tablet",
        "Akıllı telefon",
        "Televizyon",
        "Tuşlu telefon",
        "Yazıcı",
    ]
    options_dict = {
        "Anakart": "anakart",
        "Fotoğraf makinesi": "fotograf-kamera",
        "Ekran kartı": "ekran-karti",
        "İşlemci": "islemci",
        "Oyun konsolu": "oyun-konsolu",
        "Laptop": "laptop",
        "Monitör": "monitor",
        "Motosiklet": "motosiklet",
        "RAM": "bellek-ram",
        "Tablet": "tablet",
        "Akıllı telefon": "akilli-telefonlar",
        "Televizyon": "televizyon",
        "Tuşlu telefon": "tuslu-telefon",
        "Yazıcı": "yazici",
    }
    terminal_menu = TerminalMenu(options)
    menu_entry_index = terminal_menu.show()
    return options_dict[options[menu_entry_index]]


def main():
    print("\nChoose product type:\n")
    option = menu()
    df = make_dataframe(option)
    df.to_csv(f"{option.capitalize()}_{dt_string}.csv", index=False)


if __name__ == "__main__":
    main()
