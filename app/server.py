#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Creates an HTTP server with basic auth and websocket communication.
"""
import argparse
import base64
import getpass
import hashlib
import os
import time
import threading
import webbrowser

import cv2
from PIL import Image

try:
    import cStringIO as io
except ImportError:
    import io

import tornado.web
import tornado.websocket
from tornado.ioloop import PeriodicCallback

APP_ROOT = os.path.normpath(os.path.dirname(__file__))
STATIC_PATH = os.path.join(APP_ROOT, "static")
PASSWORD_PATH = "/etc/camp_password.txt"
if os.path.isfile(PASSWORD_PATH):
    with open(PASSWORD_PATH) as in_file:
        # Hashed password for comparison and a cookie for login cache
        PASSWORD = in_file.read().strip()
COOKIE_NAME = "camp"
RESOLUTIONS = {"high": (1280, 720), "medium": (640, 480), "low": (320, 240)}

class IndexHandler(tornado.web.RequestHandler):
    def initialize(self, require_login=None, port=None):
        self.require_login = require_login
        self.port = port
    
    def get(self):
        if self.require_login and not self.get_secure_cookie(COOKIE_NAME):
            self.redirect("/login")
        else:
            self.render(os.path.join(STATIC_PATH, "index.html"),
                        port=self.port)

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(os.path.join(STATIC_PATH, "login.html"))

    def post(self):
        password = self.get_argument("password", "")
        if hashlib.sha512(password).hexdigest() == PASSWORD:
            self.set_secure_cookie(COOKIE_NAME, str(time.time()))
            self.redirect("/")
        else:
            time.sleep(1)
            self.redirect(u"/login?error")

class WebSocket(tornado.websocket.WebSocketHandler):
    def initialize(self, use_usb=None, resolution=None):
        self.use_usb = use_usb
        self.resolution = resolution

    def on_message(self, message):
        """Evaluates the function pointed to by json-rpc."""
        # Start an infinite loop when this is called
        if message == "read_camera":
            if not self.use_usb:
                self.camera = picamera.PiCamera()
                self.camera.start_preview()
                self.camera.resolution = RESOLUTIONS[self.resolution]
                self.camera.capture(sio, format="jpeg", use_video_port=True)
            else:
                self.camera = cv2.VideoCapture(0)
                w, h = RESOLUTIONS[self.resolution]
                camera.set(3, w)
                camera.set(4, h)

            self.camera_loop = PeriodicCallback(self.loop, 10)
            self.camera_loop.start()

        # Extensibility for other methods
        else:
            print("Unsupported function: " + message)

    def loop(self):
        """Sends camera images in an infinite loop."""
        sio = io.StringIO()

        if self.use_usb:
            _, frame = self.camera.read()
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img.save(sio, "JPEG")
        else:
            self.camera.capture(sio, "jpeg", use_video_port=True)

        try:
            self.write_message(base64.b64encode(sio.getvalue()))
        except tornado.websocket.WebSocketClosedError:
            self.camera_loop.stop()

            if self.use_usb:
                self.camera.release()
            else:
                self.camera.stop()

            self.camera = None

def parse_cli_args():
    options_parser = argparse.ArgumentParser(description="Starts a webserver that "
                                                 "connects to a webcam.")
    options_parser.add_argument("--port", type=int, default=8000, help="The "
                                    "port on which to serve the website [8000]")
    options_parser.add_argument("--resolution", type=str, default="low", help="The "
                                    "video resolution. Can be high, medium, or low [low]")
    options_parser.add_argument("--require-login", action="store_true", help="Require "
                                    "a password to log in to webserver [False]")
    options_parser.add_argument("--use-usb", action="store_true", help="Use a USB "
                                    "webcam instead of the standard Pi camera [False]")
    options_parser.add_argument("--create-password", help="Creates a new password for "
                                "login and exists [False]", action="store_true")
    return options_parser.parse_args()

def ask_password():
    """Asks for password twice and returns both inputs"""
    pwd1 = getpass.getpass("Password: ")
    pwd2 = getpass.getpass("Retype password: ")
    return pwd1, pwd2

def create_password():
    """Creates a new password hash into /etc"""

    pwd1, pwd2 = ask_password()
    while pwd1 != pwd2:
        print "Password missmatch. Try again."
        pwd1, pwd2 = ask_password()

    password_hash = hashlib.sha512(pwd1)
    with open(PASSWORD_PATH, "w") as fh:
        fh.write(password_hash.hexdigest())
        fh.write("\n")

    os.system("chown pi:pi {}".format(PASSWORD_PATH))
    os.system("chmod 600 {}".format(PASSWORD_PATH))

def serve(options):
    """Starts web server"""
    print("APP_ROOT: {}".format(APP_ROOT))
    print("STATIC_PATH: {}".format(STATIC_PATH))
    if options.resolution not in RESOLUTIONS:
        raise RuntimeError("%s not in resolution options." % options.resolution)
    
    handlers = [
        (r"/", IndexHandler, {"require_login": options.require_login,
                              "port": options.port}),
        (r"/login", LoginHandler),
        (r"/websocket", WebSocket, {"use_usb": options.use_usb,
                                    "resolution": options.resolution}),
        (r'/static/(.*)', tornado.web.StaticFileHandler,
             {'path': STATIC_PATH})
    ]
    application = tornado.web.Application(handlers, cookie_secret=PASSWORD)
    application.listen(options.port)

    webbrowser.open("http://localhost:%d/" % options.port, new=2)
    tornado.ioloop.IOLoop.instance().start()

def _main():
    options = parse_cli_args()
    print("Called with {}".format(str(options)))

    if options.create_password:
        create_password()
    else:
        serve(options)

if __name__ == "__main__":
    _main()
