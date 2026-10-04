---
type: concept
title: "Touring Car Drivetrain Tuning"
description: "Practical belt tension, differential, and gearing tuning values for a 1/10 Modified Touring Car on asphalt, plus the mechanical drivetrain checks done before every run."
tags: [powertrain]
timestamp: "2026-09-09T00:00:00Z"
---

## Definition

Touring car drivetrain tuning covers the belt tension, differential setup, and gearing choices that sit between the motor and the wheels on a modern mid-motor touring car, and the mechanical checks that confirm the drivetrain is free before it costs pack voltage or motor temperature on track. It complements the pure gearing math in [Gearing and Traction Math](gearing-and-traction-math.md) with the practical baseline values and failure signatures drivers actually tune against.

## Key Points

- **Belt tension** is set on eccentric adjusters, counted in steps from centre. Modified baseline with low-friction belts: front 3 steps tighter than centre, rear 2 steps tighter — i.e. front one step tighter than rear. This isn't arbitrary: a rear belt tighter than the front produces an overdrive effect on the rear axle, making the car loose and twitchy under acceleration. Bumpy outdoor asphalt goes one step tighter front and rear to stop skipping; stock/blinky goes one to two steps softer to preserve pack voltage over a 5-minute run.
- **Belt failure signature**: a clacking or skipping noise under hard acceleration or heavy braking — a skipping belt strips teeth immediately. Belt-booster liquid (Montech/MR33) reduces friction and extends belt/pulley life.
- **Differentials**: the asphalt touring standard is a solid axle or spool at the front and a sealed gear differential at the rear — ball diffs are considered obsolete for modern touring car. Internal construction is a 38-tooth composite diff case gear driven by a 20-tooth centre pulley. Thinner rear diff oil frees the rear axle for turn-in and agility (risking looseness on low grip); thicker oil locks the rear under power for forward traction and exit stability (risking understeer if too stiff). Tuning range is roughly 3,000–10,000 cSt, with 3,000 cSt a common spec-class baseline. Diff height is separately adjustable via eccentric bulkhead inserts, independent of oil viscosity: lowering the diff steepens the driveshaft angle for more overall bite; raising it ("high diff") is used on low-traction surfaces to add corner-exit rear grip.
- **Drive shaft orientation is a reliability issue, not just a tuning one**: on double-joint front drive shafts, the retaining C-clip's closed end goes into the retaining hole with its open tail lying flat on the coupler tube, and the shaft must be fitted on the correct side so the open tail rotates *away* from the C-hub/steering block under forward rotation. Reversed orientation lets a curb strike, full-lock steering, or heavy chassis flex catch and unclip the tail, releasing the joint pin — an immediate mechanical DNF. Grease couplers lightly and inspect outer blades regularly.
- **Build-quality checks that masquerade as tuning problems**: fill gear diffs on a digital scale (e.g. target 1.5 g of 3,000 cSt oil) for repeatable feel across rebuilds, and keep oil out of the case's screw holes before closing — trapped oil creates hydraulic pressure that strips threads on tightening. Leave bulkhead screws loose until the diff/spool is seated, torquing down only once the outdrives show a small amount of side-to-side float, so the bulkheads don't bind the drivetrain. When tightening a wheel hex's pinch screw, do it with a wheel, washer, and nut already clamped onto the axle — this keeps the hex square and avoids internal axle deformation.
- **Gearing**: internal gear ratio (IGR) = 38/20 = 1.9, the centre pulley's revolutions per full diff revolution. **FDR = (spur teeth / pinion teeth) × 1.9.** Stock class asphalt (ETS-style spec) baseline: 3.80 FDR (e.g. 94T spur / 47T pinion). Modified asphalt with a 4.5T–5.5T motor: 7.0–7.5 FDR. Longer gearing (lower FDR) raises top speed but increases heat and softens exit acceleration; shorter gearing (higher FDR) sharpens exit acceleration and lowers temperature at the cost of top speed.
- **Myth correction recorded in the source**: reaching the same FDR through different gear sizes (90/45, 94/47, 96/48 all = 3.80) produces identical acceleration and top speed — the claim that smaller gears accelerate better due to lower rotating mass is false in practice; the mass difference is negligible. Rollout is not used in standard touring car practice — FDR is the universal metric.
- **Gearing follows from turn count, not from the track alone**: Modified 4.5T–5.5T runs 7.0–7.5 FDR, a 13.5T on outdoor asphalt 3.80–4.0, and a 21.5T spec motor longer still at roughly 3.0–3.25 FDR (an 84T spur with a 49T pinion is the worked example). See [Brushless Motor Selection and Timing](brushless-motor-selection-and-timing.md) for why turn count fixes both this and the endbell-timing starting point.
- **Overheating remedy order**: drop the pinion 1–2 teeth (shorter FDR) → reduce mechanical endbell timing or ESC boost/turbo (see [Hobbywing XR10 Pro G3 ESC Parameters](hobbywing-xr10-esc-parameters.md)) → check the drivetrain for binding or tight bearings. A hot motor loses magnetic efficiency and visibly falls off in the final minutes of a 5-minute race.
- **Pre-run mechanical checks**: spur mesh should have a tiny amount of backlash (too tight adds drag and strips teeth under braking); the drivetrain must spin completely freely by hand with the pinion pulled out of mesh (binding costs pack voltage and raises motor temperature); rotate diff outdrives by hand checking for notchiness and inspect for silicone leaks. Electric touring cars have no slipper clutch — drive goes directly from spur to centre pulleys.

## Related Concepts

- [Gearing and Traction Math](gearing-and-traction-math.md)
- [Touring Car Setup Procedure](touring-car-setup-procedure.md)
- [Touring Car Suspension Tuning](touring-car-suspension-tuning.md)
- [Touring Car Traction and Tire Management](touring-car-traction-and-tire-management.md)
- [Hobbywing XR10 Pro G3 ESC Parameters](hobbywing-xr10-esc-parameters.md)
- [Brushless Motor Selection and Timing](brushless-motor-selection-and-timing.md)
- [Yokomo BD12](yokomo-bd12.md)

## Sources

- [Pre-Track Setup Baselines: 1/10 Modified Touring Car on Asphalt](sources/pre-track-setup-baselines.md)
- [Yokomo BD11/BD12 Design Evolution, General Touring Car Assembly Practice, and Drivetrain Mechanics](sources/yokomo-bd-series-design-and-assembly.md)
- [Touring Car Motor Turns, Temperature Limits, Aerodynamics, Geometry and Radio Tuning](sources/touring-car-motor-aero-and-radio-tuning.md)
