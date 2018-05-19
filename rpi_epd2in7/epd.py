"""epd2in7 - e-paper display library for the Waveshare 2.7inch e-Paper HAT """
# Copyright (C) 2018 Elad Alfassa <elad@fedoraproject.org>
# This file has been heavily modified by Elad Alfassa for adding features,
# cleaning up the code, simplifying the API and making it more pythonic
# original copyright information below:

##
#  @filename   :   epd2in7.py
#  @brief      :   Implements for e-paper library
#  @author     :   Yehui from Waveshare
#
#  Copyright (C) Waveshare     July 31 2017
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
from __future__ import unicode_literals, division, absolute_import

import time
import spidev
from .lut import LUT, QuickLUT
import RPi.GPIO as GPIO
from PIL import ImageChops

# Pin definition
RST_PIN         = 17
DC_PIN          = 25
CS_PIN          = 8
BUSY_PIN        = 24


# Display resolution
EPD_WIDTH       = 176
EPD_HEIGHT      = 264

# EPD2IN7 commands
# Specifciation: https://www.waveshare.com/w/upload/2/2d/2.7inch-e-paper-Specification.pdf
PANEL_SETTING                               = 0x00
POWER_SETTING                               = 0x01
POWER_OFF                                   = 0x02
POWER_OFF_SEQUENCE_SETTING                  = 0x03
POWER_ON                                    = 0x04
POWER_ON_MEASURE                            = 0x05
BOOSTER_SOFT_START                          = 0x06
DEEP_SLEEP                                  = 0x07
DATA_START_TRANSMISSION_1                   = 0x10
DATA_STOP                                   = 0x11
DISPLAY_REFRESH                             = 0x12
DATA_START_TRANSMISSION_2                   = 0x13
PARTIAL_DATA_START_TRANSMISSION_1           = 0x14
PARTIAL_DATA_START_TRANSMISSION_2           = 0x15
PARTIAL_DISPLAY_REFRESH                     = 0x16
LUT_FOR_VCOM                                = 0x20
LUT_WHITE_TO_WHITE                          = 0x21
LUT_BLACK_TO_WHITE                          = 0x22
LUT_WHITE_TO_BLACK                          = 0x23
LUT_BLACK_TO_BLACK                          = 0x24
PLL_CONTROL                                 = 0x30
TEMPERATURE_SENSOR_COMMAND                  = 0x40
TEMPERATURE_SENSOR_CALIBRATION              = 0x41
TEMPERATURE_SENSOR_WRITE                    = 0x42
TEMPERATURE_SENSOR_READ                     = 0x43
VCOM_AND_DATA_INTERVAL_SETTING              = 0x50
LOW_POWER_DETECTION                         = 0x51
TCON_SETTING                                = 0x60
TCON_RESOLUTION                             = 0x61
SOURCE_AND_GATE_START_SETTING               = 0x62
GET_STATUS                                  = 0x71
AUTO_MEASURE_VCOM                           = 0x80
VCOM_VALUE                                  = 0x81
VCM_DC_SETTING_REGISTER                     = 0x82
PROGRAM_MODE                                = 0xA0
ACTIVE_PROGRAM                              = 0xA1
READ_OTP_DATA                               = 0xA2


