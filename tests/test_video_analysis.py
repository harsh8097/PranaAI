import io
import os
import tempfile

import cv2
import numpy as np

from app import create_app
from app.services.video_analysis import VideoAnalysisService


class MockFile:
    def __init__(self, filename, data):
        self.filename = filename
        self._data = data

    def read(self, size=-1):
        if size < 0:
            return self._data
        return self._data[:size]


def make_avi() -> bytes:
    fd, path = tempfile.mkstemp(suffix=".avi")
    os.close(fd)
    output = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 15.0, (160, 120))
    try:
        for index in range(270):
            frame = np.full((120, 160, 3), 128 + index % 20, dtype=np.uint8)
            output.write(frame)
    finally:
        output.release()
    try:
        with open(path, "rb") as video_file:
            return video_file.read()
    finally:
        os.remove(path)


def test_video_service_rejects_unsupported_files():
    result = VideoAnalysisService().analyze(MockFile("recording.txt", b"not video"))
    assert result["accepted"] is False
    assert result["status"] == "UNSUPPORTED_VIDEO"


def test_video_service_rejects_fake_video_content():
    result = VideoAnalysisService().analyze(MockFile("recording.mp4", b"not a real mp4 file"))
    assert result["accepted"] is False
    assert result["status"] == "INVALID_VIDEO"


def test_video_service_does_not_fabricate_estimate_without_a_face():
    result = VideoAnalysisService().analyze(MockFile("uniform.avi", make_avi()))
    assert result["accepted"] is True
    assert result["status"] == "INSUFFICIENT_SIGNAL_QUALITY"
    assert result["heart_rate_bpm"] is None


def test_video_analysis_api_is_connected():
    client = create_app().test_client()
    response = client.post(
        "/api/video-analysis",
        data={"file": (io.BytesIO(b"not a video"), "clip.mp4")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["status"] == "INVALID_VIDEO"
