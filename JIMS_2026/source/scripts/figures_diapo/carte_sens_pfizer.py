# -*- coding: utf-8 -*-
"""
carte_sens_pfizer.py — données réelles du schéma de la mesure (diapo « Chaque jour devient un point… »).
Statut : EXPLORATOIRE (illustration).

Fenêtre Pfizer/BioNTech, J−4 à J+4 (5 au 13 novembre 2020), citations et réponses de la population H3.2
(embeddings sentence-camembert-base, normalisés, 768 dimensions). Chaque jour = moyenne de ses messages.
Plan : deux premiers axes d'une ACP des neuf moyennes journalières.
Tweets candidats pour les vignettes : messages des quatre jours d'avant les plus typiques de l'avant
(projection la plus négative sur la direction avant → J+1) et messages de J+1 les plus typiques du
déplacement (projection la plus positive), de comptes vérifiés ou suivis par au moins 20 000 personnes.
Sorties : carte_sens_pfizer_jours.csv (jour, x, y, n), carte_sens_pfizer_candidats.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq
sys.stdout.reconfigure(encoding="utf-8")
ICI = Path(__file__).resolve().parent
EMB = Path("C:/Users/Olivier/Documents/GitHub/article_afm/explore/rq3_derive_serielle_2026-07-21/data/embeddings")
CORPUS = Path("C:/Users/Olivier/Documents/GitHub/article_afm/data/processed/coronavirus_tweets_all_final_2026-04-02.parquet")

ids = pd.read_parquet(EMB / "child_ids.parquet")
E = np.load(EMB / "child_emb.npy", mmap_mode="r")
ids["day"] = pd.to_datetime(ids["day"])
J0 = pd.Timestamp("2020-11-09")
ids["j"] = (ids["day"] - J0).dt.days
w = ids[ids["j"].between(-4, 4)].copy()
X = np.asarray(E[w.index.values], dtype=np.float32)
w = w.reset_index(drop=True)
print("valeurs des vecteurs : min", float(X.min()), "max", float(X.max()), "· 95 % entre",
      float(np.quantile(X, 0.025)), "et", float(np.quantile(X, 0.975)))

C = np.vstack([X[w["j"].values == j].mean(0) for j in range(-4, 5)])
mu = C.mean(0); U, S, Vt = np.linalg.svd(C - mu, full_matrices=False)
P = Vt[:2]
var = (S[:2] ** 2).sum() / (S ** 2).sum()
xy = (C - mu) @ P.T
jours = pd.DataFrame({"j": range(-4, 5), "x": xy[:, 0], "y": xy[:, 1],
                      "n": [int((w["j"] == j).sum()) for j in range(-4, 5)]})
jours.to_csv(ICI / "carte_sens_pfizer_jours.csv", index=False)
print(jours.round(4).to_string(index=False)); print(f"part de variance des deux axes : {100*var:.1f} %")

avant = C[:4].mean(0); d = C[5] - avant; d /= np.linalg.norm(d)
w["proj"] = X @ d
cand = pd.concat([w[w["j"] < 0].nsmallest(3000, "proj").assign(groupe="avant"),
                  w[w["j"] == 1].nlargest(3000, "proj").assign(groupe="J+1")])
t = pq.read_table(CORPUS, columns=["id", "user_screen_name", "user_name", "user_verified", "user_followers_count",
                                   "favorite_count", "retweet_count", "text", "tweet_url"],
                  filters=[("month", "==", "2020-11")]).to_pandas()
t["id"] = t["id"].astype(str); cand["id"] = cand["id"].astype(str)
cand = cand.merge(t, on="id", how="left")
for c in ["user_followers_count", "favorite_count", "retweet_count"]:
    cand[c] = pd.to_numeric(cand[c], errors="coerce").fillna(0).astype(int)
cand["user_verified"] = cand["user_verified"].astype(str).str.lower().isin(["true", "1"])
cand = cand[(cand["user_verified"] == True) | (cand["user_followers_count"] >= 20000)]
cand = cand.sort_values(["groupe", "favorite_count"], ascending=[True, False])
cols = ["groupe", "j", "proj", "user_screen_name", "user_name", "user_verified", "user_followers_count",
        "favorite_count", "retweet_count", "tweet_type", "text", "tweet_url"]
cand[cols].to_csv(ICI / "carte_sens_pfizer_candidats.csv", index=False, encoding="utf-8")
for g in ["avant", "J+1"]:
    print(f"\n=== {g} : {int((cand.groupe == g).sum())} candidats ===")
    for r in cand[cand.groupe == g].head(12).itertuples():
        print(f"J{r.j:+d} @{r.user_screen_name} ({r.user_followers_count} abonnés, vérifié={r.user_verified}) "
              f"likes={r.favorite_count} RT={r.retweet_count} proj={r.proj:.3f}\n   {r.text[:260]!r}")
