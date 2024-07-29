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

fovX = 30
fovY = 30
cor = "purple"
offsetY = 1
offsetX = 0
smooth = 3

rzctl = RZCONTROL()
if not rzctl.init():
    print("Failed to initialize rzctl")

resolutionX = win32api.GetSystemMetrics(0)
resolutionY = win32api.GetSystemMetrics(1)

left = (resolutionX - fovX) // 2
top = (resolutionY - fovY) // 2
right = left + fovX
bottom = top + fovY
region = (left, top, right, bottom)
camera = bettercam.create(output_color="RGB")
lock = threading.Lock()

cX = fovX // 2
cY = fovY // 2
center = np.array([cY, cX])


def filter_color_numpy(frame, color):
    if color == "purple":
        mask = (
                (np.abs(frame[:, :, 2] - frame[:, :, 0]) <= 30) &  # Diferença entre vermelho e azul
                ((frame[:, :, 2] - frame[:, :, 1]) >= 60) &  # Diferença entre vermelho e verde
                ((frame[:, :, 0] - frame[:, :, 1]) >= 60) &  # Diferença entre azul e verde
                (frame[:, :, 2] >= 140) &  # Valor do canal vermelho
                (frame[:, :, 0] >= 170) &  # Valor do canal azul
                (frame[:, :, 1] < frame[:, :, 0])  # Valor do canal verde menor que o valor do canal azul
        )

    return mask


def aimbot():
    with lock:
        frame = camera.grab(region=region)
        if frame is None:
            return
        mask = filter_color_numpy(frame, cor)
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

