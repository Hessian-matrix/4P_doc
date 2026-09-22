# Wi-Fi Configuration

This page explains how to upload `scripts/wifi_setup.sh` from the public non-ROS repository to the X5 device and configure the on-board Wi-Fi interactively from the terminal. The script supports:

- **AP mode**: turn the X5 into a 2.4 GHz Wi-Fi hotspot and assign addresses to clients via DHCP;
- **Client (STA) mode**: scan visible Wi-Fi, connect to a router, and obtain an address via DHCP;
- View current interface, connection, and saved-configuration status;
- Disable Wi-Fi;
- Optionally save the current configuration and auto-restore it at device boot.

```{warning}
When switching AP/STA or disabling Wi-Fi, the script stops existing `hostapd`, `wpa_supplicant`, `udhcpc`, and `dnsmasq`, clears the `wlan0` address, and resets the interface. If the current SSH is connected through `wlan0`, the terminal will drop. For first-time configuration and recovery, use wired-Ethernet SSH, and if necessary the product-confirmed `1.8V` DEBUG_UART.
```

## 1. Prerequisites

- Log into the X5 as `root`;
- The X5 recognizes the on-board Wi-Fi interface, default interface name `wlan0`;
- The device already provides the script dependencies: `ip`, `iw`, `hostapd`, `dnsmasq`, `wpa_supplicant`, `wpa_cli`, `udhcpc`, `killall`, `awk`, and `sed`;
- The host can SSH into the X5 over the wired network;
- You have the public non-ROS repository, with the script at `scripts/wifi_setup.sh`.

First confirm the script exists:

```bash
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # change to the actual repository directory
cd ${NON_ROS_ROOT}
test -f scripts/wifi_setup.sh
```

## 2. Upload to the Device

On the host:

```bash
X5_IP=192.168.1.12  # change to the actual board address
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # change to the actual repository directory
cd ${NON_ROS_ROOT}
scp scripts/wifi_setup.sh root@${X5_IP}:/userdata/wifi_setup.sh
ssh root@${X5_IP} "chmod 700 /userdata/wifi_setup.sh"
```

Check the file:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh root@${X5_IP} "ls -l /userdata/wifi_setup.sh"
```

The script always stores runtime configuration, state, and logs under `/userdata/wifi/`; do not enable boot autostart after placing the script only in a temporary directory.

## 3. Start Interactive Configuration

An interactive terminal must be preserved, so `ssh -t` is recommended:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh -t root@${X5_IP} "/userdata/wifi_setup.sh"
```

Alternatively, log into the device first and then run:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh root@${X5_IP}
/userdata/wifi_setup.sh
```

Main menu:

```text
1) AP mode: turn the board into a hotspot
2) Client mode: scan and connect to a router WiFi
3) View status
4) Disable WiFi (stop services and turn off wlan0)
5) Exit
```

## 4. Configure AP Hotspot

Enter `1` in the main menu. The script asks in sequence:

| Parameter | Default | Description |
|---|---|---|
| AP SSID | `RoboBaton-X5` | The hotspot name clients see when scanning. |
| AP password | empty | Empty creates an open hotspot; a WPA2 password must be 8–63 characters and requires confirmation. |
| 2.4 GHz channel | `1` | Supports `1–13`. |
| AP IP | `192.168.5.1` | Always uses a `/24` mask. |
| DHCP start address | `192.168.5.2` | Assigned to Wi-Fi clients. |
| DHCP end address | `192.168.5.254` | Assigned to Wi-Fi clients. |

Press Enter to accept the default value in brackets. Except for isolated debug environments, an open hotspot with an empty password is not recommended.

On successful startup the terminal shows something like:

```text
AP started: SSID=RoboBaton-X5, IP=192.168.5.1, DHCP=192.168.5.2-192.168.5.254
```

After a client joins the hotspot, confirm it received an address in the `192.168.5.0/24` subnet and test the board AP address:

```bash
ping 192.168.5.1
```

```{note}
AP mode only configures the local hotspot, board address, and DHCP; it does not configure NAT, IP forwarding, or upstream Internet sharing. A client joining the hotspot does not mean it can reach the Internet through the X5.
```

## 5. Configure Client (STA) Mode

Enter `2` in the main menu. The script:

1. Brings up and resets `wlan0`;
2. Scans currently visible SSIDs;
3. Shows a numbered list;
4. Waits for the Wi-Fi number input;
5. Prompts for a hidden password; open networks can leave it empty;
6. Waits for association to complete;
7. Obtains a DHCP address via `udhcpc`;
8. Prints the `wlan0` address.

In the SSID selection prompt:

- Enter a number to select a network;
- Enter `r` to rescan;
- Enter `q` to exit.

The interactive menu only allows selecting scanned, visible SSIDs; hidden SSIDs are outside the current interactive flow.

After connecting, check:

```bash
/userdata/wifi_setup.sh --status
ip -4 addr show dev wlan0
iw dev wlan0 link
ip route
```

The script prints a warning when association succeeds but DHCP fails. In that case check the router DHCP, address pool, and access control first; do not assume the network is usable merely because `iw ... link` shows association.

## 6. Boot Auto-Restore

After AP or STA startup succeeds, the script asks:

```text
Save/update the current WiFi configuration as boot autostart? [y/N]
```

After entering `y`:

- The current mode and credentials are saved to `/userdata/wifi/current.conf`;
- `/userdata/startup.sh` is generated;
- At boot the following is executed:

```bash
/userdata/wifi_setup.sh --apply-saved >/userdata/wifi/boot.log 2>&1
```

```{important}
If `/userdata/startup.sh` already exists and was not generated by this script, the script refuses to overwrite it. Keep the original startup logic, and manually merge the `--apply-saved` command above into the existing `/userdata/startup.sh`; do not delete other applications' startup commands.
```

The script sets `current.conf`, `hostapd.conf`, and `wpa_supplicant.conf` to root-readable/writable only, but the Wi-Fi password is still stored in plaintext on the device. Do not upload, share, or commit these files.

Manually verify the saved configuration:

```bash
/userdata/wifi_setup.sh --apply-saved
/userdata/wifi_setup.sh --status
```

## 7. Common Commands

```bash
# Enter the interactive menu
/userdata/wifi_setup.sh

