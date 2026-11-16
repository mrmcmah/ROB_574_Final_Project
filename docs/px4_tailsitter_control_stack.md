# PX4 Control Stack for a Duo-Tailsitter

How PX4 controls a two-motor, two-elevon tailsitter (the CA320T configuration), broken
into its components, and where a custom controller would plug in. File references are
into the `PX4-Autopilot` submodule.

## Acronyms and terms

| Term | Meaning |
|---|---|
| **PX4** | The open-source autopilot firmware this project builds on. |
| **VTOL** | Vertical Take-Off and Landing. PX4's vehicle class for aircraft that hover and fly forward. A tailsitter is one VTOL type. |
| **Tailsitter** | A VTOL that sits on its tail, takes off nose-up, and pitches over 90° to fly like a plane. No tilting motors. |
| **MC** | Multicopter. PX4's hover-mode controllers and the hover reference frame. |
| **FW** | Fixed-Wing. PX4's forward-flight controllers and the airplane reference frame. |
| **FRD** | Forward-Right-Down. PX4's body-frame axis convention: x forward, y right, z down. |
| **NED** | North-East-Down. PX4's world (local) frame convention. |
| **Elevon** | A control surface that does the job of both an elevator (pitch) and an aileron (roll). The CA320T has two. |
| **Propwash** | Air blown backwards by the propellers. In hover, the elevons only work because they sit in it. |
| **Setpoint** | A target value a controller tries to reach (position, attitude, rate, torque...). |
| **Attitude** | The aircraft's orientation (which way it points), stored as a quaternion. |
| **Quaternion** | A 4-number representation of a rotation. Unlike Euler angles, it has no singularity at ±90° pitch. |
| **Euler angles** | Roll, pitch, yaw. Easy to read, but break down (gimbal lock) at ±90° pitch, which is exactly where a tailsitter hovers. |
| **PID** | Proportional-Integral-Derivative. The standard feedback control law used in each loop. **P** alone means proportional only. |
| **TECS** | Total Energy Control System. PX4's fixed-wing altitude and airspeed controller. It coordinates throttle and pitch by trading kinetic and potential energy. |
| **EKF2** | Extended Kalman Filter, version 2. PX4's state estimator (attitude, position, velocity, wind). |
| **Beta (β)** | Sideslip angle, the angle between the aircraft's nose and the oncoming air, sideways. |
| **uORB** | PX4's internal publish/subscribe message bus. Every arrow in the diagrams below is a uORB topic. |
| **Topic** | A named uORB message, for example `vehicle_torque_setpoint`. |
| **Module** | An independent PX4 program (for example `mc_rate_control`) that subscribes to and publishes topics. |
| **CA** | Control Allocation. Turning a desired torque and thrust into individual motor and servo commands. Also the prefix of the allocation parameters (`CA_*`). |
| **Effectiveness matrix** | The table that says how much torque and thrust each actuator produces. The allocator inverts it. |
| **ESC** | Electronic Speed Controller. Drives a brushless motor. |
| **PWM** | Pulse-Width Modulation. The analog-style signal used to command servos. |
| **DShot** | A digital protocol for commanding ESCs (motors). |
| **SIH** | Simulation-In-Hardware. PX4's built-in physics simulator. |
| **ROMFS / rc** | Read-Only Memory File System, where PX4's startup scripts live. `rc.*` files are the startup ("run commands") scripts. |
| **`VT_*`, `MC_*`, `FW_*`, `CA_*`** | Parameter prefixes for VTOL, multicopter, fixed-wing, and control-allocation settings. |
| **KM** | A rotor's moment coefficient: reaction torque per unit thrust (`CA_ROTORx_KM`). Sets the small yaw torque from spinning props. |

## 1. Reference frames

**Base frame: the fixed-wing (FW) body frame.** Define FRD on the airplane as it flies
forward:

| Axis | Direction on the aircraft |
|---|---|
| FW +x | Out the nose |
| FW +y | Out the right wing |
| FW +z | Out the belly |

This is the physical airplane frame. Aerodynamics (lift along −z, drag along −x) and the
aircraft's geometry are naturally described here.

**Derived frame: the multicopter (MC) body frame.** Take the FW frame and pitch it 90° so
the nose points up. That gives the frame PX4 uses for hover:

