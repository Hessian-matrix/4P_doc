# USB Interface Functions and Switching Limits

The updated matching V2 Buildroot image provides `switch_usb_gadget` to select **Host** or **Device (gadget)** on the same USB3.0 Type-C controller. Device mode enables one function at a time: RNDIS, CDC ECM, UVC, ADB, or MSD. RNDIS remains the default for direct computer connectivity, SSH, browser preview, and file transfer.

USB functions belong to the matching BSP/system image, not the non-ROS or ROS2 application packages. An older image containing only `x5-usb-rndis` does not gain this feature by updating documentation or an application package. Do not mix the new tool with old SDK gadget scripts, GPIO386 routing scripts, or the old `/etc/usb_gadget_default` file.

## 1. Check the Image and Safety Conditions First

Read-only checks on the board:

```bash
command -v switch_usb_gadget
switch_usb_gadget status
cat /usr/share/4p-usb/manifest.json
```

The new tool requires the matching revised-carrier device-tree marker and Linux USB role-switch interface; mismatches are rejected. `status` reports the actual role, requested function, UDC binding, connection state, negotiated speed, backend process identity, and boot default. A requested function or running backend does not prove computer-side enumeration. `not attached` / `UNKNOWN` means no connection is currently established, not necessarily a missing feature.

```{warning}
Switching or stopping disconnects USB networking, SSH, the browser, ADB, or storage. Prepare a confirmed independent Ethernet or debug-serial maintenance connection first; do not operate over the only USB management link. Finalize recording normally and exit acquisition applications. Do not interrupt a starting, recording, or finalizing session, or stop/reconfigure `cam-service`.
```

The tool refuses known acquisition owners, foreign gadget owners, and mounted or process-open USB devices in Host mode. It only gracefully stops backends it started whose process identity still matches; it never force-kills another process. These checks cannot recognize every third-party program or prevent concurrent external changes, so users must still maintain exclusive ownership.

USB-C is a data interface. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md) for power, electrical, and cable constraints. A software Host role does not establish safe VBUS output or USB-C/PD power support. Before selecting Host, check the connection and power scheme confirmed by product support; do not connect conflicting powered Hosts directly.

## 2. Select a Function

Root can use commands directly, or run `switch_usb_gadget` without arguments and enter a function name; blank input cancels. Interactive Host and ADB selection also requires safety confirmation. Every command below changes the active USB function; do not run the table as a sequence of read-only checks.

| Function | Board command | Usage boundary |
|---|---|---|
| Host | `switch_usb_gadget host --host-power-confirmed` | Attach supported USB peripherals after checking VBUS/cable safety. Before leaving Host, unmount storage normally and close applications using the peripheral |
| RNDIS | `switch_usb_gadget rndis` | Virtual NIC; the computer needs a matching RNDIS driver |
| CDC ECM | `switch_usb_gadget ecm` | CDC ECM virtual NIC; the computer needs a matching ECM driver |
| UVC | `switch_usb_gadget uvc` | One MJPEG stream from four real cameras; exclusive camera ownership; see below |
| ADB | `switch_usb_gadget adb --allow-adb` | Trusted direct debugging only; exposes debug access without an Android-style authorization-prompt guarantee |
| MSD | `switch_usb_gadget msd` | Dedicated FAT image, read-only by default; initialize first as described below |

When SSH uses this USB NIC, the tool refuses disconnection by default. `--allow-disconnect` explicitly permits losing the connection; it does not provide automatic recovery or rollback. Consider it only with a confirmed independent recovery connection.

### RNDIS / CDC ECM Network

Both NIC functions use board address `192.168.7.2/24`. USB-specific DHCP allocates `192.168.7.10–192.168.7.100` to the computer, without a default gateway or DNS and without automatic Internet sharing. Addressing is independent of wired Ethernet. Enable automatic addressing for the computer's USB NIC and resolve overlapping routes first. When the board Web service is running, this address can access it; the actual port and application version must still match. See [First Power-On](../getting-started/first-boot.md).

