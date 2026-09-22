# ISP Image Quality Fix

(isp-image-quality-fix)=

```{note}
This page provides an updated SC132GS ISP tuning parameter file `sc132gs_tuning.json`, used to improve the image quality of the four cameras in some lighting scenarios. This fix only replaces the on-device ISP parameter file; it does not modify the demo runtime package and does not require redeploying `/root/demo`.
```

```{warning}
The X5 must be rebooted for the replacement to take effect. Keep power stable during the operation; do not replace while a save task or camera long-run test is in progress. Back up the original file before replacing.
```

## 1. Scope

The fix package is in the `RoboBaton_4p_demo` repository:

```text
patch/sc132gs_tuning.json
```

It applies only to the following targets:

| Item | Requirement |
|---|---|
| Board form | `board_id=0x0505` or `board_id=0x0506` (verified on `0x0506`, `0x0505` to be confirmed) |
| Root filesystem | Buildroot with `/etc/version` containing `PL5.1` |
| Camera | SC132GS four-camera, with `/usr/hobot/lib/sensor/sc132gs_tuning.json` on-device |

Before replacing, confirm `/usr/hobot/lib/sensor/sc132gs_tuning.json` exists; if it does not, the board's ISP parameter layout differs — stop and contact product support.

## 2. Confirm Before the Fix

First exit the running camera application and data-saving task. Keep `cam-service` running; do not treat stopping `cam-service` as a fix step.

On the host, confirm the fix package comes from the product delivery package or an approved `RoboBaton_4p_demo` source package. The file SHA-256 should be:

```text
0424249f9dd100f0ae6e2926ebb6cb1a36eb6615ba03071fa705eec66a2f7589
```

In the host directory holding the file, run:

```bash
sha256sum sc132gs_tuning.json
```

The output must match the SHA-256 above. If it does not, stop and re-obtain the fix package.

## 3. Upload and Replace the On-Device File

### Host Terminal

Upload the file to the X5, then log into the device:

```bash
X5_IP=192.168.1.12  # change to the actual board address
scp sc132gs_tuning.json root@${X5_IP}:/tmp/sc132gs_tuning.json.new
ssh root@${X5_IP}
```

All commands from here until `reboot` run directly in this X5 SSH terminal.

### X5 On-Device SSH Terminal

Back up the original file, verify the new file, then replace:

```bash
cp -p /usr/hobot/lib/sensor/sc132gs_tuning.json \
      /usr/hobot/lib/sensor/sc132gs_tuning.json.bak_$(date +%Y%m%d_%H%M%S)
sha256sum /tmp/sc132gs_tuning.json.new
mv /tmp/sc132gs_tuning.json.new /usr/hobot/lib/sensor/sc132gs_tuning.json
sha256sum /usr/hobot/lib/sensor/sc132gs_tuning.json
```

The SHA-256 after replacement must still be `0424249f...`. The backup file is in the same directory as the replaced file and is used for rollback.

## 4. Reboot to Take Effect

ISP parameters are loaded at camera initialization; after replacement you must reboot:

```bash
reboot
```

After reboot completes, `cam-service` starts automatically with the system; restart your camera application (e.g. `/root/demo/sensor_demo`) and it runs with the new parameters.

## 5. Acceptance

Pull the four RTSP streams on ports `554–557` and observe, taking any one channel as an example:

```bash
ffplay -rtsp_transport tcp rtsp://<X5_IP>:554/PRR
```

Acceptance points:

- All four channels stream normally;
- Exposure is normal, highlights are not overexposed, and shadows have gradation;
- No obvious color cast, and white balance converges after lighting changes;
- Color reproduction and detail meet expectations.

If the image is abnormal, restore the old parameters via rollback first, then contact product support.

## 6. Effect Description

Compared with the old parameters, the new parameters update the enable state and parameters of the following ISP modules (summarized from the old/new file diff):

| Module | Change |
|---|---|
| AE auto exposure | Updated exposure-time table and gain-damping parameters to improve exposure convergence speed and stability |
| AWB white balance | Updated weight parameters to improve white-balance accuracy under mixed lighting |
| BLS black level, LSC lens shading correction, CCM color matrix | Enabled and updated parameters to improve shadow gradation and color reproduction |
| DMSC/CPD/EE/GC detail and dynamic-scene modules | Updated parameters to improve dynamic-scene performance and edge sharpness |

The effect is governed by the actual four-channel image after replacement; performance may vary under different lighting.

## 7. Rollback

After logging into the X5, run in the on-device SSH terminal:

```bash
ls -l /usr/hobot/lib/sensor/sc132gs_tuning.json.bak_*
mv /usr/hobot/lib/sensor/sc132gs_tuning.json.bak_<timestamp> \
   /usr/hobot/lib/sensor/sc132gs_tuning.json
reboot
```

Rollback uses the backup file created in step 3; a reboot is also required after restore.

## 8. When the Problem Persists

After logging into the X5, collect the following information and contact product support:

```bash
cat /sys/class/socinfo/board_id
cat /etc/version
sha256sum /usr/hobot/lib/sensor/sc132gs_tuning.json
ls -l /usr/hobot/lib/sensor/sc132gs_tuning.json*
```

Also provide before/after screenshots or recordings of the four RTSP streams.
