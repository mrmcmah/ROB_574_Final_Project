# PX4 Control Stack for a Duo-Tailsitter

How PX4 controls a two-motor, two-elevon tailsitter (the CA320T configuration), and
where a custom controller would plug in. File references are into the `PX4-Autopilot`
submodule.

Relevant files:

- `ROMFS/px4fmu_common/init.d/airframes/13200_generic_vtol_tailsitter` — airframe config
- `ROMFS/px4fmu_common/init.d/rc.vtol_apps` — which modules get started
- `src/modules/vtol_att_control/tailsitter.cpp` — tailsitter state machine and arbitration
- `src/modules/control_allocator/.../ActuatorEffectivenessTailsitterVTOL.cpp` — allocation
- `src/modules/fw_rate_control/FixedwingRateControl.cpp`, `src/modules/fw_att_control/FixedwingAttitudeControl.cpp` — FW controllers with tailsitter frame handling

## 1. How a duo-tailsitter physically moves

The vehicle has only **four actuators**: two motors and two elevons. The airframe config
sets `CA_ROTOR_COUNT 2`, `CA_SV_CS_COUNT 2`, with surface types 5/6 (LeftElevon /
RightElevon). Everything below comes from those four.

**Key frame fact:** PX4 estimates attitude for a tailsitter in the *multicopter body
frame* — nose-up is the "level" reference. The FW body frame is that frame rotated 90° in
pitch (`_q_fw_to_mc` in `tailsitter.cpp`). So "roll" in one frame is "yaw" in the other.
This swap shows up throughout the code.

### Hover (nose up, motors pointing at the sky)

