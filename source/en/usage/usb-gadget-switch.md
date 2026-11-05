# USB Interface Functions and Switching Limits

The system includes `switch_usb_gadget` to select the USB3 Type-C function. The matching new image defaults to a **CDC NCM NIC** at the factory. Older firmware may still default to RNDIS or lack NCM support; check `switch_usb_gadget --help` first. Only one function runs at a time: selecting a camera, ADB, or disk removes USB networking.

## 1. Before Switching

Run the commands below in the **board's root terminal**, not in the computer's PowerShell.

```{warning}
Switching disconnects the current USB connection. Use independent Ethernet or debug UART, not just the USB SSH link you are about to disconnect.
```

Stop recording in the browser, wait for saving to finish, then stop acquisition using the {ref}`start/stop instructions <non-ros-autostart>`. **Stopping recording alone is not enough.** Exit manually started camera/IMU programs too, and keep `cam-service` running. All manual switches and `stop` check for acquisition users; they do not close other programs for you.

(usb-function-selection)=
## 2. Select a Function

Run only the command you need:

| Goal | Board command | Notes |
|---|---|---|
| Direct USB networking | `switch_usb_gadget ncm` | Default on the matching new image; SSH, browser access, and file transfer. The computer must support CDC NCM |
| RNDIS networking | `switch_usb_gadget rndis` | Retained compatibility option; the computer must support RNDIS. There is no automatic fallback from NCM |
| ECM networking | `switch_usb_gadget ecm` | Another USB NIC protocol; the computer must support CDC ECM |
| USB camera | `switch_usb_gadget uvc` | Four images form one camera, with exclusive camera use |
| ADB debugging | `switch_usb_gadget adb --allow-adb` | Install platform-tools on the computer; trusted direct links only |
| USB disk | `switch_usb_gadget msd` | Read-only by default; initialize before first use, as shown below |
| Connect peripherals to the board | `switch_usb_gadget host --host-power-confirmed` | Check VBUS and cable power safety first; do not connect conflicting powered Hosts. Before leaving, unmount storage and exit peripheral users |

You can also enter `switch_usb_gadget` and follow the prompt. For UVC:

```console
# switch_usb_gadget
USB3: host / rndis / ecm / uvc / adb / msd / ncm / ip (configure network)
Mode (blank cancels): uvc
```

`#` is the shell prompt, not text to enter. Type `uvc` after `Mode (blank cancels):` and press Enter; blank input cancels. Host adds `VBUS/cable power checked? Type YES:`; ADB adds `Trusted direct debug link? Type YES:`. Enter `YES` only after checking those conditions. Complete commands in the table do not prompt for a function.

NCM is appended to the existing function list; existing modes retain their VID/PID identities.

Use `switch_usb_gadget status` to inspect state; selecting the same function again still reconfigures USB. USB-C is a data interface; see [Hardware Connection and Safety](../getting-started/hardware-and-safety.md) for power requirements.

## 3. Use the UVC Camera

The default profile is **MJPEG, 1280×960, 30fps**. Four `640×480` images form a grid: CAM1 top-left, CAM2 top-right, CAM3 bottom-left, CAM4 bottom-right. It includes no IMU, audio, or recording files and cannot run alongside Web/RTSP/ROS2 camera acquisition.

Over independent Ethernet or debug UART, stop the default application and select UVC:

```bash
cd /root/demo
./start_sensor_demo.sh stop && switch_usb_gadget uvc
```

In the computer's camera software, select this USB camera and `1280×960` MJPEG, then check all four images. A High-Speed or SuperSpeed link is required; a 30fps profile does not establish sustained 30fps reception.

**Closing preview or unplugging USB does not release the cameras.** When finished, close preview and return to the NIC:

```bash
switch_usb_gadget ncm && switch_usb_gadget status
```

After confirming the switch succeeded and the UVC backend exited, restore the original application if needed:

```bash
cd /root/demo
./start_sensor_demo.sh restart
```

If networking is not needed, `switch_usb_gadget stop` also exits UVC. Switching neither restarts the original application nor changes the boot default.

## 4. Networking, ADB, and Storage

### NCM / RNDIS / ECM Networking

