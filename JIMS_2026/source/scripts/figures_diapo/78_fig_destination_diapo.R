# =============================================================================
# fig_destination.pdf — communication JIMS 2026, revision 2026-10.
# Copie de article_afm/.../scripts/78_figure_destination_commune.R (non
# modifie). Memes donnees, memes gardes, meme plan commun, meme facteur
# d'echelle unique. Changements de mise en page pour la lisibilite a 16 cm :
#   - rendu a la taille d'insertion, polices >= 9 pt (noms de themes du cadran,
#     etiquettes J-4..J+4, frise) ;
#   - la frise horizontale (9 tuiles de 0,6 cm, texte a ~5 pt une fois reduite)
#     devient une colonne verticale sous chaque cadran : une ligne par jour,
#     nom du theme dominant en entier sur une ligne ;
#   - « Plan commun : x % de la variance » sur deux lignes ;
#   - version francaise seule ; sortie vers le dossier de la revision.
# =============================================================================
suppressPackageStartupMessages({
  library(ggplot2); library(ggtext); library(data.table); library(patchwork)
  library(ggrepel); library(jsonlite)
})
source("commun_diapo.R")  # version diapo : même figure, canevas réduit, texte relativement plus grand
sysfonts::font_add_google("Barlow Semi Condensed", family = "Barlow SC")

A_all <- fread(file.path(RES, "ancres_communes.csv"))
T <- fread(file.path(RES, "trajectoire_commune.csv"))
dest <- fromJSON(file.path(RES, "destination_pas_commune.json"))
T[, day := as.Date(day)]
setorder(T, day)

EVENTS <- data.table(
  event = c("Pfizer/BioNTech", "Moderna", "AstraZeneca"),
  j0 = as.Date(c("2020-11-09", "2020-11-16", "2020-11-23"))
)

# Gardes fail-closed du script source
A <- A_all[lisible == TRUE]
stopifnot(
  abs(dest$var2 - 0.3820) < 0.005,
  nrow(A) == 6,
  dest$events$`Pfizer/BioNTech`$vers == 2,
  dest$events$Moderna$vers == 13,
  dest$events$AstraZeneca$vers == 13,
  abs(dest$events$`Pfizer/BioNTech`$cos_vers - 0.58) < 0.005,
  abs(dest$events$Moderna$cos_vers - 0.40) < 0.005,
  abs(dest$events$AstraZeneca$cos_vers - 0.58) < 0.005,
  nrow(T) == 23L
)

jours <- rbindlist(lapply(seq_len(nrow(EVENTS)), function(i) {
  ev <- EVENTS$event[i]; j0 <- EVENTS$j0[i]
  tt <- T[day >= j0 - 4 & day <= j0 + 4]
  tt[, `:=`(event = ev, j_rel = as.integer(day - j0))]
  tt
}))
jours[, event := factor(event, levels = EVENTS$event)]
stopifnot(all(jours[, .N, by = event]$N == 9L))
jours[, capte := sum(x^2 + y^2) / sum(ecart^2), by = event]

# UN SEUL facteur d'echelle pour les trois panneaux (inchange)
sc <- 0.78 / max(sqrt(jours$x^2 + jours$y^2))
jours[, `:=`(px = x * sc, py = y * sc)]
# retouche coordinateur : seuls J-4, J0, J+1, J+4 sont etiquetes, les autres
# points restent traces sans texte
jours[, lab := fifelse(j_rel %in% c(-4L, 0L, 1L, 4L), lab_j(j_rel), "")]

VACCIN <- c(2L, 9L)
CADRE <- 13L
A[, type := fifelse(topic %in% VACCIN, "vaccin", fifelse(topic == CADRE, "cadre", "autre"))]
A[, theta := atan2(y, x)]
A[, court_ring := c("obligation vaccinale" = "obligation\nvaccinale",
                    "vaccination" = "vaccination", "Noël" = "Noël",
                    "complotisme" = "complotisme", "effroi" = "effroi",
                    "défiance politique" = "défiance\npolitique")[nom]]
