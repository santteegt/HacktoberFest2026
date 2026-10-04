---
type: concept
title: "Touring Car Setup Procedure"
description: "The dependency-ordered bench sequence and baseline values for setting up a 1/10 Modified Touring Car on asphalt: chassis flatness, steering, droop, anti-roll, ride height, camber/toe, then lock and cross-tweak."
tags: [vehicle-dynamics]
timestamp: "2026-09-09T00:00:00Z"
---

## Definition

The touring car setup procedure is the ordered bench sequence for preparing a 1/10 Modified Touring Car before it reaches the track, plus the baseline values a driver starts from for each step. The order is dictated by mechanical dependency, not preference — several later steps are meaningless if an earlier one hasn't been fixed first.

## Key Points

- **Order of operations**: chassis/top-deck flatness → servo centering and steering linkage geometry → droop/downstops (shocks off) → anti-roll bar balance (shocks still off) → ride height (shocks reconnected) → camber and toe → mechanical steering lock, then radio EPA → final cross-tweak.
- **The load-bearing dependency**: ride height changes droop mechanically — raising ride height decreases droop and vice versa — so any ride-height change requires resetting the downstop screws before droop can be trusted again.
- **Droop baselines** (flat track, good grip): rear 4.6 mm gauge reading, front 5.6 mm (0.6–1.0 mm higher than rear). A lower gauge number means more suspension travel. More rear droop pitches the chassis forward under braking (more entry/mid-corner steering, looser rear on entry); more front droop lets the nose lift on power (more rear traction on exit, less turn-in sharpness).
- **Ride height baseline**: 5.0 mm front / 5.2 mm rear on carpet and smooth asphalt, rising to 5.4/5.6/5.8 mm on bumpy asphalt — measured in two unworn chassis locations (behind the front arm, in front of the rear arm), never at the chassis ends where wear falsifies the reading. Rear 0.2 mm high is the standard forward rake.
- **Camber and toe baselines**: -2.0 degrees camber front and rear; rear toe-in 2.5 degrees on decent grip (3.0–3.5 on low grip, 2.0 for high grip); front toe-out 1.0–1.5 degrees per side. Front toe-in is never used.
- **Steering lock**: 27–28 degrees per side, set mechanically with the drag link disconnected, then radio EPA trimmed per side until the set screw just touches the caster block at full lock without binding — left/right EPA values need not be numerically equal, only the physical throw must match.
- **Cross-tweak diagnostic limit**: if more than 1.0 mm of spring-preload difference between left and right is needed to make all four tyres break contact simultaneously, the tweak is masking a real fault (unequal shock lengths, spring rate variance, a bent chassis, a cracked top deck, unsquared bulkheads, uneven droop, or off-centre weight) rather than fixing it.
- **Grip levers outside the fixed sequence**: shock angle at the tower (upright = more rear traction on exit; laid down = smoother/progressive on high grip), rear track width (narrower = more rear traction; wider = less roll, more corner speed on high grip), body shell fore/aft position (forward = more front downforce and steering; back = more rear downforce and stability), and Ackermann via steering-link shims — see [Touring Car Steering Geometry](touring-car-steering-geometry.md) and [Touring Car Suspension Tuning](touring-car-suspension-tuning.md) for the mechanism-level detail behind each.
- **Front body clearance and up-stops** (mechanism and the rigid-mount failure mode now detailed on [Touring Car Aerodynamics](touring-car-aerodynamics.md)): target 7–8 mm front body lip clearance on asphalt and European carpet (9–10 mm only on high-drag CRC black carpet). Body up-stop screws (or dedicated body-stopper horns above the front tires) should barely touch the body shell only at the very end of suspension travel, not hold it up constantly — set too long, they stop the body lowering with the chassis under compression, losing front downforce and adding slow-corner understeer.
- **Five common setup errors, named against the Xray X4 platform but general to the class** (per Team Xray driver Alexander Hagberg): (1) front body height/up-stops wrong, above; (2) excessive steering EPA binding the mechanical steering stop at full lock and straining the servo — verify at full lock that the turnbuckle moves freely by hand with no servo buzz; (3) over-tightened battery holders removing torsional chassis flex and creating cross-tweak — the pack needs small float in every direction; (4) over-tightened anti-roll-bar collars binding the bar in its bulkheads and adding harsh, traction-robbing damping — front bulkheads flex more under load and need slightly more play than the rear; (5) wrong/uneven belt tension (see [Touring Car Drivetrain Tuning](touring-car-drivetrain-tuning.md)).
- **Other race-day-critical checks**: radio brake EPA above 70% in Modified risks stripping/shattering spur-gear teeth under panic braking — keep it to 60–70%; ride height measured at the chassis's extreme front/rear edges on a worn chassis gives false readings, since material there wears from track contact — always measure at the two unworn reference points (behind the front arm, in front of the rear arm), never at the ends.
- **Re-check cadence**: between every run — cross-tweak, ride height, belt skip noise, ESC data logs, battery/cutoff, tyre glue, transponder, body position, radio trims, free steering, screws. Once per event or after a crash — droop, anti-roll balance, camber/toe, steering lock/EPA, top deck alignment, ESC parameters.
- **Pre-race pit sequence** (chronological, matching the order-of-operations above but with the electronics/transmitter prep and final cross-tweak recheck bracketing it): charge the transmitter fully and zero all trims before anything else; after the final cross-tweak check, lift the chassis from the center lifting holes and adjust spring preload collars until all four tires break contact with the board at the same instant — a difference over 1.0 mm signals a bent part or mismatched shock, not a tweak to dial out. Carry spare spur/pinion gears, front and rear belts, C-hubs, steering blocks, rear uprights, and suspension arms as race-day spares.

## Related Concepts

- [Vehicle Dynamics Fundamentals](vehicle-dynamics-fundamentals.md)
- [Touring Car Drivetrain Tuning](touring-car-drivetrain-tuning.md)
- [Touring Car Steering Geometry](touring-car-steering-geometry.md)
- [Touring Car Suspension Tuning](touring-car-suspension-tuning.md)
- [Touring Car Weight Balance](touring-car-weight-balance.md)
- [Touring Car Traction and Tire Management](touring-car-traction-and-tire-management.md)
- [Hobbywing XR10 Pro G3 ESC Parameters](hobbywing-xr10-esc-parameters.md)
- [Yokomo BD12](yokomo-bd12.md)
- [Touring Car Aerodynamics](touring-car-aerodynamics.md)
- [Touring Car Radio and Servo Setup](touring-car-radio-and-servo-setup.md)
- [Brushless Motor Selection and Timing](brushless-motor-selection-and-timing.md)

## Sources

- [Pre-Track Setup Baselines: 1/10 Modified Touring Car on Asphalt](sources/pre-track-setup-baselines.md)
- [Touring Car Chassis Dynamics: Steering Geometry, Suspension Tuning, Weight Balance, and Traction](sources/touring-car-chassis-and-steering-tuning.md)
- [Touring Car Motor Turns, Temperature Limits, Aerodynamics, Geometry and Radio Tuning](sources/touring-car-motor-aero-and-radio-tuning.md)
