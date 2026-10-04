---
type: concept
title: "Touring Car Weight Balance"
description: "Target front/rear and left/right weight percentages for a 1/10 touring car, how they're measured and adjusted, and why static balance shapes dynamic weight transfer under braking and acceleration."
tags: [vehicle-dynamics]
timestamp: "2026-09-16T00:00:00Z"
---

## Definition

Weight balance is the static front/rear and left/right mass distribution of a race-ready touring car, measured on the bench and adjusted with weights or battery/electronics position. It matters because it sets the baseline that dynamic [weight transfer](vehicle-dynamics-fundamentals.md) pitches away from under braking and acceleration — the same physical mechanism the `ΔW = m·a·h / L` formula describes, but as a static starting condition rather than a transient one.

## Key Points

- **Left/right target**: 50/50; a 1–2% variance (e.g. 51/49) is acceptable if the chassis carries no mechanical tweak.
- **Front/rear target**: tuned within roughly a 4% window (48/52 to 52/48). 50/50 (neutral) is the universal new-track baseline and the primary target for Stock/Blinky spec classes — most balanced feel, maximizes mid-corner momentum. A forward bias (51/49–52/48) is used on high-grip carpet to calm turn-in and reduce traction rolling. A rearward bias (49/51–48/52) is common on outdoor asphalt and Modified class, sharpening off-power turn-in and apex rotation; the extreme end (48/52) is aggressive and hard to drive consistently over a full run.
- **Measurement**: the car must be fully race-ready (battery, body, transponder, tires) on a level board with ride height/tweak already set. In order of precision: four-corner Bluetooth scales (e.g. SkyRC/HUDY) reading all four corners simultaneously and computing cross-tweak plus left/right and front/rear percentages directly; left/right pin-balancing tools at the chassis centerline holes; a single kitchen scale with setup plates, weighing front then rear and computing the ratio by hand.
- **Adjustment**: tungsten/brass/steel weight plates near the centerline, under the battery, or under the motor mount; battery-holder repositioning fore/aft; centralizing the receiver/ESC near the centerline. A Shorty LiPo lowers CG but typically needs a 35–40 g brass battery plate underneath to offset the lost side mass. Option parts have a real, unplanned effect on balance — an Active Rear Suspension kit adds roughly 20 g directly to the rear axle on its own.
- **Why it matters**: a more rearward static bias increases how much weight pitches forward under braking, forcing the front tires into the track for sharper turn-in and mid-corner rotation; a more forward static bias reduces that pitch, calming corner entry and reducing edginess/flip risk on high-bite tracks. On corner exit, weight transfers back to the rear regardless of static bias, which is what stabilizes the rear end under power.

- **On the owner's BD12 the layout starts asymmetric**: the motor, ESC, receiver and servo all sit on the left and a full-length battery lies lengthwise on the right, per Yokomo's own setup-sheet drawing. Hitting 50/50 left/right on this chassis is a matter of balancing those two groups rather than correcting a stray part, which is why battery position and weights under the pack are the natural first levers — see [Yokomo BD12](yokomo-bd12.md).

## Related Concepts

- [Yokomo BD12](yokomo-bd12.md)
- [Vehicle Dynamics Fundamentals](vehicle-dynamics-fundamentals.md)
- [Touring Car Suspension Tuning](touring-car-suspension-tuning.md)
- [Touring Car Traction and Tire Management](touring-car-traction-and-tire-management.md)

## Sources

- [Touring Car Chassis Dynamics: Steering Geometry, Suspension Tuning, Weight Balance, and Traction](sources/touring-car-chassis-and-steering-tuning.md)
- [Yokomo BD12 Layout and Hardpoints, Measured from Yokomo's Setup-Sheet Drawings](sources/yokomo-bd12-layout-from-setup-sheet.md)
