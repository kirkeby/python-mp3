import StringIO
import unittest
import struct
import mp3

stringio = StringIO.StringIO

good_frame = '\xff\xfb\x90\x64\x76\x00\x05\x34\x66\x50\xf6\x69\x20\x00' \
             '\x9f\x0e\xaa\x1e\xcd\x20\x00\x0c\x21\x7f\x44\x9c\xf1\x80' \
             '\x09\x3a\x02\x29\x2f\x9e\x00\x00\x7b\x64\x99\x8e\x67\x5a' \
             '\xe0\x6d\xb9\xc6\x8e\x48\x71\xb2\xa8\xa6\x8e\x4a\x84\x4d' \
             '\x61\x46\x91\x77\x69\xa7\xb1\x2b\x34\xb4\xb7\xc8\x8c\x25' \
             '\x21\x84\x43\xa6\x06\xc4\x62\x30\xf6\xb4\x24\x99\x95\x4c' \
             '\xe1\xf6\x35\x9b\xb1\xa3\x5d\xb0\xf4\x2d\x2a\x21\x03\x71' \
             '\x50\x6c\x69\x66\xa8\xe2\xa5\xd1\x06\x08\x77\x16\xe5\xa2' \
             '\xa0\xb2\xb7\xff\xff\xff\xff\xff\xff\x8a\x0e\xff\xf9\x85' \
             '\x6d\x65\xa0\x00\x4a\xce\xa4\xaa\xb9\x86\x2d\x99\x2d\x6b' \
             '\xee\xd9\xa6\xb5\xcf\x27\xa9\x16\xe4\x99\x6f\x93\xdf\x37' \
             '\xfa\xc5\xfc\xec\xd0\xd4\xfa\x8b\x32\xbe\xef\xc7\xcf\x2d' \
             '\xfe\xaa\x58\x65\x25\x2c\x1b\x14\xc8\x95\x0d\xb8\x8d\xf5' \
             '\xd6\xa0\x2e\xcc\xe1\x9b\x02\xbb\x11\x3a\x1a\x16\x65\x03' \
             '\x83\x22\xf2\xcf\x77\x13\xc2\x24\x2f\x22\x9f\xb6\x7e\x77' \
             '\xd3\x92\x21\xfd\x3c\x1b\x5f\x8b\xe1\xe5\xa4\xc6\x53\x76' \
             '\x65\x24\x4f\x7e\x43\x5c\x70\xcb\xb8\xfa\x8e\x57\xbd\x6f' \
             '\x5a\x9f\x94\x1d\xf6\x1f\x93\xc7\xb4\xf6\x6a\x39\xe4\xa8' \
             '\x51\xa1\x28\x1e\x78\x54\x73\xa6\x82\x6b\x24\xd7\x0a\x03' \
             '\xe5\xc9\x14\x15\x0f\x1a\xa5\x44\x5a\x84\xa9\x34\x02\x50' \
             '\x23\x4b\x1e\x41\x13\x0a\x79\x72\x47\x40\xe4\x86\x38\x24' \
             '\x24\x8f\x61\xb4\x01\x5c\x15\x72\xd4\x91\x00\x04\x89\x1a' \
             '\xdc\xfd\x6f\x5a\x7d\x03\x78\xf0\xbc\x78\x31\xb8\x54\xe8' \
             '\x86\xa2\x3c\x9c\x3e\x76\xb2\x50\x97\xa9\x97\xa1\x9a\xf6' \
             '\xc9\x0e\x73\x95\xc9\x6d\x98\xe8\xad\x59\x50\xc6\xec\xad' \
             '\x64\x4d\xf7\x3d\xbd\xee\xc4\x5a\x30\x60\x46\x0a\x1b\x4e' \
             '\x3f\x86\x3d\x4a\x7c\xfa\x34\x8c\x24\xf4\xb8\x6e\x25\xb8' \
             '\x45\xc3\xdb\x47\xc8\x31\x78\x33\x2f\x69\x73\xb6\xad\xb4' \
             '\x0d\xfe\x15\x36\x42\x30\xe4\x40\xc0\x43\x3b\x45\x55\xd2' \
             '\xff\x72\xae\xe6\xfb\xad\x5f\xf7\xbe\xeb\x37'
good_frame_header = 1, 3, 0, 128, 44100, 0

riff_frame = 'RIFF%sWAVEfmt Hello, World!' % struct.pack('L', len('Hello, World!'))

title = 'Happy Bithday toooo meeeee!'
artist = 'My self'
album = ''
year = '1979'
comment = 'In reality I cannot sing'
track = chr(0)
genre = chr(28) # Vocal
good_id3v1_tag = 'TAG' + \
                 title + '\x00' * (30 - len(title)) + \
                 artist + '\x00' * (30 - len(artist)) + \
                 album + '\x00' * (30 - len(album)) + \
                 year + \
                 comment + '\x00' * (29 - len(comment)) + \
                 track + \
                 genre

class FramesTestCase(unittest.TestCase):
    def testGoodFrame(self):
        f = stringio(good_frame)
        l = list(mp3.frames(f))
        self.assertEquals(len(l), 1)
        self.assertEquals(l, [ (good_frame_header, good_frame) ])

class GoodDataTestCase(unittest.TestCase):
    def testGoodFrame(self):
        self.assertEquals([ good_frame ],
                          list(mp3.good_data(stringio(good_frame))))
    
        l = list(mp3.good_data(stringio(good_frame + good_frame)))
        self.assertEquals(len(l), 2)
        self.assertEquals(l, [ good_frame, good_frame ])

    def testRIFF(self):
        f = stringio(riff_frame)
        self.assertEquals([ ],
                          list(mp3.good_data(f)))
        f = stringio(good_frame + riff_frame)
        self.assertEquals([ good_frame ],
                          list(mp3.good_data(f)))
        f = stringio(riff_frame + good_frame)
        self.assertEquals([ good_frame ],
                          list(mp3.good_data(f)))

    def testGoodID3v1Tag(self):
        self.assertEquals([ good_id3v1_tag ],
                          list(mp3.good_data(stringio(good_id3v1_tag))))

    def testGoodFrameAndID3v1Tag(self):
        self.assertEquals([ good_frame, good_id3v1_tag ],
                          list(mp3.good_data(stringio(good_frame + good_id3v1_tag))))

    def testSpuriousZeros(self):
        self.assertEquals([ good_frame ],
                          list(mp3.good_data(stringio(good_frame + '\x00'))))
        self.assertEquals([ good_frame, good_frame ],
                          list(mp3.good_data(stringio(good_frame + '\x00' + good_frame))))
        self.assertEquals([ good_frame ],
                          list(mp3.good_data(stringio('\x00' + good_frame))))
        self.assertEquals([ good_frame, good_id3v1_tag ],
                          list(mp3.good_data(stringio('\x00' + good_frame + good_id3v1_tag))))
        self.assertEquals([ good_frame, good_id3v1_tag ],
                          list(mp3.good_data(stringio(good_frame + '\x00' + good_id3v1_tag))))
        self.assertEquals([ good_frame, good_id3v1_tag ],
                          list(mp3.good_data(stringio(good_frame + good_id3v1_tag + '\x00'))))

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(GoodDataTestCase, 'test')])
suite.addTests([unittest.makeSuite(FramesTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
