# =============================================================================
# fig_jour_par_jour.pdf — communication JIMS 2026, revision 2026-10 (NOUVELLE).
# Etude d'evenement jour par jour, intra-auteur (H3) : ecart a J0, en points
# de pourcentage, pour deux issues (evaluer / juger negativement l'entreprise)
# et deux familles d'evenements. Points + IC 95 % (coef +/- quantile t à G - 1 ddl x se, cohérent avec les p).
# Entree : ../jour_par_jour_h3.csv (famille, issue, j, coef, se, p) ;
#          J0 = reference fixee a 0 (se = 0).
# =============================================================================
suppressPackageStartupMessages({ library(ggplot2); library(ggtext); library(data.table) })
source("commun_diapo.R")  # version diapo : même figure, canevas réduit, texte relativement plus grand

d <- fread("jour_par_jour_h3.csv")
stopifnot(setequal(unique(d$famille), c("preannonces", "institutionnels")),
          setequal(unique(d$issue), c("evaluer", "negatif")),
          all(d[j == 0, coef] == 0), all(d[j == 0, se] == 0),
          d[famille == "preannonces", min(j)] == 0,
          d[famille == "institutionnels", min(j)] == -4)

L_PRE <- "Préannonces d'efficacité (3)"
L_INS <- "Événements institutionnels (5)"
d[, serie := factor(fifelse(famille == "preannonces", L_PRE, L_INS), levels = c(L_PRE, L_INS))]
d[, panneau := factor(fifelse(issue == "evaluer", "Le message juge
l'entreprise",
                              "Le message la juge
négativement"),
                      levels = c("Le message juge
l'entreprise", "Le message la juge
négativement"))]
# IC 95 % cohérents avec les p rapportés : ceux-ci viennent d'un t de Student à
# G - 1 degrés de liberté (erreurs-types groupées). On retrouve ces ddl à partir de
# (coef, se, p), puis on prend le quantile t correspondant au lieu de 1,96.
ddl_impl <- function(t, p) {
  if (is.na(p) || !is.finite(t) || t == 0) return(NA_real_)
  uniroot(function(v) 2 * pt(-abs(t), v) - p, c(1, 1e5))$root
}
d[, ddl := round(median(mapply(ddl_impl, coef / se, p), na.rm = TRUE)), by = famille]
stopifnot(d[famille == "preannonces", unique(ddl)] == 14, d[famille == "institutionnels", unique(ddl)] == 44)
d[, `:=`(lo = coef - qt(0.975, ddl) * se, hi = coef + qt(0.975, ddl) * se)]
# leger decalage horizontal pour que les deux series ne se masquent pas
d[, x := j + fifelse(serie == L_PRE, 0.12, -0.12)]
d[j == 0, x := 0]

cols <- setNames(c(these_bleu, these_neutral_mid), c(L_PRE, L_INS))
shp  <- setNames(c(16, 15), c(L_PRE, L_INS))

p <- ggplot(d, aes(x, coef, colour = serie, shape = serie)) +
  geom_vline(xintercept = 0, colour = these_neutral_light, linewidth = 0.4) +
  geom_hline(yintercept = 0, colour = these_neutral_dark, linewidth = 0.45) +
  geom_line(linewidth = 0.75) +
  geom_linerange(aes(ymin = lo, ymax = hi), linewidth = 0.7, show.legend = FALSE) +
  geom_point(size = 2.1) +
  scale_colour_manual(NULL, values = cols) +
  scale_shape_manual(NULL, values = shp) +
  scale_x_continuous(breaks = -4:4, labels = lab_j, limits = c(-4.4, 4.4),
                     expand = expansion(mult = 0)) +
  scale_y_continuous(breaks = seq(-10, 30, 10),
                     labels = function(x) gsub("-", "−", x),
                     expand = expansion(mult = c(0.04, 0.07))) +
  facet_wrap(~ panneau, nrow = 1) +
  labs(x = NULL,
       y = "Écart au jour de l'annonce,\nchez les mêmes auteurs (points)") +
  theme_these_blanc(base_size = BASE_PT) +
  theme(strip.text.x = element_text(family = "Barlow", face = "bold", hjust = 0.5,
                                    size = rel(0.95)),
        panel.spacing.x = unit(1.4, "lines"),
        panel.grid.major.x = element_blank(),
        legend.position = "bottom",
        legend.text = element_text(size = rel(0.85)),
        legend.key.width = unit(0.8, "cm"),
        legend.spacing.x = unit(0.15, "cm"),
        legend.margin = margin(0, 0, 0, 0),
        legend.key.spacing.x = unit(0.45, "cm"),
        legend.box.spacing = unit(0.1, "cm"),
        plot.margin = margin(4, 8, 2, 4))

save_jims(p, "fig_jour_par_jour", h_cm = 7.5)
