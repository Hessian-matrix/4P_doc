# First Power-On

This page helps first-time RoboBaton 4P users complete pre-power-on checks, view sensor data and record through the browser after power-on, and log in to the X5 when needed. The release system is pre-flashed on the board and starts `sensor_demo` automatically at boot; normal preview and recording do not require a manual launch. For CLI or ROS2 use, continue to [Quick Start](../quick-start.md). See [Deployment, Upgrade, and Rollback](../development/deployment-and-upgrade.md) for maintenance and [Troubleshooting](../troubleshooting.md) for error isolation.

## 1. Pre-Power-On Checks

Power, camera cables, UART, and thermal boundaries are governed by [Hardware Connection and Safety](hardware-and-safety.md); see the {ref}`Interface Wiring Diagram <wiring-diagram>` for interface locations, pin order, and mating connections. Before powering on, confirm:

- Camera FPC/coaxial cables are connected with power off; camera/FPC/coaxial cables do not support hot-plug and must be disconnected from power before plug/unplug.
- The confirmed XT30 input range is `9~27V DC`: check physical polarity first. USB-C is a data interface, not an assumed power input. Full-load current, the USB-C power role, and fan thresholds still await confirmation; use only a power supply and system confirmed compatible by product support.
- The fan is connected at the factory. Keep heatsink, fan, and airflow clear; check readiness from actual system status.
- UART1 uses GH1.25 4-pin and UART7 GH1.25 5-pin connectors, retaining `3.3V` logic. DEBUG_UART uses SH1.0 3-pin, `1.8V`, `921600` baud. Check pin order against the diagram and physical labeling; leave generic USB-UART VCC disconnected and wire with power off after checking common ground.
- UART power-pin ratings and hot-plug conditions await confirmation. Wire with power off by default; do not power peripherals or back-feed power.

## 2. Connect and Power On

Confirm V2 power, harnesses, and actual pinout first, then complete camera, power, network, and optional debug wiring with power off. Check readiness from actual system status after power-on. Do not hot-plug camera harnesses, stop or reconfigure `cam-service`, or start multiple camera applications together.

Boards ship with the release system pre-flashed and `sensor_demo` boot autostart configured. Once the system, network, and sensors are ready, use the browser entry below; normal use does not require reflashing, installing the runtime, or running autostart `enable` again. The default startup acquires and previews data without recording automatically; start recording from the page when needed. Do not manually launch a second `sensor_demo`, `cam_demo`, or ROS2 camera node.

The current matching image preinstalls `/root/demo`, `/root/ros2_demo/install`, and `/opt/ros/humble`. ROS2 does not autostart or need first-boot extraction. Boot defaults are four cameras at `1280x1088@30fps`, IMU `800Hz`, Web on, RTSP off, and observer/host timestamps. See [System Flashing](../ops/system-flashing.md) for image contents and public download status.

## 3. Network and Login

The matching new image defaults to the `RoboBaton-4P` WPA2 hotspot on 5 GHz channel `36` (20 MHz, non-DFS) when no Wi-Fi state exists. Connect a 5 GHz-capable computer or phone using the hotspot password supplied with the device, obtain an address automatically, then open `http://192.168.5.1/` for preview and recording. AP supports manual selection of 2.4 GHz or 5 GHz, one band at a time, without automatic fallback; if the client or regulations do not permit the current band, reconfigure through wired Ethernet or the debug console. Normal reboots preserve existing AP/STA, band/channel, or manual disable choices, while reflashing system restores the new image's 5 GHz default. Older firmware may lack this policy; this guidance does not establish replacement of published downloads. See {ref}`Factory Hotspot and Quick Connection <wifi-factory-hotspot>` for the full channel list, regulatory limits, the `12`-hour DHCP lease, configuration, and recovery. Switching Wi-Fi mode disconnects the same Wi-Fi SSH session, so do not rely on it to complete the change.