| MC axis | Equals | Direction on the aircraft |
|---|---|---|
| MC +x | FW +z | Out the belly |
| MC +y | FW +y | Out the right wing |
| MC +z | −FW x | Out the tail (motor thrust is along MC −z, i.e. out the nose) |

In hover, with the nose up, MC behaves like a normal multicopter frame: z points down,
thrust points up.

**Why this matters in PX4.** PX4 estimates the tailsitter's attitude in the MC frame, and
every torque and thrust setpoint it publishes is in the MC frame. The FW controllers
convert in and out:

- `_q_mc_to_fw` = Euler(pitch = −90°) (`fw_att_control/FixedwingAttitudeControl.hpp:117`)
- `_q_fw_to_mc` = Euler(pitch = +90°) (`vtol_att_control/tailsitter.h:91`)
- The FW rate controller rotates the gyro rates as `(−ω_z, ω_y, ω_x)` on the way in and
  rotates torque back on the way out (`fw_rate_control/FixedwingRateControl.cpp`).

The practical consequence: **FW roll is MC yaw, and FW yaw is MC roll.** Pitch is the same
axis in both.

## 2. The vehicle: four actuators

The airframe config (`ROMFS/px4fmu_common/init.d/airframes/13200_generic_vtol_tailsitter`)
sets `CA_ROTOR_COUNT 2` and `CA_SV_CS_COUNT 2`, with surface types 5/6 (left/right elevon).
Everything the aircraft does comes from:

- **Two motors**, mounted left and right of center (`CA_ROTOR0_PY −0.2`,
  `CA_ROTOR1_PY 0.2`).
- **Two elevons**, on the trailing edge of each wing.

In the FW base frame, each actuator always produces the same body torque, in every flight
phase:

| Actuator action | Body torque (FW frame) |
|---|---|
| Both elevons the same way (collective) | Pitch |
| Elevons opposite ways (differential) | Roll |
| One motor faster than the other (differential thrust) | Yaw |
| Both motors together (collective thrust) | Thrust along the nose |

What changes between hover and forward flight is how strong each effect is (elevons need
propwash or airspeed) and what that body motion does in the world.

## 3. How it moves

### Hover (nose up)

| Desired world motion | Body action (FW frame) | Actuator |
|---|---|---|
| Climb / descend | Thrust | Both motors together |
| Tip nose toward the belly or back (MC pitch) | Pitch | Collective elevons, in propwash |
| Tilt toward a wingtip (MC roll) | Yaw | Differential thrust |
| Spin about the vertical (MC yaw) | Roll | Differential elevons, in propwash, plus a little motor reaction torque (`CA_ROTORx_KM ±0.05`) |
| Move sideways | Tilt the thrust vector by pitching or tilting, then thrust has a horizontal part | As above |

The motors can't pitch the aircraft (they sit side by side). In hover the elevons only
work because the props blow air over them, so at low throttle there is little pitch or
spin authority. This is the central tailsitter difficulty.

### Forward flight (nose forward, a flying wing)

| Desired motion | Body action (FW frame) | Actuator |
|---|---|---|
| Bank | Roll | Differential elevons |
| Climb / dive | Pitch | Collective elevons |
| Nose left / right | Yaw | Differential thrust, **only if enabled** (see §5) |
| Speed and altitude | Thrust + pitch | Coordinated by TECS |

Turns are banked turns, like any airplane. There is no rudder, and `EKF2_FUSE_BETA 0` is
set because PX4's sideslip model isn't trusted for this vehicle.

### Transition

Transition is purely an attitude manoeuvre: the aircraft pitches over 90° (or back).
`Tailsitter::update_transition_state()` builds a quaternion setpoint that rotates about a
horizontal axis (`_trans_rot_axis`) at `90° / VT_F_TRANS_DUR` per second. The MC
controllers stay in charge during the pitch-over. The switch to FW mode happens when
pitch passes a threshold and, if airspeed is available, airspeed ≥ `VT_ARSP_TRANS`
(`isFrontTransitionCompletedBase()`). Without airspeed, pitch alone completes it.
Back-transition is the reverse rotation plus a throttle blend.

## 4. The control stack, component by component

`ROMFS/px4fmu_common/init.d/rc.vtol_apps` starts both the full multicopter stack and the
full fixed-wing stack, running at the same time, plus a VTOL arbiter that picks between
them.

