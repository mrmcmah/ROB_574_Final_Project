# CA320T / PX4 Build — Bill of Materials

Scope: everything except 3D-printing filament. Flight controller is the MicoAir743v2-AIO-45A
already on hand. Video is the cheapest Walksnail Avatar air unit. No airspeed sensor (flying
airspeed-less, see `px4_tailsitter_control_stack.md`).

Prices are USD list prices from retailer search results on 2026-10-31 and will drift. Several
listings were out of stock at the time; check before ordering.

## Fit check against the STLs

Measured directly from the MakerWorld STL files (slice/loop analysis, ±0.1 mm):

| Printed part | What it constrains | Measured | Consequence |
|---|---|---|---|
| `V2_MotorFront_L/R` (motor plate) | Motor bolt pattern | Ø27 mm plate, 4× Ø2.4 holes on a **6.4 × 6.4 mm square (Ø9.0 mm bolt circle)**, Ø5.0 mm center hole | Matches the T-Motor P1604 drawing (4-M2, Ø5, "9×9"). Any motor listed as **"9 mm / 9×9 M2"** with a 1.5 mm shaft should fit. 12×12 motors will **not** fit without reprinting the 2 mm plate. |
| `V2_MotorMount` position | Prop clearance | Motor axes at x = ±92.5 mm; fuselage half-width 40 mm; prop plane ~10 mm ahead of wing LE | 3" prop: 14 mm tip-to-fuselage. 3.5": 8 mm. Both OK. |
| `Wing_L/R` servo pocket | Servo size | Body cavity **20.8 (chord) × 13 (span) × 11.4 (thick) mm**, tab slot 31 mm long, Ø2.1 screw holes on **23.6 mm** centers | Fits the **3.7 g servo class** (20.2 × 8.5 body, 23.5 mm hole spacing). A 9 g SG90 (22.5 long, ~28 mm holes) will **not** fit. |
| `v2_Batt_Holder` | Battery cross-section | Rectangular tunnel **29 × 18 mm**, open-ended | "Long type" 3S 450 mAh packs (≈17–19 × 19–21 × 63 mm) fit lying flat. |
| `V2_GPS_AND_fc_holder` + `FC_Holder_Top` | FC size | Bay ≈ **38.5 × 30 mm**, designed around the Matek F405-WMO (32 × 22 mm) | The MicoAir AIO (36 × 36 mm, 25.5 mm holes) **does not fit the stock holder**. Fuselage interior is 71 × 26 mm at mid-body, so the board fits the airframe; the holder part needs a remodel. |
| `V2_VTX` | Air unit footprint | Built for the DJI O4 Lite (30 × 30 board, 25.5 × 25.5 M2) | Walksnail Mini 1S Lite VTX is 30 × 30 × 6.5, 25.5 × 25.5 — same footprint. |
| `Front_o4-14mm_*` nose | Camera | Cut for the O4 Lite camera (~13.4 × 12.4 × 16.5 mm) | Walksnail Lite camera is 14 × 14 × 16 mm — expect to open the cutout ~1–2 mm. |
| `GPS_Holder` / holder GPS pad | GPS module | 4× M2 on 24.5 × 13 mm | HGLRC M100-5883 is 21 × 21 mm; mount with tape/zip tie or add holes. |

## BOM

### Propulsion and control

| # | Item | Qty | Spec / why | Est. price | Notes |
|---|---|---|---|---|---|
| 1 | **1404 4600KV** motors (2-pack) | 1 pack (2 motors) | 1.5 mm shaft (T-mount), **9 mm M2 mount** (matches plate), 3–4S, 9 g each | **$36.99** | Primary pick: a matched pair, stated 9 mm pattern, in stock at Pyrodrone. |
|   | *alt:* BetaFPV 1404 3800KV | 2 | 1.5 mm shaft, M2, 3–4S, 9.66 g | $6.99 ea (sale) / $53.99 per 4 | Pattern spacing not stated in listings; verify 9 mm before buying. Often out of stock. |
|   | *alt (cheapest):* 2nd VCI Spark 1204 5600KV to pair with the one on hand | 1 | 4× M2 (spacing unverified), tested by vendor at 16 V / 2.5" only | ~$13–15 | 5600KV on 3S with a 3" prop is at the hot end for a 1204 stator. Measure the bolt pattern first. Do **not** mix the 1204 with the 1303. |
| 2 | **HQProp T3x1.5x3** props | on hand + 1 spare 4-pack (2CW + 2CCW) | 3" tri, 1.5 mm T-mount | **$3–4** | Need 1 CW + 1 CCW per flight. |
| 3 | **3.7 g micro servos**, digital (e.g. GH-S37D) or analog | 2 (buy 3–4 for spares) | 20.2 × 8.5 body, 23.5 mm hole spacing, ~0.6 kg·cm | **$4–9 ea** (5-pack ≈ $18.68) | Only size class that fits the wing pocket. Digital preferred for hover response. |
| 4 | **MicoAir743v2-AIO-45A** | 1 | H743 FC + 4-in-1 45 A AM32 ESC, BMI088/BMI270, SPL06 baro, SD slot | *on hand* | PX4 target `micoair_h743-v2`. Motors on M1/M2 (DShot), servos on M5/M6 pads (PWM). |