For a direct USB computer connection, the matching new image defaults to a USB3 CDC NCM NIC at factory board address `192.168.7.2/24`; set the computer to obtain an address automatically. The computer must support CDC NCM; Windows compatibility is not certified. RNDIS/ECM remain manually selectable, without automatic fallback. Older firmware may still default to RNDIS or lack NCM; check `switch_usb_gadget --help` first. Installer updates preserve an existing boot choice. USB addressing is independent of wired Ethernet. It is not a default USB camera or storage drive. To change the address, see [Change the Device IP Address](#change-the-device-ip-address) below; for Host/Device and function switching, see [USB Interface Functions and Switching Limits](../usage/usb-gadget-switch.md). Do not switch over the only USB management path.

V2 retains factory wired Ethernet address `192.168.1.12/24` and the `root` account/password. Wired Ethernet configuration continues to use `/etc/network/interfaces`. These are public factory defaults, not experiment-device addresses or credentials.

| Item | Factory default |
|---|---|
| Wired Ethernet IP | `192.168.1.12` |
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

(first-boot-web)=

### View Sensors and Record in the Browser

After establishing connectivity, open the board HTTP address for that connection: `http://192.168.5.1/` for the factory hotspot, `http://192.168.1.12/` for wired Ethernet, or `http://192.168.7.2/` for the factory USB NIC. Use the actual board address after changing it or when using STA. HTTP defaults to port `80`; use the actual port if explicitly changed. Page assets are embedded in the application, requiring no Internet, plugin, or camera/microphone permissions; online documentation links need Internet access. **No prior SSH login or manual application launch is required.**

**Preview on a phone or tablet**:

1. Connect directly to the board's factory hotspot, or connect the board to the LAN and the phone/tablet to Wi-Fi on the same router. The latter does not require Wi-Fi on the board, but the devices must be able to reach each other; guest networks or AP client isolation may block access.
2. On the board's factory hotspot, open `http://192.168.5.1/`. Over the LAN, use the board's current LAN address; its factory Ethernet address is `http://192.168.1.12/`. Use the actual address/port if changed. No dedicated app or SSH login is required.
3. Wait for four-camera and IMU updates. Narrow screens stack panels vertically for scrolling; landscape provides a wider preview. If autoplay is blocked, tap “Click to play” on the image.

Mobile preview is for viewing the interface, not recording on the phone or proving synchronization/performance. Smooth playback depends on wireless networking, device performance, and browser WebRTC/H.264 decoding support; smooth four-stream playback is not guaranteed on every phone or browser. Recording still runs on the board, and closing the page does not stop it. Use only a trusted LAN; do not expose the unauthenticated page to the Internet.

```{figure} ../_static/4P_overview_en.png
:alt: RoboBaton 4P browser device overview showing CAM1 through CAM4, attitude, raw six-axis telemetry, and recording controls
:width: 100%
:align: center

Power-on Web interface example (English UI): four cameras, attitude, raw six-axis telemetry, and recording share one homepage; use the top-right `CH` / `EN` toggle to switch language. Images, values, and recording state reflect the current device.
```

1. **View sensor data**: confirm that CAM1–CAM4 images keep updating, and inspect attitude, acceleration, angular rate, and temperature. Attitude is a browser six-axis fusion preview, not proof of absolute heading or hardware synchronization.
2. **Choose recording options**: in Recording and Saving, select `ROS bag` or `MP4 · Four-channel H.264`, then Runtime / eMMC or TF Card. TF must be mounted; a missing card does not fall back to eMMC. Web recording uses fixed directories, without custom paths.
3. **Start recording**: click Start Recording, wait for device confirmation, and observe actual state, device-timed duration, and written size. If state is not ready or an error appears, inspect the message instead of clicking repeatedly.
4. **Stop and check the result**: click Stop Recording, wait for draining and finalization, then expand Recording Details and Usage to inspect the output path and final result. Only `published_complete`, `data_complete=true`, and `cleanup_complete=true` indicate a completely published session; acknowledgment of a stop request does not mean the files are finished. Paths are on the board, not in the browser's download folder.

Selecting Runtime / eMMC in Web uses the fixed absolute root `/root/demo/save_data`, independent of the executable location: bag files use `/root/demo/save_data/session-<id>.bag`, and MP4 sessions use `/root/demo/save_data/session-<id>`. TF storage remains `/mnt/sdcard/recordings`. The device generates session names. Closing or refreshing the page or losing the network **does not stop device recording**; reopen the page and use Query Status to confirm. Stopping recording leaves cameras, IMU, and preview running; switching applications also requires a graceful stop of the whole `sensor_demo`. See [Web Recording Control](../usage/non-ros-demo.md#web-recording-control) and [Saving Data](../usage/save-data-guide.md) for details. For recording that requires UTC, confirm synchronization per [NTP Sync](../time-sync/ntp-sync.md) before starting.

```{warning}
The page has no authentication: anyone who can reach the device can view sensors and start/stop recording. Use only a trusted isolated LAN; do not expose it to the Internet or untrusted networks.
```

### Change the Device IP Address

Identify the interface first: USB networking and wired Ethernet have independent addresses and use different configuration methods. Run USB configuration commands in a **root terminal on the board**, not directly in a computer terminal.

#### USB Networking (NCM / RNDIS / ECM)

The matching new image provides the `ip` subcommand; on older firmware, check `switch_usb_gadget --help` for support first. SSH into the board using a currently reachable address, then open interactive configuration:

```bash
switch_usb_gadget ip
```

Press Enter at the address and DHCP prompts to accept the displayed defaults: saved settings if present, or factory settings on first use. At `save / apply / cancel [save]`, Enter means **save only**. Alternatively, save a specified address directly, for example:

```bash
switch_usb_gadget ip --address 192.168.8.2/24
```

Saving alone does not interrupt the current USB link or acquisition. Settings are written to `/etc/4p-usb-network.json`, survive reboot, and are used the next time NCM/RNDIS/ECM starts. This **does not modify `/etc/network/interfaces`**. Avoid subnet conflicts with board Ethernet, Wi-Fi, and existing computer routes.

Immediate application disconnects USB. Stop acquisition normally first and use independent Ethernet or debug UART; do not choose `apply` over the only USB SSH path. For full `--apply`, DHCP range, factory-address reset, status, and computer lease-renewal/reconnection instructions, see {ref}`Change the USB NIC IPv4 Address <usb-network-address>`.

#### Wired Ethernet

To adjust the wired Ethernet IP, first SSH into the device using a currently reachable address, then modify the system network configuration:

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
The supplied release system provides the startup workflow above without reflashing first. If reflashing is needed, download [4P_V2.0.0_image.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/4P_V2.0.0_image.tar.gz); confirm the release archive's SHA-256 and supported hardware with Product Support before flashing. Current firmware supports holding SW1 during power-on or reset, then flashing with XBurn over USB3 Fastboot, without a debug UART connection. See [System Flashing](../ops/system-flashing.md) for the procedure and image/hardware compatibility requirements. Back up data before flashing: official flashing overwrites on-board eMMC and user data and is not a prerequisite for normal power-on use.
```

### Debug-Console Passwordless Login

System images with this feature integrated provide `uart-autologin`. Run as `root`:

```bash
uart-autologin status    # Show the current state
uart-autologin disable   # Require username and password at the next console login
uart-autologin enable    # Enter root without a password at the next console login
```

The matching new implementation defaults to passwordless login. Anyone with DEBUG_UART access can obtain root while enabled; use only in trusted physical environments. The choice is stored in system-partition `/etc/4p/uart-autologin/state`: normal reboot retains it, while reflashing system restores image defaults without importing old userdata policy. Existing sessions, SSH, and UART1/UART7 are unaffected. Older firmware may still use userdata. If the command is missing, contact product support; copying Demo scripts alone does not enable the feature.

## 4. Minimal System Check

After logging into the X5, run:

```bash
hostname
date
df -h /
pgrep -a cam-service
```

Expect `hostname`, `date`, and root filesystem space to return normally, and the `cam-service` process to be visible. If `cam-service` is missing or abnormal, collect symptoms first per [Troubleshooting](../troubleshooting.md); do not treat stopping the service as a routine recovery step.

If the board can reach a public or private LAN NTP server, confirm synchronization before recording or other timestamp-sensitive operations; an already running boot preview does not establish clock synchronization. See [NTP Sync](../time-sync/ntp-sync.md). NTP does not require Internet access.

## 5. Confirm the Version

Only query the version when the corresponding directory is already deployed; these commands should not start the camera or IMU.

non-ROS `/root/demo`:

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
```

ROS2 `/root/ros2_demo/install`:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash \
  /root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/robobaton_ros2_env.bash \
  /root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

Even version queries require ROS2 underlay/overlay dependencies. Do not directly run install ELF files from an unconfigured shell. If `libimage_transport.so` or another library is missing, first use the wrapper above rather than copying a single SO from another package.

Software version queries identify the deployed package and may omit the `v` prefix; see [Release, License, and Support](../release-and-support.md) for current software releases. Documentation revisions follow that page's independent [Documentation Version Policy](../release-and-support.md#documentation-version-policy) and need not equal the software query results.

## 6. Choose non-ROS or ROS2

| Goal | Runtime directory | Next step |
|---|---|---|
| Browser preview of four cameras/IMU and recording | Boot-started `/root/demo/sensor_demo` | Use the {ref}`browser entry above <first-boot-web>` directly, without launching another application. |
| Four-channel RTSP, IMU, UART examples | `/root/demo` | Enter the non-ROS path in [Quick Start](../quick-start.md), or read [non-ROS Demo Usage](../usage/non-ros-demo.md). |
| ROS2 raw/compressed images, CameraInfo, IMU, temperature topics | `/root/ros2_demo/install` | Enter the ROS2 path in [Quick Start](../quick-start.md), or read [ROS2 Demo Usage](../usage/ros2-demo.md). |

Do not mix directories, headers, or `.so` between the two paths. Run only one application that uses camera resources at a time. Before switching to another demo or ROS2, stop recording and wait for complete finalization, then gracefully stop the boot-started `sensor_demo` as below. Keep `cam-service` running.

## 7. Stop the Application

The release system's boot-started application runs in the background. Before switching to another camera application, stop recording in the browser and confirm the final result, then run in the X5 SSH terminal:

```bash
cd /root/demo
./start_sensor_demo.sh stop
```

Wait for a successful return. On failure, inspect the message instead of force-killing or starting another instance. This command does not disable next-boot autostart or manage `cam-service`. To restore browser use, run `./start_sensor_demo.sh restart` and check the actual page; see {ref}`Stop, Restart, and Boot Autostart <non-ros-autostart>`. The browser's Stop Recording only stops saving, and closing the page does not exit the application.

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
| Web page does not open or has no live data | Current IP, HTTP `80` (or actual port), media UDP/TCP `8189`, autostart state | Log in and run `/root/demo/start_sensor_demo.sh status`; inspect `/userdata/sensor_demo_autostart.log`. Do not launch duplicates or stop `cam-service`; see [LAN Preview Has No Video or IMU Is Stale](../troubleshooting.md#lan-preview-has-no-video-or-imu-is-stale). |
| SSH cannot log in | `ping 192.168.1.12` (adjust to the actual board address), SSH error text | See [Troubleshooting](../troubleshooting.md#ssh-cannot-connect). |
| Camera application fails to start | Whether another camera application already holds resources | Exit the old application normally; see [Troubleshooting](../troubleshooting.md#camera-service-or-resource-conflict). |
| A single channel has no image | camera ID, cables, and power state | Check connections with power off; do not hot-plug. |
| UART has no data | UART1/UART7 `3.3V` TX/RX/GND, common ground, adapter VCC disconnected | See [Hardware Connection and Safety](hardware-and-safety.md). |
