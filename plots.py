import glob
import math
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

RPM_TO_RAD_S = 2 * math.pi / 60
KGF_TO_N = 9.80665
MIN_PWM_US = 1060 # minimum PWM at which the motor spins


def quadratic_through_origin(x, c):
    return c * (x ** 2)


def plot_9_2():
    """9.2: extract cT and cM from a pure quadratic thrust/torque fit."""
    plot_dir = "9.2_plots"
    os.makedirs(plot_dir, exist_ok=True)

    for filepath in glob.glob("test_data/*_SWEEP.csv"):
        filename = os.path.splitext(os.path.basename(filepath))[0]
        df = pd.read_csv(filepath)
        shaft_speed = df["Motor Electrical Speed (RPM)"] * RPM_TO_RAD_S
        thrust = -df["Thrust (kgf)"] * KGF_TO_N
        torque = -df["Torque (N·m)"]

        print(filename)

        ct, _ = curve_fit(quadratic_through_origin, shaft_speed, thrust)
        ct = ct[0]
        print("ct:", ct)

        cm, _ = curve_fit(quadratic_through_origin, shaft_speed, torque)
        cm = cm[0]
        print("cm:", cm)

        a_t, b_t, c_t = np.polyfit(shaft_speed, thrust, 2)
        print(f"thrust quadratic diagnostic: a={a_t:.5g}, b={b_t:.5g}, c={c_t:.5g}")

        a_m, b_m, c_m = np.polyfit(shaft_speed, torque, 2)
        print(f"torque quadratic diagnostic: a={a_m:.5g}, b={b_m:.5g}, c={c_m:.5g}")

        x = np.linspace(min(shaft_speed), max(shaft_speed))
        y1 = quadratic_through_origin(x, ct)
        y2 = quadratic_through_origin(x, cm)
        plt.figure()
        plt.plot(shaft_speed, thrust)
        plt.plot(x, y1, label=rf"T={ct:.5g}$\omega^2$")
        plt.xlabel("Shaft Speed (rad/s)")
        plt.ylabel("Thrust (N)")
        plt.title(filename)
        plt.legend()
        plt.savefig(os.path.join(plot_dir, filename + "_thrust.pdf"))
        plt.close()
        plt.figure()
        plt.plot(shaft_speed, torque)
        plt.plot(x, y2, label=rf"M={cm:.5g}$\omega^2$")
        plt.xlabel("Shaft Speed (rad/s)")
        plt.ylabel("Torque (N·m)")
        plt.title(filename)
        plt.legend()
        plt.savefig(os.path.join(plot_dir, filename + "_torque.pdf"))
        plt.close()


def plot_9_3():
    """9.3: extract C_R and omega_b from throttle command vs. steady-state speed."""
    plot_dir = "9.3_plots"
    os.makedirs(plot_dir, exist_ok=True)

    for filepath in glob.glob("test_data/*_SWEEP.csv"):
        filename = os.path.splitext(os.path.basename(filepath))[0]
        df = pd.read_csv(filepath)
        command = df["ESC signal (µs)"].to_numpy()
        speed_ss = df["Motor Electrical Speed (RPM)"].to_numpy() * RPM_TO_RAD_S

        # Drop the dead band: below MIN_PWM_US the motor doesn't spin
        spinning = command >= MIN_PWM_US
        command = command[spinning]
        speed_ss = speed_ss[spinning]

        print(filename)
        print("throttle commands (µs) used:", command)

        c_r, omega_b = np.polyfit(command, speed_ss, 1)
        print(f"C_R: {c_r:.5g} (rad/s)/µs")
        print(f"omega_b: {omega_b:.5g} rad/s  (sigma in µs; extrapolation to sigma=0 is not a physically meaningful command, so a large negative value here is expected, not an error)")

        x = np.linspace(command.min(), command.max())
        y = c_r * x + omega_b
        plt.figure()
        plt.plot(command, speed_ss, "o", label="steady-state data")
        plt.plot(x, y, label=rf"$\omega$={c_r:.5g}$\sigma$+({omega_b:.5g})")
        plt.xlabel("Throttle Command (µs)")
        plt.ylabel("Steady-State Shaft Speed (rad/s)")
        plt.title(filename)
        plt.legend()
        plt.savefig(os.path.join(plot_dir, filename + "_throttle.pdf"))
        plt.close()