The factory board address is `192.168.7.2/24`. Set the computer to obtain an address automatically; the allocation range is `192.168.7.10–192.168.7.100`. No default gateway, DNS, or automatic Internet sharing is provided. This is separate from Ethernet addressing; avoid conflicting routes for the same subnet. See [First Power-On](../getting-started/first-boot.md) for browser access.

The computer must support the selected protocol. NCM requires CDC NCM support; this page does not certify Windows compatibility. Select legacy RNDIS or ECM manually when needed; there is no automatic fallback. NCM uses the image's existing `usb_f_ncm.ko`. This default change does not rebuild or replace the kernel or establish real-board or computer-side compatibility acceptance.

(usb-network-address)=
### Change the USB NIC IPv4 Address

The matching new image adds the `ip` subcommand to `switch_usb_gadget`. Older firmware may lack it; check `switch_usb_gadget --help` first. Run the following commands in a **root terminal on the board**. They configure only the USB NIC address shared by NCM/RNDIS/ECM, not wired Ethernet or Wi-Fi, and do not configure USB through `/etc/network/interfaces`.

```bash
switch_usb_gadget ip
```

The interactive screen shows the fixed factory settings (`192.168.7.2/24`, DHCP `192.168.7.10–192.168.7.100`), saved settings, and current configuration. Press Enter at the address prompt to accept its default: the saved address if present, or the factory address on first use. A bare IPv4 address uses `/24`; CIDR prefixes from `/8` through `/30` are also accepted. Finally, choose save, apply, or cancel. **Save only is the default**; applying requires additional explicit confirmation.

Alternatively, specify an address directly or restore the factory network settings. Both commands below **save only**:

```bash
switch_usb_gadget ip --address 192.168.8.2/24
switch_usb_gadget ip --reset
```

Run whichever one you need. The tool automatically generates a DHCP range that excludes the board address. To specify a range, supply both `--dhcp-start` and `--dhcp-end`; the range must be in the same subnet and exclude the board address. No default gateway or DNS is offered.

**Saving alone does not reconfigure USB or interrupt the link, requires no acquisition shutdown, and works in any USB mode.** Settings are stored in `/etc/4p-usb-network.json` and used when networking starts at the next boot or on re-entry into NCM/RNDIS/ECM. The file survives reboot, but not necessarily firmware reflashing. `/etc/4p-usb-default.json` still stores only the boot mode, not network addresses.

Choose a USB subnet distinct from IPv4 subnets on the board's Ethernet, Wi-Fi, and other interfaces. Immediate application and network-mode entry reject detected board-side overlap before teardown, preventing replies on an independent maintenance link from being routed to USB. Save-only does not check live interfaces; resolve conflicts before enabling networking. Check computer-side route conflicts separately.

For immediate application, append `--apply` to the address command or `--reset`. Choose one as needed:

```bash
switch_usb_gadget ip --address 192.168.8.2/24 --apply
switch_usb_gadget ip --reset --apply
```

```{warning}
`--apply` is valid only while the current function is NCM, RNDIS, or ECM. It retains that mode and uses the existing manager switch path, reconfiguring USB and disconnecting existing links. Use independent Ethernet or debug UART. Follow this page's pre-switch instructions: stop recording normally, wait for saving to finish, exit acquisition applications, and keep `cam-service` running. Immediate application over USB SSH is refused unless `--allow-disconnect` is explicit. That flag only accepts disconnection; it neither ensures recovery nor bypasses acquisition checks.
```

After application, renew the computer's DHCP lease or disable and re-enable the USB adapter. For a static computer address, choose a different address in the board's new subnet and leave gateway and DNS blank. Reconnect the browser or SSH using the new board address. In `status`, `network.saved` and `network.active` distinguish saved settings from the last successfully configured profile; the latter does not establish computer reachability. This guidance does not establish new hardware verification or remote publication of a release.

### ADB

After selecting ADB, run `adb devices` on the computer and use `adb shell` once the device is recognized. Do not assume an Android-style authorization prompt. Return to networking or stop USB when finished.

### MSD Storage

Before first use, create the dedicated `128 MiB` FAT image `/root/usb-share.img`. Existing files are not overwritten:

```bash
switch_usb_gadget init-msd
switch_usb_gadget msd
```

