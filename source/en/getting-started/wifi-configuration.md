# Wi-Fi Configuration

This page describes how to use the `wifi_setup` command. Features:

- **AP mode**: turn the X5 into a selectable 2.4 GHz or 5 GHz Wi-Fi hotspot, operating one band at a time (not simultaneous dual-band), and assign addresses to clients via DHCP;
- **Client (STA) mode**: scan visible Wi-Fi, connect to a router, and obtain an address via DHCP;
- View current interface, connection, and saved-configuration status;
- Disable Wi-Fi;
- Optionally save the current configuration and auto-restore it at device boot.

```{warning}
When switching AP/STA or disabling Wi-Fi, the script stops wireless `hostapd`, `wpa_supplicant`, `udhcpc`, and its own Wi-Fi `dnsmasq`, clears the `wlan0` address, and resets the interface. If the current SSH uses `wlan0`, it will disconnect. For first-time configuration and recovery, use wired-Ethernet SSH, or the product-confirmed `1.8V` DEBUG_UART if necessary.
```

(wifi-factory-hotspot)=
## Factory Hotspot and Quick Connection

The matching new image initializes and enables the hotspot below only when no Wi-Fi state exists. Older firmware may lack this policy. Updating this documentation does not replace an already published image download or upgrade existing devices.

| Item | Factory hotspot configuration |
|---|---|
| Hotspot name (SSID) | `RoboBaton-4P` |
| Band and channel | 5 GHz, channel `36` (`AP_CHANNEL=36`), 20 MHz, non-DFS |
| Security | WPA2-PSK / CCMP; use the hotspot password supplied with the device, not an open hotspot |
| Board address | `192.168.5.1/24` |
| Client DHCP pool | `192.168.5.2–192.168.5.254` |
| DHCP lease | `12` hours, renewed automatically by the client; not a connection-duration limit |

1. Wait for the device and wireless service to become ready, select `RoboBaton-4P` on a 5 GHz-capable computer or phone, and enter the supplied hotspot password. If the client lacks support or local regulations restrict use, run `wifi_setup` through wired Ethernet or the debug console and manually select a permitted band and channel; there is no automatic fallback to 2.4 GHz.
2. Obtain an address automatically and confirm it belongs to the subnet above. A “no Internet” notice does not establish failure of the local connection.
3. Open `http://192.168.5.1/` directly to view sensors or control recording on the board. Normal use needs no prior SSH login or manual application start. The page has no authentication: use only a trusted isolated network and do not expose it to the Internet. See the {ref}`First Power-On browser entry <first-boot-web>` for functions.

The `/etc/init.d/S98wifi_default` initializer prepares configuration and a boot-enable marker from the protected template only when system-partition `/etc/4p/wifi` is absent. `/etc/init.d/S99wifi_setup` then starts the hotspot. Normal reboots preserve AP/STA, the selected AP band/channel, and disabled choices in that directory. Reflashing system restores the new image defaults, including 5 GHz AP channel `36`, even when userdata is retained; old `/userdata/wifi` settings are not imported. Changing the default band does not change the factory SSID, WPA2 security, hotspot password, or IP/DHCP settings. Failed initialization publishes no partial state, can retry at a later boot, and never falls back to an open hotspot. Use `wifi_setup` for routine changes; do not format userdata or delete recordings.

Wi-Fi and USB NCM/RNDIS/ECM networking use separate DHCP instances and can coexist; their default subnets are `192.168.5.0/24` and `192.168.7.0/24`. Wi-Fi AP advertises its own address as gateway/DNS; USB advertises neither. AP does not automatically provide NAT or Internet sharing. Custom subnets must avoid overlap between these interfaces and the client's existing networks. Both currently use a `12`-hour lease: successful automatic renewal permits continued use, without a forced disconnect at that time. If renewal fails until expiry, the client must stop using the leased address.

These matching-image configuration details do not establish real-board cold-boot, radio-association, or arbitrary phone/computer compatibility acceptance.

## 1. Prerequisites

- Log into the X5 as `root`;
- The X5 recognizes the on-board Wi-Fi interface, default interface name `wlan0`;
- The system provides Bash, `/usr/bin/env`, `ip`, `iw`, `hostapd`, `dnsmasq`, `wpa_supplicant`, `wpa_cli`, `udhcpc`, `killall`, `awk`, `sed`, `flock`, `stat`, `readlink`, `seq`, and common BusyBox commands;
- Trusted root owns `/etc/4p`; saving or changing settings requires a writable system partition. `/run` is cleared on every boot;
- The system includes `/usr/bin/wifi_setup` and `/etc/init.d/S99wifi_setup`, ordered after wireless driver readiness. Wi-Fi configuration does not require userdata to be mounted;
- This tool exclusively owns wireless service processes. Wi-Fi DHCP stops only its own instance after checking PID/interface identity, leaving the matching USB DHCP instance alone. `hostapd`, `wpa_supplicant`, and `udhcpc` are still stopped by process name, so do not share those wireless/client services with other interfaces.

