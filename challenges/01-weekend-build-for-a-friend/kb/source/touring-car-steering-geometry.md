---
type: concept
title: "Touring Car Steering Geometry"
description: "The mechanics and setup values behind Ackermann effect, bump steer, and caster on a 1/10 touring car, and how each trades off turn-in sharpness against stability and traction-rolling risk."
tags: [vehicle-dynamics]
timestamp: "2026-09-16T00:00:00Z"
---

## Definition

Touring car steering geometry covers the front-end mechanisms that determine how the car actually turns beyond the raw steering input: Ackermann effect (the inner/outer wheel angle difference), bump steer (unwanted toe change under suspension compression), and caster (the steering axis's backward tilt). All three are shimmed or angled at the bench, not adjusted from the radio, and all three trade turn-in sharpness against stability and traction-rolling risk.

## Key Points

- **Ackermann effect**: the inner front wheel turns at a sharper angle than the outer wheel in a corner, matching their different turning radii. Adjusted via shims under the ball studs on the central steering rack — fewer/zero shims means *more* Ackermann effect (smoother, more forgiving turn-in); more shims (up to a ~1.0 mm ceiling) means *less* Ackermann effect, i.e. wheels closer to parallel (sharper, twitchier turn-in, more prone to traction rolling on high grip). Baseline: 0–0.5 mm. Shortening the wheelbase acts like adding 1.0 mm of Ackermann shim, so rack shimming needs rechecking after any wheelbase change.
- **Bump steer**: unwanted toe-in that appears as the front suspension compresses, with no steering input, because the suspension arm, camber link, and steering turnbuckle sweep through different arcs. Adjusted via shims under the ball stud on the outer steering block — more shims add toe-in under compression (more mid-corner-to-exit steering, more aggressive/nervous front end); fewer shims keep toe flatter (smoother turn-in). Outdoor asphalt baseline is 1.0–2.0 mm (more bump steer helps generate front grip on lower-traction surfaces); carpet runs less, 0–1.0 mm, to avoid edginess.
- **Caster**: the backward tilt of the C-hub/kingpin axis from vertical; positive caster puts the steering pivot ahead of the tire's contact patch. Baseline is 4° positive. More caster (5–6°) trades sharper off-power entry for better straight-line stability, smoother entry, more on-power mid-corner/exit steering, and better bump absorption on outdoor asphalt. Less caster (2°) sharpens off-power entry bite (useful for tight hairpins) at the cost of straight-line twitchiness and on-power push at corner exit.
- **These three interact with each other and with weight balance** — reducing bump steer and Ackermann shims is one of the standard countermeasures for [traction rolling](touring-car-traction-and-tire-management.md), alongside front toe-out, camber, and weight-forward bias.

## Related Concepts

- [Vehicle Dynamics Fundamentals](vehicle-dynamics-fundamentals.md)
- [Touring Car Setup Procedure](touring-car-setup-procedure.md)
- [Touring Car Suspension Tuning](touring-car-suspension-tuning.md)
- [Touring Car Traction and Tire Management](touring-car-traction-and-tire-management.md)

## Sources

- [Touring Car Chassis Dynamics: Steering Geometry, Suspension Tuning, Weight Balance, and Traction](sources/touring-car-chassis-and-steering-tuning.md)
- [Yokomo BD12 Layout and Hardpoints, Measured from Yokomo's Setup-Sheet Drawings](sources/yokomo-bd12-layout-from-setup-sheet.md)