### Radio, navigation, video

| # | Item | Qty | Spec / why | Est. price | Notes |
|---|---|---|---|---|---|
| 5 | **Happymodel EP1 RX** (ELRS 2.4 GHz) | 1 | 0.4 g, CRSF to UART6 (RX6/TX6) | **$20.49** | Same RX the creator uses. TCXO version ~$22. |
| 6 | **HGLRC M100-5883** GPS + compass | 1 | u-blox M10 + QMC5883L, 21 × 21 mm, 7.7 g, UART + I2C | **$20.49** | Board has no onboard compass; this is the cheapest M10 + compass found. Goes on the GPS/I2C connector (UART3). |
| 7 | **Walksnail Avatar HD Mini 1S Lite Kit** (VTX + camera + antenna) | 1 | VTX 30 × 30 × 6.5 mm, 25.5 × 25.5 holes, ~5–7 g; camera 14 × 14 × 16 mm, 1.8 g; **3.1–13 V input** (V3) | **$89** (CaddxFPV) / $88.99 (RC Papa) | Cheapest Walksnail air unit. Can run from 3S directly or the board's 12 V/5 V pad. PX4 has no OSD support for it; video only. Verify you get the V3 (13 V) revision. |

### Power

| # | Item | Qty | Spec / why | Est. price | Notes |
|---|---|---|---|---|---|
| 8 | **GNB 3S 450 mAh 80C, long type, XT30** | 2 | 64 × 17.5 × 19 mm, 40 g | **$9.99 ea** | Fits the 29 × 18 mm holder tunnel lying flat. Tattu 3S 450 75C long (63 × 16 × 21, 45 g, $12.19) also fits. |
| 9 | Low-ESR capacitor, 35 V 470 µF | 1 | Across battery pads per MicoAir wiring diagram | **$2** | |
| 10 | XT30 pigtail (male, 18 AWG) | 1 | Battery lead to the AIO BAT+/BAT− pads | **$2** | |

### Hardware and consumables

| # | Item | Qty | Est. price | Notes |
|---|---|---|---|---|
| 11 | M2 × 5–6 mm screws (motor to plate) | 8 + spares | $3 | Check motor base thickness; too long = shorted windings. |
| 12 | M2 × 8–10 mm screws + nuts/standoffs (FC, VTX, plate-to-mount) | ~12 | $3 | FC/VTX stack on 25.5 mm pattern; M2 nylon standoffs fine. |
| 13 | 1.0 mm steel pushrod wire + Z-bends or micro clevises | 2 | $3 | Servo at ~y = 35 mm to aileron horn at ~y = 90 mm: ~55 mm rods. Aileron horn and hinge pins are printed. |
| 14 | Servo extension / 28–30 AWG silicone wire, heat-shrink | — | $4 | Servo leads run through the wing channel to M5/M6 pads. |
| 15 | microSD card, 16–32 GB, UHS-I | 1 | $8 | Required for PX4 logging/tuning. |
| 16 | CA / epoxy for pins, velcro strap | — | $5 | Build guide: pins are glued in. |

### Not included (assumed on hand or already covered)

- ELRS 2.4 GHz transmitter, LiPo charger, Walksnail goggles/VRX, laptop with QGroundControl.
- 3D-printing filament (PETG/PLA per the creator).
- 5 V BEC for servos: **skipped**. Two 3.7 g servos stall at ~0.3–0.5 A each; the board's 2 A 5 V rail also feeds RX (~0.1 A) and GPS (~0.1 A). Add a BEC only if you see brownouts.

## Totals (primary picks)

| Group | Est. |
|---|---|
| Motors (Skystars pair) | $37 |
| Props spare pack | $4 |
| Servos (4 × ~$4.50) | $18 |
| RX | $20 |
| GPS/compass | $20 |
| Walksnail kit | $89 |
| Batteries (2) | $20 |
| Power/hardware/consumables | $30 |
| **Total** | **≈ $240** |

