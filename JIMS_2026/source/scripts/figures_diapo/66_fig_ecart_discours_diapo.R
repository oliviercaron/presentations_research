# =============================================================================
# fig_ecart_discours.pdf — communication JIMS 2026, revision 2026-10.
# Copie de article_afm/.../scripts/66_figure_deux_horloges_trois_annonceurs.R
# (non modifie). Changements :
#   - rendu a la taille d'insertion (16 cm) avec polices >= 9 pt ;
#   - zone grise legendee (legende en bas) ; etiquette J0 au lieu de J+0 ;
#   - version francaise seule ; sortie vers le dossier de la revision.
# Les annotations « x16 » / « % resorbe » et les cercles etaient deja absents
# de la version source (retires le 2026-08-18) : rien a supprimer ni a garder.
# Les gardes fail-closed du script source sont conservees.
# =============================================================================
suppressPackageStartupMessages({
  library(data.table); library(ggplot2); library(ggtext); library(jsonlite)
})
source("commun_diapo.R")  # version diapo : même figure, canevas réduit, texte relativement plus grand

radial <- fromJSON(file.path(RES, "retour_radial.json"))
spec <- data.table(
  cle = c("pfizer_clean", "moderna", "az"),
  event = c("PFIZER_90PCT", "MODERNA_945", "AZ_OXFORD_70"),
  firme = c("Pfizer/BioNTech\n9 nov. 2020", "Moderna\n16 nov. 2020",
            "AstraZeneca/Oxford\n23 nov. 2020")
)
spec[, r_pic := sapply(cle, function(k) radial[[k]]$R_pic$obs)]
spec[, p_comp := sapply(cle, function(k) radial[[k]]$R_pic$comp_p)]
stopifnot(
  all(abs(spec$r_pic - c(0.4420, 0.1282, 0.5968)) < 0.001),
  all(abs(spec$p_comp - c(0.006, 0.518, 0.002)) < 0.0005)
)
spec[, firme := factor(firme, levels = firme)]

cos <- fread(file.path(RES, "cosinus_series.csv"))
cos <- cos[serie == "base" & window %chin% spec$cle]
d <- merge(cos, spec[, .(window = cle, event, firme)], by = "window", all.x = TRUE)
event_days <- c(pfizer_clean = "2020-11-09", moderna = "2020-11-16", az = "2020-11-23")
d[, `:=`(
  j_rel = as.integer(as.Date(day) - as.Date(event_days[window])),
  value = 1 - obs, null_lo = 1 - comp_hi, null_hi = 1 - comp_lo
)]
setorder(d, firme, j_rel)
stopifnot(
  all(d[, min(j_rel), by = firme]$V1 == -4L),
  all(d[, max(j_rel), by = firme]$V1 == 4L),
  abs(d[event == "PFIZER_90PCT", max(value)] - 0.0107033) < 1e-5,
  abs(d[event == "MODERNA_945", max(value)] - 0.0043389) < 1e-5,
  abs(d[event == "AZ_OXFORD_70", max(value)] - 0.0139813) < 1e-5
)

LAB_ZONE <- "Journées recomposées au hasard (95 %)"
LAB_OBS  <- "Écart observé"

p <- ggplot(d, aes(j_rel, value, group = firme)) +
  geom_vline(xintercept = 0, colour = these_neutral_mid,
             linetype = "42", linewidth = 0.45) +
  geom_ribbon(aes(ymin = null_lo, ymax = null_hi, fill = LAB_ZONE), colour = NA) +
  geom_line(aes(colour = LAB_OBS), linewidth = 0.9) +
  geom_point(aes(colour = LAB_OBS), size = 2.0) +
  scale_fill_manual(NULL, values = setNames("#C7D3DD", LAB_ZONE)) +
  scale_colour_manual(NULL, values = setNames(these_bleu, LAB_OBS)) +
  scale_x_continuous(breaks = seq(-4, 4, by = 2), labels = lab_j,
                     limits = c(-4.45, 4.45), expand = expansion(mult = 0)) +
  scale_y_continuous(
    breaks = c(0, 0.005, 0.010, 0.015), limits = c(0, 0.0165),
    labels = function(x) gsub(".", ",", sprintf("%.3f", x), fixed = TRUE),
    expand = expansion(mult = 0)) +
  facet_wrap(~ firme, nrow = 1) +
  guides(colour = guide_legend(order = 1), fill = guide_legend(order = 2)) +
  labs(x = "Jours avant et après la préannonce",
       y = "Écart au discours d'avant\n(1 − similarité cosinus)") +
  theme_these_blanc(base_size = BASE_PT) +
  theme(
    strip.text.x = element_text(family = "Barlow", face = "bold", hjust = 0.5,
                                lineheight = 1.0, size = rel(0.95)),
    panel.spacing.x = unit(1.4, "lines"),
    panel.grid.major.x = element_blank(),
    legend.position = "bottom",
    legend.text = element_text(size = rel(0.85)),
    legend.key.width = unit(0.9, "cm"),
    legend.spacing.x = unit(0.2, "cm"),
    legend.margin = margin(0, 0, 0, 0),
        legend.key.spacing.x = unit(0.45, "cm"),
    legend.box.spacing = unit(0.15, "cm"),
    plot.margin = margin(4, 8, 2, 4)
  )

save_jims(p + ggplot2::theme(strip.clip = "off", plot.margin = ggplot2::margin(4, 16, 4, 4)), "fig_ecart_discours", h_cm = 7.6)
