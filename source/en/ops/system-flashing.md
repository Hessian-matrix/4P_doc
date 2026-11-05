# System Flashing

(system-flashing)=

```{warning}
Current images support **holding SW1 during power-on/reset to enter Fastboot and flash over USB**, without DEBUG_UART. Flashing may overwrite the on-board eMMC system and user data. Back up data and check the image's hardware compatibility and supplied checksums first. The image download is linked below; this page does not yet provide the release archive's SHA-256. Do not use an unknown or incompatible image.
```

## V2 Image Release Status

| Item | Status |
|---|---|
| V2 factory system image | Built; the booted system and preinstalled applications have been inspected on a flashed device, not full system acceptance |
| Image-package identifier and download | `V2.0.0`: [4P_V2.0.0_image.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/4P_V2.0.0_image.tar.gz); identify image packages separately from software and documentation versions |
| SHA-256 and supported hardware | This page does not yet provide the release archive's SHA-256; confirm the checksum and supported hardware with Product Support before flashing |
| Flashing tool and connection | XBurn; SW1 button + USB 3.0 data cable, without DEBUG_UART |
| Procedure and configuration image | See below; the screenshot path is an example, not a required local directory |

Download the complete image package from the table above. Before flashing, confirm supported hardware and the publisher-provided SHA-256. Contact [Product Support](../release-and-support.md) if compatibility cannot be confirmed, the checksum is unavailable, or the device cannot enter flashing mode.

## Button + USB Flashing

### 1. Prepare the Image and Connection

1. Prepare a Windows computer, XBurn, a USB 3.0 data cable, and a complete image package matching this board. Install the USB driver required by XBurn on the computer.
2. Verify the archive's SHA-256 and extract it completely. If the package includes `SHA256SUMS`, verify that inventory too. Do not select files inside an archive or mix partition files from different image packages.
3. Finish acquisition and recording normally, back up required data, and power the device off. Connect the computer to the board's USB3 port with the data cable; the board still requires its matching power supply.
4. **Hold SW1 before applying power or resetting the board. Keep it held until the computer/XBurn recognizes the Fastboot device, then release it.** No debug-console cable is required. An NCM/RNDIS/ECM network device after normal startup is not a Fastboot flashing device.

### 2. Configure XBurn

The numbered highlights below identify the settings to check in order. The image path is only an example.

```{figure} ../../image/flash_config.png
:alt: XBurn button and USB flashing settings highlighting X5, USB, Fastboot, Emmc, secure, the image directory, USB 3.0, and Start Burn

Button + USB flashing configuration (XBurn v1.2.1 original window layout, 800 × 882)
```

| Number | Setting | Value or action |
|---|---|---|
| 1 | Product Type | `X5` |
| 2 | Link Type | **`USB`** |
| 3 | Download Mode | **`Fastboot`** |
| 4 | Storage | `Emmc` (eMMC) |
| 5 | Firmware Type | `secure` |
| 6 | Image Directories / Browse | Select the fully extracted image directory; if the delivered package uses a `package` subdirectory, select it, not the archive or an individual `.img` |
| 7 | Enable USB 3.0 Mode | **Checked**, for USB 3.0 flashing |
| 8 | Start Burn | Click only after the device is recognized and settings/image directory are correct |

```{warning}
Do not enable `Full eMMC erase` by default. Set partition backup/restore or individual-partition options only as directed by the matching image's delivery instructions. Leaving full erase unchecked does not guarantee that user data survives. Keep power and USB stable during writing; do not disconnect or reset the board.
```

### 3. Flash and Restart

1. Click **Start Burn** and wait for XBurn to report success. A progress bar or some completed partitions do not establish successful flashing of the full package.
2. `Reboot after burning` is checked in the example, so the device restarts automatically after success. If unchecked, restart as prompted by the tool after flashing succeeds. **Do not hold SW1 for normal startup**, or the board will enter Fastboot again.
3. Wait for the system to boot, then check networking, preinstalled applications, and versions per [First Power-On](../getting-started/first-boot.md). Use the image's defaults after reflashing; do not assume old network settings or user data remain.
4. If no device is recognized, check power, USB data cable/port, USB driver, and the order of holding SW1 before power-on. If it still fails, stop writing and contact [Product Support](../release-and-support.md).