def plot_9_4():
    """9.4: step response of shaft speed vs. time, extracting T_m."""
    plot_dir = "9.4_plots"
    os.makedirs(plot_dir, exist_ok=True)

    for filepath in glob.glob("test_data/*_STEP.csv"):
        filename = os.path.splitext(os.path.basename(filepath))[0]
        df = pd.read_csv(filepath)

        time = df["Time (s)"].to_numpy()
        command = df["ESC signal (µs)"].to_numpy()
        speed = df["Motor Electrical Speed (RPM)"].to_numpy() * RPM_TO_RAD_S

        segment_id = np.cumsum(np.concatenate(([True], command[1:] != command[:-1])))

        # "One commanded omega_ss": the first step up from rest to a spinning
        # command level.
        rest_segment = segment_id[0]
        step_segment = None
        for seg in np.unique(segment_id):
            if seg == rest_segment:
                continue
            if command[segment_id == seg][0] >= MIN_PWM_US:
                step_segment = seg
                break
        if step_segment is None:
            continue

        rest_mask = segment_id == rest_segment
        step_mask = segment_id == step_segment

        omega_0 = speed[rest_mask][-1]
        omega_ss = speed[step_mask][-1]
        threshold = omega_0 + 0.632 * (omega_ss - omega_0)

        t_step = time[step_mask]
        omega_step = speed[step_mask]
        t0 = t_step[0]

        crossed = omega_step >= threshold
        crossing_idx = np.argmax(crossed)
        if crossing_idx == 0:
            t_m = t_step[0] - t0
        else:
            t_prev, t_curr = t_step[crossing_idx - 1], t_step[crossing_idx]
            w_prev, w_curr = omega_step[crossing_idx - 1], omega_step[crossing_idx]
            frac = (threshold - w_prev) / (w_curr - w_prev)
            t_m = (t_prev + frac * (t_curr - t_prev)) - t0

        print(filename)
        print(f"omega_0: {omega_0:.4g} rad/s, omega_ss: {omega_ss:.4g} rad/s")
        print(f"T_m: {t_m:.4g} s")

        plt.figure()
        plt.plot(t_step - t0, omega_step, "-", label="measured")
        plt.axhline(omega_ss, linestyle="--", color="gray", label=r"$\omega_{ss}$")
        plt.axhline(threshold, linestyle=":", color="red", label=r"$\omega_0+0.632(\omega_{ss}-\omega_0)$")
        plt.axvline(t_m, linestyle=":", color="red")
        plt.xlabel("Time since step (s)")
        plt.ylabel("Shaft Speed (rad/s)")
        plt.title(f"{filename}: step to {command[step_mask][0]:.0f} µs, T_m={t_m:.3g} s")
        plt.legend()
        plt.savefig(os.path.join(plot_dir, filename + "_step_response.pdf"))
        plt.close()


def plot_9_5():
    """9.5: compute P_mech, P_elec, eta per Equations (3)-(5); plot eta vs. shaft speed."""
    plot_dir = "9.5_plots"
    os.makedirs(plot_dir, exist_ok=True)

    for filepath in glob.glob("test_data/*_SWEEP.csv"):
        filename = os.path.splitext(os.path.basename(filepath))[0]
        df = pd.read_csv(filepath)

        shaft_speed = df["Motor Electrical Speed (RPM)"] * RPM_TO_RAD_S
        torque = -df["Torque (N·m)"]

        p_mech = torque * shaft_speed
        p_elec = df["Voltage (V)"] * df["Current (A)"]
        eta = p_mech / p_elec

        print(filename)
        print(f"eta range: {eta.min():.3g} to {eta.max():.3g}")
        if eta.max() > 1:
            print("WARNING: eta exceeds 1 -- check for a unit error (RPM vs rad/s) in Equation (3)")

        plt.figure()
        plt.plot(shaft_speed, eta, "-")
        plt.xlabel("Shaft Speed (rad/s)")
        plt.ylabel(r"Efficiency $\eta$")
        plt.title(filename)
        plt.savefig(os.path.join(plot_dir, filename + "_efficiency.pdf"))
        plt.close()