| Hover-frame motion | Physical mechanism |
|---|---|
| Vertical (thrust) | Collective motor throttle |
| Pitch (tip nose fore/aft) | Both elevons deflect the same way in propwash → aerodynamic pitching moment. Motors are mounted left/right (`CA_ROTOR0_PY -0.2`, `CA_ROTOR1_PY 0.2`) so they have *no* pitch authority |
| Roll (tilt left/right about the thrust axis) | **Differential thrust** between the two motors (offset in ±Y) |
| Yaw (spin about the thrust axis = the airplane's roll axis) | **Differential elevons** in propwash (opposite deflections), plus a small contribution from motor reaction torque (`CA_ROTORx_KM ±0.05`) |
| Horizontal translation | As any multicopter: command pitch/roll to tilt the thrust vector, which then has a horizontal component |

In hover the elevons only work because the props are blowing air over them. At low
throttle there is little pitch/yaw authority — this is the central tailsitter difficulty.

### Forward flight (nose forward, a flying wing)

| FW-frame motion | Physical mechanism |
|---|---|
| Roll | Differential elevons (aileron function) |
| Pitch | Collective elevons (elevator function) |
| Yaw | **Differential thrust only**, and only if the `VT_FW_DIFTHR_EN` yaw bit is set (see §3). There is no rudder; the elevons cannot produce yaw torque. `EKF2_FUSE_BETA 0` is set because sideslip isn't well-modeled for this vehicle |
| Speed / altitude | Throttle + pitch, coordinated by TECS |

Turns are banked turns like any airplane — roll tilts the lift vector, and its horizontal
component curves the path.

### Transition

Purely an attitude maneuver. `Tailsitter::update_transition_state()` builds a quaternion
setpoint that rotates from the current attitude about a horizontal axis (`_trans_rot_axis`)
at `90° / VT_F_TRANS_DUR` per second. The vehicle pitches over while the *MC* controllers
are still in charge; once pitch passes a threshold and airspeed ≥ `VT_ARSP_TRANS`
(`isFrontTransitionCompletedBase()`), it flips to FW mode. Back-transition is the reverse
rotation plus a throttle blend (`blendThrottleBeginningBackTransition()`).

## 2. The PX4 control stack for this airframe

`rc.vtol_apps` starts **both** the full multicopter stack and the full fixed-wing stack,
running concurrently, plus a VTOL arbiter in the middle.

```
                 commander / navigator / flight_mode_manager
                        (mode selection, mission setpoints)
                                  │
            ┌─────────────────────┴──────────────────────┐
     MC STACK (hover)                            FW STACK (forward)
     mc_pos_control                              fw_lat_lon_control (TECS + lateral guidance)
       → vehicle_attitude_setpoint (virtual_mc)    → vehicle_attitude_setpoint (virtual_fw)
     mc_att_control                              fw_att_control
       → vehicle_rates_setpoint                    → vehicle_rates_setpoint
     mc_rate_control                             fw_rate_control
       → torque/thrust_setpoint_virtual_mc         → torque/thrust_setpoint_virtual_fw
            └─────────────────────┬──────────────────────┘
                          vtol_att_control  (Tailsitter class)
                   state machine: MC / TRANSITION_FRONT / FW / TRANSITION_BACK
                   picks/blends the virtual setpoints → real
                   vehicle_torque_setpoint[0,1], vehicle_thrust_setpoint[0,1]
                                  │
                          control_allocator  (CA_AIRFRAME 4)
                   matrix 0: motors    matrix 1: control surfaces
                   solves effectiveness matrix → actuator_motors / actuator_servos
                                  │
                          PWM / DShot outputs
```

### Loop by loop

1. **Position / velocity loop.** `mc_pos_control` in hover: P on position → PID on
   velocity → acceleration → tilt + thrust → attitude setpoint. In FW,
   `fw_lat_lon_control` runs TECS for altitude/airspeed and a lateral guidance law for
   heading. Both run at all times; the "virtual" suffix on their outputs means the VTOL
   arbiter decides which one is real.

2. **Attitude loop.** `mc_att_control`: quaternion error → rate setpoint (`MC_ROLL_P`
   etc.). `fw_att_control`: same idea with `FW_R_P` / `FW_P_P`. For a tailsitter,
   `FixedwingAttitudeControl.cpp` first rotates the estimated attitude from MC frame into
   FW frame (`q_current = Quatf(att.q) * _q_mc_to_fw.inversed()`).

3. **Rate loop.** `mc_rate_control`: PID on body rates → normalized torque [-1,1]³ +
   thrust. `fw_rate_control`: PID with airspeed scaling → torque. In
   `FixedwingRateControl.cpp` the gyro is rotated into FW frame on the way in and the
   torque is rotated back to MC frame on the way out, so **every torque setpoint PX4
   publishes is in the MC frame**, regardless of which controller produced it.

4. **VTOL arbiter** — `Tailsitter::fill_actuator_outputs()`. The key piece:
   - **Motor matrix (index 0):** in MC / transition, MC torque + thrust pass straight
     through. In FW, thrust comes from the FW controller's X axis; torque is zero unless
     differential-thrust bits in `VT_FW_DIFTHR_EN` are set.
   - **Surface matrix (index 1):** always receives the *FW* torque setpoint, even in
     hover, unless `VT_ELEV_MC_LOCK` is set. That is how the elevons act in propwash
     during hover: the FW rate controller is still running and its output drives the
     elevons while the MC controller's output drives the motors.
   - During transitions, `update_transition_state()` overrides the attitude setpoint fed
     to `mc_att_control`.

5. **Control allocation** — `ActuatorEffectivenessTailsitterVTOL`. Two separate
   least-squares problems: a 2-rotor effectiveness matrix (differential thrust → MC roll,
   `KM` → small MC yaw) and a 2-elevon matrix (`CA_SV_CS0_TRQ_P 0.5 / TRQ_Y 0.5`,
   `CS1_TRQ_P 0.5 / TRQ_Y -0.5` — same sign for pitch, opposite sign for yaw, MC frame).
   In FW mode it swaps the motors' longitudinal/vertical bitmasks so "up" becomes
   "forward".

## 3. Yaw authority in detail

Because of the roll/yaw frame swap this is easy to get wrong.

**Hover:** full yaw authority. MC-frame yaw = spin about the thrust axis = differential
elevons in propwash. Works as long as the motors are spinning.

**Forward flight:** FW-frame yaw = MC-frame roll = the only thing the two motors can do
(they sit at ±Y). So FW yaw is **differential thrust**, and it is gated. In
`fill_actuator_outputs()`, FW mode:

```cpp
if (_param_vt_fw_difthr_en.get() & YAW_BIT) {
    _torque_setpoint_0->xyz[0] = _vehicle_torque_setpoint_virtual_fw->xyz[0] * _param_vt_fw_difthr_s_y.get();
}
```

(`xyz[0]` is MC-frame roll, i.e. FW-frame yaw after the rotation in `fw_rate_control`.)
If the bit is clear — the default, and the generic tailsitter airframe doesn't set it —
the motor torque setpoint is zeroed in FW mode and the FW yaw rate controller's output
is discarded. Yaw is then uncontrolled: the vehicle weathervanes with whatever sideslip
the roll produces. `FW_RLL_TO_YAW_FF` is applied but its result is also thrown away.

This is normal for a rudderless flying wing; sweep and wingtips give natural yaw
stiffness. Whether differential-thrust yaw is needed for coordinated turns on the CA320T
is an empirical question — the ArduPilot parameters in the creator's GitHub repo may show
what they settled on.

Options:

- Set the `VT_FW_DIFTHR_EN` yaw bit and tune `VT_FW_DIFTHR_S_Y` in the stock stack.
  Costs some thrust efficiency and couples yaw commands into airspeed.
- In a custom unified controller, include differential thrust in the effectiveness model
  at all times, with authority scaling as `(T_left − T_right) · arm`. More principled, and
  sidesteps the on/off bit entirely.

## 4. Where a custom module plugs in

`control_allocator` only consumes `vehicle_torque_setpoint` + `vehicle_thrust_setpoint`
(MC frame, normalized), so any number of the layers above it can be replaced:

- **Replace only the rate loops.** Publish torque/thrust setpoints yourself; keep
  `vtol_att_control` as the arbiter and the stock allocator. Smallest change.
- **Replace rate + attitude + arbiter.** A single unified controller that doesn't switch
  between two stacks (e.g. one quaternion / geometric attitude controller valid at all
  pitch angles — the usual research approach for tailsitters). Consume
  `vehicle_attitude_setpoint` or your own setpoint, publish directly to the two
  torque/thrust instances, and stop `vtol_att_control`, `mc_*`, `fw_*`. Would also need
  to inform `commander` about transitions, or treat the whole envelope as one mode.
- **Replace allocation too.** Publish `actuator_motors` / `actuator_servos` directly. Only
  worth it for nonlinear allocation (e.g. accounting for propwash velocity over the
  elevons, which the linear effectiveness matrix ignores).

The stock design's two biggest weaknesses, and the likely places to differentiate:

1. The hover/FW split means two separate tuning sets with a hard switch.
2. Elevon effectiveness is treated as constant, though it actually scales with propwash
   and airspeed.

A single unified controller with an airspeed/throttle-scheduled actuator model can
address both.
