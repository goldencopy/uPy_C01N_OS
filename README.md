# uPy_C01N_OS
Updated: 31 July 2024

- Added BLE functionality to the C01N, and a camera remote control app for Fujifilm cameras (tested with GFX100s).
- Updated MicroPython core for BLE support

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
