# **blind\_assistance\_helmet (Smart Blind Assistance Helmet Based on D-Robotics RDK X5)**

## Project Overview

This work is an entry for the Application Track of the 2026 National Embedded System Design Competition. It implements an all-in-one wearable smart blind assistance helmet built on the D-Robotics RDK X5 embedded development kit, targeting outdoor and indoor travel scenarios for visually impaired people.

Adopting a distributed multi-node architecture based on ROS 2 Humble, the system integrates seven core capabilities: dual YOLOv5 edge-side object detection, ATGM336H satellite navigation, Baidu walking route planning, MQTT cloud positioning reporting, end-to-end ASR/TTS voice interaction, dual-AI scheme combining local offline LLM and cloud vision LLM, and WeChat Mini Program remote guardian monitoring. It forms a complete closed-loop system that delivers obstacle detection for indoor and outdoor environments, real-time voice navigation, scene semantic image interpretation, and remote location tracking for family guardians.

All hardware components are highly integrated inside a 3D-printed helmet housing. Equipped with a 3000 mAh lithium battery, the device delivers 4 hours of continuous operation under full load and 8 hours of standby time under light load. All software modules are fully decoupled; a single launch file starts all service nodes with one click, eliminating hardware resource contention and repetitive voice broadcast interference, and adapting to all daily indoor and outdoor travel scenarios.

## Core Functions

### 1 Machine Vision Environmental Perception (Dual YOLOv5s Models)

* Outdoor detection targets: tactile paving, zebra crossings, road barriers, traffic lights
* Indoor detection targets: emergency exits, accessibility facilities, restroom signage for men and women
* Trigger-based inference: the system automatically broadcasts the position (Left / Center / Right) of detected objects via voice
* NMS (Non-Maximum Suppression) + short-time message deduplication to avoid redundant voice alerts

### 2 Satellite Voice Navigation System

* ATGM336H GPS module with weighted filtering to suppress positioning drift, achieving a horizontal positioning accuracy of 2.5 m
* Baidu Map API: WGS84 / BD09 coordinate conversion, walking route planning, segmented voice navigation prompts
* Wake word activation for navigation; supports oral destination input with natural phrases such as "Navigate to XX"
* Real-time longitude and latitude data uploaded to the cloud via MQTT (Huawei IoTDA) at fixed intervals

### 3 End-to-End Voice Interaction

* Real-time ASR speech-to-text and TTS speech synthesis, with single-round latency below 300 ms
* Isolated wake words for independent functional triggering without mutual interference:

  * Start / Activate / Tactile Paving: Enable 10-second cyclic road condition detection
  * Stop / End: Disable cyclic visual detection
  * Describe: Call cloud Doubao vision LLM to interpret the captured scene image
  * Navigate: Wake up voice navigation module and receive destination voice input
* Global singleton ASR/TTS service: all business modules publish broadcast text to a unified topic without overlapping voice playback

### 4 Dual Large Model Fusion Scheme

1. Local Offline Model: Quantized Tongyi Qwen 2.5 0.5B LLM, supporting offline voice Q\&A without network access
2. Cloud Online Model: Doubao doubao-seed vision large model, generates natural language scene descriptions from captured images

### 5 WeChat Mini Program Remote Guardian Monitoring

* Lightweight MQTT client subscribes to cloud positioning data, rendering real-time location and travel trajectories on Tencent Maps
* Family guardians can view the user’s location in real time via WeChat without installing extra mobile apps, with positioning latency under 1.5 s

## Hardware Bill of Materials

|Hardware|Model \& Specification|Function|
|-|-|-|
|Main Controller|D-Robotics RDK X5|AI inference, ROS node computation, network communication|
|Positioning Module|ATGM336H|GPS satellite positioning, NMEA 0183 protocol output|
|Camera|USB HD Camera (640 × 480)|Environmental image capture, input for AI inference|
|Audio Module|3.5 mm Microphone + Headset|ASR audio pickup, TTS voice output|
|Power Supply|3000 mAh Lithium Battery with Voltage Regulator Module|Power supply for the whole device|
|Auxiliary Hardware|STM32F1 adapter board, 3D-printed helmet shell, shock-absorbing foam|Hardware wiring, wearable mechanical structure, anti-interference|

## Software Architecture (ROS 2 Humble)

### Layered Design

1. Hardware Perception Layer: usb\_cam image node, GPS reading node, SenseVoice ASR audio node
2. Local Service Layer (all decoupled independent nodes)

   * blind\_road\_detector: Three-YOLO fusion inference node for tactile paving and obstacle detection
   * vision\_controller\_blind: Vision control node for blind assistance
   * image\_upload\_analyzer: Image analysis node interfacing with Doubao cloud vision LLM
   * vision\_controller\_llm: Control node for visual LLM scene description
   * navigator\_node: Core navigation node (GPS filtering, route planning, MQTT cloud upload)
   * voice\_controller\_node: Voice control node for navigation wake word parsing
   * hobot\_tts: Global singleton voice broadcast node
3. Cloud Forwarding Layer: Huawei IoTDA MQTT service, receiving JSON packets of positioning data
4. Mini Program Terminal Layer: WeChat Mini Program, rendering real-time device location and trajectories on maps

### Topic Isolation Design (Core Solution to Eliminate Duplicate Broadcasts)

1. Two independent topics for visual AI outputs with dedicated subscriber controllers:

   * Tactile paving detection outputs to `/image\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_ai\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_blind` → only subscribed by blind assistance vision controller
   * Doubao scene description outputs to `/image\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_ai\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_llm` → only subscribed by LLM vision controller