def _nearest_mult_of_8(number, up=True):
    """ Find the nearest multiple of 8, rounding up or down """
    if up:
        return ((number + 7) // 8) * 8
    else:
        return (number // 8) * 8


class EPD(object):
    def __init__(self, partial_refresh_limit=32, fast_refresh=True):
        """ Initialize the EPD class.
        `partial_refresh_limit` - number of partial refreshes before a full refrersh is forced
        `fast_frefresh` - enable or disable the fast refresh mode,
                          see smart_update() method documentation for details"""
        self.width = EPD_WIDTH
        """ Display width, in pixels """
        self.height = EPD_HEIGHT
        """ Display height, in pixels """
        self.fast_refresh = fast_refresh
        """ enable or disable the fast refresh mode """
        self.partial_refresh_limit = partial_refresh_limit
        """ number of partial refreshes before a full refrersh is forced """

        self._last_frame = None
        self._partial_refresh_count = 0
        self._init_performed = False
        self.spi = spidev.SpiDev(0, 0)

    def digital_write(self, pin, value):
        return GPIO.output(pin, value)

    def digital_read(self, pin):
        return GPIO.input(pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def send_command(self, command):
        self.digital_write(DC_PIN, GPIO.LOW)
        self.spi.writebytes([command])

    def send_data(self, data):
        self.digital_write(DC_PIN, GPIO.HIGH)
        self.spi.writebytes([data])

    def init(self):
        """ Preform the hardware initialization sequence """
        # Interface initialization:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.setup(DC_PIN, GPIO.OUT)
        GPIO.setup(CS_PIN, GPIO.OUT)
        GPIO.setup(BUSY_PIN, GPIO.IN)

        self.spi.max_speed_hz = 2000000
        self.spi.mode = 0b00
        # EPD hardware init
        # The specifics of how this works or what "power optimization" actually means
        # are unclear to me, so I'm leaving it as-is.
        self.reset()
        self.send_command(POWER_SETTING)
        self.send_data(0x03)                  # VDS_EN, VDG_EN
        self.send_data(0x00)                  # VCOM_HV, VGHL_LV[1], VGHL_LV[0]
        self.send_data(0x2b)                  # VDH
        self.send_data(0x2b)                  # VDL
        self.send_data(0x09)                  # VDHR
        self.send_command(BOOSTER_SOFT_START)
        self.send_data(0x07)
        self.send_data(0x07)
        self.send_data(0x17)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x60)
        self.send_data(0xA5)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x89)
        self.send_data(0xA5)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x90)
        self.send_data(0x00)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x93)
        self.send_data(0x2A)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0xA0)
        self.send_data(0xA5)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0xA1)
        self.send_data(0x00)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x73)
        self.send_data(0x41)
        self.send_command(PARTIAL_DISPLAY_REFRESH)
        self.send_data(0x00)
        self.send_command(POWER_ON)
        self.wait_until_idle()

        self.send_command(PANEL_SETTING)
        self.send_data(0xAF)        # KW-BF   KWR-AF    BWROTP 0f
        self.send_command(PLL_CONTROL)
        self.send_data(0x3A)        # 3A 100HZ   29 150Hz 39 200HZ    31 171HZ
        self.send_command(VCM_DC_SETTING_REGISTER)
        self.send_data(0x12)
        self.delay_ms(2)
        self.set_lut()
        # EPD hardware init end
        self._init_performed = True

    def wait_until_idle(self):
        """ Wait until screen is idle by polling the busy pin """
        while(self.digital_read(BUSY_PIN) == 0):      # 0: busy, 1: idle
            self.delay_ms(50)

    def reset(self):
        """ Module reset """
        self.digital_write(RST_PIN, GPIO.LOW)
        self.delay_ms(200)
        self.digital_write(RST_PIN, GPIO.HIGH)
        self.delay_ms(200)

    def set_lut(self, fast=False):
        """ Set LUT for the controller.
        If `fast` is srt to True, quick update LUTs from Ben Krasnow will be used"""
        lut_to_use = LUT if not fast else QuickLUT

        # Quick LUTs courtsey of Ben Krasnow:
        # http://benkrasnow.blogspot.co.il/2017/10/fast-partial-refresh-on-42-e-paper.html
        # https://www.youtube.com/watch?v=MsbiO8EAsGw

        self.send_command(LUT_FOR_VCOM)               # vcom
        for byte in lut_to_use.lut_vcom_dc:
            self.send_data(byte)

        self.send_command(LUT_WHITE_TO_WHITE)         # ww --
        for byte in lut_to_use.lut_ww:
            self.send_data(byte)

        self.send_command(LUT_BLACK_TO_WHITE)         # bw r
        for byte in lut_to_use.lut_bw:
            self.send_data(byte)

        self.send_command(LUT_WHITE_TO_BLACK)         # wb w
        for byte in lut_to_use.lut_wb:
            self.send_data(byte)

        self.send_command(LUT_BLACK_TO_BLACK)         # bb b
        for byte in lut_to_use.lut_bb:
            self.send_data(byte)

    def _get_frame_buffer(self, image):
        """ Get a full frame buffer from a PIL Image object """
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError('Image must be same dimensions as display \
                ({0}x{1}).' .format(self.width, self.height))
        return self._get_frame_buffer_for_size(image_monocolor, self.height, self.width)

    def _get_frame_buffer_for_size(self, image_monocolor, height, width):
        """ Get a frame buffer object from a PIL Image object assuming a specific size"""
        buf = [0x00] * (width * height // 8)
        pixels = image_monocolor.load()
        for y in range(height):
            for x in range(width):
                # Set the bits for the column of pixels at the current position
                if pixels[x, y] != 0:
                    buf[(x + y * width) // 8] |= (0x80 >> (x % 8))
        return buf

    def display_frame(self, image):
        """ Display a full frame, doing a full screen refresh """
        if not self._init_performed:
            # Initialize the hardware if it wasn't already initialized
            self.init()
        self.set_lut()
        frame_buffer = self._get_frame_buffer(image)
        self.send_command(DATA_START_TRANSMISSION_1)
        self.delay_ms(2)
        for _ in range(0, self.width * self.height // 8):
            self.send_data(0xFF)
        self.delay_ms(2)
        self.send_command(DATA_START_TRANSMISSION_2)
        self.delay_ms(2)
        for i in range(0, self.width * self.height // 8):
            self.send_data(frame_buffer[i])
        self.delay_ms(2)
        self.send_command(DISPLAY_REFRESH)
        self.wait_until_idle()
        self._last_frame = image.copy()
        self._partial_refresh_count = 0  # reset the partial refreshes counter

    def _send_partial_frame_dimensions(self, x, y, l, w):
        self.send_data(x >> 8)
        self.send_data(x & 0xf8)
        self.send_data(y >> 8)
        self.send_data(y & 0xff)
        self.send_data(w >> 8)
        self.send_data(w & 0xf8)
        self.send_data(l >> 8)
        self.send_data(l & 0xff)

    def display_partial_frame(self, image, x, y, h, w, fast=False):
        """ Display a partial frame, only refreshing the changed area.

        `image` is a Pillow Image object
        `x` and `y` are the top left coordinates
        `h` is the height of the area to update
        `w` is the width of the area to update.


        if `fast` is True, fast refresh lookup tables will be used.
        see `smart_update()` method documentation for details."""
        if fast:
            self.set_lut(fast=True)
            self.delay_ms(2)

        # According to the spec, x and w have to be multiples of 8.
        # round them up and down accordingly to make sure they fit the requirement
        # adding a few more pixels to the refreshed area.
        # This is mandatory, otherwise the display might get corrupted until
        # the next valid update that touches the same area.
        x = _nearest_mult_of_8(x, False)
        w = _nearest_mult_of_8(w)

        self.send_command(PARTIAL_DATA_START_TRANSMISSION_1)
        self.delay_ms(2)

        self._send_partial_frame_dimensions(x, y, h, w)
        self.delay_ms(2)

        # Send the old values, as per spec
        old_image = self._last_frame.crop((x, y, x+w, y+h))
        old_fb = self._get_frame_buffer_for_size(old_image, h, w)
        for i in range(0, w * h // 8):
            self.send_data(old_fb[i])
        self.delay_ms(2)

        self.send_command(PARTIAL_DATA_START_TRANSMISSION_2)
        self.delay_ms(2)

        self._send_partial_frame_dimensions(x, y, h, w)

        # Send new data
        self._last_frame = image.copy()
        image = image.crop((x, y, x+w, y+h))
        new_fb = self._get_frame_buffer_for_size(image, h, w)
        for i in range(0, w * h // 8):
            self.send_data(new_fb[i])
        self.delay_ms(2)

        self.send_command(PARTIAL_DISPLAY_REFRESH)
        self.delay_ms(2)
        self._send_partial_frame_dimensions(x, y, h, w)
        self.wait_until_idle()
        if fast:
            self.set_lut()  # restore LUT to normal mode
        self._partial_refresh_count += 1

    def smart_update(self, image):
        """ Display a frame, automatically deciding which refresh method to use.
        If `fast_frefresh` is enabled, it would use optimized LUTs that shorten
        the refresh cycle, and don't do the full "inverse,black,white,black again,
        then draw" flush cycle.

        The fast refresh mode is much faster, but causes the image to apper
        gray instead of black, and can cause burn-in if it's overused.

        It's recommended to do a full flush "soon" after using the fast mode,
        to avoid degrading the panel. You can tweak `partial_refresh_limit`
        or
        """
        if self._last_frame is None or self._partial_refresh_count == self.partial_refresh_limit:
            # Doing a full refresh when:
            # - No frame has been displayed in this run, do a full refresh
            # - The display has been partially refreshed more than LIMIT times
            # the last full refresh (to prevent burn-in)
            self.display_frame(image)
        else:
            # Partial update. Let's start by figuring out the bounding box
            # of the changed area
            difference = ImageChops.difference(self._last_frame, image)
            bbox = difference.getbbox()
            if bbox is not None:
                # the old picture and new picture are different, partial
                # update is needed.
                # Get the update area. x and w have to be multiples of 8
                # as per the spec, so round down for x, and round up for w
                x = _nearest_mult_of_8(bbox[0], False)
                y = bbox[1]
                w = _nearest_mult_of_8(bbox[2] - x)
                if w > self.width:
                    w = self.width
                h = bbox[3] - y
                if h > self.height:
                    h = self.height
                # now let's figure out if fast mode is an option.
                # If the area was all white before - fast mode will be used.
                # otherwise, a slow refresh will be used (to avoid ghosting).
                # Since the image only has one color, meaning each pixel is either
                # 0 or 255, the following convinent one liner can be used
                fast = 0 not in self._last_frame.crop(bbox).getdata() and self.fast_refresh
                self.display_partial_frame(image, x, y, h, w, fast)

    def sleep(self):
        """Put the chip into a deep-sleep mode to save power.
        The deep sleep mode would return to standby by hardware reset.
        Use EPD.reset() to awaken and use EPD.init() to initialize. """
        self.send_command(DEEP_SLEEP)
        self.delay_ms(2)
        self.send_data(0xa5)  # deep sleep requires 0xa5 as a "check code" parameter