This is not the whole eMMC, TF card, or recordings directory, and recordings are not copied into it automatically. For computer writes, use `switch_usb_gadget msd --writable`. Do not mount or modify the image on the board while it is exported.

When finished writing, **safely eject on the computer and wait for completion**, then run:

```bash
switch_usb_gadget ncm --host-ejected
```

To stop without selecting a NIC, use `switch_usb_gadget stop --host-ejected`. `--host-ejected` confirms ejection; it does not perform it. Ejection is also recommended for read-only storage.

## 5. Boot Default and Stopping

```bash
switch_usb_gadget set-default ncm
```

You can also save `rndis` or `ecm`; saving `host` requires `--host-power-confirmed`. This affects the next boot, not the current function. UVC, ADB, and MSD cannot be boot defaults.

The setting is stored in `/etc/4p-usb-default.json` and read by `/etc/init.d/S99usb.sh`. Installer updates preserve an existing boot choice. The matching new image candidate explicitly sets its factory default to NCM; this neither overwrites existing devices' saved choices nor changes the contents of previously published image downloads. Normal use does not require running `boot` or rerunning startup scripts. `boot` actually reconfigures USB; it is not a query.

`switch_usb_gadget stop` stops the current function and tool-started backend. It does not change the default or guarantee a change from Host to Device.

## 6. Status and Troubleshooting

```bash
switch_usb_gadget status
switch_usb_gadget --help
```

| Status field | Interpretation |
|---|---|
| `role` / `requested` | Current Host/Device role / requested function |
| `bound` | Device usually binds to `35100000.usb`; Host needs no binding |
| `udc_state` | `configured`: the computer selected a configuration; `not attached`: disconnected |
| `speed` | `super-speed` is negotiated speed; `UNKNOWN` means unconfirmed. Neither establishes sustained throughput |
| `backend` / `default.mode` | Associated backend process / saved boot default |
| `network.saved` | Saved USB IPv4/DHCP settings, used on the next entry into networking |
| `network.active` | Last successfully configured network profile, not a live connectivity or computer-reachability assertion |

Follow the error: exit the occupying program, use independent management, check power, or eject the disk first. Backend logs are in `/run/4p-usb/backend.log` and do not survive reboot. Do not bypass checks by force-killing, deleting ownership records, or writing GPIOs. After a failure, use `status` to inspect the actual state rather than assuming the old function was restored.

`--allow-disconnect` only accepts loss of USB SSH; it provides no automatic recovery and bypasses no other checks. An independent maintenance connection is still needed.

The NCM default and integrated kernel module do not establish computer-side enumeration, video reception, storage operations, sustained throughput, repeated-switching, or reboot acceptance. Existing RNDIS checks do not certify NCM. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

(usb-uvc-development)=
## 7. Modify and Rebuild UVC

**Camera acquisition, mosaic processing, and JPEG encoding run in a board-side userspace application, not the kernel.** The standalone `/usr/bin/x5-uvc-mosaic` produces USB video; a browser can provide controls but cannot replace it. Sources and tools are under `scripts/env_setup/x5_usb/` in the public non-ROS Demo repository:

