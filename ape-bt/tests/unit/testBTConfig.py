"""
"""
import unittest
from autonomotorrent.BTApp import BTApp, BTConfig

class testBTConfig(unittest.TestCase):
    """Tests the BT Config which holds information for a single torrent.
    """
    def test_bt_file(self):
        """Tests the config using a BT meta file on disk.
        """
        config = BTConfig(torrent_path="tests/unit/damn_small_linux.torrent")
        self.assertNotEqual(config, None)
        config.check()

    def test_full_meta_info(self):
        """Tests the config using a hardcoded meta info dicionarity with most
        of the values.
        """
        full_torrent = {'creation date': 1316733309, 'announce':
        'http://107.10.137.161:8082/announce', 'info': {'length': 26039, 
        'piece length': 2048, 'name': '378ae2e61395da95c3cddf7d2acfc491.png',
        'private': 0, 'pieces':
        "\xbbBOX\n\xb5P#\xb5\x11q\x8e\xd3\x7fI\x12\xa6\xc3v\xc9\xeav\x18\xd3$\xce\xb6HB\xc3\x1a\xb0\x1eW#\xa8<\x11\xb4w\xe2Y\xd3\x95\x93f\x90]\x19\x87\xda\xb3\xf6\xf9\x9e\xed\xad\x1a\xf6\x0b\x04m7\xbf\x82pj\xe0W\xb23\x92&l\x9a\xbe\xff\xb7\xce&!\x88\xc4\xdbK\xc9\xad{\xc1\xd4\xf5o\xd8\\47\xeem\xaeVSe\xce\xcaH\xbf0\x1bfZ\xc77V\xec\x9c{\xd35\xef'S!\xe5\xd4>\x03\xa9\x1b\x90\x0et\r\xd4\xb9\x0cdh\x0fMJ\x86\x9b\xf6Gc+e\xe2\xd8\xc4\xf7\xaa\xa4\x14\x80\xd1\x9f&4v\x13\xff+\xe7\xcf\xeen\xbd\xad\x96a\xa9\x00\xc7\x02\xdcU\xda\xe7\xb40\x14E\x96C\x8d)\xd7\x8d\xa8\x8b\xbboe\xf7u\x18!\xe7\x8e\x1e\x02\x17\x8ab\xa3u\xb0\n!\xf2\x01Q\x8eK\x94\xd3\xee\x1c\xf7\xde\xdb\x19\x9e\xe3\xfd+\xc6\x07|\x8c\xec{\xeau.\xf8\x92\x9a/\xf3W\x85\xf5\x8f\xfeC\xc1\xabj\xbc\xe5,7\xcdh\xfe\xa6\r"},
        'encoding': 'UTF-8'}
        
        config = BTConfig(meta_info=full_torrent)
        self.assertNotEqual(config, None)
        config.check()

    def test_minimal_meta_info(self):
        """Tests the config using a hardcoded meta info dicionarity with the
        minimal set of values/keys.
        """
        min_torrent = {'info': {'length': 26039, 
        'piece length': 2048, 'name': '378ae2e61395da95c3cddf7d2acfc491.png',
        'pieces':
        "\xbbBOX\n\xb5P#\xb5\x11q\x8e\xd3\x7fI\x12\xa6\xc3v\xc9\xeav\x18\xd3$\xce\xb6HB\xc3\x1a\xb0\x1eW#\xa8<\x11\xb4w\xe2Y\xd3\x95\x93f\x90]\x19\x87\xda\xb3\xf6\xf9\x9e\xed\xad\x1a\xf6\x0b\x04m7\xbf\x82pj\xe0W\xb23\x92&l\x9a\xbe\xff\xb7\xce&!\x88\xc4\xdbK\xc9\xad{\xc1\xd4\xf5o\xd8\\47\xeem\xaeVSe\xce\xcaH\xbf0\x1bfZ\xc77V\xec\x9c{\xd35\xef'S!\xe5\xd4>\x03\xa9\x1b\x90\x0et\r\xd4\xb9\x0cdh\x0fMJ\x86\x9b\xf6Gc+e\xe2\xd8\xc4\xf7\xaa\xa4\x14\x80\xd1\x9f&4v\x13\xff+\xe7\xcf\xeen\xbd\xad\x96a\xa9\x00\xc7\x02\xdcU\xda\xe7\xb40\x14E\x96C\x8d)\xd7\x8d\xa8\x8b\xbboe\xf7u\x18!\xe7\x8e\x1e\x02\x17\x8ab\xa3u\xb0\n!\xf2\x01Q\x8eK\x94\xd3\xee\x1c\xf7\xde\xdb\x19\x9e\xe3\xfd+\xc6\x07|\x8c\xec{\xeau.\xf8\x92\x9a/\xf3W\x85\xf5\x8f\xfeC\xc1\xabj\xbc\xe5,7\xcdh\xfe\xa6\r"}}

        config = BTConfig(meta_info=min_torrent)
        self.assertNotEqual(config, None)
        config.check()

if __name__ == '__main__':
    unittest.main()