# Apply the saved configuration
/userdata/wifi_setup.sh --apply-saved

# View interface, connection, saved configuration, and boot-autostart status
/userdata/wifi_setup.sh --status

# Stop Wi-Fi processes, clear the address, and turn off wlan0; does not unload the kernel driver
/userdata/wifi_setup.sh --stop
/userdata/wifi_setup.sh --disable

# Show help
/userdata/wifi_setup.sh --help
```

After choosing "Disable Wi-Fi" in the interactive menu, it also asks whether to disable the boot autostart managed by this script. Running `--stop` or `--disable` directly only stops the current runtime state; it does not delete the saved configuration nor automatically modify the boot-autostart setting.

## 8. Files and Logs

| Path | Content |
|---|---|
| `/userdata/wifi_setup.sh` | Wi-Fi configuration script. |
| `/userdata/wifi/current.conf` | Saved mode and credentials, permissions `600`. |
| `/userdata/wifi/hostapd.conf` | AP mode configuration. |
| `/userdata/wifi/wpa_supplicant.conf` | STA mode configuration. |
| `/userdata/wifi/scan_ssids.txt` | The most recently scanned SSIDs. |
| `/userdata/wifi/logs/hostapd.log` | AP startup log. |
| `/userdata/wifi/logs/dnsmasq.log` | DHCP service log. |
| `/userdata/wifi/logs/wpa_supplicant.log` | STA connection log. |
| `/userdata/wifi/boot.log` | Boot auto-restore log. |
| `/userdata/startup.sh` | Optional late-boot startup entry. |

`/userdata/wifi/` defaults to permissions `700`. You can read logs when troubleshooting, but before providing logs externally remove SSIDs, passwords, IPs, and other site network information.

## 9. Troubleshooting

### Missing Command Prompt

The script checks all AP/STA dependencies at startup. A `missing command` prompt means the current system image does not include the complete Wi-Fi user-space tools; do not overwrite system commands from unknown sources — record the missing commands and system version and contact product support.

### STA Scans No SSID

Check:

```bash
ip link show wlan0
iw dev wlan0 info
iw dev wlan0 scan
```

Confirm antenna, distance, router broadcast, and band compatibility. The current interactive flow cannot manually enter a hidden SSID.

### STA Authentication Failure

Re-run the script and confirm SSID, password, and signal; check:

```bash
cat /userdata/wifi/logs/wpa_supplicant.log
```

### STA Associated but No IP

Check:

```bash
iw dev wlan0 link
ip -4 addr show dev wlan0
ip route
```

Confirm router DHCP is enabled and the address pool is not exhausted. The script does not auto-configure a static address after DHCP failure.

### AP Cannot Start or Clients Get No Address

Check:

```bash
/userdata/wifi_setup.sh --status
cat /userdata/wifi/logs/hostapd.log
cat /userdata/wifi/logs/dnsmasq.log
```

Confirm the channel is `1–13`, the AP IP and DHCP addresses are in the same `/24` subnet, and avoid conflicts with other board interfaces or the current network.

### Wi-Fi Not Restored After Boot

Check:

```bash
ls -l /userdata/startup.sh /userdata/wifi/current.conf
cat /userdata/wifi/boot.log
/userdata/wifi_setup.sh --status
```

If the device already has a custom `/userdata/startup.sh`, confirm the `--apply-saved` command has been merged manually and the original startup logic preserved.

### Restore the Wired Configuration Entry

Log in through wired Ethernet or the `1.8V` DEBUG_UART and run:

```bash
/userdata/wifi_setup.sh --disable
```

This command turns off `wlan0` but does not unload the on-board Wi-Fi kernel driver, nor change the wired network configuration.
