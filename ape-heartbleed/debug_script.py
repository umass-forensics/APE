__author__ = 'wallsr'

import main

protocol = main.TesterProtocol(None, {"model": "trouble.dot"})

protocol.get_response()
