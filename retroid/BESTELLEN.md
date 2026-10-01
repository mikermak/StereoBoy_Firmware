# StereoBoy bestellen – checklist

Gemaakt op 1-10-2026 met KiCad 10.0.6 uit het printbestand van iamericmin (commit a4c152c).


## 0. Kleurversie (rood/zwart zoals de foto's) – gekozen route

- Upload **`hoofdprint/gerbers_hoofdprint_KLEUR.zip`**. Dat zijn de KiCad-gerbers met nulpunt linksonder, plus de 4 `Fabrication_Colorful*`-bestanden uit EasyEDA Pro (project "StereoBoy kleur").
- Instellingen: 4 lagen, 1,0 mm, **White**, **ENIG 1U**, via 0,2 mm, en onder *Advanced Options* → Silkscreen Technology → **EasyEDA multi-color silkscreen**.
- **Confirm Production File: Yes** en **Confirm Parts Placement: Yes**, allebei met "Do not confirm automatically". JLC maakt pas iets nadat jij hun preview (met de kleur) hebt goedgekeurd.
- De afbeeldingen staan in `kleur/` (1200 dpi, exact de printmaat). Controleer in de preview van JLC of de rode lijnen over de banen vallen. Is de kleur weg of verschoven, gebruik dan route 1: het chatbericht aan JLC-support.
- Gebruik de eerdere upload van de zwarte variant niet meer (het eerste JLC-tabblad). De BOM en CPL hieronder blijven hetzelfde; de CPL is al omgerekend naar het nieuwe nulpunt.

## 1. Hoofdprint bij JLCPCB (print + montage)

Upload `hoofdprint/gerbers_hoofdprint.zip` op jlcpcb.com en zet:

| Optie | Waarde |
|---|---|
| Layers | 4 |
| Afmeting | 69,7 × 116,7 mm (vult JLC zelf in) |
| PCB Qty | 5 |
| PCB Thickness | **1.0 mm** (moet, anders past hij niet in de shell) |
| Kleur | zwart (zoals het origineel) of groen (scheelt $8) |
| Surface Finish | ENIG |
| Min via hole size | **0.2mm/(0.3/0.35mm)** (het ontwerp gebruikt vias van 0,2 mm) |
| Copper | buiten 1 oz, binnen 0,5 oz |

Let op: linksonder zit het **PSU-moduletje** vast via breeklipjes. Het hoort bij hetzelfde ontwerp. Vraagt JLC om "different designs", antwoord dan dat het één print is met een afbreekbaar deel.

**PCB Assembly** aan:
- Type: **Standard** (er zitten onderdelen aan beide kanten)
- Assembly side: **Both sides**
- Aantal: 2
- Upload `hoofdprint/JLCPCB_BOM.csv` en `hoofdprint/JLCPCB_CPL.csv`

In het BOM-scherm moet je zelf nog onderdelen kiezen voor de regels zonder LCSC-nummer:
- **Weerstanden en gewone condensatoren**: neem JLC's voorstel, liefst "Basic". Controleer waarde en behuizing.
- **C1 (100 µF) en C2 (47 µF), 7343-15**: kies een tantaal- of polymeercondensator, ≥10 V en **maximaal ~1,9 mm hoog**.
- **C28, 100 µF 0603**: is er geen met voorraad, neem dan 47 µF 0603.
- **C83/C84, 22 µF 0402**: Murata C3894351 was op 1-10 uitverkocht. Kies een andere 22 µF 0402 met voorraad.
- **C43/C44**: 10 µF elco, SMD 6,3 × 4,5 mm.
- **L10**: ferriet 600 Ω @ 100 MHz, 0805, ≥1 A.
- **VS1053B (C9922)** en **RGB-LED D17 (C5187905)**: pre-order. Levertijd ca. 11 en 25 dagen. D17 mag je ook overslaan.

**Preview-check (belangrijk):** loop in de plaatsingspreview van JLC elk IC na. Klopt de pin-1-stip, en staan diodes, LED's en tantaal goed om?
Gaat dat het vaakst mis: U11 RP2350B, U1 VS1053B, U10 TLV320, U2 PCA9685, U3 TPS61090, U7 TPS2116, U6 74HC165, U14 FRAM, U12, alle SOT-23's, D22, D23, C1, C2.

## 2. Cartridge bij JLCPCB (alleen print)

Upload `cartridge/gerbers_cartridge.zip`. Zet: 2 layers, **1.0 mm**, ENIG, 5 stuks. Gold fingers en een afgeschuinde rand zijn optioneel.
Bestel hem in dezelfde order als de hoofdprint, dan betaal je maar één keer verzending.

De onderdelen soldeer je zelf (SOIC/0603). Zie het tabblad *Cartridge* in de Excel. Neem minimaal U1 (flash), J6 (microSD), C1/C2/C3/C6–C8, R1/R2 en D1.

De KiCad-controle vond op deze print twee foutjes van de ontwerper. Ze zijn onschadelijk zolang je de 2×10-header J2 niet gebruikt:
- I2S_WSEL en I2S_BCLK zijn bij de randconnector verwisseld. Ze gaan alleen naar J2.
- R2/C3 (reset-RC) zijn niet aangesloten.

## 3. Digikey (of Mouser)

| Onderdeel | Aantal | Waarom |
|---|---|---|
| AMPLH7020S-6R8MT (L1) | 2 | niet bij JLC |
| AMELA3012S-2R2MT (L4, L5) | 4 | niet bij JLC |
| RK10J11R0A0L (volumewiel) | 2 | niet bij JLC |

Deze soldeer je zelf aan de onderkant. L1 zit op het PSU-moduletje, L4/L5 naast de buck-converters (U4/U8).

## 4. Zelf solderen (niet door JLC geplaatst)

- Knoppen: niets te solderen. A/B, D-pad en Select/Start werken met de originele GBP-membranen (de print heeft het GB-contactpatroon). SW1/SW2 (reset/BOOTSEL, KMR221GLFS) plaatst JLC.
- 16× 3 mm LED (2 rood, 4 geel, 10 groen, zoals op de 3D-render), J5 (koptelefoon), J10/J11 (headers PSU-module)
- Uit een **donor-GBP**: J3 (cartridge-slot), SW3 (aan/uit), speaker (SPK_CONN1), batterijcontacten, membranen, knoppen
- Scherm (FPC op J1)

## 5. Firmware

`../firmware/StereoBoy_FW_sd-spi.uf2` leest de SD-kaart via SPI, zoals de gepubliceerde cartridge is bedraad.
Steek de cartridge erin, houd SW2 (BOOTSEL) ingedrukt en druk op SW1 (reset). Sleep daarna het .uf2-bestand naar de USB-schijf die verschijnt.
Deze versie compileert, maar is nog niet op echte hardware getest.