```
     Mode & mission layer:  commander / navigator / flight_mode_manager
                                  │
            ┌─────────────────────┴──────────────────────┐
     MC STACK (hover)                            FW STACK (forward)
     ① mc_pos_control                            ① fw_lat_lon_control
     ② mc_att_control                            ② fw_att_control
     ③ mc_rate_control                           ③ fw_rate_control
            └─────────────────────┬──────────────────────┘
                     ④ vtol_att_control  (VTOL arbiter)
                                  │
                     ⑤ control_allocator
                                  │
                     ⑥ Output drivers (DShot → ESCs, PWM → servos)
```

Each component below has the same layout: what it does, what it takes in, what it puts
out, and the tailsitter-specific detail.

### Mode and mission layer

- **Modules:** `commander`, `navigator`, `flight_mode_manager`.
- **Does:** Arming, flight mode selection, failsafes, missions, and turning pilot sticks or
  waypoints into position/velocity targets.
- **Tailsitter detail:** `commander` publishes the VTOL state other modules read:
  `is_vtol_tailsitter` and `in_transition_mode` (`Commander.cpp`).

### ① Position and velocity control

- **Modules:** `mc_pos_control` (hover), `fw_lat_lon_control` (forward flight).
- **In:** Position, velocity and heading targets; current position and velocity from EKF2.
- **Out:** An attitude setpoint (`vehicle_attitude_setpoint`) and a thrust demand.
- **How:**
  - `mc_pos_control`: P on position error → PID on velocity error → desired acceleration →
    tilt and thrust → attitude setpoint.
  - `fw_lat_lon_control`: TECS for altitude and airspeed; a lateral guidance law for
    heading and path.
- **Tailsitter detail:** Both run all the time. Their outputs are "virtual" setpoints; the
  arbiter (④) decides which one is used.

### ② Attitude control

- **Modules:** `mc_att_control`, `fw_att_control`.
- **In:** Attitude setpoint; current attitude from EKF2.
- **Out:** A body-rate setpoint (`vehicle_rates_setpoint`): how fast to rotate about each
  axis.
- **How:** A P controller on the quaternion attitude error (gains `MC_ROLL_P`,
  `FW_R_P`, `FW_P_P` and similar).
- **Tailsitter detail:** `fw_att_control` first rotates the attitude from MC frame into FW
  frame (`FixedwingAttitudeControl.cpp:233`).

### ③ Rate control

- **Modules:** `mc_rate_control`, `fw_rate_control`.
- **In:** Body-rate setpoint; measured body rates from the gyro.
- **Out:** A normalized torque setpoint (range −1 to 1 per axis) and a thrust setpoint
  (`vehicle_torque_setpoint`, `vehicle_thrust_setpoint`).
- **How:** PID on the rate error. The FW version scales its gains with airspeed.
- **Tailsitter detail:** `fw_rate_control` rotates the gyro rates into FW frame on the way
  in and the torque back to MC frame on the way out. So **every torque setpoint is in the
  MC frame**, whichever stack produced it.

### ④ VTOL arbiter

- **Module:** `vtol_att_control`, `Tailsitter` class (`vtol_att_control/tailsitter.cpp`).
- **In:** The MC and FW virtual torque/thrust setpoints, plus the requested mode.
- **Out:** The real torque and thrust setpoints, in two instances:
  - **Instance 0 → motors.**
  - **Instance 1 → control surfaces (elevons).**
- **How:**
  - A state machine with four states: MC, TRANSITION_FRONT, FW, TRANSITION_BACK
    (`update_vtol_state()`).
  - `fill_actuator_outputs()` routes the setpoints:
    - **Motors:** in hover and transition, MC torque and thrust pass straight through. In
      FW, thrust comes from the FW controller; motor torque is zero unless
      differential-thrust bits in `VT_FW_DIFTHR_EN` are set.
    - **Elevons:** always get the FW torque setpoint, even in hover, unless
      `VT_ELEV_MC_LOCK` is set. That's how the elevons work in propwash during hover: the
      FW rate controller keeps running and drives the elevons, while the MC controller
      drives the motors.
  - During transitions, `update_transition_state()` overrides the attitude setpoint sent
    to `mc_att_control`.

### ⑤ Control allocation

- **Module:** `control_allocator`, with `ActuatorEffectivenessTailsitterVTOL`
  (`CA_AIRFRAME 4`).
- **In:** Torque and thrust setpoints (instances 0 and 1).
- **Out:** Individual motor commands (`actuator_motors`) and servo commands
  (`actuator_servos`).
