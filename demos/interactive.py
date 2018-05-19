"interactive.py - Interactive demo, prints input on the EPD"
# Copyright (c) 2018 Elad Alfassa <elad@fedoraproject.org>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function
from rpi_epd2in7.epd import EPD
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import sys
if sys.version_info.major < 3:
    input = raw_input

# This demo shows usage of both display_frame and display_partial_frame


def main():
    print("initializing...")
    epd = EPD()
    epd.init()

    image = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    draw.text((0, 5), 'Interactive demo', font=font, fill=0)

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    epd.display_frame(image)
    loc = 25
    full_update = False
    print("Ready.")
    try:
        while True:
            text = input("> ")
            if loc > epd.height - 10:
                loc = 0
                image = Image.new('1', (epd.width, epd.height), 255)
                draw = ImageDraw.Draw(image)
                full_update = True

            draw.text((5, loc), text, font=font, fill=0)
            if full_update:
                print("Doing a full update...")
                epd.display_frame(image)
                full_update = False
            else:
                print("...")
                epd.display_partial_frame(image, 0, loc, 20, epd.width, fast=True)

            loc += 20
    except KeyboardInterrupt:
        epd.sleep()
        print("Bye!")
        raise


if __name__ == '__main__':
    main()