## 2. Command Entry

The system includes `/usr/bin/wifi_setup` and `/etc/init.d/S99wifi_setup` as the Wi-Fi configuration command and boot-restore entry, respectively. Normal use requires no additional script upload or installation. Check the entries and help on the device:

```bash
command -v wifi_setup
test -x /etc/init.d/S99wifi_setup
test -w /etc
wifi_setup --help
```

## 3. Start Interactive Configuration

An interactive terminal must be preserved, so `ssh -t` is recommended:

```bash
X5_IP='BOARD_IP'  # replace BOARD_IP with the actual board address
ssh -t root@${X5_IP} "wifi_setup"
```

Alternatively, log into the device first and then run:

```bash
X5_IP='BOARD_IP'  # replace BOARD_IP with the actual board address
ssh root@${X5_IP}
wifi_setup
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

Enter `1` in the main menu. The following are **manual AP creation** defaults, not the factory hotspot configuration above; the interactive flow does not automatically reuse the factory SSID or password. The script asks in sequence:

| Parameter | Manual configuration default | Description |
|---|---|---|
| AP SSID | `RoboBaton-X5` | The hotspot name clients see when scanning. |
| AP password | empty | Empty creates an open hotspot; a WPA2 password must be 8–63 characters and requires confirmation. |
| AP band | `5` | Enter `2.4` or `5`, then select a channel in that band; only one band is active at a time. |
| AP channel | `36` for 5 GHz; `1` for 2.4 GHz | 2.4 GHz permits `1–13`; 5 GHz permits only `36`, `40`, `44`, `48`, `149`, `153`, `157`, `161`, `165`. |
| AP IP | `192.168.5.1` | Always uses a `/24` mask. |
| DHCP start address | `192.168.5.2` | Assigned to Wi-Fi clients. |
| DHCP end address | `192.168.5.254` | Assigned to Wi-Fi clients. |

Press Enter to accept the default value in brackets. Except for isolated debug environments, an open hotspot with an empty password is not recommended.

AP uses country code `CN`, matching the existing STA configuration. 5 GHz supports only the listed 20 MHz, non-DFS channels, not DFS or 40/80 MHz. Channels `36–48` are indoor-only where required by applicable regulations. The script's allowlist does not override actual driver, firmware, or regulatory-domain constraints: use channels permitted by the device and local regulations. An unavailable channel or failed AP startup reports an error, without automatically changing channel or falling back to another band; reconfigure manually through an independent wired/console connection.

The saved format still uses only `AP_CHANNEL` for AP band/channel, without a new band field: `1–13` means 2.4 GHz, and the listed 5 GHz channels mean 5 GHz. Existing saved 2.4 GHz configurations continue to restore their original channel rather than switching to 5 GHz on normal reboot.

On successful startup the terminal shows something like:

```text
AP started: SSID=RoboBaton-X5, channel=36, IP=192.168.5.1, DHCP=192.168.5.2-192.168.5.254
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
wifi_setup --status
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

After successful configuration, mode and credentials are saved to `/etc/4p/wifi/current.conf` regardless of the autostart choice. Entering `y` creates `/etc/4p/wifi/autostart.enabled`; otherwise the marker is removed. A saved configuration does not imply permission to restore at boot. Choices survive normal reboots, but reflashing system restores image defaults; old userdata configuration is no longer read.

After driver readiness, `/etc/init.d/S99wifi_setup` executes:

```bash
/usr/bin/wifi_setup --boot
```

Disabled restore never touches the interface; enabled restore with missing configuration fails explicitly without creating an open default hotspot. Repeated start after a successful restore in the same boot does not reset the connection. `/run/wifi_setup.boot-applied` records only that restore, not live connection health. `--stop` clears this runtime marker but preserves the persistent opt-in marker. No background reconnection supervisor or new DHCP renewal service is added.

The matching new image initializes the factory hotspot and enables restore only under the no-existing-state condition above. Later boots follow the saved marker rather than resetting settings. To stop Wi-Fi now and disable restore on future boots, run `wifi_setup`, select “Disable WiFi,” and answer `y` to the boot-autostart question. Running only `--stop` / `--disable` does not disable restore on the next boot.

The script sets `current.conf`, `hostapd.conf`, and `wpa_supplicant.conf` to root-readable/writable only, but the Wi-Fi password is still stored in plaintext on the device. Do not upload, share, or commit these files.

Manually verify the saved configuration:

```bash
wifi_setup --apply-saved
wifi_setup --status
```

## 7. Common Commands

```bash
# Enter the interactive menu
wifi_setup

# Apply the saved configuration
wifi_setup --apply-saved

# View interface, connection, saved configuration, and boot-autostart status
wifi_setup --status

# Stop Wi-Fi processes, clear the address, and turn off wlan0; does not unload the kernel driver
wifi_setup --stop
wifi_setup --disable

# Show help
wifi_setup --help
```

