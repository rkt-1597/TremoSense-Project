<div align="center">

# TremoSense

## Zephyr RTOS Based Tremor Suppression and Motion Stabilization Platform

<table>
<tr>
<td width="42%" align="center">
  <img src="assets/zephyr.png" width="380" alt="Zephyr Logo"/>
</td>
<td width="1%"></td>
<td width="57%" align="center">
  <img src="assets/tremosense.gif" width="100%" alt="TremoSense Demo"/>
</td>
</tr>
</table>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Zephyr_RTOS-6DB33F?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Language-C-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Hardware-XIAO_BLE_SENSE-purple?style=for-the-badge" />
</p>

</div>

---

## ✨ Abstract

TremoSense is a real-time embedded motion stabilization platform built on **Zephyr RTOS** and the **Seeed XIAO nRF52840 Sense**. The system combines inertial sensing, **Extended Kalman Filter (EKF) state estimation, Linear Quadratic Regulator (LQR)** control, and servo actuation to suppress tremor-induced motion. This project aims to assist individuals affected by neurological disorders such as Parkinson's Disease, in which patient generally suffers from tremors in the range of **3 to 7 Hz**.  

An Extended Kalman Filter (EKF) performs motion estimation and noise reduction, while a Linear Quadratic Regulator (LQR)-based controller computes optimal compensatory control signals in real time. These control inputs drive a **two-axis servo-actuated gimbal mechanism** that generates counter-directional motion to attenuate tremor-induced displacement and improve spoon stability during assistive feeding operations, in the Roll & Pitch directions. The control algorithm for this project executes at **1000 Hz** on the nRF52840 using Zephyr RTOS.

---

## 🎯 Objectives

* Real-time acquisition and monitoring of hand motion dynamics
* Identification and characterization of tremor frequency and amplitude
* Generation of active counter-motion for tremor attenuation
* Enhancement of utensil stability during assistive feeding tasks
* Facilitation of future clinician-oriented reporting and patient monitoring capabilities

---

## 🧰 Hardware Configuration

* **Seeed XIAO nRF52840 Sense** for embedded processing and onboard IMU sensing
* **MG995 Servo** for roll-axis stabilization
* **FS90MG Servo** for pitch-axis stabilization

---

## 💻 Software Stack and Development Environment

* **Zephyr RTOS** for embedded firmware architecture and hardware abstraction
* **MATLAB & Simulink** for control-system modeling, simulation, and analytical validation

## Required Libraries and Installation

### Operating System Support

The project development environment has been configured and tested to build on:

* **Ubuntu 22.04 LTS**

### Zephyr RTOS Installation and Setup

The following setup procedure installs the Zephyr RTOS workspace, SDK, ARM toolchain, Python dependencies, and development utilities required for building and flashing the TremoSense firmware.

**1. Install Zephyr RTOS**

Follow the instructions [here](https://docs.zephyrproject.org/latest/develop/getting_started/index.html) till [this section](https://docs.zephyrproject.org/latest/develop/getting_started/index.html#get-zephyr-and-install-python-dependencies)

**2. Installing the Zephyr SDK**

Currently this project uses XIAO BLE Sense board which has nRF52840 SoC onboard it which requires GNU ARM toolchain. To optimize the installation of Zephyr SDK
and reduce disk usage we can install the GNU ARM toolchain specifically, uing:
```bash
west sdk install -t zephyr-arm-eabi
```
Otherwise,
```bash
west sdk install
```
installs all toolchains.

**3. Install the Tremosense Application**

```bash
cd ~/zephyrproject
git clone https://github.com/rkt-1597/TremoSense-Project
cd TremoSense-Project/tremosense-app
```

**4. Build the Tremosense Application**

```bash
west build -b xiao_ble/nrf52840/sense -p always -- -DDTC_OVERLAY_FILE=boards/xiao_ble.overlay -DCONF_FILE=boards/xiao_ble.conf
```

**5. Flash the Tremosense Application**

Now, double-click on the XIAO BLE Sense board and copy the file `zephyr.uf2` to XIAO-SENSE directory; board will reset immediately and start running the application. <username> is your Linux username, which can be found uinsg `whoami` command.
```bash
cp -r ~/zephyrproject/TremoSense-Project/tremosense-app/build/zephyr/zephyr.uf2 /media/<username>/XIAO-SENSE
```
**Note:**
Just after flashing, make sure to hold the board horizontally levelled since it immediately starts calibration processs for the IMU. It will switch on onboard blue LED for 3 seconds before beginning calibration and after calibration, it will 
blink the blue LED for 5 seconds; the obtained offsets will be available on console during this time. Immdiately after this the servos will be activated for tremor cancellation.

---

## 🚀 Future Scope

* Integration of servo dynamics and actuator non-linearities into the control model
* Adaptive or gain-scheduled control for improved tremor suppression across varying user conditions
* Quantitative hardware benchmarking using IMU-based performance metrics
* Prototype miniaturized and ergonomically optimized mechanical design for daily use
* Design of a robust and power efficient battery and power management system for making the prototype portable
* Closed-loop evaluation on varied multi-axis stabilization platforms
---

## MATLAB & Simulink Modelling Results

* ### **Roll Axis Frequency Analysis**

![Roll Frequency Analysis](MATLAB_Simulink/assets/roll_freq_analysis.png)

*Frequency-response analysis of the roll stabilization axis under tremor amplitudes ranging from 2° to 7° indicates that the controller maintains approximately 90% tremor suppression across most of the clinically relevant tremor band (3–7 Hz). For this test, the model was provided a Roll tremor signal with variable frequency sweep and amplitude (representing Roll angle) varying from 2 to 7 with step size of 1 and Pitch and Yaw tremor signals being sine waves of amplitude 8 (i.e. 8° of anglular displacement along that axis) & frequency of 8 Hz; this helps to obtain the frequency analysis of Roll axis taking into account cross-coupling among the axes.*

* ### **Pitch Axis Frequency Analysis**
![Pitch Frequency Analysis](MATLAB_Simulink/assets/pitch_freq_analysis.png)
*Frequency-response analysis of the pitch stabilization axis under tremor amplitudes ranging from 2° to 7° demonstrates stable tremor suppression across most of the clinically relevant tremor band (3–7 Hz) - about 80% tremor suppression. For this test, the model was provided a Pitch tremor signal with variable frequency sweep and amplitude (representing Pitch angle) varying from 2 to 7 with step size of 1 and Roll and Yaw tremor signals being sine waves of amplitude 8 (i.e. 8° of anglular displacement along that axis) & frequency of 8 Hz; this helps to obtain the frequency analysis of Roll axis taking into account cross-coupling among the axes.*

* ### **EKF vs Input**
![EKF vs Input](MATLAB_Simulink/assets/ekf_vs_ip.png)
*Time-domain comparison between simulated 8 degree (across roll and pitch axis separately) and 8 Hz tremor input and EKF state estimate reveals the estimator accurately tracks tremor motion with minimal amplitude distortion and phase lag, providing reliable state information for closed-loop control.*


* ### **LQR vs Input**
![LQR vs Input](MATLAB_Simulink/assets/lqr_vs_ip.png)
*Time-domain response of the LQR controller shows the generated control action produces counter-motion that opposes the measured tremor, resulting in significant attenuation of residual motion in the stabilized output.*

## 👥 Project Contributors

<div align="center">

**Prithvi Tambewagh** · **Pawan Shinde** · **Pranshu Kumar**<br>
B.Tech. Electronics and Telecommunication Engineering<br>
Veermata Jijabai Technological Institute (VJTI), Mumbai, India<br>

</div>