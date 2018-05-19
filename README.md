# rpi_epd2in7
<img align="right" src="https://raw.githubusercontent.com/elad661/ghpages_test/master/rpi_epd.gif" alt="an animation showing rpi_epd2in7 in action">

A python library for interfacing with the "[Waveshare 2.7inch e-Paper HAT](https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT)" display from the Raspberry Pi.

This library is based on the original code by Waveshare, heavily modified by Elad Alfassa.

Note that Waveshare has a lot of different models of e-paper displays, and this library only supports the 2.7inch b/w model.

This MIT-licensed library comes with absolutely no warranty and no gurantees.
Bugs or improper usage might mess up your display or even brick it entirely.

## Changes comparing to the original library
* Cleaner, more pythonic code
* Easier to use API
* Support partial display updates (no need to flush the entire screen)
* Support fast updates (not going through the entire flush cycle)
* Python 3 support

## Installation

Install the dependencies from `requirements.txt`

`pip3 install -r requirements.txt`

on Raspbian, compiling Pillow might fail due to missing dependencies. Install them with
`sudo apt-get install python3-dev libjpeg-dev zlib1g-dev` and re-run the pip command.

You can also install `python3-pil` from apt-get, but the version in debian is very old, so it's better to install from pip.

And then run `python3 setup.py install`

Make sure to enable the SPI interface in rpi-config.

For connecting the screen to your pi see the [Waveshare 2.7inch e-Paper HAT](https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT)
and the [Raspberry Pi pinout diagrams](https://elinux.org/RPi_Low-level_peripherals) aplicable for your model.

## Usage
Because this library uses GPIO, and the GPIO library it uses uses mmap on /dev/mem (ugh) to access GPIO, you have to run as root (with sudo).

See complete demos in `demos/`.

Initialize the hardware and the EPD object:

```python
from rpi_epd2in7.epd import EPD
epd = EPD()
epd.init()
```

Drawing is done using [Pillow](http://python-pillow.org/) Image objects
(see [Pillow documentation](https://pillow.readthedocs.io/en/5.1.x/index.html) for detailed explanations).

Make sure to create the image with mode `"1"`, meaning it's 1-bit color (black/white), and with the appropriate size for the dispaly.
The 2.7 inch display supported by this library has a resolution of `176x264`.

You can use `epd.width` and `epd.height` instead of hardcoding these numbers.

```python
image = Image.new('1', (epd.width, epd.height), 255)
draw = ImageDraw.Draw(image)
```

For this example, we'll draw a black sqaure in the middle of the screen:

```python
x1 = epd.width/2 - 32
y1 = epd.height/2 - 32
x2 = x1+64
y2 = y1+64
draw.rectangle((x1, y1, x2, y2), fill=0)

# Now send the image to the screen:
epd.smart_update(image)
```

Note that we used `epd.smart_update(image)`, which automatically decide which method to use to display the image on the screen.

Another possibility is to use `epd.display_frame(image)` which does a full screen refresh & flush every time its called.

`smart_update` is the recommeded way to send images to the display, as it hides away the complexity of doing partial updates.

When done using the EPD, or when you think there's going to be a long time until the next update,
you can call `epd.sleep()` to put the chip into deep-sleeep mode. To wake up the screen from deep sleep, call `epd.init()`.

### Note on different refresh options

On a normal refresh, the only option available in the original Waveshare code, the entire screen is flushed and refreshed in a lengthy
flush cycle - inverse image, black, white, black again, etc. this process takes a couple of seconds, but reduces burn-in and ghosting.

Use the normal refresh explicitly by calling `epd.display_frame(image)`.

Another option, that was documented in the [specification from Waveshare](https://www.waveshare.com/w/upload/2/2d/2.7inch-e-paper-Specification.pdf) 
is partial refresh. Partial refresh does the same flush cycle as the full refresh, but only refreshes the part of the screen that actually changed,
making it a bit faster and less distracting (because only a smaller area of the screen would flash).

You can call partial refresh explicitly by calling `epd.display_partial_frame(image, x, y, h, w)`,

where `x` and `y` are the top left corner of the refreshed area, `h` is the height of the area and `w` is the width.

Another option, that was not documented in the specification but [discovered by Ben Krasnow](http://benkrasnow.blogspot.co.il/2017/10/fast-partial-refresh-on-42-e-paper.html)
is quick partial refresh by modifying the lookup tables the controller uses to determine the waveform for the flush cycle.
See [Ben Krasnow's video on the subject](https://www.youtube.com/watch?v=MsbiO8EAsGw) for more technical details.

This mode is much faster than the default flush cycle, **but may cause burn-in** if a "slow" refresh is not done "soon" afterwards - so don't leave
the display idling for days after one of these flushes! You can enable usage of this mode by specifying `fast=True` in the parameters for `epd.display_partial_frame()`.

This library also comes with one convinent method which was not included in the original, `epd.smart_update(image)`. It will automatically
figure out if a full or partial refresh is needed, and will use the faster refresh in some cases.

If you don't trust the faster refresh and want to be as safe as possible, you can disable it by creating the EPD object like so: 

```python
epd = EPD(fast_refresh=False)
```

You can also enable or disable fast refresh after the `EPD` object was created by modifying the `fast_refresh` variable on the EPD object: `epd.fast_refresh = False`

#### Timing

* Full refresh: ~10 seconds
* Partial refresh: ~7 seconds (depends on the size of the refreshed area)
* Fast partial refresh: ~500ms (depends on the size of the refreshed area)

All refresh methods are synchrounous and will wait until the display is done updating.
