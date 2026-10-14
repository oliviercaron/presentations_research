# =============================================================================
# annexe_par_preannonce.R : régressions intra-auteur de H3a, préannonce par préannonce (annexe du diaporama).
# Statut : EXPLORATOIRE. Même modèle que 04_reestimer_h3a.R et 01_hostilite_fait_vs_hors_fait.R :
#   Y ~ i(j_rel, ref = 0) | user_id^event, erreurs-types groupées par auteur et par journée d'événement.
# Deux issues : le message juge l'entreprise (evaluatif), le message la juge négativement (hostile).
# Effectifs : messages et auteurs du panel H3a par jour et par préannonce.
# Garde : Pfizer, hostile, J+2 = +25,0 (resultats_fait_vs_hors_fait.csv).
# Sorties : annexe_par_preannonce.csv, annexe_effectifs.csv (dans ce dossier).
# =============================================================================
suppressPackageStartupMessages({ library(data.table); library(fixest) })
base <- "C:/Users/Olivier/Documents/GitHub/jpim_preannouncement_communication"
ici <- "C:/Users/Olivier/Documents/jims2026_communication/slides_jims2026/scripts/figures_diapo"
P <- fread(file.path(base, "revalidation_annotations_2026-10/jugement_entreprise/panel_h3a_lignes.csv"),
           colClasses = list(character = c("user_id", "event")))
stopifnot(nrow(P) == 2816)
P[, ev_day := paste0(event, "_J", j_rel)]
res <- list()
for (ev in c("PFIZER_90PCT", "AZ_OXFORD_70", "MODERNA_945")) for (y in c("evaluatif", "hostile")) {
  D <- P[event == ev]
  m <- feols(as.formula(paste(y, "~ i(j_rel, ref = 0) | user_id^event")), D, cluster = ~user_id + ev_day)
  ct <- coeftable(m)
  for (k in 1:4) {
    cn <- paste0("j_rel::", k)
    res[[length(res) + 1]] <- data.table(event = ev, issue = y, jour = k, coef = 100 * ct[cn, 1], se = 100 * ct[cn, 2],
                                         p = ct[cn, 4], niveau_J0 = 100 * D[j_rel == 0, mean(get(y))], nobs = nobs(m))
  }
}
R <- rbindlist(res)
stopifnot(abs(R[event == "PFIZER_90PCT" & issue == "hostile" & jour == 2, coef] - 25.0) < 0.1)
fwrite(R, file.path(ici, "annexe_par_preannonce.csv"))
E <- P[, .(messages = .N, auteurs = uniqueN(user_id)), by = .(event, j_rel)][order(event, j_rel)]
fwrite(E, file.path(ici, "annexe_effectifs.csv"))
print(R[, .(event, issue, jour, coef = round(coef, 1), se = round(se, 1), p = round(p, 3), J0 = round(niveau_J0, 1), nobs)])
print(E)
