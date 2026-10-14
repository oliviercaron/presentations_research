# =============================================================================
# fig_jugement_negatif.pdf — communication JIMS 2026, revision 2026-10.
# Bloc « Figure 1 » (fig1_hostilite_trajectoire) isole de
# article_afm/.../scripts/21_figures.R (non modifie). Changements :
#   - rendu a la taille d'insertion (16 cm), polices >= 9 pt ;
#   - « part » -> « proportion » dans tous les libelles ;
#   - legende en bas : proportion observee, IC de Wilson, serie sans les
#     comptes hyperactifs ; etiquette J0 ; version francaise seule.
# Gardes fail-closed du script source conservees.
# =============================================================================
suppressPackageStartupMessages({
  library(ggplot2); library(ggtext); library(data.table)
})
source("commun_diapo.R")  # version diapo : même figure, canevas réduit, texte relativement plus grand

v <- fread(file.path(RES, "effectifs_firme_jour.csv"))
lab_ev <- c(PFIZER_90PCT = "Pfizer/BioNTech\n9 nov. 2020", MODERNA_945 = "Moderna\n16 nov. 2020",
            AZ_OXFORD_70 = "AstraZeneca/Oxford\n23 nov. 2020")
v <- v[event %in% names(lab_ev)]
v[, ev_lab := factor(lab_ev[event], levels = lab_ev)]

vj <- fread(file.path(RES, "valence_jour.csv"))
chk_j <- merge(v[j_rel >= 0, .(event, j_rel, n_annotes, hostile_pct)],
               vj[, .(event, j_rel, n, hostile_pct_18 = hostile_pct)], by = c("event", "j_rel"))
stopifnot(nrow(chk_j) == 15L,
          all(chk_j$n_annotes == chk_j$n),
          all(abs(chk_j$hostile_pct - chk_j$hostile_pct_18) < 0.06),
          abs(v[event == "PFIZER_90PCT" & j_rel == 2, hostile_pct] - 52.8) < 0.15,
          abs(v[event == "MODERNA_945" & j_rel == 4, hostile_pct] - 60.2) < 0.15)

v20 <- v[n_annotes >= 20]
post <- v20[j_rel >= 0]
pre  <- v20[j_rel < 0]
stopifnot(nrow(post) == 15L, all(pre$event == "AZ_OXFORD_70"))
note_pre <- data.table(ev_lab = factor(lab_ev[c("PFIZER_90PCT", "MODERNA_945")], levels = lab_ev),
                       x = -2.2, y = 50, label = "moins de\n20 textes\npar jour")

sans <- post[event %in% post[n_hyper > 0, unique(event)] & n_annotes_sans >= 20]
stopifnot("MODERNA_945" %in% sans$event,
          abs(sans[event == "MODERNA_945" & j_rel == 3, hostile_pct_sans] - 16.1) < 0.15)

L_OBS  <- "Proportion observée"
L_IC   <- "IC de Wilson à 95 %"
L_SANS <- "Sans comptes hyperactifs"

p1 <- ggplot(post, aes(j_rel, hostile_pct)) +
  geom_vline(xintercept = 0, colour = these_neutral_mid,
             linetype = "42", linewidth = 0.45) +
  geom_ribbon(aes(ymin = ci_lo_pct, ymax = ci_hi_pct, fill = L_IC), colour = NA) +
  geom_linerange(data = pre, aes(x = j_rel, ymin = ci_lo_pct, ymax = ci_hi_pct),
                 inherit.aes = FALSE, colour = "#C7D3DD", linewidth = 2.6) +
  geom_line(data = sans, aes(j_rel, hostile_pct_sans, colour = L_SANS, linetype = L_SANS),
            inherit.aes = FALSE, linewidth = 0.8) +
  geom_point(data = sans, aes(j_rel, hostile_pct_sans, colour = L_SANS, shape = L_SANS),
             inherit.aes = FALSE, size = 1.9, stroke = 0.9) +
  geom_line(aes(colour = L_OBS, linetype = L_OBS), linewidth = 0.9) +
  geom_point(aes(colour = L_OBS, shape = L_OBS), size = 2.0) +
  geom_point(data = pre, aes(j_rel, hostile_pct), inherit.aes = FALSE,
             colour = these_bleu, size = 2.0) +
  geom_text(data = note_pre, aes(x, y, label = label), inherit.aes = FALSE,
            family = "Barlow", colour = these_neutral_mid, size = pt2mm(9.5),
            lineheight = 0.9) +
  scale_colour_manual(NULL, values = setNames(c(these_bleu, these_neutral_mid), c(L_OBS, L_SANS)),
                      breaks = c(L_OBS, L_SANS)) +
  scale_linetype_manual(NULL, values = setNames(c("solid", "22"), c(L_OBS, L_SANS)),
                        breaks = c(L_OBS, L_SANS)) +
  scale_shape_manual(NULL, values = setNames(c(16, 1), c(L_OBS, L_SANS)),
                     breaks = c(L_OBS, L_SANS)) +
  scale_fill_manual(NULL, values = setNames("#C7D3DD", L_IC)) +
  guides(colour = guide_legend(order = 1), linetype = guide_legend(order = 1),
         shape = guide_legend(order = 1), fill = guide_legend(order = 2)) +
  scale_x_continuous(breaks = seq(-4, 4, by = 2), labels = lab_j,
                     limits = c(-4.45, 4.45), expand = expansion(mult = 0)) +
  scale_y_continuous(limits = c(0, 100), breaks = seq(0, 100, 25),
                     labels = function(x) paste0(x, " %"), expand = expansion(mult = 0)) +
  facet_wrap(~ ev_lab, nrow = 1) +
  labs(x = "Jours avant et après la préannonce",
       y = "Proportion d'évaluations négatives\n(entreprise ou produit)") +
  theme_these_blanc(base_size = BASE_PT) +
  theme(strip.text.x = element_text(family = "Barlow", face = "bold", hjust = 0.5,
                                    lineheight = 1.0, size = rel(0.95)),
        panel.spacing.x = unit(1.4, "lines"),
        panel.grid.major.x = element_blank(),
        legend.position = "bottom",
        legend.text = element_text(size = rel(0.85)),
        legend.key.width = unit(0.75, "cm"),
        legend.spacing.x = unit(0.12, "cm"),
        legend.margin = margin(0, 0, 0, 0),
        legend.key.spacing.x = unit(0.45, "cm"),
        legend.box.spacing = unit(0.15, "cm"),
        plot.margin = margin(4, 8, 2, 4))

save_jims(p1 + ggplot2::theme(strip.clip = "off", plot.margin = ggplot2::margin(4, 30, 4, 4), legend.text = ggplot2::element_text(size = ggplot2::rel(0.72)), legend.box.margin = ggplot2::margin(0, 20, 0, 0)), "fig_jugement_negatif", h_cm = 7.8)
