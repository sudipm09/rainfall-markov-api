"""Compare two binary rainfall sequences with first-order Markov chains."""
from typing import Literal
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from scipy.stats import chi2

app = FastAPI(title="Rainfall Markov Comparison API", version="1.0.0")

class RainfallInput(BaseModel):
    july: list[Literal[0, 1]] = Field(min_length=2)
    january: list[Literal[0, 1]] = Field(min_length=2)
    bootstrap_iterations: int = Field(default=5000, ge=100, le=20000)
    random_seed: int = 2026

def counts(sequence):
    a = np.asarray(sequence, dtype=np.int8)
    mat = np.zeros((2, 2), dtype=np.int64)
    np.add.at(mat, (a[:-1], a[1:]), 1)
    return mat

def stat(j, n):
    """Pearson homogeneity statistic, stratified by previous state."""
    out = 0.0
    for prev in (0, 1):
        observed = np.vstack([j[prev], n[prev]]).astype(float)
        totals_rows = observed.sum(axis=1, keepdims=True)
        totals_cols = observed.sum(axis=0, keepdims=True)
        grand = observed.sum()
        if grand == 0:
            continue
        expected = totals_rows @ totals_cols / grand
        valid = expected > 0
        out += float(np.sum((observed[valid] - expected[valid])**2 / expected[valid]))
    return out

def matrix_info(m):
    probs = []
    for row in m:
        count = int(row.sum())
        probs.append([round(float(v/count), 6) if count else None for v in row])
    return {"transition_counts": m.tolist(), "transition_probabilities": probs}

def simulate(start, probabilities, length, rng):
    seq = np.zeros(length, dtype=np.int8)
    seq[0] = start
    for i in range(1, length):
        seq[i] = rng.random() < probabilities[seq[i-1]]
    return seq

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/compare")
def compare(payload: RainfallInput):
    july, jan = counts(payload.july), counts(payload.january)
    observed = stat(july, jan)
    pooled = july + jan
    pooled_p_rain = np.divide(pooled[:, 1], pooled.sum(axis=1),
                              out=np.full(2, 0.5), where=pooled.sum(axis=1)>0)
    rng = np.random.default_rng(payload.random_seed)
    at_least = 0
    for _ in range(payload.bootstrap_iterations):
        j_sim = counts(simulate(payload.july[0], pooled_p_rain, len(payload.july), rng))
        n_sim = counts(simulate(payload.january[0], pooled_p_rain, len(payload.january), rng))
        at_least += stat(j_sim, n_sim) >= observed - 1e-12
    p_mc = (at_least + 1) / (payload.bootstrap_iterations + 1)
    p_asymptotic = float(chi2.sf(observed, 2))
    return {
        "hypothesis_null": "July and January share the same first-order transition probabilities",
        "july": {"days": len(payload.july), "rainy_days": sum(payload.july), **matrix_info(july)},
        "january": {"days": len(payload.january), "rainy_days": sum(payload.january), **matrix_info(jan)},
        "state_order": ["dry (0)", "rain (1)"],
        "chi_square_statistic": round(observed, 6),
        "degrees_of_freedom_nominal": 2,
        "asymptotic_p_value": round(p_asymptotic, 6),
        "simulation_p_value": round(p_mc, 6),
        "bootstrap_iterations": payload.bootstrap_iterations,
        "random_seed": payload.random_seed,
        "different_at_alpha_0_05": p_mc < 0.05,
        "method": "Two row-stratified Pearson chi-square comparisons; parametric Monte Carlo null simulation from the pooled first-order Markov chain with fixed initial states."
    }