- **How:** Two separate small least-squares problems, one per effectiveness matrix:
  - **Motor matrix:** differential thrust → MC roll (= FW yaw); `KM` → a small MC yaw.
  - **Elevon matrix:** `CA_SV_CS0_TRQ_P 0.5 / TRQ_Y 0.5` and `CS1_TRQ_P 0.5 / TRQ_Y −0.5`.
    Same sign for pitch, opposite sign for MC yaw (= FW roll).
- **Tailsitter detail:** In forward flight, `updateMotorMasks()` swaps the motors'
  "vertical" and "longitudinal" bitmasks so that "up" thrust becomes "forward" thrust.

### ⑥ Output drivers

- **Does:** Sends the allocator's commands to hardware: DShot to the ESCs (motors), PWM to
  the elevon servos.
- On the MicoAir743v2-AIO: motors on M1/M2 (DShot), servos on M5/M6 (PWM).

## 5. Yaw authority in forward flight

**Hover:** spin about the vertical (MC yaw = FW roll) comes from differential elevons in
propwash. Works as long as the motors are spinning.

**Forward flight:** turning the nose left/right (FW yaw = MC roll) can only come from
differential thrust, because the motors sit at ±y and there is no rudder. In
`fill_actuator_outputs()`, FW mode:

```cpp
if (_param_vt_fw_difthr_en.get() & YAW_BIT) {
    _torque_setpoint_0->xyz[0] = _vehicle_torque_setpoint_virtual_fw->xyz[0] * _param_vt_fw_difthr_s_y.get();
}
```

(`xyz[0]` is MC roll, which is FW yaw after `fw_rate_control`'s rotation.)

If the yaw bit is clear (the default, and the generic tailsitter airframe doesn't set it),
the motor torque is zeroed in FW mode and the FW yaw controller's output is thrown away.
Yaw is then uncontrolled: the aircraft weathervanes into the wind like a normal flying
wing. `FW_RLL_TO_YAW_FF` is applied but its result is also discarded.

That's normal for a rudderless flying wing: sweep and wingtips give natural yaw
stability. Whether the CA320T needs differential-thrust yaw for clean turns is an open
question; the creator's ArduPilot parameters may show what they chose.

Options:

- Set the `VT_FW_DIFTHR_EN` yaw bit and tune `VT_FW_DIFTHR_S_Y` in the stock stack. Costs
  some thrust efficiency and couples yaw into airspeed.
- In a custom controller, keep differential thrust in the effectiveness model all the
  time (authority ≈ `(T_left − T_right) · arm`). This removes the on/off bit.

## 6. Where a custom module plugs in

`control_allocator` (⑤) only needs torque and thrust setpoints, in MC frame and
normalized. So any of the layers above it can be replaced:

| Option | Replace | Keep | Effort |
|---|---|---|---|
| A | Rate loops (③) | Arbiter, allocator, everything above | Smallest |
| B | Rate + attitude + arbiter (②③④), as one unified controller | Position control (①), allocator (⑤) | Medium-large. This project's plan: see [scope.md](scope.md) |
| C | Everything down to the actuators, including allocation (⑤) | Mode layer | Largest. Only worth it for nonlinear allocation (e.g. propwash-dependent elevon effectiveness) |

The stock design's two weaknesses, and where a custom controller can do better:

1. The hover/FW split means two separate tuning sets and a hard switch between them.
2. Elevon effectiveness is treated as constant, though it really scales with propwash and
   airspeed.

A single controller in the FW base frame (§1), with an effectiveness model scheduled on
throttle and airspeed, addresses both. It converts to the MC frame only once, at the
output to the allocator.

## Relevant files

- `ROMFS/px4fmu_common/init.d/airframes/13200_generic_vtol_tailsitter`: airframe config
- `ROMFS/px4fmu_common/init.d/rc.vtol_apps`: which modules start
- `src/modules/vtol_att_control/tailsitter.cpp`: tailsitter state machine and arbitration
- `src/modules/control_allocator/VehicleActuatorEffectiveness/ActuatorEffectivenessTailsitterVTOL.cpp`: allocation
- `src/modules/fw_att_control/FixedwingAttitudeControl.cpp`, `src/modules/fw_rate_control/FixedwingRateControl.cpp`: FW controllers with tailsitter frame handling
