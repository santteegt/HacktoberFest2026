---
type: concept
title: "Touring Car Radio and Servo Setup"
description: "The transmitter and steering servo as a setup surface: servo mounting and the 90-degree horn rule, steering EPA and its binding failure, dual rate and total steering angle, and where expo belongs."
tags: [vehicle-dynamics]
timestamp: "2026-09-18T00:00:00Z"
---

## Definition

Radio and servo setup is the part of a touring car's configuration that lives in the transmitter and in how the steering servo is mounted, rather than in shims and turnbuckles: servo mounting and horn alignment, mechanical steering lock and its matching radio end points, total steering travel, and exponential curves. It matters as setup rather than as convenience because two of its settings have direct mechanical consequences — excessive steering EPA binds chassis flex at full lock, and excessive brake EPA strips spur gears — both of which are recorded among the common errors on [Touring Car Setup Procedure](touring-car-setup-procedure.md).

## Key Points

- **Servo choice and BEC voltage**: low-profile servos are universal in 1/10 touring. HV servos can be run at 7.4 V for maximum speed and torque, but some fade as pack voltage drops over a 5-minute run, which is why 6.0 V BEC output is described as the choice that gives consistent, fade-free steering from start to finish — the same conclusion reached on [Hobbywing XR10 Pro G3 ESC Parameters](hobbywing-xr10-esc-parameters.md).
- **Servo mounting**: on mid-motor chassis where the front drive belt passes alongside the servo, remove or dremel away the lower-left (fourth) mounting lug so the belt cannot rub or bind on the case. Standard button-head screws with washers let the servo shift in a crash; one-piece aluminium servo screws with an integrated guide collar that fits the lug holes lock it square instead. Keep an equal gap between the servo case and the mounting plate.
- **The 90-degree horn rule**: with transmitter and receiver on and every trim and sub-trim at zero, mount the servo saver or horn at 90 degrees to the drag link, pointing slightly toward the car's centreline, then centre with sub-trim only. Set both steering turnbuckles to exactly equal length with a caliper. This is step two of the bench sequence, before any suspension setting is touched.
- **Steering EPA**: set mechanical lock first with the set screws in the caster blocks, drag link disconnected, to 27–28 degrees per side. Reconnect and adjust left and right EPA individually until the set screw just barely touches the caster block at full lock without binding. The two EPA numbers need not match (109 left against 123 right on a Sanwa M17 is the cited example) as long as the physical throw does. Verify at full lock that the linkage still moves freely by hand: excessive EPA makes the servo strain and buzz and presses the steering link against the arm, binding the chassis flex the car relies on mid-corner — see [Touring Car Suspension Tuning](touring-car-suspension-tuning.md) on flex locked out by accident.
- **Dual rate and total steering angle**: 22–26 degrees total on indoor carpet and high grip, 24–28 degrees on outdoor asphalt and up to 30 on open tracks, with one driver cited running 40% dual rate for initial track testing in Modified. The principle is to run as much steering as is needed to hit the apexes and as little as possible beyond that, because excess steering angle scrubs speed mechanically through the turn.
- **Steering expo**: −5% to −10% on a wheel radio, −10% to −20% on a stick radio. Negative expo reduces sensitivity around neutral, making initial steering smoother and easier to drive consistently over a run.
- **Throttle expo belongs in the ESC, not the radio**: transmitter throttle curvature is left Linear, because shaping delivery inside the ESC through Throttle Rate Control, PWM drive frequency and the ESC's own curvature is described as far more effective and consistent. ESC neutral range stays at its 6% default (4% and 8% being the alternatives) to keep a clean transition between throttle and drag brake.
- **Brake EPA is the other mechanically consequential radio setting**: 60–70% in Modified, because 100% strips or shatters spur-gear teeth under panic braking.

## Related Concepts

- [Touring Car Setup Procedure](touring-car-setup-procedure.md)
- [Touring Car Steering Geometry](touring-car-steering-geometry.md)
- [Touring Car Suspension Tuning](touring-car-suspension-tuning.md)
- [Hobbywing XR10 Pro G3 ESC Parameters](hobbywing-xr10-esc-parameters.md)

## Sources

- [Touring Car Motor Turns, Temperature Limits, Aerodynamics, Geometry and Radio Tuning](sources/touring-car-motor-aero-and-radio-tuning.md)
- [Pre-Track Setup Baselines: 1/10 Modified Touring Car on Asphalt](sources/pre-track-setup-baselines.md)
