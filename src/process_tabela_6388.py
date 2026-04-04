#!/usr/bin/env python3
"""
Transforma CSV com janelas 3-meses em série mensal.
Dois modos: 'aggregate' (distribui e média) e 'invert' (inverte média móvel por LS com suavização).
"""
import re
import argparse
import pandas as pd
import numpy as np

MONTH_MAP = {'jan':1,'fev':2,'mar':3,'abr':4,'mai':5,'jun':6,'jul':7,'ago':8,'set':9,'out':10,'nov':11,'dez':12}

def parse_label(label):
    m = re.search(r'(.+)\s+(\d{4})$', label.strip(), re.I)
    if not m:
        raise ValueError(f"Label inválido: {label}")
    months_part, year = m.group(1).lower(), int(m.group(2))
    months = [p.strip() for p in re.split(r'[-–—]', months_part)]
    return months, year

def assign_years(months, year):
    last_num = MONTH_MAP[months[-1][:3]]
    res = []
    for m in months:
        mn = MONTH_MAP[m[:3]]
        y = year - 1 if mn > last_num else year
        res.append((y, mn))
    return res

def build_matrix(start_dates, months_index):
    S = len(start_dates); N = len(months_index)
    A = np.zeros((S, N), dtype=float)
    idx_map = {d:i for i,d in enumerate(months_index)}
    for i,sd in enumerate(start_dates):
        k = idx_map[pd.Timestamp(sd.year, sd.month, 1)]
        A[i, k:k+3] = 1.0/3.0
    return A

def months_range_from_starts(starts):
    start_min = min(starts)
    start_max = max(starts)
    end = start_max + pd.DateOffset(months=2)
    return pd.date_range(start_min, end, freq='MS')

def main(args):
    df = pd.read_csv(args.input, header=0)
    headers = list(df.columns)
    values = df.iloc[0].astype(float).values

    # parse headers -> start dates
    starts = []
    for h in headers:
        months, year = parse_label(h)
        assigned = assign_years(months, year)
        sy, sm = assigned[0]
        starts.append(pd.Timestamp(sy, sm, 1))

    months_index = months_range_from_starts(starts)
    A = build_matrix(starts, months_index)
    b = values

    if args.method == 'aggregate':
        sumarr = np.zeros(len(months_index))
        counts = np.zeros(len(months_index))
        idx_map = {d:i for i,d in enumerate(months_index)}
        for i,sd in enumerate(starts):
            k = idx_map[pd.Timestamp(sd.year, sd.month, 1)]
            v = b[i]
            if np.isnan(v): continue
            sumarr[k:k+3] += v
            counts[k:k+3] += 1
        est = sumarr / np.where(counts==0, np.nan, counts)
    else:  # invert via LS + regularização
        mask = ~np.isnan(b)
        A_sub = A[mask]; b_sub = b[mask]
        N = len(months_index)
        # second-difference penalization
        D = np.zeros((N-2, N))
        for i in range(N-2):
            D[i,i] = 1; D[i,i+1] = -2; D[i,i+2] = 1
        reg = float(args.reg)
        M = A_sub.T @ A_sub + reg * (D.T @ D)
        rhs = A_sub.T @ b_sub
        est = np.linalg.solve(M, rhs)

    s = pd.Series(est, index=months_index)
    s.index = pd.PeriodIndex(s.index, freq='M').to_timestamp()
    df_out = pd.DataFrame({
        'ano': [d.year for d in s.index],
        'mes': [f"{d.month:02d}" for d in s.index],
        'renda_media': s.values
    })
    df_out.to_csv(args.output, index=False)
    # diagnostics
    print(f"Wrote {args.output} | rows={len(df_out)} | method={args.method}")

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--method', choices=['aggregate','invert'], default='invert')
    p.add_argument('--reg', default=1e-2, help='regularização (apenas invert)')
    args = p.parse_args()
    main(args)