Dropping to the BetaFPV motors at sale price saves ~$20; buying a second Spark 1204 instead saves ~$22 but adds thermal risk.

## Weight / thrust budget (estimate, verify on a scale)

| | g |
|---|---|
| MicoAir AIO | 10 |
| 2× 1404 motors | 18 |
| 2× props + screws | 4 |
| 2× 3.7 g servos + rods | 10 |
| Walksnail kit | 8 |
| EP1 RX | 0.5 |
| M100-5883 GPS | 8 |
| 3S 450 battery | 40 |
| Wiring, capacitor, screws | 12 |
| **Electronics subtotal** | **≈ 110** |
| Printed airframe (creator's sub-250 build with heavier P1604s/O4 implies ≤ ~140) | ~130 |
| **AUW** | **≈ 240** |

A 1404 ~3800–4600KV on 3S with a 3" tri-blade is typically in the 250–300 g static thrust range
per motor (no published test for this exact combo was found). Two motors → ~500–600 g, so
T/W ≈ 2.1–2.5 — adequate for hover and transition. Hover should sit near 45–50 % throttle,
which leaves differential-thrust authority for roll in hover.

## Printed parts that need changes for this hardware

1. **`V2_GPS_AND_fc_holder`** — remodel the FC bay for a 36 × 36 mm board on 25.5 × 25.5 holes (stock bay is ~38.5 × 30 mm for the F405-WMO).
2. **`Front_o4-14mm_*`** — open the camera cutout to ≥ 14 × 14 mm for the Walksnail Lite camera.
3. **`GPS_Holder`** — adapt to the 21 × 21 mm M100-5883, or use tape.
4. Skip `VTX_Ant_mount` unless the Walksnail antenna (Ø5 × 70 mm) needs it; the O4 and Walksnail antennas differ.

## Sources

- MakerWorld listing (recommended parts): https://makerworld.com/en/models/2734689
- CarviLabs build guide: https://carvilabs.com/products/carvifpv/ca320t/wiki/build-instructions
- Skystars 1404 4600KV 2-pack: https://pyrodrone.com/products/skystars-1404-brushless-motor-for-2-5-inch-to-4-inch-lighweight-drones-3-4s-4600kv-2-pcs
- BetaFPV 1404 3800KV: https://betafpv.com/products/1404-3800kv-brushless-motors , https://www.getfpv.com/betafpv-1404-3800kv-brushless-motors-4pcs.html
- T-Motor P1604 mounting (4-M2, Ø5, 9×9, 1.5 mm shaft): https://rcdrone.top/products/t-motor-p1604-fpv-motor-kv2850 , https://www.fpvfaster.com.au/products/t-motor-p1604-fpv-drone-motor-3-5-inch-freestyle-2850kv
- VCI Spark 1204: https://rcdrone.top/products/vci-spark-1204-motor
- 3.7 g servo dimensions (20.2 × 8.5 × 20.2, 23.5 mm holes): https://core-electronics.com.au/sub-micro-servo-3-7g-generic.html , https://www.pololu.com/product/1053
- HQProp T3x1.5x3: https://pyrodrone.com/collections/t-mount-propellers/products/hq-prop-t3x1-5x3-durable-tri-blade-3-prop-grey
- Happymodel EP1 RX: https://www.racedayquads.com/products/happymodel-2-4ghz-ep1-rx-express-lrs-receiver
- HGLRC M100-5883: https://racedayquads.com/collections/sensors-more/products/hglrc-m100-5883-gps-module-10th-gen
- Walksnail Avatar HD Mini 1S Lite Kit: https://www.caddxfpv.com/products/walksnail-avatar-hd-mini-1s-lite-kit , https://www.rcpapa.com/products/walksnail-avatar-hd-mini-1s-lite-kit , https://kiwiquads.co.nz/product/walksnail-avatar-hd-mini-1s-lite-kit/
- DJI O4 Lite footprint (30 × 30, 25.5 × 25.5 M2): https://oscarliang.com/dji-o4-air-unit-lite/
- GNB 3S 450 mAh long: https://www.racedayquads.com/products/gaoneng-gnb-11-1v-3s-450mah-80c-lihv-micro-battery-long-type-xt30
- Tattu 3S 450 mAh long: https://www.getfpv.com/tattu-450mah-3s-75c-lipo-battery-long-size-xt30.html
- Matek F405-WMO size (32 × 22 mm): https://www.flyingtech.co.uk/product/matek-f405-wmo-wing-flight-controller/
- MicoAir H743V2-AIO-45A: https://store.micoair.com/product/micoair743v2-aio-45a/
