# ============================================================
#  corpus_diapo.R : panneau du volume quotidien de la figure du corpus (tweets par type, encart des
#  trois préannonces, étiquettes des pics), seul et plus haut, en SVG pour la diapo du corpus (2026-10-13).
#  Reprend figure_volume.R et commun.R (tournoi de figures du corpus, thèse) sans les modifier :
#  le texte des deux scripts est lu puis adapté en mémoire (sans frise du bas, hauteur de la diapo).
#  Lancer : Rscript corpus_diapo.R   → assets/fig/corpus_diapo.svg
# ============================================================
DIR <- "C:/Users/Olivier/Documents/GitHub/research_papers/thesis/audits/tournoi_figure_corpus_2026-10-02/deux_figures"
ICI_DIAPO <- "C:/Users/Olivier/Documents/jims2026_communication/slides_jims2026/scripts/figures_diapo"
src <- readLines(file.path(DIR, "commun.R"), encoding = "UTF-8")
src <- sub("^FUSION <- .*$", sprintf('FUSION <- "%s"', ICI_DIAPO), src)   # copie restaurée de fusion_D_MAX
src <- sub('garde(length(k) == 1, "ligne absente des tableaux du chapitre 4 : "',
           'if (length(k) != 1) warning("ligne absente des tableaux du chapitre 4 : "', src, fixed = TRUE)
# étiquettes des pics : pics_consolides.csv, retiré lui aussi (commit 736ce68), copie restaurée ici
src <- sub('file.path(TOURNOI, "analyse_pics/pics_consolides.csv")', sprintf('"%s/pics_consolides.csv"', ICI_DIAPO), src, fixed = TRUE)
Sys.setenv(FIG_LARG = Sys.getenv("LARG", "11.3"), FIG_HAUT = Sys.getenv("HAUT", "5.5"))
eval(parse(text = src, encoding = "UTF-8"))

fv <- readLines(file.path(DIR, "figure_volume.R"), encoding = "UTF-8")
fv <- fv[!grepl("^source\\(", fv)]
# panneau du volume seul : pas de bande des mesures ni de frise des vaccins (elles sont sur la diapo 2)
i <- grep("^assemble <- function", fv)
fv[i] <- "assemble <- function(pl = NULL, pan = NULL) (panneau_A(pl, pan) + inset_element(encart_zoom(\"volume\"), left = ENC[[\"gauche\"]], right = ENC[[\"droite\"]], bottom = ENC[[\"bas\"]], top = ENC[[\"haut\"]], align_to = \"panel\")) + plot_annotation(theme = theme(plot.margin = margin(4, 4, 2, 26)))"
fv[i + 1:5] <- ""   # ancien corps de assemble()
fv <- sub('garde(pan[["w"]] > 8 && pan[["h"]] > 2.5', 'garde(pan[["w"]] > 8 && pan[["h"]] > 3', fv, fixed = TRUE)
fv[grepl('prolonger_pointilles(PAN)', fv, fixed = TRUE)] <- ''   # pointillés des mois : servent seulement à la frise
fv <- sub('^sortie\\(assemble\\(pl, pan\\), "figure_volume"\\)', 'FIG_FINALE <- assemble(pl, pan)', fv)
eval(parse(text = fv, encoding = "UTF-8"))

OUT <- "C:/Users/Olivier/Documents/jims2026_communication/slides_jims2026/assets/fig/corpus_diapo"
grDevices::svg(paste0(OUT, ".svg"), width = LARG, height = HAUT, bg = "white")
print(FIG_FINALE); grDevices::dev.off()
ggsave(paste0(OUT, ".pdf"), FIG_FINALE, width = LARG, height = HAUT, device = cairo_pdf, bg = "white")
system2("pdftoppm", c("-r", "110", "-png", "-singlefile", shQuote(paste0(OUT, ".pdf")), shQuote(paste0(OUT, "_apercu"))))
message("ok : ", OUT, ".svg")
