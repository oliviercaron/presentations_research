# -*- coding: utf-8 -*-
"""
carte_sens_pfizer_tweets.py — textes intégraux, compteurs et coordonnées réelles des tweets cités sur la
diapo de la mesure, plus les candidats de J+2 à J+4 (direction avant → J+4). EXPLORATOIRE (illustration).
Sortie : carte_sens_pfizer_tweets.json (tweets retenus : texte verbatim, compte, j'aime, retweets,
six premières composantes du vecteur, position sur la carte).
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq
sys.stdout.reconfigure(encoding="utf-8")
ICI = Path(__file__).resolve().parent
EMB = Path("C:/Users/Olivier/Documents/GitHub/article_afm/explore/rq3_derive_serielle_2026-07-21/data/embeddings")
CORPUS = Path("C:/Users/Olivier/Documents/GitHub/article_afm/data/processed/coronavirus_tweets_all_final_2026-04-02.parquet")

ids = pd.read_parquet(EMB / "child_ids.parquet"); E = np.load(EMB / "child_emb.npy", mmap_mode="r")
ids["j"] = (pd.to_datetime(ids["day"]) - pd.Timestamp("2020-11-09")).dt.days
w = ids[ids["j"].between(-4, 4)].copy()
X = np.asarray(E[w.index.values], dtype=np.float32); w = w.reset_index(drop=True); w["id"] = w["id"].astype(str)
C = np.vstack([X[w["j"].values == j].mean(0) for j in range(-4, 5)])
mu = C.mean(0); _, _, Vt = np.linalg.svd(C - mu, full_matrices=False); P = Vt[:2]
avant = C[:4].mean(0)

t = pq.read_table(CORPUS, columns=["id", "user_screen_name", "user_name", "user_verified", "user_followers_count",
                                   "favorite_count", "retweet_count", "text", "tweet_type", "parsed_created_at"],
                  filters=[("month", "==", "2020-11")]).to_pandas()
t["id"] = t["id"].astype(str)
for c in ["user_followers_count", "favorite_count", "retweet_count"]:
    t[c] = pd.to_numeric(t[c], errors="coerce").fillna(0).astype(int)
t["user_verified"] = t["user_verified"].astype(str).str.lower().isin(["true", "1"])

# candidats J+2 à J+4 : direction avant -> J+4
d4 = C[8] - avant; d4 /= np.linalg.norm(d4)
w["proj4"] = X @ d4
c4 = w[w["j"].between(2, 4)].nlargest(3000, "proj4").merge(t, on="id")
c4 = c4[(c4.user_verified) | (c4.user_followers_count >= 20000)].sort_values("favorite_count", ascending=False)
print("=== candidats J+2 à J+4 ===")
for r in c4.head(10).itertuples():
    print(f"J{r.j:+d} @{r.user_screen_name} ({r.user_followers_count}, vérifié={r.user_verified}) likes={r.favorite_count} RT={r.retweet_count}\n   {r.text!r}")

RETENUS = sys.argv[1:]   # identifiants de comptes à retenir, dans l'ordre : avant, J+1, (J+2..J+4)
out = []
for sn in RETENUS:
    sn, jj = sn.split(":")
    m = w.merge(t, on="id"); m = m[(m.user_screen_name == sn) & (m.j == int(jj))].sort_values("favorite_count", ascending=False)
    assert len(m), sn
    r = m.iloc[0]; i = int(w.index[w["id"] == r["id"]][0])
    v = X[i]
    xy = (v - mu) @ P.T
    out.append({"compte": sn, "nom": r["user_name"], "verifie": bool(r["user_verified"]), "abonnes": int(r["user_followers_count"]),
                "j": int(r["j"]), "date": str(r["parsed_created_at"]), "type": r["tweet_type_y"], "jaime": int(r["favorite_count"]),
                "retweets": int(r["retweet_count"]), "texte": r["text"], "id": r["id"],
                "vecteur_6": [round(float(x), 3) for x in v[:6]], "x": float(xy[0]), "y": float(xy[1])})
    print(json.dumps(out[-1], ensure_ascii=False, indent=1))
if out:
    json.dump(out, open(ICI / "carte_sens_pfizer_tweets.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