“USB3 controller” does not prove negotiated SuperSpeed. Use the actual connection, `current_speed`, computer enumeration, and data transfer as evidence; the displayed NIC rate is not sustained throughput.

### Four-Camera UVC Preview

`x5-uvc-mosaic` consumes real complete SC132 four-camera groups. Four `640×480` images form a `1280×960` image: **CAM1 top-left, CAM2 top-right, CAM3 bottom-left, CAM4 bottom-right**. The X5 hardware JPEG encoder supplies one MJPEG stream with a `30fps` descriptor. This is not four independent USB cameras and includes no IMU, audio, or recording files. It cannot run alongside existing Web/RTSP/ROS2 camera acquisition.

Stop acquisition applications normally before selecting UVC. On the computer, select the device and `1280×960` mode in MJPEG-capable camera software. This profile requires High-Speed or SuperSpeed; Full-Speed is not supported. Backend readiness only means the output node, event subscriptions, and acquisition startup completed, not that the computer received frames or sustained 30fps. Inspect all four real images on the computer. After stopping the backend and switching functions, restart the original application normally if needed.

### ADB Debugging

The computer needs Android platform-tools and matching drivers. After selecting ADB, run `adb devices` on the computer; use `adb shell` only after actual connectivity is established. ADB may expose privileged access: use trusted direct connections and return to RNDIS or stop the USB function afterward. A running backend or FunctionFS mount does not prove computer connectivity or authorization.

### Dedicated MSD Disk

Initialization creates only a new `128 MiB` FAT backing image at `/root/usb-share.img`; existing files are never overwritten. It does not export the root partition, TF card, or existing recording directories, and does not copy recordings into the image:

```bash
switch_usb_gadget init-msd
switch_usb_gadget msd
```

To allow computer writes, explicitly run `switch_usb_gadget msd --writable`. The image must not be mounted or used by a local process. The tool checks loop ownership and direct open users, but users must maintain exclusivity. Never mount or modify the backing file locally while exported, even when the computer sees a read-only disk.

To finish writable export, **safely eject the disk on the computer and wait for completion first**, then run:

```bash
switch_usb_gadget rndis --host-ejected
# Or stop only the current function: switch_usb_gadget stop --host-ejected
```

`--host-ejected` is the user's acknowledgement that computer-side ejection completed; the board cannot verify it automatically. Never use it to bypass an unejected disk. Unplugging or stopping a service is not a substitute for safe ejection. Ejection is also recommended for read-only export.

## 3. Boot Default and Stopping

Only Host, RNDIS, or ECM can be saved as the boot default. Saving does not switch the current function:

```bash
switch_usb_gadget set-default rndis
# ecm is also allowed; Host requires confirmed wiring and power:
# switch_usb_gadget set-default host --host-power-confirmed
```

The setting is stored in `/etc/4p-usb-default.json`. The sole boot entry `/etc/init.d/S99usb.sh` reads it through `switch_usb_gadget boot`. The factory candidate defaults to RNDIS. Boot networking is independent of sensor applications and does not take camera ownership. UVC, ADB, and MSD are not boot defaults, avoiding unexpected camera takeover, debugging, or disk exposure. Building a new image does not change an already-flashed device's default.

`switch_usb_gadget stop` unbinds/removes the owned function and gracefully stops its backend. Writable MSD still requires safe ejection and `--host-ejected`. `stop` does not change the persistent default or guarantee a change from Host to Device. Failures are reported explicitly. Once a transition is host-visible, the tool does not pretend the previous function was automatically restored; inspect and recover using the independent maintenance connection.

## 4. Verification Boundaries

An image containing the tools, backend, and matching dependencies is not proof of flashing or real-board acceptance. Confirm Host peripheral enumeration, RNDIS/ECM addressing and actual bidirectional transfers, four-camera UVC reception, ADB connectivity, MSD read/write/ejection, repeated switching, and reboot defaults on a matching board and computer. Existing USB state-dependent/asymmetric bidirectional throughput and re-enumeration issues do not close automatically, and no sustained-performance guarantee is made. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.
