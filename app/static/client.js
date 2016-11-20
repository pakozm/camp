/*global $, WebSocket, console, window, document*/
"use strict";

/**
 * Connects to Pi server and receives video data.
 */
var client = {

    // Connects to Pi via websocket
    connect: function (port) {
        var self = this, video = document.getElementById("video");

        var protocol = "ws";
        if (location.protocol === 'https:') protocol = "wss";
        this.socket = new WebSocket(protocol + "://" + window.location.hostname + ":" + port + "/websocket");

        // Request the video stream once connected
        this.socket.onopen = function () {
            console.log("Connected!");
            self.readCamera();
        };

        // Currently, all returned messages are video data. However, this is
        // extensible with full-spec JSON-RPC.
        this.socket.onmessage = function (messageEvent) {
            video.src = "data:image/jpeg;base64," + messageEvent.data;
        };
    },

    // Requests video stream
    readCamera: function () {
        this.socket.send("read_camera");
    },

    moreResolution: function() {
        this.socket.send("more_resolution");
    },

    lessResolution: function() {
        this.socket.send("less_resolution");
    }
};
