import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
filelist = ["8_ Prop 10V","8_ Prop 12V","12_ Prop 10V","12_ Prop 12V"]

for filename in filelist:
    df = pd.read_csv(filename + "_Unit_Converted.csv")
    shaft_speed = df["Shaft Speed (rad/s)"]
    thrust = df["Thrust (N)"]
    torque = -df["Torque (N·m)"]

    def func(x,c):
        return c*(x**2)

    print(filename)

    ct, _ = curve_fit(func,shaft_speed,thrust)
    ct = ct[0]
    print("ct:", ct)

    cm, _ = curve_fit(func,shaft_speed,torque)
    cm = cm[0]
    print("cm:", cm)

    a_t, b_t, c_t = np.polyfit(shaft_speed, thrust, 2)
    print(f"thrust quadratic diagnostic: a={a_t:.5g}, b={b_t:.5g}, c={c_t:.5g}")

    a_m, b_m, c_m = np.polyfit(shaft_speed, torque, 2)
    print(f"torque quadratic diagnostic: a={a_m:.5g}, b={b_m:.5g}, c={c_m:.5g}")

    x = np.linspace(min(shaft_speed),max(shaft_speed))
    y1 = func(x,ct)
    y2 = func(x,cm)
    plt.figure()
    plt.plot(shaft_speed, thrust)
    plt.plot(x,y1,label=rf"T={ct:.5g}$\omega^2$")
    plt.xlabel("Shaft Speed (rad/s)")
    plt.ylabel("Thrust (N)")
    plt.title(filename)
    plt.legend()
    plt.savefig(filename + "_thrust.pdf")
    plt.figure()
    plt.plot(shaft_speed, torque)
    plt.plot(x,y2,label=rf"M={cm:.5g}$\omega^2$")
    plt.xlabel("Shaft Speed (rad/s)")
    plt.ylabel("Torque (N·m)")
    plt.title(filename)
    plt.legend()
    plt.savefig(filename + "_torque.pdf")
