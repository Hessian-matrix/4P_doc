# First Power-On

This page helps first-time RoboBaton 4P users complete pre-power-on checks, log in to the X5, confirm the minimal system state, and choose the non-ROS or ROS2 path in [Quick Start](../quick-start.md). For deployment, upgrade, and rollback details see [Deployment, Upgrade, and Rollback](../development/deployment-and-upgrade.md); for complete troubleshooting see [Troubleshooting](../troubleshooting.md).

## 1. Pre-Power-On Checks

Power, camera cables, UART, and thermal boundaries are governed by [Hardware Connection and Safety](hardware-and-safety.md). Before powering on, confirm:

- Camera FPC/coaxial cables are connected with power off; camera/FPC/coaxial cables do not support hot-plug and must be disconnected from power before plug/unplug.
- V2 rated input range, USB-C power role, full-load current, and fan thresholds are pending confirmation. Use only a power supply and system confirmed for V2 by product support; do not inherit V1 `12V ~ 24V`/`600 mA` claims.
- Keep heatsink, fan, and airflow clear; V1 fan/LED boot patterns are not V2 readiness criteria.
- V2 UART1/UART7 have 5 pins and retain `3.3V` logic; DEBUG_UART retains `1.8V`, `921600` baud. Use official V2 labeling for complete pin order and power-pin function; leave generic USB-UART VCC disconnected and wire with power off after checking common ground.
- V1 UART `500 mA`/hot-plug acceptance is not a V2 rating or hot-plug promise.

## 2. Connect and Power On

Confirm V2 power, harnesses, and actual pinout first, then complete camera, power, network, and optional debug wiring with power off. Check actual system status after power-on rather than infer readiness from V1 LED/fan images. Do not hot-plug camera harnesses, stop or reconfigure `cam-service`, or start multiple camera applications together.

## 3. Network and Login

Wired Ethernet is recommended for first login. To configure the on-board Wi-Fi as an AP hotspot or connect to a router, see [Wi-Fi Configuration](wifi-configuration.md); switching Wi-Fi mode resets `wlan0`, so do not rely on the same Wi-Fi SSH session to complete the switch.

V2 retains factory address `192.168.1.12/24` and the `root` account/password. Network configuration continues to use `/etc/network/interfaces`. These are public factory defaults, not experiment-device addresses or credentials.

| Item | Factory default |
|---|---|
| IP | `192.168.1.12` |
| User | `root` |
| Password | `root` |


### Configure the Host Ethernet

The device factory address is `192.168.1.12/24`. When connecting directly to the device or through an isolated switch, the host Ethernet interface needs an unused address inside `192.168.1.0/24`, e.g. `192.168.1.100/24`. Do not set the host address to `192.168.1.12`, and do not use an address already occupied by another device on that network; direct or isolated networks do not need gateway or DNS. If the host already has another active interface or route occupying `192.168.1.0/24`, resolve the route conflict before testing.

Linux temporary configuration example:

```bash
ETHERNET_IFACE=enp1s0  # change to the actual host Ethernet interface
ip link
sudo ip addr add 192.168.1.100/24 dev ${ETHERNET_IFACE}
sudo ip link set ${ETHERNET_IFACE} up
ping -c 4 192.168.1.12
```

The `ip addr add` setting is a temporary address that disappears after reboot or network-service restart; if the address is already configured on the interface, do not add it again.

Windows GUI configuration:

- Settings -> Network & Internet -> Ethernet -> IP assignment -> Edit -> Manual -> IPv4.
- Set IP to `192.168.1.100`, subnet mask to `255.255.255.0`; leave gateway/DNS empty on direct or isolated networks.
- Run `ping 192.168.1.12` in PowerShell or cmd to verify connectivity.

### Change the Device IP Address

