# Project Scope: Custom Tailsitter Control in PX4

## Goal

Fly the CA320T duo-tailsitter (two motors, two elevons) in hover, through transition, and in forward flight, with our own hover and transition controller running as a module inside PX4.

The module is a drop-in replacement for PX4's multicopter attitude and rate controllers. Everything else (position control, the VTOL state machine, the transition schedule, forward-flight control and the control allocator) stays stock. This keeps the project to about one month and leaves a stock baseline to compare against.

## Why this cut works

In PX4's stock tailsitter, the multicopter (MC) attitude and rate controllers fly **both hover and the transition**. During the forward transition, `vtol_att_control` produces a quaternion attitude setpoint that ramps the nose down ([`tailsitter.cpp`](../PX4-Autopilot/src/modules/vtol_att_control/tailsitter.cpp), `update_transition_state()`), and the MC controllers track it. The fixed-wing (FW) controllers only take over once the transition completes.

So replacing `mc_att_control` and `mc_rate_control` puts our control loops in charge of hover and transition, without touching:

- the VTOL state machine and transition logic in `vtol_att_control`,
- the commander vehicle state (`vehicle_type`, `in_transition_mode`),
- the allocator flight phase (`ControlAllocator` sets it from `vehicle_status.vehicle_type`, which commander takes from `vtol_att_control`),
- position control, navigation and forward-flight control.

## Background

PX4's stock tailsitter stack:

- MC stack for hover and transition: `mc_pos_control` → `mc_att_control` → `mc_rate_control`.
- FW stack for forward flight: `fw_lat_lon_control` → `fw_att_control` → `fw_rate_control`.
- `vtol_att_control` runs the state machine, generates the transition attitude setpoint and blends the MC and FW outputs.
- `control_allocator` maps torque and thrust setpoints to the motors and elevons.

See [px4_tailsitter_control_stack.md](px4_tailsitter_control_stack.md) for the full breakdown.

## Reference frames

- **FW body frame (base):** FRD on the airplane in forward flight. +x out the nose, +y out the right wing, +z out the belly.
- **MC body frame (derived):** the FW frame pitched 90° nose-up. MC +x = FW +z (belly), MC +y = FW +y, MC +z = −FW x (tail).

Our module replaces MC-stack modules, so it works in the **MC frame**, the same as the modules it replaces. See [px4_tailsitter_control_stack.md](px4_tailsitter_control_stack.md#1-reference-frames).

## In scope

1. **Custom attitude and rate controller module** under `src/modules/`, replacing `mc_att_control` and `mc_rate_control` (both started with `vtol`).
   - **Inputs (same as stock):** `vehicle_attitude_setpoint`, `vehicle_attitude`, `vehicle_angular_velocity`, `vehicle_control_mode`, `vehicle_status`, `manual_control_setpoint`.
   - **Outputs (same as stock):** `vehicle_rates_setpoint`, `vehicle_torque_setpoint_virtual_mc`, `vehicle_thrust_setpoint_virtual_mc`.
   - **Control law:** quaternion attitude error → rate setpoint → PID rate loop → torque. Valid across the full pitch range, so it can track the transition pitch-down.
   - **Our addition:** schedule the elevon gains on throttle and pitch angle, because elevon authority depends on propwash and airspeed. This is the main difference from the stock controller and the main thing to evaluate.
2. **Startup integration.** The CA320T airframe starts our module instead of `mc_att_control` and `mc_rate_control`. All other VTOL apps start as normal.
3. **Simulation first.** Hover and transition in the duo-tailsitter SIH airframe (`1102_tailsitter_duo_sih.hil`) before hardware.
4. **Flight.** Hover, forward transition, stock forward flight, back transition.
5. **Comparison.** The same flight with the stock controllers and with ours, for the write-up.

## Out of scope

- Position, velocity and navigation control (stock `mc_pos_control`, `fw_lat_lon_control`, `navigator`).
- Forward-flight attitude and rate control (stock `fw_att_control`, `fw_rate_control`).
- The VTOL state machine and transition schedule (stock `vtol_att_control`).
- Unified position, attitude and rate control, wing models, INDI and airspeed estimation. These are possible future work.
- Changes to commander or the control allocator.
- Airspeed sensing. Transition completes on pitch angle (stock `isFrontTransitionCompletedBase()`), with `VT_F_TR_OL_TM` as the time limit.

## Deliverables

| # | Deliverable | Done when |
|---|---|---|
| 1 | Custom attitude and rate controller module | Builds for `px4_sitl` and `micoair_h743-v2` |
| 2 | Airframe startup that swaps in the module | Boots with our module instead of `mc_att_control` and `mc_rate_control` |
| 3 | SIH results | Hover and full transition cycle in simulation |
| 4 | Bench test | Motor and elevon directions confirmed, tethered hover |
| 5 | Flight logs | Hover and transition with the stock controller and with ours |
| 6 | Write-up | Control law, gain scheduling, and comparison against stock |

## Schedule (about four weeks)

| Week | Work |
|---|---|
| 1 | Run the stock duo-tailsitter in SIH. Create the module by copying the structure of `mc_att_control` and `mc_rate_control`. Swap it in and match stock behaviour in hover. Start building the aircraft. |
| 2 | Add elevon gain scheduling. Fly the full transition cycle in SIH. Finish the build and set up the CA320T airframe (actuator mapping, directions). |
| 3 | Bench and tethered hover with the stock controller, then with ours. Free hover. First transition. |
| 4 | Comparison flights (stock vs ours). Write-up. Buffer for problems. |

**Fallback:** if the custom module is not flight-ready by week 3, fly the stock stack for the hardware demonstration and present our module from SIH results.

## Constraints

- **No airspeed sensor.** The transition completes on pitch angle and time.
- **Hardware.** MicoAir743v2-AIO-45A (PX4 target `micoair_h743-v2`). Motors on M1/M2 (DShot), elevon servos on M5/M6 (PWM). The 5 V rail is 2 A total, shared with the receiver and GPS.
- **Airframe.** Duo-tailsitter with 3.7 g elevon servos and 1404-class motors on 3" props. The FC holder needs remodelling for the 36 × 36 mm board.

## Open questions

1. What do we schedule the elevon gains on: throttle only, or throttle and pitch angle?
2. Which signals do we log for the comparison (attitude tracking error, rate tracking error, actuator saturation, battery current)?

## References

- [PX4 control stack breakdown](px4_tailsitter_control_stack.md)
- [Bill of materials](bom.md)
- Creator's build and models: [MakerWorld](https://makerworld.com/en/models/2734689), [CarviLabs](https://carvilabs.com), [GitHub](https://github.com/CarviFPV/CA320T)