stopifnot(!anyNA(A$court_ring))
# vaccination (9) et obligation vaccinale (2) pointent presque au meme endroit :
# graduations exactes, seules les etiquettes s'ecartent angulairement
A[, theta_lab := theta]
A[topic == 9L, theta_lab := theta - 22 * pi / 180]
A[topic == 2L, theta_lab := theta + 22 * pi / 180]
# les etiquettes de bord s'intercalent en hauteur avec celles du cadran voisin
# (Noel un peu plus bas, defiance un peu plus haut, complotisme un peu plus bas)
A[topic == 13L, theta_lab := 15 * pi / 180]
A[topic == 11L, theta_lab := 147 * pi / 180]
A[topic == 15L, theta_lab := 203 * pi / 180]
A[, `:=`(lx = 1.10 * cos(theta_lab), ly = 1.10 * sin(theta_lab))]
A[, hj := fifelse(cos(theta_lab) > 0.25, 0, fifelse(cos(theta_lab) < -0.25, 1, 0.5))]
A[, vj := fifelse(sin(theta_lab) > 0.45, 0, fifelse(sin(theta_lab) < -0.45, 1, 0.5))]
# effroi : centre au-dessus de sa graduation, pour laisser la place a « defiance politique »
A[topic == 4L, `:=`(theta_lab = 112 * pi / 180, hj = 0.5, vj = 0)]
A[topic == 4L, `:=`(lx = 1.08 * cos(theta_lab), ly = 1.08 * sin(theta_lab))]

noms <- A_all[, .(topic_dom = topic, nom)]
dom <- merge(jours[, .(event, j_rel, topic_dom, cos_dom)], noms, by = "topic_dom", all.x = TRUE)
stopifnot(dom[is.na(nom), .N] == 0)
dom[, type := fifelse(topic_dom %in% VACCIN, "vaccin", fifelse(topic_dom == CADRE, "cadre", "autre"))]
setorder(dom, event, j_rel)

cols <- c(vaccin = these_bleu, cadre = these_neutral_dark, autre = these_neutral_mid)
FMT_PCT <- function(v) gsub(".", ",", sprintf("%.1f", v), fixed = TRUE)

PT_RING  <- 9.5  # noms des themes du cadran
PT_J     <- 9    # etiquettes J-4..J+4
PT_FRISE <- 9.5  # noms des themes de la frise
XL <- c(-1.55, 1.55)  # fenetre du cadran (unites : rayon de l'anneau = 1) ;
YL <- c(-2.00, 1.22)  # les etiquettes de bord debordent dans l'intervalle voisin

# geometrie exacte en cm : trois panneaux jointifs sur 16 cm, echelle 1:1
MARGE_G_CM <- 1.0   # debord des etiquettes gauches du premier cadran
MARGE_D_CM <- 0.15
PANEL_CM <- (LARGEUR_CM - MARGE_G_CM - MARGE_D_CM) / 3
U_CM <- PANEL_CM / diff(XL)             # 1 unite (rayon de l'anneau) en cm
CAD_H <- diff(YL) * U_CM                # hauteur du panneau cadran
STRIP_H <- 0.62
FRISE_H <- 9 * 0.56
message(sprintf("  rayon de l'anneau : %.2f cm", U_CM))

plan_lab <- jours[, .(capte = capte[1]), by = event]
plan_lab[, label := ""]   # retiré du diaporama (2026-10-14), la part de variance reste dans les notes
seg <- jours[order(event, j_rel), .(x0 = head(px, -1), y0 = head(py, -1),
                                    x1 = tail(px, -1), y1 = tail(py, -1),
                                    arrivee = tail(j_rel, -1)), by = event]
seg[, phase := fifelse(arrivee <= 0, "avant", "apres")]
ring <- data.table(x = cos(seq(0, 2 * pi, length.out = 240)), y = sin(seq(0, 2 * pi, length.out = 240)))

theme_vide <- theme_these_blanc(base_size = BASE_PT) +
  theme(axis.text = element_blank(), axis.ticks = element_blank(),
        axis.title = element_blank(), panel.grid = element_blank(),
        panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.spacing.x = unit(0, "cm"),
        strip.text.x = element_text(family = "Barlow", face = "bold", size = 11.5,
                                    hjust = 0.5, colour = these_neutral_dark,
                                    margin = margin(b = 2)),
        plot.margin = margin(0, 0, 0, 0))

