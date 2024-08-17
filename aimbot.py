import threading
import win32api
import numpy as np
from rzctl import RZCONTROL
import bettercam
import time
from hash import calculate_script_hash

calculate_script_hash()

print("só o auxilio")
print("presente do lhnbala")

camera = bettercam.create()

lock = threading.Lock()  # Cria um bloqueio

fovX = 50
fovY = 50
cor = "purple"
offsetY = 1
offsetX = 0
smooth = 1
resolutionX = win32api.GetSystemMetrics(0)
resolutionY = win32api.GetSystemMetrics(1)

left = (resolutionX - fovX) // 2
top = (resolutionY - fovY) // 2
right = left + fovX
bottom = top + fovY
region = (left, top, right, bottom)

cX = fovX // 2
cY = fovY // 2
center = np.array([cY, cX])

rzctl = RZCONTROL()
if not rzctl.init():
    print("Failed to initialize rzctl")

resolutionX = win32api.GetSystemMetrics(0)
resolutionY = win32api.GetSystemMetrics(1)

color_conditions = {
            "yellow": lambda r, g, b: np.logical_and.reduce(
                (r >= 250, r <= 255, g >= 250, g <= 255, b >= 27, b <= 104)),
            "red": lambda r, g, b: np.logical_and(g < 81, np.logical_or(
                np.logical_and.reduce((r >= 180, r <= 255, b >= 30, b <= 120)),
                np.logical_and.reduce((r >= 180, r <= 255, b >= 30, b <= 150)))),
            "purple": lambda r, g, b: np.logical_and.reduce(
                (np.abs(r - b) <= 30, r - g >= 60, b - g >= 60, r >= 140, b >= 170, g < b))
        }

def process_frame(frame, enemy_type):
        r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
        return color_conditions[enemy_type](r, g, b)


def aimbot():
        with lock:  # Adquire o bloqueio antes de acessar a câmera
            frame = camera.grab(region=region)  # captura a tela
            if frame is None:
                return
            mask = process_frame(frame, cor)
            points = np.transpose(np.nonzero(mask))
            if len(points) > 0:
                distances = np.linalg.norm(points - center, axis=1)
                combined_scores = points[:, 0] + distances
                closest_point_index = np.argmin(combined_scores)
                closest_point = points[closest_point_index]
                x_diff = closest_point[1] - cX
                y_diff = closest_point[0] - cY
                y_adjusted_magnet = y_diff + offsetY
                x_adjusted_magnet = x_diff + offsetX
                rzctl.mouse_move(int(x_adjusted_magnet), int(y_adjusted_magnet), smooth, True)

aimbot_thread = threading.Thread(target=aimbot)
aimbot_thread.daemon = True
aimbot_thread.start()


if __name__ == "__main__":
    while True:
        if win32api.GetAsyncKeyState(18):
            aimbot()
        time.sleep(0.001)

