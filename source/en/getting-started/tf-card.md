# TF Card (microSD) Usage

## 1. Purpose and Safety Boundaries

A TF card can serve as a data disk on an already flashed system; this does not require reflashing or change the system boot medium. This guide applies to boards with a TF slot and an SD-enabled BSP. It is not a TF boot or flashing guide.

```{warning}
The TF hot-plug hardware repair is user-confirmed, not certification of every board/BSP/card model or permission to remove a card during recording/writes. Finish acquisition and saving, wait for finalization, sync, and successfully unmount before removal. Hardware not confirmed to have the applicable repair still requires normal shutdown and power-off insertion/removal. Back up existing data first. Never partition, format, repair, or write raw data to an unidentified device, especially the system eMMC. This guide does not provide automatic formatting or boot-time mounting scripts.
```

“Inserted,” “controller present,” “SD block device present,” “filesystem mounted,” and “successful I/O and recording” are separate states. Creating a directory or seeing `/media` does not establish a TF mount: `/media` itself may be tmpfs. Continuing after a failed mount can write into RAM or the system disk.

## 2. Check Detection Without Writing

Run in a board terminal:

```sh
cat /proc/partitions
lsblk -o NAME,MAJ:MIN,RM,SIZE,RO,TYPE,FSTYPE,MOUNTPOINT
for d in /sys/class/block/mmcblk*; do
    [ -f "$d/device/type" ] || continue
    printf '%s: ' "${d##*/}"
    cat "$d/device/type"
done
cat /proc/mounts
```

Distinguish devices by type, not only their name or the `RM` column:

| Observation | Meaning and next step |
|---|---|
| Whole-disk `device/type` is `MMC` | Usually onboard eMMC; cross-check the root partition and mounts. Do not format it as a TF card. |
| Whole-disk `device/type` is `SD`, with `/dev/mmcblkN` present | The TF card has enumerated; check its partitions, filesystem, and mounts next. The number is not guaranteed to remain fixed. |
| `/dev/mmcblkNp1` exists | The first partition was parsed; this does not establish a mount or writability. |
| Only MMC, without any SD block device | The card has not enumerated, rather than merely being unmounted. Follow section 7 before mounting or formatting. |
| The only additional MMC-bus device is `SDIO` | This may be a wireless module, not a TF storage disk. |

For example, if `/dev/mmcblk0p9` is mounted as `/` and `mmcblk0/device/type` is `MMC`, that device is the system disk. A capacity near 32GB does not make it the inserted card.

## 3. Select the Device and Filesystem

**Continue only after section 2 has identified an SD device.** These variables are examples and must match your actual system. Run subsequent blocks in the same board shell:

```sh
TF_DISK=mmcblk1             # replace with the whole disk whose type is SD
TF_DEV=/dev/mmcblk1p1       # replace with the card's actual filesystem partition
TF_MOUNT=/media/tfcard      # dedicated mountpoint, not an existing business directory
cat "/sys/class/block/$TF_DISK/device/type"
lsblk -o NAME,MAJ:MIN,SIZE,RO,TYPE,FSTYPE,MOUNTPOINT "/dev/$TF_DISK"
blkid -p "$TF_DEV"
findmnt -rn -S "$TF_DEV" -o SOURCE,TARGET,FSTYPE,OPTIONS
cat /proc/filesystems
```

An unmounted device normally gives no output and a nonzero status from `findmnt -S`. If already mounted, first identify its purpose and use the confirmed mountpoint; do not mount it again or cover it. If the card has a whole-disk filesystem without partitions, use the whole disk for `TF_DEV` only after `blkid -p /dev/mmcblkN` confirms it. Do not guess or create `p1`. If `blkid` cannot identify a filesystem, back up and inspect the card on a computer rather than formatting it immediately.

