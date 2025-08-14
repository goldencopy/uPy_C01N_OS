# uPy_C01N_OS
Updated 14 Aug 2025

- General bug fixes for BLE Fujifilm remote control app (tested to work with GFX100s and GFX100sii, should work with most other Fujifilm cameras)
- App now stores previous pairing information for future reconnection without going through a new pairing sequence

Updated: 31 July 2024

- Added BLE functionality to the C01N, and a camera remote control app for Fujifilm cameras (tested with GFX100s).
- Updated MicroPython core for BLE support
- Also credits to [@gkoh](https://github.com/gkoh/)'s furble project for the Fuji pairing UUIDs (https://github.com/gkoh/furble/)

To get a basic flashing station make sure you have these dependencies

```
-> python3 
-> pip3
-> adafruit-ampy (through pip3)
-> esptool (through pip3)
```

Then get our stuff

```
git clone https://github.com/goldencopy/uPy_C01N_OS.git
cd uPy_C01N_OS

chmod +x flash.sh

./flash.sh /dev/<yourC01Nlocation>
```

ragulbalaji hojiefeng andreng
