# =============================================================================
# fig_h2_diapo.R — figure H2 du diaporama JIMS 2026 (aucune estimation).
# Statut : EXPLORATOIRE. Reprend la double différence H2 recalculée avec les mentions
# d'effets secondaires VÉRIFIÉES une par une (« chaîne vérifiée » : classifieur r2, puis
# relecture par trois modèles de langage, un tweet compte s'il est confirmé par 2 sur 3).
# Source : jpim_preannouncement_communication/nouveau_classifieur_effets/resultats/h2_chaine.txt
# Variation J+2–J+4 contre J0–J+1 de la proportion de messages qui mentionnent un effet
# secondaire, messages qui nomment l'entreprise moins les autres messages du corpus, en
# points de pourcentage. Intervalle affiché : estimation ± 1,96 erreur-type (indicative).
# =============================================================================
suppressPackageStartupMessages({ library(ggplot2) })
source("C:/Users/Olivier/Documents/GitHub/article_afm/analysis/scripts/theme_these_blanc.R")  # lecture seule
OUT <- "C:/Users/Olivier/Documents/jims2026_communication/slides_jims2026/assets/fig/fig_h2_diapo"

d <- data.frame(
  annonce = factor(c("Pfizer", "Moderna", "AstraZeneca"), levels = rev(c("Pfizer", "Moderna", "AstraZeneca"))),
  est = c(2.12, 0.73, -0.29),
  se  = c(0.39, 0.53, 1.07)
)
# Garde : chiffres de h2_chaine.txt (colonne « chaîne vérifiée »)
stopifnot(identical(d$est, c(2.12, 0.73, -0.29)), identical(d$se, c(0.39, 0.53, 1.07)))
d$lo <- d$est - 1.96 * d$se
d$hi <- d$est + 1.96 * d$se
virg <- function(x) sub("-", "\u2212", formatC(x, format = "f", digits = 2, decimal.mark = ",", flag = "+"), fixed = TRUE)
d$lab <- sub("-", "−", formatC(round(d$est + 1e-9, 1), format = "f", digits = 1, decimal.mark = ",", flag = "+"), fixed = TRUE)
d$col <- ifelse(d$annonce == "Pfizer", "s", "n")   # seul Pfizer se distingue de zéro

# Parts de messages qui mentionnent un effet secondaire, J0–J+1 puis J+2–J+4 (h2_chaine.txt),
# arrondi au dixième, demi supérieur (0,35 → 0,4 ; 2,25 → 2,3)
parts <- data.frame(
  annonce = factor(rep(c("Pfizer", "Moderna", "AstraZeneca"), 2), levels = levels(d$annonce)),
  grp = rep(c(1, 2), each = 3),
  t0 = c(0.80, 0.78, 2.25, 0.83, 0.44, 0.57),
  t1 = c(2.43, 1.57, 2.08, 0.35, 0.50, 0.68))
stopifnot(identical(parts$t1, c(2.43, 1.57, 2.08, 0.35, 0.50, 0.68)))
u <- function(x) formatC(floor(x * 10 + 0.5 + 1e-9) / 10, format = "f", digits = 1, decimal.mark = ",")
parts$lab <- paste0("de ", u(parts$t0), " % à ", u(parts$t1), " %")   # Barlow n'a pas de flèche

p <- ggplot(d, aes(est, annonce)) +
  geom_vline(xintercept = 0, colour = "#1f2328", linewidth = 0.7) +
  geom_errorbar(aes(xmin = lo, xmax = hi, colour = col), width = 0.18, linewidth = 1.1, orientation = "y") +
  geom_point(aes(colour = col), size = 5) +
  geom_text(aes(x = hi, label = lab, colour = col), hjust = -0.25, size = 7, family = "Barlow", fontface = "bold") +
  scale_colour_manual(values = c(s = "#c0392b", n = "#8a96a3"), guide = "none") +
  scale_x_continuous(limits = c(-2.4, 4.0), breaks = -2:3,
                     labels = function(v) sub("-", "−", format(v, trim = TRUE), fixed = TRUE)) +
  labs(x = "Écart, en points (barre : intervalle à 95 %)", y = NULL,
       title = "Hausse propre aux messages qui nomment l'entreprise\n(leur hausse moins celle des autres messages)") +
  (theme_these_blanc(base_size = 22) %+replace%
     theme(plot.title = element_text(family = "Barlow", size = 19, face = "bold", colour = "#5b6672", hjust = 0.5,
                                     margin = margin(b = 8)))) +
  theme(panel.grid.major.y = element_blank(), panel.grid.minor = element_blank(),
        axis.text.y = element_text(family = "Barlow", size = 21, face = "bold", colour = "#1f2328"))

q <- ggplot(parts, aes(grp, annonce, label = lab)) +
  geom_text(size = 6.6, family = "Barlow", colour = "#1f2328") +
  scale_x_continuous(limits = c(0.45, 2.55), breaks = 1:2, position = "top",
                     labels = c("Messages qui nomment
l'entreprise", "Autres messages
du corpus")) +
  labs(title = "Part qui mentionne un effet secondaire
de J0–J+1 à J+2–J+4", x = NULL, y = NULL) +
  theme_void(base_size = 22) +
  theme(axis.text.x.top = element_text(family = "Barlow", size = 18, colour = "#5b6672", lineheight = 0.95,
                                       margin = margin(b = 6)),
        plot.title.position = "plot",
        plot.title = element_text(family = "Barlow", size = 19, face = "bold", colour = "#5b6672", hjust = 0.5,
                                  lineheight = 1.05, margin = margin(b = 8)))

fig <- patchwork::wrap_plots(p, q, widths = c(1.15, 1))
ggsave(paste0(OUT, ".pdf"), fig, width = 34, height = 9.5, units = "cm", device = cairo_pdf, bg = "white", scale = 1.15)
system2("pdftoppm", c("-png", "-r", "260", "-singlefile", shQuote(paste0(OUT, ".pdf")), shQuote(OUT)))
file.remove(paste0(OUT, ".pdf"))
cat("ok fig_h2_diapo\n")