def plot_report_figures():
    plot_dir = "report_plots"
    os.makedirs(plot_dir, exist_ok=True)

    configs = sorted(
        os.path.basename(f).replace("_SWEEP.csv", "")
        for f in glob.glob("test_data/*_SWEEP.csv")
    )

    for config in configs:
        sweep = pd.read_csv(f"test_data/{config}_SWEEP.csv")
        step = pd.read_csv(f"test_data/{config}_STEP.csv")

        pwm = sweep["ESC signal (µs)"].to_numpy()
        rpm = sweep["Motor Electrical Speed (RPM)"].to_numpy()
        shaft_speed = rpm * RPM_TO_RAD_S
        thrust = -sweep["Thrust (kgf)"].to_numpy() * KGF_TO_N
        torque = -sweep["Torque (N·m)"].to_numpy()
        p_mech = torque * shaft_speed
        p_elec = (sweep["Voltage (V)"] * sweep["Current (A)"]).to_numpy()
        eta = p_mech / p_elec

        spinning = pwm >= MIN_PWM_US
        c_r, omega_b = np.polyfit(pwm[spinning], shaft_speed[spinning], 1)
        ct, _ = curve_fit(quadratic_through_origin, shaft_speed, thrust)
        ct = ct[0]
        cm, _ = curve_fit(quadratic_through_origin, shaft_speed, torque)
        cm = cm[0]

        time = step["Time (s)"].to_numpy()
        command = step["ESC signal (µs)"].to_numpy()
        rpm_step_full = step["Motor Electrical Speed (RPM)"].to_numpy()
        segment_id = np.cumsum(np.concatenate(([True], command[1:] != command[:-1])))
        rest_segment = segment_id[0]
        step_segment = None
        for seg in np.unique(segment_id):
            if seg == rest_segment:
                continue
            if command[segment_id == seg][0] >= MIN_PWM_US:
                step_segment = seg
                break
        rest_mask = segment_id == rest_segment
        step_mask = segment_id == step_segment
        omega_0 = rpm_step_full[rest_mask][-1]
        omega_ss = rpm_step_full[step_mask][-1]
        threshold = omega_0 + 0.632 * (omega_ss - omega_0)
        t_step = time[step_mask]
        rpm_step = rpm_step_full[step_mask]
        t0 = t_step[0]
        crossing_idx = np.argmax(rpm_step >= threshold)
        if crossing_idx == 0:
            t_m = t_step[0] - t0
        else:
            t_prev, t_curr = t_step[crossing_idx - 1], t_step[crossing_idx]
            w_prev, w_curr = rpm_step[crossing_idx - 1], rpm_step[crossing_idx]
            frac = (threshold - w_prev) / (w_curr - w_prev)
            t_m = (t_prev + frac * (t_curr - t_prev)) - t0

        print(config)
        print(f"C_R: {c_r:.5g} rad/s per µs, omega_b: {omega_b:.5g} rad/s")
        print(f"cT: {ct:.5g}, cM: {cm:.5g}")
        print(f"T_m: {t_m:.4g} s")

        fig, axes = plt.subplots(2, 3, figsize=(15, 8))

        ax = axes[0, 0]
        ax.plot(pwm[spinning], rpm[spinning], "o", label="data")
        pwm_line = np.linspace(pwm[spinning].min(), pwm[spinning].max())
        ax.plot(pwm_line, (c_r * pwm_line + omega_b) / RPM_TO_RAD_S, label="fit")
        ax.set_xlabel("PWM (µs)")
        ax.set_ylabel("RPM")
        ax.set_title("RPM vs. PWM")
        ax.legend()

        ax = axes[0, 1]
        ax.plot(pwm, thrust, "-")
        ax.set_xlabel("PWM (µs)")
        ax.set_ylabel("Thrust (N)")
        ax.set_title("Thrust vs. PWM")

        ax = axes[0, 2]
        ax.plot(rpm, eta, "-")
        ax.set_xlabel("RPM")
        ax.set_ylabel(r"Efficiency $\eta$")
        ax.set_title("Efficiency vs. RPM")

        rpm_line = np.linspace(rpm.min(), rpm.max())
        ax = axes[1, 0]
        ax.plot(rpm, thrust, "o", label="data")
        ax.plot(rpm_line, quadratic_through_origin(rpm_line * RPM_TO_RAD_S, ct), label=rf"$c_T$={ct:.3g}")
        ax.set_xlabel("RPM")
        ax.set_ylabel("Thrust (N)")
        ax.set_title("Thrust vs. RPM")
        ax.legend()

        ax = axes[1, 1]
        ax.plot(rpm, torque, "o", label="data")
        ax.plot(rpm_line, quadratic_through_origin(rpm_line * RPM_TO_RAD_S, cm), label=rf"$c_M$={cm:.3g}")
        ax.set_xlabel("RPM")
        ax.set_ylabel("Torque (N·m)")
        ax.set_title("Torque vs. RPM")
        ax.legend()

        ax = axes[1, 2]
        ax.plot(t_step - t0, rpm_step, "-", label="measured")
        ax.axhline(omega_ss, linestyle="--", color="gray", label=r"$\omega_{ss}$")
        ax.axhline(threshold, linestyle=":", color="red", label="63.2% threshold")
        ax.axvline(t_m, linestyle=":", color="red")
        ax.set_xlabel("Time since step (s)")
        ax.set_ylabel("RPM")
        ax.set_title(f"Step Response, T_m={t_m:.3g} s")
        ax.legend()

        fig.suptitle(config)
        fig.tight_layout()
        fig.savefig(os.path.join(plot_dir, f"{config}.pdf"))
        plt.close(fig)


if __name__ == "__main__":
    plot_9_2()
    plot_9_3()
    plot_9_4()
    plot_9_5()
    plot_report_figures()
