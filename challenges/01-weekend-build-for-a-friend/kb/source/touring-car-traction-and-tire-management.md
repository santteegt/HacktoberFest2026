---
type: concept
title: "Touring Car Traction and Tire Management"
description: "What causes traction loss, the separate lever sets for overall versus rear-specific traction, traction rolling and its countermeasures, and tire prep/rotation/additive practice for a 1/10 touring car."
tags: [vehicle-dynamics]
timestamp: "2026-09-16T00:00:00Z"
---

## Definition

Traction and tire management covers how much grip a touring car actually generates and keeps over a run — the practical, adjustment-level counterpart to the friction-circle concept in [Vehicle Dynamics Fundamentals](vehicle-dynamics-fundamentals.md). It spans mechanical causes of traction loss, the distinct sets of setup levers for raising overall versus rear-specific traction, the failure mode of having *too much* lateral grip (traction rolling), and the tire-care routine that keeps grip consistent across a race day.

## Key Points

- **What kills traction**: cold/dusty/unconditioned track surface; tire overheating and fade on hot tracks over a full run; over-tightened battery holders or anti-roll-bar collars locking out [chassis flex](touring-car-suspension-tuning.md); belts too tight (friction/heat) or rear tighter than front (rear-axle "overdrive" causing looseness — see [Touring Car Drivetrain Tuning](touring-car-drivetrain-tuning.md)); a front body mounted too high (lost downforce) or tires scrubbing the body shell; excessive ESC timing or an aggressive throttle profile causing wheelspin.
- **Increasing overall traction**: increase chassis flex (fewer top-deck screws, thinner 1.6 mm top deck, removed motor-mount screws, a floating battery); raise the roll center; lower the diff/spool position to steepen driveshaft angle; pair softer shock oil with harder springs (or shorter shock shafts) to speed/increase weight transfer onto the tires; shorten camber links for more camber gain; soften ESC throttle response (lower Throttle Rate Control, raise PWM drive frequency, enable timing Softening — see [Hobbywing XR10 Pro G3 ESC Parameters](hobbywing-xr10-esc-parameters.md)).
- **Increasing rear-specific traction**: more static rear toe-in (3.0–3.5°); an Active Rear Suspension toe link angled so rear toe-in grows dynamically under compression (e.g. 3.0° → 3.8°); softer rear diff oil (down to ~3,000 cSt on low-grip asphalt); rear shocks stood upright; a thinner rear anti-roll bar; more front droop (shifts load rearward under power); a rearward weight bias; a narrower rear track; the body shell mounted further back.
- **Traction rolling**: on high-grip surfaces, lateral grip becomes high enough that the outer tire digs in and the car trips or rolls instead of sliding. Countermeasures: thin CA glue on the front tire's outer sidewall/edge; reduced front negative camber (~1.0°) so the outer tire loses flat contact deep in fast corners; shorter additive soak time or additive applied only to the inner tire half; more front toe-out (~1.5°/side); shocks laid down and/or softer springs; a more forward weight bias (51/49); less droop (higher gauge values, restricting chassis pitch/roll); a lower roll center; reduced [bump steer and Ackermann shimming](touring-car-steering-geometry.md).
- **Tire preparation**: remove the molding line and check bead glue on new tires; re-glue beads every 3–4 runs. Additive soak is longer (~20 min, with tire warmers) on low-grip asphalt, shorter or inner-band-only on high-grip carpet to avoid traction rolling.
- **Rotation cadence is per pack, not per session**: swap front tyres left-to-right and rear tyres left-to-right after every single battery pack from run one, because tracks turn more in one direction and the outer tyres otherwise wear unevenly across their own tread. Spec series often restrict drivers to two new sets per event, which is what makes the cycling strategy below matter.
- **Tire rotation and cycling**: rotate front and rear tires left-to-right after every run to equalize wear against a track's directional turn bias. Cycle tire sets by wear across a race day — oldest/highest-mileage tires for cold, dusty morning practice; medium-wear for mid-day tuning; freshest (1–2 run) tires reserved for qualifying/finals to match true grip conditions. Soft springs reduce tire overheating on hot tracks; avoid running heavily worn or overheated tires back-to-back, since rubber degradation makes handling unpredictable.

- **Tyre diameter is a geometry input, not just a wear figure**: as rubber wears the diameter drops, which lowers chassis ride height, which in turn increases droop travel — so both ride height and the downstop screws have to be re-set as a set wears through a day. Separately, HW Link exposes a Tire Diameter parameter used purely for telemetry calculation, so logged speed and motor RPM come out right; see [Gearing and Traction Math](gearing-and-traction-math.md) on why rolling diameter is better treated as a fitted parameter than a calliper measurement.
- **A real gap, not an extraction failure**: across this whole source set there are no shore-hardness numbers (28, 30, 32, 36 and similar) and no foam-insert brands or compounds, despite thorough coverage of mould lines, bead gluing, additive, warmers, rotation and CA sidewall treatment. Anything on compound selection or inserts has to come from elsewhere.

## Related Concepts

- [Vehicle Dynamics Fundamentals](vehicle-dynamics-fundamentals.md)
- [Touring Car Steering Geometry](touring-car-steering-geometry.md)
- [Touring Car Suspension Tuning](touring-car-suspension-tuning.md)
- [Touring Car Weight Balance](touring-car-weight-balance.md)
- [Touring Car Drivetrain Tuning](touring-car-drivetrain-tuning.md)
- [Gearing and Traction Math](gearing-and-traction-math.md)
- [Touring Car Aerodynamics](touring-car-aerodynamics.md)

## Sources

- [Touring Car Chassis Dynamics: Steering Geometry, Suspension Tuning, Weight Balance, and Traction](sources/touring-car-chassis-and-steering-tuning.md)
- [Touring Car Motor Turns, Temperature Limits, Aerodynamics, Geometry and Radio Tuning](sources/touring-car-motor-aero-and-radio-tuning.md)
