# PitNode

![PitNode](/assets/images/PitNode_Logo_Master_black_250_x_100.png)

PitNode is an open-source DIY BBQ thermometer. It is based on the RPi Pico 2W (2350) microcontroller
but can be easily adapted for other platforms.

It is intended for makers and technically experienced users who want to build
their own temperature monitoring system for BBQ and smoking applications.

There is also a separate hardware repository available for the [PitNode Pico Touch Extension Board](https://github.com/PitNode/PitNode-pico-touch-eb).

For more information and documentation see

https://www.pitnode.de/

"PitNode" is the project name used for this open-source project.

> [!NOTE]
> This project is not a finished consumer product, but a DIY project intended for makers and technically experienced users.

## Project Status

Status: **Active development**

- First hardware prototype is running
- Core functionality (measurement, alarms, Touch-UI, WiFi, Webserver, Websocket) is implemented
- APIs and internal structure may still change
- Not yet considered feature-complete or production-ready

## Features
### Functional
- Monitoring of core temperature on 3 channels
- Compatible with many NTC based probes  
  (RTD probes possible in theory, not yet implemented)
- Additional channel for thermocouple probes type K for grill temperature monitoring
- Temperature readout on a colored touch display
- Target core temperatures can be set individually for each channel
- Acoustic and optical alarm function when target core temperature is reached
- Wifi connection (obfuscated password storage)
- Webserver for accessing via browser with smartphone or other device with nice web UI
- Live update via websocket
- PCB layout available in the hardware repository
- Enclosure files for 3D print available in the hardware repository

### Installation
- Software ready to upload to a Raspberry Pi Pico 2W with included deployment script

## Getting Started

This project targets MicroPython on the Raspberry Pi Pico 2 W. It should be possible to port it to other microcontrollers. The documentation is assuming that you are using the [PitNode Pico Touch Extension Board](https://github.com/PitNode/PitNode-pico-touch-eb).

**Basic steps:**  
Prerequisites:
* `mpremote`is installed
* You have a compatible HW available.

1. Flash MicroPython to the Pico 2 W. Detailed instructions can be found on [micropython page](https://micropython.org/download/RPI_PICO2_W/)
1. Clone this repository into you workspace  
`git clone https://github.com/PitNode/PitNode-SW.git`
1. Configure your NTC probes in config.txt
1. Make sure you eventually deleted all files from the Pico.
1. Upload the software using the `deploy.sh` script  
The script will upload all needed data to your Pico by using mpremote and auto detect the HW. Make sure only one Pico is connected to avoid unintended uploads.
1. Power on and BBQ

Detailed instructions are available at:
https://www.pitnode.de/

## License
This project is licenced under different licenses.
SW is licenced under - AGPL-3.0-or-later
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