| Filesystem | Guidance |
|---|---|
| ext4 | Prefer for long Linux acquisition sessions; Windows does not read it natively. When preparing a card, consider which ext4 features the target kernel supports. |
| exFAT | Convenient for exchanging large files with a computer; verify support in the current BSP kernel or supplied driver. Computer readability alone does not establish board support. |
| FAT32 (`vfat`) | Maximum individual file size is `4GiB−1` bytes. Unsuitable for bags or individual MP4 files that may exceed it. Do not assume the recorder automatically splits files. |

Validate card capacity, speed class, and model compatibility against the actual board and BSP. A filesystem driver does not establish card detection or sustained-write acceptance. Before preparing a new card on a computer, back up its contents and confirm the selected device is the TF card, then use appropriate partitioning and formatting tools. Never reuse a system-disk device name blindly.

## 4. Mount Manually

These are user-initiated mounting steps that change mount state. Continue only with an enumerated card, a healthy filesystem, and a free mountpoint. Any failed step stops the subshell:

```sh
(
    set -eu
    test "$(cat "/sys/class/block/$TF_DISK/device/type")" = SD
    test -b "$TF_DEV"
    if [ "$TF_DEV" != "/dev/$TF_DISK" ]; then
        test "$(lsblk -ndo PKNAME "$TF_DEV")" = "$TF_DISK"
    fi
    if findmnt -rn -S "$TF_DEV"; then
        echo 'Device is already mounted; identify its purpose first.' >&2
        exit 1
    fi
    if mountpoint -q "$TF_MOUNT"; then
        echo 'Mountpoint is in use; identify its purpose first.' >&2
        exit 1
    fi
    mkdir -p "$TF_MOUNT"
    FSTYPE=$(blkid -p -s TYPE -o value "$TF_DEV")
    case "$FSTYPE" in
        ext4|exfat|vfat) ;;
        *) echo 'Filesystem is unidentified or outside this example.' >&2; exit 1 ;;
    esac
    mount -t "$FSTYPE" -o rw,nosuid,nodev,noexec "$TF_DEV" "$TF_MOUNT"
    findmnt -rn -M "$TF_MOUNT" -o SOURCE,TARGET,FSTYPE,OPTIONS
    df -h "$TF_MOUNT"
)
```

Before writing, confirm that SOURCE is the selected TF filesystem device, the filesystem type is correct, and OPTIONS contains `rw`. This data-only mount uses `noexec`, not execution of programs stored on the card. Mounting hides existing files beneath the mountpoint, so use a dedicated empty directory.

For viewing existing files only, replace `rw,nosuid,nodev,noexec` with `ro,noload,nosuid,nodev,noexec` for ext4 or `ro,nosuid,nodev,noexec` for exFAT/FAT32. For ext4, `ro` alone may still replay the journal and write to the card. `noload` skips journal recovery: an uncleanly unmounted card can expose inconsistent data and is not suitable for normal-use acceptance in that state. Back up important or damaged data before handling the unmounted filesystem.

Manual mounts do not automatically survive reboot. Check again after every boot or card replacement. Do not copy a generic `/etc/fstab` entry blindly: BSP mount timing, missing-card handling, UUID uniqueness, and application startup prerequisites require separate confirmation.

## 5. Save Acquisition Data to the Card

First follow [Data Saving](../usage/save-data-guide.md) for runtime-package, camera/IMU, `cam-service`, tool, and capacity checks. Keep `cam-service` running and avoid concurrent camera applications. Merely changing the default path to an unmounted directory is insufficient.

This example creates the output directory and starts MP4 recording only after checking the TF mount identity and writability:

```sh
(
    set -eu
    test "$(cat "/sys/class/block/$TF_DISK/device/type")" = SD
    test -b "$TF_DEV"
    if [ "$TF_DEV" != "/dev/$TF_DISK" ]; then
        test "$(lsblk -ndo PKNAME "$TF_DEV")" = "$TF_DISK"
    fi
    EXPECTED=$(lsblk -dnro MAJ:MIN "$TF_DEV")
    test -n "$EXPECTED"
    test "$(findmnt -rn -M "$TF_MOUNT" -o MAJ:MIN)" = "$EXPECTED"
    case ",$(findmnt -rn -M "$TF_MOUNT" -o OPTIONS)," in
        *,rw,*) ;;
        *) echo 'TF mount is not writable; stop saving.' >&2; exit 1 ;;
    esac
    df -h "$TF_MOUNT"
    mkdir -p "$TF_MOUNT/robobaton"
    cd /root/demo  # replace with the actual full runtime package directory
    ./sensor_demo --fps 30 --codec h264 \
        --sample-rate-hz 800 --print-rate-hz 0 \
        --record-mp4-dir "$TF_MOUNT/robobaton/run_mp4"
)
```