After choosing "Disable Wi-Fi" in the interactive menu, it also asks whether to disable the boot autostart managed by this script. Running `--stop` or `--disable` directly only stops the current runtime state; it does not delete the saved configuration nor automatically modify the boot-autostart setting.

## 8. Files and Logs

| Path | Content |
|---|---|
| `/usr/bin/wifi_setup` | Wi-Fi configuration program. |
| `/etc/init.d/S99wifi_setup` | Dedicated boot-restore entry. |
| `/etc/init.d/S98wifi_default` | Matching new image's first-time factory hotspot initializer, before S99 restore. |
| `/etc/default/4p-wifi-ap` | Protected factory AP template, root:root, `600`; contains a password and must not be shared publicly. |
| `/etc/4p/wifi/autostart.enabled` | System-partition boot-enable marker, permissions `600`. |
| `/etc/4p/wifi/current.conf` | Saved mode and credentials, permissions `600`. |
| `/run/4p-wifi/hostapd.conf` | AP runtime configuration, cleared on reboot. |
| `/run/4p-wifi/wpa_supplicant.conf` | STA runtime configuration, cleared on reboot. |
| `/run/4p-wifi/scan_ssids.txt` | The most recently scanned SSIDs. |
| `/run/4p-wifi/logs/hostapd.log` | AP startup log for this boot. |
| `/run/4p-wifi/logs/dnsmasq.log` | DHCP service log for this boot. |
| `/run/4p-wifi/logs/wpa_supplicant.log` | STA connection log for this boot. |
| `/run/4p-wifi/boot.log` | Auto-restore log for this boot. |
| `/run/wifi_setup.boot-applied` | Successful restore marker for this boot, cleared on reboot. |
| `/run/wifi_setup.lock` | Operation lock against concurrent configuration. |
| `/etc/init.d/S41eth0-route-fallback` | Preserve static Ethernet configuration; ignore only eth0 IPv4 carrier-down routes. |

`/etc/4p/wifi/` and `/run/4p-wifi/` default to permissions `700`. Runtime configuration and logs are cleared on reboot; old userdata logs are not deleted automatically. Read logs for troubleshooting, but remove SSIDs, passwords, IPs, and other site network information before providing them externally.

## 9. Troubleshooting

### Missing Command Prompt

The script checks all AP/STA dependencies at startup. A `missing command` prompt means the current system does not include the complete Wi-Fi user-space tools; do not overwrite system commands from unknown sources — record the missing commands and system version and contact product support.

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
cat /run/4p-wifi/logs/wpa_supplicant.log
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
wifi_setup --status
cat /run/4p-wifi/logs/hostapd.log
cat /run/4p-wifi/logs/dnsmasq.log
```

Confirm the channel is permitted for the selected band: `1–13` for 2.4 GHz, or only `36`, `40`, `44`, `48`, `149`, `153`, `157`, `161`, `165` for 5 GHz. Also check the actual driver/regulatory domain, country code `CN`, and applicable indoor restrictions. 5 GHz uses 20 MHz, non-DFS, without automatic fallback; manually select a permitted channel or band through wired Ethernet/the console. Confirm client band support, keep the AP IP and DHCP addresses in the same `/24` subnet, and avoid conflicts with other board interfaces or the current network.

### Factory Hotspot Is Not Visible After Power-On

Through wired Ethernet or the debug console, confirm that the matching image is installed, run `wifi_setup --status`, and inspect `/etc/4p/wifi` and this boot's logs. The factory default is 5 GHz channel `36`: confirm client support and local regulatory permission. If unsupported, configure 2.4 GHz manually; there is no automatic fallback. Normal reboot does not overwrite saved choices; the device may be in STA mode, use a different SSID/band/channel, or have boot restore disabled. Reflashing system restores image defaults without reading old userdata configuration. Use the interactive menu to configure AP and boot restore explicitly. Do not delete recordings or share templates, credentials, or password-bearing logs. Diagnose wireless-driver, antenna, and association issues using the AP troubleshooting above.

### Wi-Fi Not Restored After Boot

Check:

```bash
ls -l /etc/4p/wifi/autostart.enabled /etc/4p/wifi/current.conf
cat /run/4p-wifi/boot.log
wifi_setup --status
```

Confirm the dedicated entry runs after driver readiness. No boot.log is normal when restore is disabled. Verify cold-boot restoration on the actual device; manual start is not a substitute for a full reboot. With static Ethernet routes, `S41eth0-route-fallback` sets `net.ipv4.conf.eth0.ignore_routes_with_linkdown=1` after `S40network`. Addresses, gateway, and metric remain unchanged. This handles carrier-down IPv4 routes only, not upstream failures or IPv6.

### Stop Wi-Fi

Log in through wired Ethernet or the `1.8V` DEBUG_UART and run:

```bash
wifi_setup --disable
```

This command turns off `wlan0` but does not unload the on-board Wi-Fi kernel driver, nor change the wired network configuration.
