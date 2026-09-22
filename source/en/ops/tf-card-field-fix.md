# TF Card Not Detected Kernel Fix

```{note}
This page handles the issue on some early systems where the system cannot detect a TF card after insertion. The problem is a device-tree configuration issue in the on-board boot partition and cannot be resolved by remounting, reformatting the TF card, or redeploying the `/root/demo` runtime package. Systems manufactured after 20260818 already fixed this issue; if the TF card is already detected normally, you do not need to read this section.
```

```{warning}
This operation writes to the boot partition and requires a reboot. Power must remain stable during the write; do not power off, unplug, or force-restart while the script indicates writing or verification. Do not manually write the boot partition with `dd`; use only the fix script specified on this page.
```

## 1. Scope

The fix package is in the `RoboBaton_4p_demo` repository:

```text
patch/x5-fieldfix-buildroot-20260818.tar.gz
```

It applies only to the following targets:

| Item | Requirement |
|---|---|
| Board form | `board_id=0x0505` or `board_id=0x0506` |
| Root filesystem | Buildroot, `/etc/version` contains `PL5.1` |
| Device tree | The board layout corresponding to `x5-md-v0p2.dts` |
| boot image | 12,582,912 bytes, MD5 `df51ccd2b809ab85f5ceea52773ec894` |

Before writing, the script automatically checks the board form, root filesystem, boot partition device, partition size, and image fingerprint. Any mismatched condition rejects the write.

This page only describes the Buildroot fix package. Do not use it on Ubuntu/Jammy systems whose `/etc/version` contains `PL5.2`, and do not force execution on boards where `board_id` or the boot partition cannot be read.

The fix package also includes the fan device-tree fix, so the script's acceptance additionally outputs a fan-check result; the required acceptance target on this page is that the TF card can be detected.

## 2. Confirm Before the Fix

First exit the running camera application and data-saving task, ensuring no recording or other work that must be preserved is in progress. Keep `cam-service` running; do not treat stopping `cam-service` as a fix step.

On the host, confirm the fix package comes from the product delivery package or an approved `RoboBaton_4p_demo` source package. The archive SHA-256 should be:

```text
9859e221c46cb514190b64159db622e545cae9639ef8dfda3429b7d9840aa7b1
```

In the host directory holding the archive, run:

```bash
sha256sum x5-fieldfix-buildroot-20260818.tar.gz
```

The output must match the SHA-256 above. If it does not, stop and re-obtain the fix package. The host does not unpack the fix files; the next step uploads the complete archive to the X5 directly.

## 3. Upload the Archive and Unpack On-Device

### Host Terminal

Upload the complete archive to the X5's `/userdata/`, then log into the device:

```bash
X5_IP=192.168.1.12  # change to the actual board address
scp x5-fieldfix-buildroot-20260818.tar.gz root@${X5_IP}:/userdata/
ssh root@${X5_IP}
```

All commands from here until `reboot` run directly in this X5 SSH terminal; do not nest further SSH. The examples above use the factory default address; when the address has been changed, connect with the actual value.

### X5 On-Device SSH Terminal

First verify the uploaded archive, then unpack on-device:

```bash
cd /userdata
sha256sum x5-fieldfix-buildroot-20260818.tar.gz
tar -tzf x5-fieldfix-buildroot-20260818.tar.gz
tar -xzf x5-fieldfix-buildroot-20260818.tar.gz
cd x5-fieldfix-buildroot-20260818
chmod +x x5-fieldfix.sh
```

The on-device archive SHA-256 must still be:

```text
9859e221c46cb514190b64159db622e545cae9639ef8dfda3429b7d9840aa7b1
```

Confirm the unpacked script, image, board form, and system version:

```bash
test -x x5-fieldfix.sh
test -f boot.img
wc -c boot.img
md5sum boot.img
cat /sys/class/socinfo/board_id
cat /etc/version
readlink -f /dev/block/platform/by-name/boot
```

Expected results:

- `boot.img` size is `12582912` bytes;
- `boot.img` MD5 is `df51ccd2b809ab85f5ceea52773ec894`;
- `board_id` is `0x0505` or `0x0506`;
- `/etc/version` contains `PL5.1`;
- The boot link points to a valid block device.

If any item does not match, stop and do not run the fix script. The script and `boot.img` must be in the same directory; do not place boot images of other X5 board forms in that directory.

## 4. Run the Read-Only Health Check First

Continue in the current X5 SSH terminal and unpack directory. The read-only health check does not write the boot partition:

```bash
./x5-fieldfix.sh --check
echo "check_exit_code=$?"
```

Judge by exit code:

| Exit code | Meaning | Next step |
|---:|---|---|
| `0` | Prerequisites passed and a write is currently needed | Run the formal fix |
| `3` | The fixed boot is already written and the current kernel is in effect | Do not re-write; run TF-card acceptance directly |
| `4` | The fixed boot is already written but the device has not rebooted | Run `reboot`, then run acceptance |
| `1` | Board-form, version, partition, image, or permission check failed | Stop, do not bypass the checks |

The current boot MD5 in the health-check report is only a record of the current state. It is not a requirement to match some old version; as long as the script confirms the target board form, partition size, and image-to-write all match, you may continue.

## 5. Run the Fix

Only when `--check` passes and returns `0`, continue in the current X5 SSH terminal to run the formal fix:

```bash
./x5-fieldfix.sh
```

The script completes in sequence:

1. Check root privileges, board form, and Buildroot version;
2. Locate the boot partition via `/dev/block/platform/by-name/boot`;
3. Check that the boot partition size strictly equals the image size;
4. Verify the `boot.img` size and MD5;
5. Back up the current boot partition to `/userdata/fieldfix/boot-backup-<old MD5>.img`;
6. Write the new boot image;
7. Clean caches and read back the boot partition to verify;
8. Save the acceptance script and fix record to `/userdata/fieldfix/`.

The script is idempotent: if the target boot is already written but not yet rebooted, the script returns `4`; if the target boot is already written and in effect, it returns `3` and does not re-write.

After seeing the "fix write complete" or "already the fixed version" prompt, run in the current on-device terminal:

```bash
reboot
```

Do not reboot before the script completes. The script tries to auto-rollback on write or read-back verification failure; if auto-rollback also fails, do not keep retrying — preserve the site and contact product support.

## 6. Verify the TF Card After Reboot

After reboot completes, insert a known-good TF card. Log back into the X5 from the host:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh root@${X5_IP}
```

In the new X5 SSH terminal, run the acceptance script from the persistent directory directly:

```bash
/userdata/fieldfix/x5-fieldfix.sh --verify
```

Passing TF-card fix requires simultaneously:

- Output `SD: cd-inverted has disappeared`;
- Output `SD: detected /dev/mmcblk1, card usable`;
- `test -b /dev/mmcblk1` returns success.

Additionally confirm the device node in the same on-device terminal:

```bash
test -b /dev/mmcblk1
ls -l /dev/mmcblk1 /dev/mmcblk1p* 2>/dev/null || true
```

This system does not auto-mount the TF card. After confirming the device node appears, manually mount the corresponding partition per the site filesystem and mount policy; do not mistake "not auto-mounted" for "TF card not detected".

If acceptance reports no card inserted, first confirm the card is inserted, then re-run `--verify`. If it reports the card-present state but no `/dev/mmcblk1`, the fix is not complete; confirm whether the device was rebooted and keep the logs:

```bash
cat /userdata/fieldfix/fieldfix.log
```

`/etc/version` staying unchanged before and after acceptance is expected, because this fix does not update the rootfs.

## 7. Rollback

Before the formal fix, the script backs up the original boot partition to `/userdata/fieldfix/` and records it in:

```text
/userdata/fieldfix/last-backup.path
```

If acceptance keeps failing after the fix and you need to restore the pre-fix boot, log into the X5 and run directly in the on-device SSH terminal:

```bash
/userdata/fieldfix/x5-fieldfix.sh --rollback
reboot
```

The rollback script verifies the original MD5 in the backup filename and re-reads for verification after writing back. If no backup is found, the backup is corrupted, or the board-form/system-version check fails, the script refuses to roll back; do not replace it with a manual `dd`.

If the device can no longer boot after the fix, rollback over SSH is impossible; stop further power-on attempts, contact product support, and use the DEBUG_UART/serial or the formal rescue flow.

## 8. When the Problem Persists

After logging into the X5, collect information in the on-device SSH terminal in the following order; do not repeatedly re-write:

```bash
cat /sys/class/socinfo/board_id
cat /etc/version
cat /userdata/fieldfix/fixed.info 2>/dev/null || true
cat /userdata/fieldfix/fieldfix.log 2>/dev/null || true
ls -l /dev/mmcblk1 /dev/mmcblk1p* 2>/dev/null || true
```

Also provide:

- The fix package SHA-256;
- Full output of `--check`, the formal fix, and `--verify`;
- Whether `reboot` was actually run;
- The TF card model, capacity, and filesystem;
- If it failed to boot, provide the DEBUG_UART/serial site information.

Do not use other X5 images before confirming the board ID, rootfs type, and boot partition size. This fix only targets the Buildroot board forms and image fingerprints listed on this page.
