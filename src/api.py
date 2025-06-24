import json
import os
from typing import Any

from PySide6.QtCore import QByteArray, QObject, QUrl, Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from requests import delete


from PySide6.QtCore import Signal
# TODO Attach network signal to each call -> callback

class NetworkClient(QObject):
    responseReceived = Signal(dict)  # define signal

    def __init__(self, uri: str, verb: str, body: Any):
        super().__init__()
        self.manager = QNetworkAccessManager()
        self.uri = uri
        self.verb = verb
        self.body = body
        self.manager.finished.connect(self.handle_response)

    def send(self):
        url = QUrl(f"http://{os.getenv('URL')}:{os.getenv('PORT')}/{self.uri}")
        request = QNetworkRequest(url)
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        json_data = json.dumps(self.body).encode("utf-8")

        match self.verb.lower():
            case "get":
                self.manager.get(request)
            case "post":
                self.manager.post(request, QByteArray(json_data))
            case "put":
                self.manager.put(request, QByteArray(json_data))
            case "delete":
                self.manager.deleteResource(request)

    def handle_response(self, reply: QNetworkReply):
        if reply.error():
            print("Request failed:", reply.errorString())
            self.responseReceived.emit({})
        else:
            data = reply.readAll().data()
            print("RECEIVED")
            self.responseReceived.emit(json.loads(data))