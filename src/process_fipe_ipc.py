#!/usr/bin/env python3
"""
Parse HTML exportado pela FIPE (table id="tabela_resultsEx") e gera CSV
colunas: ano, mes, habitação, alimentação, transporte, despesas pessoais,
saúde, vestuário, educação, geral
"""
import argparse
import os
import re
import unicodedata
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup

MONTH_MAP = {
    "jan": 1, "janeiro": 1,
    "fev": 2, "fevereiro": 2,
    "mar": 3, "marco": 3, "março": 3,
    "abr": 4, "abril": 4,
    "mai": 5, "maio": 5,
    "jun": 6, "junho": 6,
    "jul": 7, "julho": 7,
    "ago": 8, "agosto": 8,
    "set": 9, "setembro": 9,
    "out": 10, "outubro": 10,
    "nov": 11, "novembro": 11,
    "dez": 12, "dezembro": 12,
}

DISPLAY_COLS = [
    "habitação",
    "alimentação",
    "transporte",
    "despesas pessoais",
    "saúde",
    "vestuário",
    "educação",
    "geral",
]

def strip_accents(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_accents(str(s)).lower()).strip()

def parse_numeric(x) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    s = re.sub(r"[^\d\-,\.]", "", s)
    if s == "":
        return None
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None

def map_head_to_col(h: str) -> Optional[str]:
    n = normalize(h)
    if "habit" in n:
        return "habitação"
    if "aliment" in n:
        return "alimentação"
    if "transp" in n:
        return "transporte"
    if "desp" in n:
        return "despesas pessoais"
    if "saud" in n:
        return "saúde"
    if "vest" in n:
        return "vestuário"
    if "educ" in n:
        return "educação"
    if "geral" in n or "indice" in n or "ipc" in n:
        return "geral"
    if "mes" in n or "mês" in n:
        return "mes"
    return None

def month_to_int(s: Optional[int | str]) -> Optional[int]:
    if s is None:
        return None
    t = strip_accents(str(s)).lower().strip()
    if t == "":
        return None
    t_clean = re.sub(r"[^a-z0-9]", "", t)
    if t_clean.isdigit():
        try:
            v = int(t_clean)
            if 1 <= v <= 12:
                return v
        except:
            pass
    key = t_clean[:3]
    return MONTH_MAP.get(key)

def parse_html(input_path: str):
    with open(input_path, "rb") as f:
        soup = BeautifulSoup(f, "lxml")
    table = soup.find("table", id="tabela_resultsEx") or soup.find("table")
    if table is None:
        raise SystemExit("Tabela não encontrada no HTML.")
    records = []
    current_year = None
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        # ano: linha com apenas um td central e apenas o ano
        if len(tds) == 1:
            txt = tds[0].get_text(strip=True)
            if re.fullmatch(r"\d{4}", txt):
                current_year = int(txt)
                continue
        # linhas de dados (espera-se data-head em cada td)
        row: dict[str, int | str | float | None] = {"ano": current_year}
        row_month: str | int | None = None
        has_datahead = False
        for td in tds:
            dh = td.get("data-head")
            if dh is None:
                continue
            has_datahead = True
            col = map_head_to_col(str(dh))
            text = td.get_text(strip=True)
            if col == "mes":
                row_month = text
            elif col is not None:
                row[col] = parse_numeric(text)
        # somente gravar se tivermos ano e mês (e pelo menos uma coluna)
        if not has_datahead:
            continue
        if row.get("ano") is None:
            # sem ano atual, não sabemos a que ano pertence — pular
            continue
        if row_month is None:
            continue
        month_num = month_to_int(row_month)
        if month_num is None:
            continue
        row["mes"] = month_num
        # garantir todas as colunas de interesse existam (None quando ausente)
        for c in DISPLAY_COLS:
            row.setdefault(c, None)
        records.append(row)
    return records

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", default="data/raw/pesquisaFIPE_IPC.html")
    p.add_argument("--output", "-o", default="data/processed/fipe_ipc_199406.csv")
    p.add_argument("--scale", choices=("none", "percent", "proportion"), default="percent",
                   help="none: keep raw; percent: 100000 -> 100.0 (divide por 1000); proportion: 100000 -> 1.0 (divide por 100000)")
    args = p.parse_args()

    recs = parse_html(args.input)
    if not recs:
        print("Nenhum registro extraído do HTML.", flush=True)
        return
    df = pd.DataFrame(recs)
    # organizar colunas
    cols = ["ano", "mes"] + DISPLAY_COLS
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]
    # aplicar escala
    if args.scale == "percent":
        df[DISPLAY_COLS] = df[DISPLAY_COLS].astype(float) / 1000.0
    elif args.scale == "proportion":
        df[DISPLAY_COLS] = df[DISPLAY_COLS].astype(float) / 100000.0
    # filtrar até junho de 1994 (inclusive)
    df = df.dropna(subset=["ano", "mes"])
    df = df[(df["ano"] > 1994) | ((df["ano"] == 1994) & (df["mes"] >= 6))]
    df = df.sort_values(["ano", "mes"]).reset_index(drop=True)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    df.to_csv(args.output, index=False, float_format="%.6f", encoding="utf-8")
    print(f"Salvo {len(df)} linhas em {args.output}")

if __name__ == "__main__":
    main()