For a ROS1 bag, replace the final `--record-mp4-dir ...` with `--record-bag "$TF_MOUNT/robobaton/run.bag"`; do not enable both modes together. With YAML, set `save_data.save_path` to an absolute path under the confirmed TF mount and still check mount identity before starting.

Use `Ctrl+C` to finish foreground recording normally, then wait for finalization. Check the exit status, `SENSOR_MP4_RESULT` or `SENSOR_BAG_RESULT`, and final health counters as described in Data Saving. File presence, playable RTSP, and a successful mount are not substitutes for complete-save criteria. Before a production-length session, validate sustained throughput, free capacity, and data integrity under the actual acquisition load; card-label speed ratings do not guarantee zero loss.

## 6. Unmount and Remove

1. Finish every application writing to the card normally and wait for recorder finalization. Stopping `cam-service` is not a substitute for stopping recording.
2. Move the current and other terminals outside the mountpoint, then sync and unmount:

   ```sh
   cd /
   sync
   umount "$TF_MOUNT"
   findmnt -rn -M "$TF_MOUNT"
   ```

3. Unmounting is complete only if `umount` succeeds and the last command reports no mount record. For `target is busy`, inspect users with `fuser -m "$TF_MOUNT"` and exit each application through its own normal protocol. Do not kill unknown processes or bypass the problem with forced/lazy unmounting.
4. On hardware matching the confirmed TF repair, remove the card only after successful unmount and confirmation that no users remain. Shut down and disconnect power on other hardware. Never remove it or cut power during writes; after reinsertion, repeat enumeration and mount-identity checks from section 2.

## 7. Troubleshooting

| Symptom | Checks |
|---|---|
| Card inserted but no SD block device | Shut down and disconnect power, then check orientation and seating. Inspect the card with a reader or try a known-good card. After restarting, inspect `dmesg`, `/sys/class/mmc_host/`, and `device/type`. Formatting does not solve failure to enumerate. |
| MMC host exists but no SD device | A host only establishes controller presence. Read `/sys/kernel/debug/mmcN/ios` if the BSP exposes it. `0 Hz` or `power mode: off` alone cannot distinguish contact, detect-signal, power, or driver causes. Product support should inspect the actual device tree and card-detect path; do not arbitrarily toggle GPIO, unbind the driver, or rescan. |
| SD device exists but no `p1` | The card may lack a partition table or it was not parsed. Inspect with `lsblk`/`blkid` without writing, then back up before changes. |
| `unknown filesystem type` / `wrong fs type` | Cross-check the partition, `blkid`, and kernel support; filesystem damage is another possibility. Do not repeatedly force mounting, repair a mounted filesystem, or immediately format. |
| `Read-only file system` / I/O error | Inspect mount options, the `lsblk` RO column, and kernel logs. Stop saving and back up first; do not force a remount to hide media errors. |
| Failure near 4GiB per file | Check for FAT32; after backup, consider ext4/exFAT supported by the target BSP. |
| Directory survives reboot but the card is unmounted | Manual mounts are not persistent. Repeat sections 2–4. A directory or free space reported by `df` does not prove TF backing; verify the exact mountpoint and device number. |

See [Linux mount(8)](https://manpages.debian.org/bookworm/mount/mount.8.en.html) for mount options and ext4 read-only journal behavior. The TF hot-plug repair is user-confirmed, not a new real-board retest by this guide. It implies neither a new hardware version nor acceptance of every card model, capacity, automatic mount, or long recording. Actual detection and functionality still apply; see {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.
