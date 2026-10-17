# USB Interface Function Switching

The USB3.0 Type-C port on the 4P board operates in USB device (gadget) mode, enumerating as the corresponding USB device when connected to a computer. Use the on-board `switch_usb_gadget` command to switch the function provided by this interface without rebooting.

## 1. Available Functions

| Function | Purpose | On the Computer |
|---|---|---|
| `rndis` | USB virtual NIC (RNDIS) | Enumerates as a USB NIC; board `192.168.7.2/24`, provides DHCP to the computer |
| `ecm` | USB virtual NIC (CDC ECM) | Enumerates as a USB NIC |
| `uvc` | USB camera (UVC) | Enumerates as a UVC camera (1920×1080) |
| `adb` | ADB debugging | Enumerates as an ADB device |
| `msd` | USB mass storage | Enumerates as a USB drive (128 MB) |

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

- **Take effect now [1]**: switches to the chosen function immediately; the USB connection briefly disconnects and re-enumerates during the switch.
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
