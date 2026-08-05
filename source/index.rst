RoboBaton 4P 产品文档
=======================

这是 RoboBaton 4P 的公开在线产品文档，面向拿到 4P 硬件、non-ROS demo 或 ROS2 demo 的用户。文档目标是帮助用户完成部署、运行、参数配置和常见问题排查。

公开边界
--------

本文档只记录用户可执行、可理解、可复现的公开内容：运行包目录、部署命令、启动命令、公开参数、RTSP 地址、ROS2 topics 和用户侧排查步骤。内部测试资料、原始证据、历史调试记录、未公开板端路径和维护记录不属于本仓公开内容。

代码仓库
--------

- non-ROS Demo：`RoboBaton_4p_demo <https://github.com/Hessian-matrix/RoboBaton_4p_demo>`_
- ROS2 Demo：`RoboBaton_4P_ROS2_demo <https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo>`_，发布四目 NV12/raw+compressed 图像、CameraInfo、IMU 和温度 topic。
- 公开文档：`4P_doc <https://github.com/Hessian-matrix/4P_doc>`_，维护产品兼容、部署、安全、数据/API、故障排查和发布状态说明。


.. toctree::
   :maxdepth: 1

   Product_Introduction
   product-and-compatibility
   hardware-and-safety
   first-boot
   system-time-sync
   quick-start
   non-ros-demo
   ros2-demo
   troubleshooting
   code-and-interfaces
   changelog
   release-and-support
