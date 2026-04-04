#!/usr/bin/env python3
import argparse
import csv
import os
import re
import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup

DEFAULT_URL = "https://www.dieese.org.br/analisecestabasica/salarioMinimo.html#1994"
DEFAULT_OUTPUT = "data/raw/salario_minimo_dieese.csv"

def parse_currency(text: str) -> Optional[float]:
    if not text:
        return None
    text = text.strip()
    # remove non numeric chars except . , and -
    text = re.sub(r'[^\d\.,\-]', '', text)
    if text == '':
        return None
    # if both '.' and ',' present => '.' thousands, ',' decimal
    if '.' in text and ',' in text:
        s = text.replace('.', '').replace(',', '.')
    else:
        if ',' in text:
            s = text.replace(',', '.')
        else:
            s = text  # assume '.' is decimal separator
    try:
        return float(s)
    except ValueError:
        return None

def find_table(soup: BeautifulSoup):
    # try to locate the relevant table by looking for the 'subtitulo' rows
    for tbl in soup.find_all('table'):
        if tbl.find('tr', class_='subtitulo'):
            return tbl
    # fallback: first table
    return soup.find('table')

def scrape(url: str):
    resp = requests.get(url, headers={'User-Agent': 'python-requests'}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')
    table = find_table(soup)
    if table is None:
        return []
    rows = table.find_all('tr')
    data = []
    current_year = None
    for tr in rows:
        classes = tr.get('class') or []
        # year marker rows
        if any('subtitulo' in c for c in classes):
            year_text = tr.get_text(strip=True)
            m = re.search(r'(\d{4})', year_text)
            current_year = m.group(1) if m else None
            continue
        tds = tr.find_all(['td', 'th'])
        if not tds:
            continue
        if len(tds) == 1:
            # some rows might contain only the year
            text = tds[0].get_text(strip=True)
            m = re.search(r'(\d{4})', text)
            if m:
                current_year = m.group(1)
            continue
        if len(tds) < 3:
            continue
        month = tds[0].get_text(strip=True)
        nominal_raw = tds[1].get_text(strip=True)
        necessario_raw = tds[2].get_text(strip=True)
        # skip until we have a detected year
        if not current_year:
            continue
        # skip header-like rows (ex.: "Período")
        if month.lower().strip() in ('período', 'periodo', ''):
            continue
        nominal = parse_currency(nominal_raw)
        necessario = parse_currency(necessario_raw)
        if nominal is None and necessario is None:
            continue
        # mapear nome do mês para número usando map_month_name_to_num()
        mnum = map_month_name_to_num(month)
        if mnum is not None:
            mes = f"{int(mnum):02d}"
        else:
            m = re.search(r'(\d{1,2})', month)
            mes = f"{int(m.group(1)):02d}" if m else month
        data.append([current_year, mes, nominal, necessario])
    return data

def write_csv(rows, output_path):
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ano', 'mes', 'salario_min_nominal', 'salario_min_necessario'])
        for row in rows:
            writer.writerow(row)

def map_month_name_to_num(name: str) -> Optional[int]:
    name = name.strip().lower()
    month_map = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9,
        'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    return month_map.get(name)

def main():
    parser = argparse.ArgumentParser(description='Scrape DIEESE salário mínimo e exportar CSV')
    parser.add_argument('--url', default=DEFAULT_URL)
    parser.add_argument('--output', default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = scrape(args.url)
    if not rows:
        print('Nenhum dado extraído.', file=sys.stderr)
        sys.exit(2)
    write_csv(rows, args.output)
    print(f'Gravado {len(rows)} linhas em {args.output}')

if __name__ == '__main__':
    main()