| Public file | Modification entry points and responsibilities |
|---|---|
| [`uvc_mosaic.cpp`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/uvc_mosaic.cpp) | [`Source::Start()`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/uvc_mosaic.cpp#L146-L164) configures acquisition; [`Compose()`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/uvc_mosaic.cpp#L266-L298) tiles the four images; [`Encoder`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/uvc_mosaic.cpp#L340-L423) uses hardware JPEG encoding; `FixedControl()` / `Gadget` handle UVC negotiation and output |
| [`build_uvc.sh`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/build_uvc.sh) | Standalone cross-build entry; does not rebuild producer libraries |
| [`switch_usb_gadget`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/switch_usb_gadget) | Manages USB functions and backend start/stop; [`uvc()`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/switch_usb_gadget#L384-L415) creates UVC descriptors and launches the program |
| [`install.py`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/install.py) | `install(root, package)` installs staged artifacts into an offline rootfs and generates the USB manifest |
| [`S98rootfs.sh`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/S98rootfs.sh) / [`S99usb.sh`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/S99usb.sh) | Prepare the root filesystem / start USB using the saved default |

Online source links point to `V2_main` and become accessible only after that branch and the corresponding Demo source revision are pushed; see the Demo README for local file links. These files are not root CMake targets. Rebuilding `sensor_demo`, the browser frontend, or other mosaic examples does not update UVC.

### Standalone Build

Run on the development host from the **`RoboBaton_4p_demo` root**; Go is not needed:

```bash
SDK_ROOT=/path/to/platform_source_code # replace with the X5 SDK source tree matching the target system
USB_DIR=scripts/env_setup/x5_usb
OUTPUT_DIR=build_uvc
mkdir -p "$OUTPUT_DIR"
bash "$USB_DIR/build_uvc.sh" "$SDK_ROOT" "$OUTPUT_DIR/x5-uvc-mosaic" \
  --sc132-include "$PWD/include" --producer-lib "$PWD/lib"
```

You must provide matching SDK `hbre/libmm/inc` headers (including `hb_media_codec.h`), real AArch64 `libmultimedia.so.1` / `libhbmem.so.1`, and the Demo's matched ABI3 headers and `libsc132.so.3`. Add `--sdk-lib-dir /path/to/sdk/lib` if SDK libraries are outside the default search locations. Optional `--cxx /path/to/aarch64-linux-gnu-g++` and `--sysroot /path/to/sysroot` select the toolchain. **The compiler and sysroot must match**; do not mix arbitrary toolchain headers and libraries. The script does not download the SDK, rebuild/copy producers, or deploy to a board. See [Building the Public Demo Source](../development/open-source-build.md) for general application builds.

### Install into an Offline System Image

In the same terminal, stage the three runtime scripts beside the binary, then run the installer:

```bash
cp "$USB_DIR/switch_usb_gadget" "$USB_DIR/S98rootfs.sh" \
  "$USB_DIR/S99usb.sh" "$OUTPUT_DIR/"
python3 "$USB_DIR/install.py" \
  --rootfs /path/to/OFFLINE-rootfs --package "$OUTPUT_DIR"
```

Replace the example rootfs path with an unpacked **offline SDK rootfs**. `--package` names the directory containing the binary and the three scripts, not the binary itself. The installer rejects `/`: it is not for a running system and does not upload, flash, or reboot a board. The offline image must already provide Python3, `adbd`, `dnsmasq`, complete `/root/demo/lib`, and SDK runtime dependencies; the installer does not supply these dependencies. Preserve SDK hbre partition libraries, relative SONAME links, and matching dependencies.

### Update an Existing Board

| Change | What to update |
|---|---|
| Tile order or image processing, keeping the output profile unchanged | Rebuild and replace `x5-uvc-mosaic`; mosaic logic is compiled into the executable, not a separate SO |
| Camera-library internals | If ABI and dependencies remain compatible, update the matching `libsc132.so.3` real file, links, and dependencies under `/root/demo/lib` as a set; other camera applications use this library too |
| Resolution, frame rate, or format | Align backend acquisition, mosaic/encoder buffers, UVC negotiation, manager `uvc()` descriptors, and the UVC profile in the installer and runtime manifests; replacing an SO alone is insufficient |

**With an unchanged output profile and existing kernel/device-tree support, application-logic changes normally do not require reflashing.** Use independent Ethernet or debug UART. Stop recording and wait for saving to finish, exit other acquisition applications normally, then stop UVC with `switch_usb_gadget stop`. Confirm the backend exited and keep `cam-service` running.

Back up old programs, scripts, libraries, and manifests. Stage replacements on the destination filesystem, check architecture, dependencies, and SHA-256, then use atomic renames rather than overwriting executables or SOs in use. Preserve complete libraries and SONAME links. Synchronize `/usr/share/4p-usb/manifest.json` and affected application-package manifests/provenance with the actual artifacts and profile, rather than manually changing hashes alone. The manager launches the fixed `/usr/bin/x5-uvc-mosaic` path; moving it also requires changing that launch path.

Restart UVC, let the computer re-enumerate, then check output format, all four images, and return to the original application. Restore backups on failure. Kernel-driver or device-tree support changes require separate updates to those system components. This section does not establish remote publication, board deployment, video reception, or mode-switching acceptance.
