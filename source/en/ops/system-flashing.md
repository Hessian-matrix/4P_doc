# System Flashing

(system-flashing)=

```{warning}
The V2 system image has not been released. No public V2 image download, checksum, or confirmed flashing procedure is currently available. Do not write an image or repair package unless its compatibility with the current hardware is confirmed.
```

## V2 Image Release Status

| Item | Status |
|---|---|
| V2 factory system image | Not yet released |
| Version, package name, and download URL | To be published when the image is ready |
| SHA-256 and supported hardware | To accompany the official image |
| Flashing tool, connections, and procedure | To be confirmed with the matching V2 image |
| Flashing screenshots and interface diagrams | To be confirmed with the matching V2 image |

Flashing overwrites the on-board eMMC system and user data; back up data before an authorized operation. Until the image is published, do not perform recovery using unconfirmed screenshots, package names, or flashing procedures. Contact [Product Support](../release-and-support.md) if the board cannot boot.

## Runtime Package Updates

Updating only the non-ROS or ROS2 runtime package does not require system flashing; use [Deployment, Upgrade, and Rollback](../development/deployment-and-upgrade.md). Software versions, documentation revisions, and system image versions are identified separately; this page does not change them.