## Current Image and Boot Behavior

The current matching image uses Buildroot `2022.08` and Linux `6.1.83-DR-PL5.1_V1.1.2` (AArch64). Identify the actual system with these read-only commands. `/etc/version` identifies the image build, not the Demo software version or a public download-package version:

```bash
cat /etc/version
cat /etc/os-release
uname -r
cat /usr/share/4p-applications/manifest.json
```

| Component | Current image behavior |
|---|---|
| Network and login | Factory Ethernet IP is `192.168.1.12/24`, with account/password `root` / `root`. Use the actual address after changing it; that does not change other devices' factory defaults |
| non-ROS | `/root/demo` is preinstalled and `sensor_demo` starts at boot. Defaults: four cameras at `1280x1088@30fps`, IMU `800Hz`, Web on, RTSP off, no automatic recording, observer/host timestamp pair |
| ROS2 | `/root/ros2_demo/install` and `/opt/ros/humble` are preinstalled without first-boot extraction or automatic acquisition. Use the package environment script and gracefully exit non-ROS before running ROS2 |
| System dependencies | The image supplies Python `3.10.12`, C++/SDK runtime libraries, Wi-Fi, debug-console policy, fan control, and USB management tools. Copying only the two application directories does not supply these components |
| USB | The matching new image candidate defaults to USB3 Device/CDC NCM at the factory. Older firmware may still default to RNDIS or lack NCM; this does not establish that the published download above has changed. Board USB address `192.168.7.2/24` is independent of Ethernet. The computer must support CDC NCM; Windows compatibility is not certified. Select RNDIS/ECM manually if needed, without automatic fallback. See [USB Usage and Switching](../usage/usb-gadget-switch.md) |
| Wi-Fi | The matching new image initializes the `RoboBaton-4P` WPA2 hotspot only without state in system-partition `/etc/4p/wifi`, defaulting to 5 GHz channel `36` (`AP_CHANNEL=36`, 20 MHz, non-DFS) with the same supplied password. Board: `192.168.5.1/24`; DHCP: `192.168.5.2–192.168.5.254`, renewable `12`-hour lease. Connect and open `http://192.168.5.1/`. AP supports selectable 2.4/5 GHz, one band at a time, without automatic fallback; actual driver and regulatory constraints take precedence. Normal reboot preserves AP/STA, band/channel, or disabled choices; reflashing system restores the image's 5 GHz default without reading old userdata configuration. USB DHCP is independent. Older firmware may lack this policy; this does not establish replacement of the published download above or new real-board acceptance. See {ref}`Factory Hotspot and Quick Connection <wifi-factory-hotspot>` for channels and limits |
| System time | A boot-started `ntpd` does not establish synchronization. Without a reachable source, the date may remain at its initial value; check [NTP Sync](../time-sync/ntp-sync.md) before recording |
| Configuration lifecycle | The matching new implementation stores Wi-Fi, UART passwordless-login, and Demo autostart choices in `/etc/4p`. USB, DNS, Ethernet, and application YAML already reside in system. Normal reboot retains manual choices; reflashing system restores image contents even with retained userdata, without importing old Wi-Fi, UART, or autostart registration state. Recording paths are unchanged: do not delete bags, MP4, or logs to reset settings. Refer to older images' own delivery notes for their behavior; replacing only the Demo package cannot complete the system-entry cutover. |

Use the preinstalled applications per [First Power-On](../getting-started/first-boot.md), without reinstalling or launching a second instance. Checks on the flashed device cover non-ROS/ROS2 checksum manifests, actual non-ROS loaded libraries, and ROS2 version queries in the package environment. They do not replace ROS2 topic/DDS, all USB modes, recording, long-duration, or repeated-reboot acceptance. Establish image compatibility from its delivery instructions and checksums, not software or documentation versions.

## Runtime Package Updates

Updating only the non-ROS or ROS2 runtime package does not require system flashing; use [Deployment, Upgrade, and Rollback](../development/deployment-and-upgrade.md). Software versions, documentation revisions, and system image versions are identified separately; this page does not change them.
