# ============================================================
#  frise_diapo.R : la frise du bas de la figure du corpus (mesures nationales, annonces des
#  laboratoires et décisions publiques, campagne de vaccination), seule, au format de la diapo 3,
#  avec des polices et des symboles agrandis (2026-10-13).
#  Reprend le dessin de commun.R (tournoi de figures du corpus, thèse) sans le modifier :
#  les tailles de texte sont multipliées par K après chargement.
#  Lancer : Rscript frise_diapo.R   → assets/fig/frise_diapo.png
# ============================================================
# commun.R lit risque_plafonne_quotidien.csv dans fusion_D_MAX, dossier retiré du dépôt de la
# thèse (commit 736ce68) : la copie restaurée depuis git est posée à côté de ce script.
src <- readLines("C:/Users/Olivier/Documents/GitHub/research_papers/thesis/audits/tournoi_figure_corpus_2026-10-02/deux_figures/commun.R",
                 encoding = "UTF-8")
src <- sub("^FUSION <- .*$", 'FUSION <- "C:/Users/Olivier/Documents/jims2026_communication/slides_jims2026/scripts/figures_diapo"', src)
# Le contrôle croisé avec les tableaux du chapitre 4 de la thèse (texte modifié depuis) devient un
# avertissement : il ne touche pas au dessin, les dates viennent d'evenements.json.
src <- sub('garde(length(k) == 1, "ligne absente des tableaux du chapitre 4 : "',
           'if (length(k) != 1) warning("ligne absente des tableaux du chapitre 4 : "', src, fixed = TRUE)
eval(parse(text = src, encoding = "UTF-8"))

K <- as.numeric(Sys.getenv("K", "1.35"))
TXT <- 7.4 * K; TXT_MIN <- 7.0 * K; TITRE <- 8.6 * K; AXE <- 7.2 * K
titre_panneau <- element_text(family = "Barlow", face = "bold", size = TITRE, colour = ENCRE,
                              hjust = 0, margin = margin(b = 4))
LARG <- as.numeric(Sys.getenv("LARG", "11.3")); HAUT <- as.numeric(Sys.getenv("HAUT", "4.9"))
SORTIE <- "C:/Users/Olivier/Documents/jims2026_communication/slides_jims2026/assets/fig/frise_diapo"

K_LEG <- 1.12     # légende des symboles un peu moins agrandie : elle doit tenir avant « Pfizer-BioNTech »
L <- panneau_L()
for (i in seq_along(L$layers)) {
  d <- L$layers[[i]]$data
  if (is.data.frame(d) && "lab" %in% names(d)) {
    lab <- d$lab
    # « Décision publique étudiée » : la diapo ne parle pas encore de décisions étudiées
    lab <- sub("Décision publique étudiée", "Décision publique", lab, fixed = TRUE)
    lab <- sub("Annonce publiée par le laboratoire (efficacité, retard, abandon)",
               "Annonce du laboratoire (efficacité, retard, abandon)", lab, fixed = TRUE)
    # libellé le plus long, raccourci de « puis » pour ne pas sortir à droite
    lab <- sub("suspendu en France, puis réservé aux 55 ans et plus, thromboses reconnues",
               "suspendu en France, réservé aux 55 ans et plus, thromboses reconnues", lab, fixed = TRUE)
    L$layers[[i]]$data$lab <- lab
    # « 29 janv. » d'AstraZeneca calé à gauche du rond, loin de « 15 et 19 mars »
    k <- which(lab == "29 janv." & abs(d$yl - 4.42) < 1e-6)
    if (length(k)) { L$layers[[i]]$data$xl[k] <- X(UE[3]) + 4; L$layers[[i]]$data$hj[k] <- 1 }
    # textes posés sur les barres pâles : un peu plus petits, « 70 % en moyenne » doit finir avant le rond
    if (any(lab == "70 % en moyenne")) L$layers[[i]]$aes_params$size <- pt(7.0 * 1.2)
    # légende des symboles
    if (any(grepl("Premier signal|De l'annonce d'efficacité", lab)))
      L$layers[[i]]$aes_params$size <- pt(7.0 * K_LEG)
  }
  # barres pâles et symboles agrandis comme le texte
  lw <- L$layers[[i]]$aes_params$linewidth
  if (!is.null(lw) && lw > 2) L$layers[[i]]$aes_params$linewidth <- lw * K
  st <- L$layers[[i]]$aes_params$stroke
  if (!is.null(st)) L$layers[[i]]$aes_params$stroke <- st * K
}
L <- suppressMessages(L + scale_size_manual(values = c(labo = 2.0, tiers = 2.0, ue = 2.0, public = 2.0, etape = 1.3, ema = 1.8) * K)) +
  theme(axis.text.x = element_text(family = "Roboto Mono", size = AXE, colour = ENCRE, lineheight = 0.95,
                                   margin = margin(t = 5)),
        plot.margin = margin(3, 4, 2, 0))
S <- panneau_S()
# libellés des bandes (1er confinement…) à peine agrandis : ils doivent tenir dans leur bande
for (i in seq_along(S$layers)) if (!is.null(S$layers[[i]]$aes_params$size))
  S$layers[[i]]$aes_params$size <- pt(7.0 * 1.12)
fig <- S / L + plot_layout(heights = c(0.50, 4.0)) &
  theme(plot.title = titre_panneau)
fig <- fig + plot_annotation(theme = theme(plot.margin = margin(4, 40, 2, 24)))

grDevices::svg(paste0(SORTIE, ".svg"), width = LARG, height = HAUT, bg = "white")   # vectoriel pour la diapo
print(fig); grDevices::dev.off()
ggsave(paste0(SORTIE, ".pdf"), fig, width = LARG, height = HAUT, device = cairo_pdf, bg = "white")
system2("pdftoppm", c("-r", "300", "-png", "-singlefile", shQuote(paste0(SORTIE, ".pdf")), shQuote(SORTIE)))
message("ok : ", SORTIE, ".png")
