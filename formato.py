"""Formatação de números no padrão brasileiro (vírgula decimal, ponto de milhar, sinal − tipográfico)."""
from __future__ import annotations

import math


def num(v: float, casas: int = 3) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return '—'
    s = f'{v:,.{casas}f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    return s.replace('-', '−')


def pct(v: float, casas: int = 2) -> str:
    """`v` como fração: 0,6946 -> '69,46%'."""
    return num(v * 100, casas) + '%' if v is not None and not (isinstance(v, float) and math.isnan(v)) else '—'


def pval(p: float) -> str:
    return '< 0,0001' if p < 1e-4 else num(p, 4)


def inteiro(v) -> str:
    return num(float(v), 0)


def data(d) -> str:
    return f'{d:%d/%m/%Y}'
