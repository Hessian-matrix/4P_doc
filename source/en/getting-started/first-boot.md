# First Power-On

This page helps first-time RoboBaton 4P users complete pre-power-on checks, log in to the X5, confirm the minimal system state, and choose the non-ROS or ROS2 path in [Quick Start](../quick-start.md). For deployment, upgrade, and rollback details see [Deployment, Upgrade, and Rollback](../development/deployment-and-upgrade.md); for complete troubleshooting see [Troubleshooting](../troubleshooting.md).

## 1. Pre-Power-On Checks

Power, camera cables, UART, and thermal boundaries are governed by [Hardware Connection and Safety](hardware-and-safety.md). Before powering on, confirm:

- Camera FPC/coaxial cables are connected with power off; camera/FPC/coaxial cables do not support hot-plug and must be disconnected from power before plug/unplug.
- The main board input range is DC `12V ~ 24V` (3S-6S), supply current recommended no less than `600 mA`; the bundled adapter is `12V`, which does not mean the board only supports 12V.
- Heatsink, fan, and airflow are unobstructed; the fan starts at power-on, stops after system startup completes, then the fan thermal control starts when CPU temperature `> 55°C` and stops when temperature drops below `< 50°C`.
- If using UART1/UART7, connect only matching `3.3V`-level TX/RX and common GND; generic USB-UART adapters leave VCC disconnected by default.
- The two 3.3V power pins of UART1/UART7 have a combined rated boundary of `500 mA` for powering peripherals; above that use an independent supply, keep common ground, and prevent reverse-feeding the board 3.3V rail.
- DEBUG_UART is only for the system console/debug and must use a `1.8V` USB-UART adapter; do not connect `3.3V` or `5V` logic to DEBUG_UART.

## 2. Connect and Power On

With power off, complete the camera, power, network, and optional UART debug cable connections, then power on using the bundled `12V` adapter and wait for system startup. If using another input power supply, it must meet the input range and power boundary published on the hardware page. At power-on the fan starts and the outer green LED stays solid (first-batch boards are green; later boards were changed to a red LED for better distinction); after system startup completes, the fan stops and the inner green LED blinks. During startup, do not plug/unplug camera FPC/coaxial cables, do not stop or reconfigure `cam-service`, and do not start multiple applications that use camera resources at the same time.

## 3. Network and Login

Wired Ethernet is recommended for first login. To configure the on-board Wi-Fi as an AP hotspot or connect to a router, see [Wi-Fi Configuration](wifi-configuration.md); switching Wi-Fi mode resets `wlan0`, so do not rely on the same Wi-Fi SSH session to complete the switch.

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
If the system cannot boot or needs factory restore, re-flash the factory system image to recover. Flashing overwrites the on-board eMMC and erases all user data; see [System Flashing](../ops/system-flashing.md) for image acquisition, flashing steps, and cautions.
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

The latest official release baseline is docs `v1.3.0`, non-ROS `v1.3.0`, ROS2/package `v1.3.0`; file and package version queries may show `1.3.0` without the `v` prefix.

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