2. All business modules send broadcast text to the unique global topic `/tts\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_text`, processed by a single TTS node to eliminate duplicate voice playback from multiple modules
3. The navigation module does not subscribe to visual AI topics; message filtering logic is deployed in the vision controller to prevent cross-topic message forwarding between modules

## Repository Directory Structure

```
blind\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_assistance\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_helmet
├── launch/
│   └── all.launch.py       # Master launch file to start all nodes with one click
├── blind\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_road\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_test/               # Indoor \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\& outdoor dual-YOLO visual detection package
│   ├── blind\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_road\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_test/
│   │   ├── blind\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_road\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_detector.py  # Main node for three-model fusion inference
│   │   └── vision\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_controller.py    # Voice controller for blind assistance vision
│   └── models/                    # Quantized YOLOv5s bin model files
├── image\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_upload\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_analyzer/         # Doubao cloud vision LLM integration package
│   ├── image\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_upload\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_analyzer/
│   │   ├── image\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_upload\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_analyzer.py
│   │   └── vision\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_controller.py
│   └── config/ark\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_api.yaml        # Configuration file for Doubao API credentials
├── voice\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_navigation/              # GPS navigation \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\& MQTT cloud upload package
│   ├── voice\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_navigation/
│   │   ├── navigator\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_node.py      # GPS filtering, route planning, MQTT reporting
│   │   ├── voice\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_controller\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_node.py # Navigation wake word parser
│   ├── gps/                       # NMEA parsing and weighted filtering logic
│   ├── map/                       # Encapsulated Baidu Map API interfaces
│   └── config.py                  # MQTT \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\& Huawei IoT cloud configuration
├── CMakeLists.txt \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\& package.xml   # ROS package compilation configuration
└── README.md                      # This project documentation
```

## Quick Deployment \& Execution

### Environment Dependencies

1. Hardware: D-Robotics RDK X5 pre-installed with ROS 2 Humble and Hobot DNN inference library
2. Python Dependencies

bash
pip install paho-mqtt opencv-python numpy requests

3. Model File Placement Path

/userdata/blind\_road\_test/blind\_road\_test/models/



Model files included:

* yolov5s\_2.bin (Outdoor tactile paving detection model)
* traffic\_yolov5s\_new.bin (Traffic object detection model)
* signs\_yolov5s\_new.bin (Indoor signage detection model)

### Compilation \& Startup Steps

1. Place the entire project folder into the `src` directory of the RDK X5 ROS workspace
2. Compile all functional packages

bash
colcon build --packages-select blind\_road\_test image\_upload\_analyzer voice\_navigation



3. Source environment variables

bash
source install/setup.bash



4. One-click launch of all hardware and service nodes

bash
ros2 launch all.launch.py



## Operation Instructions

### 1 Cyclic Road Condition Detection

Speak the wake word into the headset: `Start` / `Activate` / `Tactile Paving`
The system captures images every 10 seconds to detect tactile paving, zebra crossings, road barriers, traffic lights, restroom signs, accessibility facilities and emergency exits, and broadcasts their horizontal positions via voice.
Speak `Stop` / `End` to disable cyclic visual detection.

### 2 Scene Semantic Description

Speak the wake word: `Describe`
The device captures the current frame, invokes the cloud Doubao vision LLM, and broadcasts full natural language descriptions of all objects within the frame.

### 3 Voice Navigation

1. Speak the wake word `Navigate`; the TTS module prompts: "Navigation activated, please state your destination."
2. Directly speak the destination, supporting natural sentence formats such as:

   * Navigate to XX Library, XX City, XX Province
3. The system automatically executes coordinate conversion and walking route planning, broadcasting real-time turning prompts and distance reminders throughout the journey; navigation terminates automatically upon arrival at the destination.
4. During navigation, GPS coordinates are uploaded to Huawei Cloud every 3 seconds via MQTT, enabling real-time location viewing on the WeChat Mini Program.

## Key Optimizations \& Solutions to Development Challenges

1. Zero Duplicate Broadcast Architecture: Topic isolation, message filtering in controllers and singleton global TTS completely eliminate overlapping voice playback from multiple nodes
2. Computing Resource Scheduling Optimization: Visual detection assigned high processing priority, positioning reporting frequency reduced to avoid frame stalling during multi-model parallel inference
3. GPS Data Smoothing: Weighted average filtering suppresses satellite positioning jitter for stable navigation prompts
4. Low-Power Design: Inference frame rate reduced during idle periods, achieving 4–8 hours of continuous battery life
5. MQTT Automatic Reconnection: Built-in reconnection logic for MQTT clients to resume cloud positioning uploads automatically after Wi-Fi switching
6. Fault Tolerance Mechanism: Exception handling for model loading failures, image decoding errors and API request failures; single module crashes will not break the entire node system

## Future Expansion Directions

1. Add emergency wake word `Help` to push real-time location alerts to bound contacts via the Mini Program
2. Implement electronic fence function: push alarm notifications to the guardian Mini Program when the user moves outside pre-defined safe zones
3. Add text-to-voice two-way communication channel for family guardians to send voice messages remotely
4. Integrate low-power MCU standby wake-up hardware to drastically extend sleep-mode battery life
5. Expand detection categories for daily obstacles and implement priority strategies for target voice alerts

## Competition Information

* Contest: 2026 National Embedded System Design Competition, Application Track
* Main Control Platform: D-Robotics Hobot RDK X5
* Development Frameworks: ROS 2 Humble, Hobot DNN, YOLOv5, MQTT, Baidu Map Open Platform, Huawei IoTDA

## References

\[1] D-Robotics Official RDK X5 Development Manual
\[2] ROS 2 Humble Official Documentation
\[3] ATGM336H GPS Module Datasheet
\[4] Baidu Map Web Service API Documentation
\[5] Huawei Cloud IoTDA MQTT Device Access Specification


