# ROB 574 Final Project

3D printed Tailsitter drone. We will be analyzing flight efficiencies and tradeoffs.

## Project Goal

The goal of this project is to design our own control scheme for the CA320T and run it as a custom module within [PX4](https://px4.io). Rather than relying on the stock tailsitter controllers, we are writing our own control loops for this aircraft, building on existing tailsitter control approaches. Our fork of PX4 is included as the [`PX4-Autopilot`](PX4-Autopilot) submodule.

## Airframe Credit

The airframe used in this project is the **CA320T** sub-250g tailsitter, designed by **CarviFPV** of [Carvi Labs](https://carvilabs.com). All credit for the airframe design goes to the original creator.

The creator's GitHub repository, [CarviFPV/CA320T](https://github.com/CarviFPV/CA320T), contains the X-Plane simulator models and ArduPilot parameters, but we could not find the printable model files on GitHub. The STL files in [`CA320T+sub250+Tailsitter+(Ardupilot+_+DJI+o4+Lite)/`](<CA320T+sub250+Tailsitter+(Ardupilot+_+DJI+o4+Lite)/>) were downloaded from the [MakerWorld listing](https://makerworld.com/en/models/2734689). Build instructions are available on the [Carvi Labs website](https://carvilabs.com).
