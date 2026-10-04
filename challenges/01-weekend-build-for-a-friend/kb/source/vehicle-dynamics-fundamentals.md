---
type: concept
title: "Vehicle Dynamics Fundamentals"
description: "The domain layer that gives telemetry numbers meaning: weight transfer, the friction circle, and what springs, dampers, and suspension geometry each actually control."
tags: [vehicle-dynamics]
timestamp: "2026-08-26T00:00:00Z"
---

## Definition

Vehicle dynamics fundamentals are the physical concepts that turn raw telemetry (speed, acceleration, current draw) into something that explains why a car handles the way it does — the semantic layer that must sit above any data-collection effort or the resulting charts describe quantities that drive no decision.

## Key Points

- **Grip is a budget.** A tyre has a finite friction capacity shared between longitudinal and lateral demand — the friction circle. Spending it all on cornering leaves none for braking, and vice versa.
- **Weight transfer** under acceleration follows `ΔW = m·a·h / L` (mass × acceleration × centre-of-gravity height, divided by wheelbase). Laterally, substitute track width for wheelbase.
- **Springs set how much weight transfer happens; damper oil sets how fast it arrives** — which is why a car can feel right mid-corner (a steady-state, spring-dominated phase) and wrong on turn-in (a transient, oil-dominated phase).
- **Droop** limits how far a wheel can extend, which changes how much load the chassis can transfer before the inside wheel unloads entirely — a cheap adjustment with a fast, visible effect on lap time.
- **Camber, caster, and toe are compromises, not settings with a single correct value**: camber keeps the contact patch flat under body roll; caster trades turn-in sharpness for straight-line stability; toe trades corner-entry response against straight-line stability. See [Touring Car Steering Geometry](touring-car-steering-geometry.md) for the mechanics and shim-level detail behind Ackermann, bump steer, and caster specifically.
- **Chassis flex is a deliberate grip lever, not just structural tolerance**: a softer chassis (fewer top-deck screws, a thinner top deck, split suspension blocks) raises mechanical grip on loose/dusty surfaces, while a stiffer one sharpens responsiveness on high-grip surfaces — but flex locked out by accident (an over-tightened battery holder or motor-mount screw) strips grip as an unintended fault rather than a setting; see [Touring Car Suspension Tuning](touring-car-suspension-tuning.md).
- **Static weight balance (front/rear, left/right) sets the baseline dynamic weight transfer pitches away from** under braking and acceleration — see [Touring Car Weight Balance](touring-car-weight-balance.md) for target percentages and measurement method.
- **Grip is also a budget that can be overspent laterally**: on very high-grip surfaces, too much side-bite can cause a car to dig in and trip or roll instead of sliding — "traction rolling," with its own distinct set of countermeasures; see [Touring Car Traction and Tire Management](touring-car-traction-and-tire-management.md).
- **Track grip changes across a race day** as rubber goes down and temperature climbs — the single biggest confound for comparing any two setup-testing runs; see [Minimum Detectable Lap-Time Difference](minimum-detectable-lap-time-difference.md).

## Related Concepts

- [Gearing and Traction Math](gearing-and-traction-math.md)
- [Minimum Detectable Lap-Time Difference](minimum-detectable-lap-time-difference.md)
- [OpenGrid Canonical Data Schema](opengrid-canonical-data-schema.md)
- [Touring Car Setup Procedure](touring-car-setup-procedure.md)
- [Touring Car Steering Geometry](touring-car-steering-geometry.md)
- [Touring Car Suspension Tuning](touring-car-suspension-tuning.md)
- [Touring Car Weight Balance](touring-car-weight-balance.md)
- [Touring Car Traction and Tire Management](touring-car-traction-and-tire-management.md)
- [Yokomo BD12](yokomo-bd12.md)
- [Touring Car Aerodynamics](touring-car-aerodynamics.md)
- [Touring Car Radio and Servo Setup](touring-car-radio-and-servo-setup.md)
- [Brushless Motor Selection and Timing](brushless-motor-selection-and-timing.md)

## Sources

- [Reference Extracts from the Study Guide: Vehicle Dynamics, Gearing Math, Statistics, and Circuit Design](sources/opengrid-study-guide-reference.md)
- [Pre-Track Setup Baselines: 1/10 Modified Touring Car on Asphalt](sources/pre-track-setup-baselines.md)
- [Touring Car Chassis Dynamics: Steering Geometry, Suspension Tuning, Weight Balance, and Traction](sources/touring-car-chassis-and-steering-tuning.md)
