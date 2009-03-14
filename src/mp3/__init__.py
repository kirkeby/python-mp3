#
# mp3.py -- MP3-frame meta-data parser
# Copyright (C) 2003-2004  Sune Kirkeby
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""Routines for parsing MP3-frame meta-data.

This is a collection of routines for parsing MP3-files and extracting
raw frame-data and meta-data (such as frame bitrates)."""

from __future__ import generators

import struct

class MP3Error(Exception):
    """I signal a generic error related to MP3-data."""
    pass
class MP3FrameHeaderError(MP3Error):
    """I signal that there was an error parsing the meta-data in an
    MP3-frame header."""
    pass

bitrates = [
    [
        [32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448],
        [32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384],
        [32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
    ],
    [
        [32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256],
        [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
    ],
]
bitrates[1].append(bitrates[1][1])

samplingrates = [
    [44100, 48000, 32000],
    [22050, 24000, 16000],
]

def frameheader(dat, i):
    """frameheader(buf, i) -> header
    Parse the header of the MP3-frame found at offset i in buf.

    MP3-frame headers are tuples of
    
        (version, layer, crc, bitrate, samplingrate, padding)

    The fields returned in the header-tuple are mostly self-explaining,
    if you know MP3-files. There are a few pit-falls, though:
    
    The version is an integer for MP3-versions 1 and 2, but there
    exists an unofficial version 2.5 (which supports different bitrates
    and sampling rates than version 2), for which version is a float.

    The bitrate is returned in kbit/s (e.g. 128, 192).

    The sampling rate is returned in Hz (e.g. 44100)."""
    
    if len(dat) - i < 4:
        raise MP3FrameHeaderError, 'frame too short for MPEG-header'

    bytes = map(ord, dat[i : i+4])

    # bits 31 - 21 (frame sync)
    if not bytes[0] == 255 and (bytes[1] & 224) == 224:
        raise MP3FrameHeaderError, 'frame sync not found'

    # bits 20 - 19 (mpeg version)
    id = (bytes[1] & 24) >> 3
    if id == 0:
        version = 2.5
    elif id == 1:
        raise MP3FrameHeaderError, 'unknown MPEG version (bad frame sync?)'
    else:
        version = 4 - id

    # bits 18 - 17 (mpeg layer)
    layer = (bytes[1] & 6) >> 1
    if layer == 0:
        raise MP3FrameHeaderError, 'unknown Layer description'
    else:
        layer = 4 - layer
    
    # bit 16 (crc present)
    crc = not (bytes[1] & 1)

    # bits 15 - 12 (bitrate)
    bitrate = bytes[2] >> 4
    if bitrate == 15:
        raise MP3FrameHeaderError, 'bad bitrate'
    elif bitrate:
        bitrate = bitrates[int(version)-1][layer-1][bitrate-1]

    # bits 11 - 10 (sampling rate)
    samplingrate = (bytes[2] & 12) >> 2
    if samplingrate == 3:
        raise MP3FrameHeaderError, 'bad sampling-rate'
    if version == 2.5:
        samplingrate = samplingrates[int(version)-1][samplingrate] / 2
    else:
        samplingrate = samplingrates[int(version)-1][samplingrate]

    # bit 9 (padding present)
    padding = (bytes[2] & 2) >> 1

    # bit 8 (private, ignored)

    # bits 7 - 0 not read, they contain no information useful
    # outside MPEG-decoding

    return version, layer, crc, bitrate, samplingrate, padding

def time(hdr):
    """time(header) -> seconds

    Calculate the length in seconds of the MP3-frame given it's
    header."""
    version, layer, crc, bitrate, samplingrate, padding = hdr
    if layer == 1:
        return 384.0 / 44100
    else:
        return 1152.0 / 44100

def framedata(dat, i, hdr):
    """framedata(buf, i, header) -> frame-date

    Extract the actual MP3-frame data from the MP3-frame starting at
    offset i in buf."""
    
    version, layer, crc, bitrate, samplingrate, padding = hdr
    start = i + 4 + crc * 2
    end = i + framelen(hdr)
    return frame[i+start : i+end]

def framelen(hdr):
    """framelen(header) -> length

    Calculate the length of an MP3-frame; both header and data."""
    version, layer, crc, bitrate, samplingrate, padding = hdr

    if version == 1:
        if layer == 1:
            mul, slot = 12, 4
        else:
            mul, slot = 144, 1
    else:
        if layer == 1:
            mul, slot = 240, 4
        else:
            mul, slot = 72, 1

    return ((mul * bitrate * 1000 / samplingrate) + (padding * slot)) * slot

def frames(f):
    """frames(file) -> (header, frame) generator
    
    Extract all MP3-frames from a file-like object, returning them as
    (header, data) tuples, where header is as returned by frameheader
    and data is the entire MP3-frame data (including header).
    
    This is (unlike all other MP3 readers and players I know of) a
    strict MP3-reader; if there are any errors or bogus data in the file
    MP3Error is raised. The only accomodation made for non-MP3 data is
    ID3 tags, which it will skip."""

    # how many bytes we would like in the buffer at a minimum
    min_dat = 16

    try:
        # dat is our read buffer
        dat = ''
        # frame tells if the last iteration found an MP3-frame
        # or something else (e.g. an ID3-tag)
        frame = 0
        # number of MP3-frames we have found
        no = 0
        # i is the length of the 'something' (e.g. MP3-frame, ID3-tag)
        # we found last iteration; j is our position in the file
        i = j = 0

        while 1:
            # fill buffer
            while len(dat) < i + min_dat:
                rd = f.read(i + min_dat - len(dat))
                if rd == '':
                    break
                dat = dat + rd

            # pass frame up to caller
            if len(dat) < i:
                break
            if frame:
                yield hdr, dat[:i]

            # throw away the frame or ID3-tag we found in the last
            # iteration.
            j = j + i
            dat = dat[i:]

            if len(dat) < min_dat:
                break

            if dat.startswith('TAG'):
                # skip ID3v1 tags
                frame = 0
                i = 128

            elif dat.startswith('ID3'):
                # skip ID3v2 tags
                frame = 0
                i = (ord(dat[6]) << 21) + (ord(dat[7]) << 14) + \
                    (ord(dat[8]) << 7) + ord(dat[9]) + 10

            else:
                hdr = frameheader(dat, 0)
                i = framelen(hdr)
                frame = 1
                no = no + 1

    except MP3FrameHeaderError, e:
        raise MP3Error, 'bad frame-header at offset %d (%x): %s' \
                        % (j, j, e.args[0])

def good_data(f):
    """good_data(file) -> good-data-buffer generator
    
    Extract all MP3-frames and ID3-tags from a file-like object,
    yielding their raw data buffers one at a time."""

    # read entire file into memory
    buffer = ''
    while 1:
        r = f.read()
        if r == '':
            break
        buffer = buffer + r

    index = 0
    max = len(buffer)
    while index < max - 4:
        good, length = 0, 1
        if buffer.startswith('TAG', index):
            # ID3v1 tag
            good = 1
            length = 128
            
        elif buffer.startswith('ID3', index) and max - index > 9:
            # IV3v2 tag
            good = 1
            length = (ord(buffer[index + 6]) << 21) + \
                     (ord(buffer[index + 7]) << 14) + \
                     (ord(buffer[index + 8]) << 7) + \
                     ord(buffer[index + 9]) + 10
                     
        elif buffer[index] == '\xff' and \
             not buffer[index + 1] == '\xff' and \
             (ord(buffer[index + 1]) & 224) == 224:
            # MP3 frames
            try:
                hdr = frameheader(buffer, index)
                length = framelen(hdr)
                good = 1
            except MP3Error, e:
                pass

        if good:
            if index + length <= max:
                yield buffer[index : index + length]
        index = index + length
