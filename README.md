# PitNode

PitNode is an open-source DIY BBQ thermometer based on the Raspberry Pi Pico 2 W.

It is intended for makers and technically experienced users who want to build
their own temperature monitoring system for BBQ and smoking applications.

There is also a separate hardware repository available for the PitNode Pico Extension Board.

For more information and documentation see

https://www.pitnode.de/

"PitNode" is the project name used for this open-source project.

This project is not a finished consumer product, but a DIY project intended for makers and technically experienced users.

## Project Status

Status: **Active development**

- First hardware prototype is running
- Core functionality (measurement, alarms, UI, WiFi) is implemented
- APIs and internal structure may still change
- Not yet considered feature-complete or production-ready

## Features
- Software ready to upload to a Raspberry Pi Pico 2W
- Monitoring of core temperature on 3 channels
- Additional channel for thermocouple probes type K for grill temperature monitoring
- Compatible with many NTC based probes  
  (RTD probes possible in theory, not yet implemented)
- Large 2,8" color LCD Touch display
- Temperature readout on display
- Target core temperatures can be set individually for each channel
- Acoustic alarm function when target core temperature is reached
- Wifi connection (obfuscated password)
- Webserver for accessing via browser
- Live update via websocket
- PCB layout available in the hardware repository
- Case files for 3D print available in the hardware repository

## Getting Started

This project targets MicroPython on the Raspberry Pi Pico 2 W.

Basic steps:
1. Flash MicroPython to the Pico 2 W
2. Upload the software using `mpremote`
3. Configure probes in config.py
4. Power on and BBQ

Detailed instructions are available at:
https://www.pitnode.de/

## License
This project is licenced under different licenses.
SW/FW is licenced under - AGPL-3.0-or-later
HW design files are licensed under - CC BY-NC-SA 4.0

See `LICENSE.md` for details.

## Third-Party Software

This project includes third-party components licensed under different terms
(e.g. MIT).

See `THIRD_PARTY_NOTICES.md` for a full list.

## Disclaimer
Before building or using the PitNode project based on the information published here or on GitHub, please ensure that doing so is permitted in your local jurisdiction. Local laws, regulations, or patents may apply.  
This project and all associated documentation are provided “as is”, without warranty of any kind, express or implied, including but not limited to warranties of merchantability or fitness for a particular purpose.  
PitNode is a DIY project intended for technically experienced users. You are responsible for ensuring correct assembly, configuration, and safe operation. The author does not guarantee that the project is safe, legal, or suitable for any particular use case.

## Credits
Thanks to OpenAI / ChatGPT for design discussions and debugging support.

## Copyright
Copyright (c) 2026 Philipp Geisseler