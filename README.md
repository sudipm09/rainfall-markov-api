# Rainfall Markov Chain Comparison API

**Synthetic example, not observed meteorological data.** Two 30-day sequences for January and July (days 1–30, 2026). `1` = rainy, `0` = dry. July was simulated from P(rain | dry)=0.68, P(rain | rain)=0.83; January from 0.16 and 0.40. Generator seed = 20260701.

## Statistical test

Fit separate binary, first-order, time-homogeneous Markov chains. For each previous state (dry or rain), compare the two months' next-state transition proportions with a 2x2 Pearson chi-square statistic, then sum across strata. Nominal asymptotic degrees of freedom = 2. Small or zero counts reduce validity of the chi-square approximation, so primary inference uses a parametric Monte Carlo null simulation: generate two sequences of the same lengths and initial states using the pooled transition probabilities, recompute the statistic, and estimate the p-value. At alpha=0.05, reject equal transition probabilities if simulated p<0.05. This assesses **first-order temporal transition behavior**, not just the rainy-day totals.

## Local quick start

```bash
python -m pip install -r requirements.txt
python -m pip install pytest httpx
python generate_data.py
pytest -q
uvicorn app:app --reload --port 8000
```

In a second terminal:

```bash
curl -X POST http://127.0.0.1:8000/compare \
  -H 'Content-Type: application/json' \
  --data @data/fastapi_input.json
```

Interactive Swagger API docs: `http://127.0.0.1:8000/docs`.

## Docker

```bash
docker build -t rainfall-markov-api .
docker run --rm -p 8000:8000 rainfall-markov-api
```

## Deploy on Render (requires your GitHub and Render access)

1. Create a GitHub repository and push this directory (`git init; git add .; git commit -m 'Rainfall Markov API'; git branch -M main; git remote add origin <repo_url>; git push -u origin main`).
2. In Render, choose **New → Blueprint**, connect the GitHub repository, and deploy `render.yaml`. Alternatively create a **Web Service** with runtime **Docker**, pointed to the repository.
3. Once Render reports healthy, open `https://YOUR-SERVICE.onrender.com/docs`.
4. Run the same request against `https://YOUR-SERVICE.onrender.com/compare` using `data/fastapi_input.json`.

The service has no external database or persistent storage. It accepts datasets in each POST request. Render free-plan availability and limits can change; check Render's current options.

## Important caveats

This is a demonstration with only 30 days per month and deliberately different synthetic weather regimes. Do not interpret p-values as evidence about real January/July climate. July and January are months of 31 days; this exercise intentionally uses only days 1–30. Null-based Monte Carlo is an approximation for short sequences; the result depends on the simulated data-generating assumptions. Real observed data can replace the JSON lists without changing the API.
