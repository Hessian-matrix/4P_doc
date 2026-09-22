# System Flashing

(system-flashing)=

```{note}
System flashing is the whole-device operation of writing the RoboBaton 4P factory system image to the on-board eMMC, used to restore the factory system, upgrade the system version, or repair a system that cannot boot normally. This operation overwrites the on-board system partition and differs from the deployment, upgrade, and rollback of the runtime packages (`/root/demo`, `/root/ros2_demo`); for the latter see [Deployment, Upgrade, and Rollback](../development/deployment-and-upgrade.md).
```

```{warning}
Flashing overwrites the on-board eMMC and erases all user data in it. Power must remain stable during the write; do not power off, unplug the flashing medium, or force-restart, otherwise the device may fail to boot. Use only the `v1.3.0` image published on this page; do not use images for other X5 board forms.
```

## 1. Scope

This flashing flow applies only to the original product board; the factory system image applies only to the original product board and does not guarantee compatibility with other target boards, see [Product Version and Compatibility](../getting-started/product-and-compatibility.md).

Typical scenarios requiring system flashing:

| Scenario | Description |
|---|---|
| System cannot boot normally | Cannot be recovered via [Troubleshooting](../troubleshooting.md) and needs the system rewritten |
| Restore factory system | Restore the on-board system to factory state |
| System version upgrade | Upgrade the system to a new factory image version |

When only upgrading the non-ROS demo or the ROS2 runtime package, system flashing is **not** required; runtime packages use the whole-package deployment, verification, and rollback flow, see [Deployment, Upgrade, and Rollback](../development/deployment-and-upgrade.md).

## 2. Current Image Release Status

- The system image matching on-device software `v1.3.0` ships with this release; the image package name is `product-20260918-v1.3.0.tar.gz`.
- The image applies only to the original product board and does not guarantee compatibility with other target boards ([Product Version and Compatibility](../getting-started/product-and-compatibility.md)).

## 3. Image Acquisition and Verification

Image: [V1.3.0 image](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/product-20260918-v1.3.0.tar.gz)
Flashing tool: [D-Robotics official flashing tool](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/xburn-gui_1.2.1_x64-setup.exe)

## 4. Pre-Flashing Preparation

- Download the flashing tool and image file.
- Install the flashing tool by double-clicking xburn-gui_1.2.1_x64-setup.exe to install it locally.
- Install the corresponding driver:

  ```{figure} ../../image/driver.png
  :alt: Driver installation interface required by the xburn flashing tool

  Driver installation interface required by the xburn flashing tool.
  ```

- Flashing erases all user data in on-board storage; first back up the data that must be kept (e.g. site configuration and evidence under `/userdata/`).
- Confirm the image matches the target board: the image comes from this page's `v1.3.0` link and the device is an original board.

## 5. Flashing Steps

1. Connect the on-device debug-uart and usb-c.
2. Select the serial port and image path:

   ```{figure} ../../image/burn.png
   :alt: xburn flashing tool main interface, configuring serial port and image path

   xburn flashing tool main interface, configuring serial port and image path.
   ```

3. Click flash and wait for flashing to complete.
4. Reboot after flashing completes.

Note: use only the `v1.3.0` image published on this page; do not flash unconfirmed images yourself.

## 6. Post-Flashing Acceptance

After flashing completes, complete the minimal system check per [First Power-On](../getting-started/first-boot.md):

```bash
hostname
date
df -h /
pgrep -a cam-service
```

## 7. When the Problem Persists

If the device cannot boot or is abnormal after flashing, stop repeated flashing, preserve the site, and collect:

- `board_id` and `/etc/version`;
- Image source and verification result;
- Flashing tool output and exit code;
- Whether a reboot was actually run and the post-reboot symptoms;
- If available, DEBUG_UART/serial site information.

Submit it with the feedback checklist in [Release, License, and Support](../release-and-support.md) to product support. Do not repeatedly flash other X5 images without product-support confirmation.
