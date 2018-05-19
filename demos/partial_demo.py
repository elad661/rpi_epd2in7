"partial_demo.py - demo partial refresh and smart_update()"
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


def main():
    print("initializing", end="")
    sys.stdout.flush()
    epd = EPD()
    epd.init()
    print(".", end="")
    sys.stdout.flush()

    image = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    draw.text((0, 5), 'Partial refresh', font=font, fill=0)

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    draw.line([0, 28, epd.width, 28], fill=0, width=3)
    epd.display_frame(image)
    print(".")
    loc = 30

    draw.text((0, loc), "Look!", font=font, fill=0)
    epd.smart_update(image)
    loc += 20
    print(".", end="")
    sys.stdout.flush()

    draw.text((0, loc), "No need to refresh", font=font, fill=0)
    draw.text((0, loc+20), "the entire screen.", font=font, fill=0)
    epd.smart_update(image)
    loc += 45
    print(".", end="")
    sys.stdout.flush()

    draw.text((0, loc), "It's fast", font=font, fill=0)
    draw.text((0, loc+20), "and convenient", font=font, fill=0)
    epd.smart_update(image)
    loc += 20
    print(".", end="")
    sys.stdout.flush()

    epd.sleep()
    print("!")


if __name__ == '__main__':
    main()