p_cad <- ggplot() +
  geom_path(data = ring, aes(x, y), colour = these_grid, linewidth = 0.5) +
  geom_segment(data = A, aes(x = 0, y = 0, xend = 0.985 * cos(theta), yend = 0.985 * sin(theta),
                             colour = type), linewidth = 0.3, linetype = "22", alpha = 0.5) +
  geom_segment(data = A, aes(x = 0.95 * cos(theta), y = 0.95 * sin(theta),
                             xend = 1.05 * cos(theta), yend = 1.05 * sin(theta), colour = type),
               linewidth = 1.0) +
  geom_text(data = A, aes(lx, ly, label = court_ring, hjust = hj, vjust = vj, colour = type),
            family = "Barlow SC", fontface = "bold", size = pt2mm(PT_RING), lineheight = 0.85) +
  geom_segment(data = seg[phase == "avant"], aes(x0, y0, xend = x1, yend = y1),
               colour = these_neutral_light, linewidth = 0.9, lineend = "round") +
  geom_segment(data = seg[phase == "apres"], aes(x0, y0, xend = x1, yend = y1),
               colour = these_neutral_dark, linewidth = 1.0, lineend = "round",
               arrow = arrow(length = unit(0.13, "cm"), type = "closed")) +
  geom_point(data = jours, aes(px, py), fill = "white", colour = these_neutral_dark,
             shape = 21, size = 2.6, stroke = 0.8) +
  geom_label_repel(data = jours, aes(px, py, label = lab), family = "Roboto Mono",
                  colour = these_neutral_dark, size = pt2mm(PT_J), seed = 42,
                  fill = scales::alpha("white", 0.85), label.size = NA,
                  label.padding = unit(0.04, "cm"), label.r = unit(0, "cm"),
                  box.padding = 0.30, point.padding = 0.25, force = 6, force_pull = 0.3,
                  max.iter = 50000, max.time = 5,
                  min.segment.length = 0.1,
                  segment.colour = these_neutral_mid, segment.size = 0.3,
                  max.overlaps = Inf, xlim = c(-0.98, 0.98), ylim = c(-0.98, 0.98)) +
  geom_text(data = plan_lab, aes(x = -0.1, y = -1.74, label = label), lineheight = 0.9,
            family = "Barlow", colour = these_neutral_mid, size = pt2mm(9)) +
  scale_colour_manual(values = cols, guide = "none") +
  facet_wrap(~ event, nrow = 1) +
  coord_fixed(xlim = XL, ylim = YL, expand = FALSE, clip = "off") +
  theme_vide

# FRISE verticale : une ligne par jour, theme dominant (768D), nom entier
dd <- copy(dom)
dd[, lab := lab_j(j_rel)]
fills <- c(vaccin = these_bleu, cadre = these_neutral_mid, autre = "#EDF0F3")
# texte blanc seulement sur tuile foncee (opacite >= 0,8), sinon texte sombre
data.table::fwrite(dd[, .(event, j_rel, nom, type, cos_dom)], "destination_frise.csv")  # tableau HTML de la diapo 13
dd[, txt_col := fifelse(type != "autre" & cos_dom >= 0.48, "blanc", "sombre")]
p_frise <- ggplot(dd, aes(y = -j_rel)) +
  geom_tile(aes(x = 0.6, fill = type, alpha = pmin(cos_dom / 0.6, 1)),
            width = 0.76, height = 0.88, colour = NA) +
  geom_text(aes(x = 0.6, label = nom, colour = txt_col), family = "Barlow",
            fontface = "bold", size = pt2mm(PT_FRISE)) +
  geom_text(aes(x = 0.19, label = lab), family = "Roboto Mono", hjust = 1,
            colour = these_neutral_dark, size = pt2mm(PT_J)) +
  annotate("segment", x = 0.03, xend = 0.98, y = 0.5, yend = 0.5,
           colour = these_neutral_dark, linetype = "42", linewidth = 0.45) +
  scale_fill_manual(values = fills, guide = "none") +
  scale_colour_manual(values = c(blanc = "white", sombre = these_neutral_dark), guide = "none") +
  scale_alpha_identity() +
  scale_x_continuous(limits = c(0, 1), expand = expansion(mult = 0)) +
  scale_y_continuous(limits = c(-4.5, 4.5), expand = expansion(mult = 0)) +
  facet_wrap(~ event, nrow = 1) +
  theme_vide + theme(strip.text.x = element_blank(), plot.margin = margin(3, 0, 0, 0))

p <- (p_cad / p_frise) +
  plot_layout(heights = unit(c(CAD_H, FRISE_H), "cm")) &
  theme(plot.background = element_rect(fill = "white", colour = NA))
p <- p + plot_annotation(theme = theme(plot.margin = margin(4, MARGE_D_CM, 4, MARGE_G_CM, unit = "cm")))

save_jims(p, "fig_destination", h_cm = CAD_H + STRIP_H + FRISE_H + 0.45)