To adjust the device IP, first SSH into the device using the current IP, then modify the system network configuration:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh root@${X5_IP}
```

After login, back up the current configuration first:

```bash
cp -a /etc/network/interfaces /etc/network/interfaces.bak
```

Edit the network configuration:

```bash
vi /etc/network/interfaces
```

Modify `address` and `gateway` in the corresponding existing interface configuration block. Unless the deployment explicitly requires changes, keep the interface name and other settings. Before saving, confirm the new IP and gateway are compatible with the host routes and that the new IP is not occupied by another device.

Reboot for the configuration to take effect:

```bash
reboot
```

The current SSH session drops during reboot, which is expected. After the device boots, SSH back in with the new IP.

If the new configuration makes the network unreachable, enter the system through the confirmed `1.8V` DEBUG_UART recovery path, restore the backup, and reboot:

```bash
cp -a /etc/network/interfaces.bak /etc/network/interfaces
reboot
```

### Log In and Change the Factory Password

After configuring the network, log in from the host:

```bash
ssh root@192.168.1.12
```

After the first SSH login you can change the password:

```bash
passwd
```

`passwd` is an interactive command; enter the new password as prompted. It is recommended to change the root password only in the final production process and keep the factory password during testing.

If the user has changed the IP and needs to enter the system through the debug port to check the address, only DEBUG_UART can be used: `1.8V` logic, debug terminal baud rate `921600`, board TX to adapter RX, board RX to adapter TX, with common ground. Do not use a `3.3V` or `5V` USB-UART on DEBUG_UART.

```{note}
The V2 system image has not been released; do not recover V2 using a V1 image. See [System Flashing](../ops/system-flashing.md) for release status. Official flashing overwrites on-board eMMC and user data.
```

## 4. Minimal System Check

After logging into the X5, run:

```bash
hostname
date
df -h /
pgrep -a cam-service
```

Expect `hostname`, `date`, and root filesystem space to return normally, and the `cam-service` process to be visible. If `cam-service` is missing or abnormal, collect symptoms first per [Troubleshooting](../troubleshooting.md); do not treat stopping the service as a routine recovery step.

If the board can reach the Internet, it is recommended to perform NTP sync before starting demos, ROS2 nodes, or other timestamp-sensitive acquisition; see [System Time Synchronization](../time-sync/system-time-sync.md).

## 5. Confirm the Version

Only query the version when the corresponding directory is already deployed; these commands should not start the camera or IMU.

non-ROS `/root/demo`:

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
```

ROS2 `/root/ros2_demo/install`:

```bash
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

Software version queries identify the deployed package and may omit the `v` prefix; see [Release, License, and Support](../release-and-support.md) for current software releases. Documentation revisions follow that page's independent [Documentation Version Policy](../release-and-support.md#documentation-version-policy) and need not equal the software query results.

## 6. Choose non-ROS or ROS2

| Goal | Runtime directory | Next step |
|---|---|---|
| Four-channel RTSP, IMU, UART examples | `/root/demo` | Enter the non-ROS path in [Quick Start](../quick-start.md), or read [non-ROS Demo Usage](../usage/non-ros-demo.md). |
| ROS2 raw/compressed images, CameraInfo, IMU, temperature topics | `/root/ros2_demo/install` | Enter the ROS2 path in [Quick Start](../quick-start.md), or read [ROS2 Demo Usage](../usage/ros2-demo.md). |

Do not mix directories, headers, or `.so` between the two paths. Run only one application that uses camera resources at a time; before switching paths, exit the old application with `Ctrl+C` and keep `cam-service` running.

## 7. Stop the Application

Foreground demos, ROS2 launch, or nodes exit normally with `Ctrl+C`, then confirm the process has ended:

```bash
pgrep -af 'sensor_demo|cam_demo|robobaton_sensors_node' || true
```

## 8. Normal Shutdown

To power off the device, run in the X5 terminal:

```bash
poweroff
```

No need to run `sync` first. Wait for the system to fully exit: the originally blinking green status LED becomes solid and the fan keeps spinning; only after confirming this state, disconnect external power. Do not unplug power directly during application stop or filesystem activity.

## 9. Troubleshooting

Common first-step handling:

| Symptom | First check | Next step |
|---|---|---|
| Cannot confirm the address | Network topology, host subnet, switch or direct link | The default Ethernet IP is `192.168.1.12`; if the user changed the IP, enter the system through DEBUG_UART to check, using a `1.8V` USB-UART adapter. See [Change the Device IP Address](#change-the-device-ip-address). |
| SSH cannot log in | `ping 192.168.1.12` (adjust to the actual board address), SSH error text | See [Troubleshooting](../troubleshooting.md#ssh-cannot-connect). |
| Camera application fails to start | Whether another camera application already holds resources | Exit the old application normally; see [Troubleshooting](../troubleshooting.md#camera-service-or-resource-conflict). |
| A single channel has no image | camera ID, cables, and power state | Check connections with power off; do not hot-plug. |
| UART has no data | UART1/UART7 `3.3V` TX/RX/GND, common ground, adapter VCC disconnected | See [Hardware Connection and Safety](hardware-and-safety.md). |
