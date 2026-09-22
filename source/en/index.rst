RoboBaton 4P Product Documentation
==================================

This is the public online product documentation for RoboBaton 4P, aimed at users
who have the 4P hardware, the non-ROS demo, or the ROS2 demo. It helps with
deployment, operation, parameter configuration, and common troubleshooting.

Public boundary
---------------

This documentation records only public, user-runnable, understandable, and
reproducible content: runtime package layout, deployment commands, startup
commands, public parameters, RTSP addresses, ROS2 topics, and user-side
troubleshooting steps.

Code repositories
-----------------

- non-ROS Demo: `RoboBaton_4p_demo <https://github.com/Hessian-matrix/RoboBaton_4p_demo>`_
- ROS2 Demo: `RoboBaton_4P_ROS2_demo <https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo>`_, publishing four-camera NV12/raw+compressed images, CameraInfo, IMU, and temperature topics.

.. toctree::
   :maxdepth: 1

   getting-started/Product_Introduction
   getting-started/product-and-compatibility
   getting-started/hardware-and-safety
   getting-started/first-boot
   getting-started/wifi-configuration
   time-sync/system-time-sync
   quick-start
   development/code-and-interfaces
   troubleshooting
   ops/fix-and-upgrade
   changelog
   release-and-support
