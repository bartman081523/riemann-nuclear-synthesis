# KNOWN_GAPS — primequant (first-class Artefakt)

Garantie-Deklaration dieser Paketschicht mit ihren offenen Lücken. Was hier
steht, ist NICHT garantiert — eine Ausrede ist das nicht: jede Lücke benennt
den Grund und das Kriterium, an dem sie geschlossen würde.

## GAP-1 — transzendente Winkel (E-Diagonale) nie exakt
Die nicht-hermitesche Diagonalebene H = diag(E) + i·γ·A hat Eigenwerte/Winkel,
die np.log/np.exp transzendenter Konstanten (E_DIAG, f) enthalten — eine exakte
Wiedergabe über ℚ(ζ_q) existiert dafür nicht. Status: alle Zeitentwicklungen auf
der E-Diagonale bleiben ABGELEITET (float statevector/poly) und tragen Schranken
(z. B. LAPACK-Rest ≤ EXACT_TOL), nie die Klasse EXAKT.
Kriterium zum Schließen: eine symbolische Konstantendarstellung der
Einzelspektrum-Werte plus exakte Schranken-Verifikation darüber.

## GAP-2 — Ring-Performance für große q
cyc_mul skaliert ∝ q² (gemessen 2026-10-06: q=3 1.25 µs, q=5 2.47 µs, q=7 4.20 µs,
q=11 9.31 µs, q=13 10.55 µs pro Mult), DFT/Parseval-Tests sind O(q³)/O(q⁴).
Pilot-q ∈ {2,3,5,7,11} kostet die komplette Anker-Suite < 5 s; q ≈ 100 ist ein
einzelner DFT noch im 10-ms-Bereich, q > 1000 ist ein dokumentierter Knackpunkt
(kein Karatsuba/Kronecker; kein allgemeiner Zahlkörper-CAS im Scope).
Kriterium zum Schließen: messbare Notwendigkeit großer q + implementierte
Schnellmultiplikation mit verifizierter Bit-Idempotenz gegen diese Referenz.

## GAP-3 — sympy ist auf Python 3.14 offiziell nicht validiert
sympy 1.14.0 (Klassifizierer 3.9-3.13, requires_python >= 3.9) dient NUR als
Anker-Oracle im Extra "anchor"; der Kern importiert sympy nie. Fehlt oder krankeht
sympy, skippen die Orakel-Tests MIT Grund — der Kern bleibt von dieser Lücke
unabhängig (2 Prüfpfade: eigener Ring + bestehender q=5-Kernel).
Kriterium zum Schließen: offizielle sympy-3.14-Klassifizierer oder ein
festgestellter, reproduzierbarer 3.14-Fehler mit dokumentierter Umgehung.

## GAP-4 — nur ro ist kalibriert; p1/ratio_2q/t1/t2 sind keine on-disk Daten
Der ISA-Report trägt Op-Counts-Dicts, keine Kalibrier-Raten; die QPU-Roh-Dateien
tragen readout_cal-Counts, sonst keine Raten. Deshalb ist in primequant ONLY
`ro` (aus den committeten readout_cal-Reihen, Herkunft `kalibriert+<fetched_at_utc>`)
kalibriert; Depolarisations-/Relaxations-Parameter liegen als
`geschätzt:Hypothese` vor (z. B. die gefrorenen Stress-Grid-Level), KEINE
implizite "kalibrierte Physik". Kriterium: on-disk Kalibrierquelle (gerät
gelieferte, committete Raten-Datei mit Zeitstempel) -> Umwandlung in
`kalibriert+` über eine eigene Validierungszeile, nie per stiller Code-Änderung.

## GAP-5 — Copy-Paste-Fehler im committeten 055-Prereg
Das gefrorene Prereg trägt `"kind": "composite_q5"` sowohl für die q3- als auch
die q5-Composite-Negative-Control. Der Freeze wird NICHT umgeschrieben; der
exakte Verteilungs-Layer liest `n_d`/`m` direkt statt dem Label zu folgen, was
den Fehler neutralisiert. Als Erinnerung, dass Labels niemals Modelle tragen.

## GAP-6 — float-Schatten der exakten Quote
np.fft / np.exp-Leitungen (ABSOLUT-FFT, float-Faltung) dürfen NIE Quelle sein;
der exakte Wert ist die Quelle und die Float-Leitung nur ABGELEITET-Kreuzprüfung
mit Schranke |Δ| ≤ 2 ULP (gemessen 2026-10-06: 1 ULP 8.88e-16 der ABSOLUT-FFT-
Route, 0.0 bit-identisch gegen die Float-Faltform). Kriterium zum Schließen:
keins nötig — solange float-Tracks nur als Prüfpfad mit Schranke leben.