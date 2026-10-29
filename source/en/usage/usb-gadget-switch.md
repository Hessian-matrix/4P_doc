# USB Interface Function Switching

The USB3.0 Type-C port on the 4P board operates in USB device (gadget) mode and enumerates according to system configuration. Matching systems provide `switch_usb_gadget` to request interface-function changes. A present command or listed function does not certify every mode, reboot behavior, or re-enumeration.

## 1. Available Functions

| Function | Purpose | On the Computer |
|---|---|---|
| `rndis` | USB virtual NIC (RNDIS) | Requests USB NIC enumeration; board addressing and DHCP behavior follow actual system configuration and `switch_usb_gadget status` |
| `ecm` | USB virtual NIC (CDC ECM) | Enumerates as a USB NIC |
| `uvc` | USB camera (UVC) | Enumerates as a UVC camera (1920×1080) |
| `adb` | ADB debugging | Enumerates as an ADB device |
| `msd` | USB mass storage | Enumerates as a USB drive (128 MB) |

These are gadget command modes, not extensions to camera NV12 dimensions or acquisition capabilities. USB state-dependent behavior, asymmetric transmit/receive throughput, full Bulk mode combinations, and re-enumeration remain unresolved. Sustained throughput for the current system or successful arbitrary switching is not promised; see {ref}`Capability and Verification Boundaries <capability-verification-boundary>`. Switching over USB networking can disconnect the current session. Prepare an independent confirmed maintenance connection first, and do not switch during acquisition/saving.

## 2. Usage

The `switch_usb_gadget` command requires root privileges (the board logs in as root by default).

### 2.1 Interactive Selection

Run without arguments to list the available functions and pick one by number; after choosing a function, choose when it takes effect:

```bash
switch_usb_gadget
```

Example output:

```text
Current function: USB NIC (RNDIS, with DHCP, default)
Default function: (TBD)
Available functions:
  1) rndis  USB NIC (RNDIS, with DHCP, default)
  2) ecm    USB NIC (CDC ECM)
  3) uvc    USB camera (UVC 1920x1080)
  4) adb    ADB debugging
  5) msd    USB drive (Mass Storage, 128MB)
Select [1-5] (Enter to quit): 3
Take effect now [1] or after reboot [2] (Enter to cancel): 1
```

When it takes effect:

- **Take effect now [1]**: requests an immediate function switch; USB disconnects and the computer must re-enumerate it. Re-enumeration reliability is not fully closed; issuing the command does not establish a successful switch.
- **After reboot [2]**: sets the chosen function as the boot default, taking effect on the next boot without changing the current running state.

### 2.2 Direct Switch (Takes Effect Immediately)

```bash
switch_usb_gadget rndis    # switch to the RNDIS NIC
switch_usb_gadget uvc      # switch to the UVC camera
switch_usb_gadget msd      # switch to the USB drive
```

Specifying a function name directly is equivalent to choosing "take effect now" in interactive selection.

### 2.3 Status and List

```bash
switch_usb_gadget status   # show current/default function, GPIO routing, and network
switch_usb_gadget list     # list available functions
```

## 3. Default Function

The boot default function is set via the "after reboot" option in interactive selection, stored on the board in `/etc/usb_gadget_default`, and takes effect on the next boot.

| Item | Value |
|---|---|
| Boot default function | (TBD) |
