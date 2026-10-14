# =============================================================================
# Version DIAPO des figures de la communication JIMS 2026.
# Mêmes scripts, mêmes données et mêmes gardes que revision_2026-10/figures (figures_work/),
# mais le canevas est réduit (facteur K) : texte, points et traits sont donc relativement
# plus gros dans l'image, pour une lecture en salle. Sortie : PNG ~2 000 px de large.
# =============================================================================
ROOT_AFM <- "C:/Users/Olivier/Documents/GitHub/article_afm"
ROOT <- file.path(ROOT_AFM, "explore/rq3_discourse_drift_2026-07-22")
RES <- file.path(ROOT, "results")
OUT <- "C:/Users/Olivier/Documents/jims2026_communication/slides_jims2026/assets/fig"
source(file.path(ROOT_AFM, "analysis/scripts/theme_these_blanc.R"))  # lecture seule

LARGEUR_CM <- 16
BASE_PT <- 12
pt2mm <- function(pt) pt / ggplot2::.pt
lab_j <- function(x) ifelse(x < 0, paste0("J\u2212", abs(x)),
                     ifelse(x == 0, "J0", paste0("J+", x)))

# facteur de réduction du canevas et allongement vertical, par figure
FORMAT_DIAPO <- list(
  fig_ecart_discours   = c(K = 0.88, H = 1.25),
  fig_jugement_negatif = c(K = 0.88, H = 1.25),
  fig_jour_par_jour    = c(K = 0.88, H = 1.25),
  fig_destination      = c(K = 1.00, H = 1.00)
)
save_jims <- function(p, name, h_cm, w_cm = LARGEUR_CM) {
  f <- FORMAT_DIAPO[[name]]; if (is.null(f)) f <- c(K = 0.8, H = 1)
  w <- w_cm * f[["K"]]; h <- h_cm * f[["K"]] * f[["H"]]
  pdf_f <- file.path(tempdir(), paste0(name, "_diapo.pdf"))
  ggplot2::ggsave(pdf_f, p, width = w, height = h, units = "cm", device = grDevices::pdf, bg = "white")
  dpi <- round(2000 / (w / 2.54))
  system2("pdftoppm", c("-png", "-r", dpi, "-singlefile", shQuote(pdf_f),
                        shQuote(file.path(OUT, paste0(name, "_diapo")))))
  message(sprintf("  ok %s_diapo  [%.1f x %.1f cm, %d dpi]", name, w, h, dpi))
}
