from rzctl_nt import (
    ntdll,
    kernel32,
    find_sym_link,
    INVALID_HANDLE_VALUE,
    FILE_SHARE_READ,
    FILE_SHARE_WRITE,
    OPEN_EXISTING,
    Structure,
    c_int32,
    c_ulong,
    pointer,
    sizeof,
    byref,
    BOOL,
    GetLastError,
    windll
)
import math

def get_screen_resolution():
    user32 = windll.user32
    screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    return screensize

def enum(**enums):
    return type("Enum", (), enums)


MOUSE_CLICK = enum(
    LEFT_DOWN=1,
    LEFT_UP=2,
    RIGHT_DOWN=4,
    RIGHT_UP=8,
    SCROLL_CLICK_DOWN=16,
    SCROLL_CLICK_UP=32,
    BACK_DOWN=64,
    BACK_UP=128,
    FOWARD_DOWN=256,
    FOWARD_UP=512,
    SCROLL_DOWN=4287104000,
    SCROLL_UP=7865344,
)

KEYBOARD_INPUT_TYPE = enum(KEYBOARD_DOWN=0, KEYBOARD_UP=1)


class RZCONTROL_IOCTL_STRUCT(Structure):
    _fields_ = [
        ("unk0", c_int32),
        ("unk1", c_int32),
        ("max_val_or_scan_code", c_int32),
        ("click_mask", c_int32),
        ("unk3", c_int32),
        ("x", c_int32),
        ("y", c_int32),
        ("unk4", c_int32),
    ]


IOCTL_MOUSE = 0x88883020
RZCONTROL_MOUSE = 2
RZCONTROL_KEYBOARD = 1


class RZCONTROL:

    hDevice = INVALID_HANDLE_VALUE

    def __init__(self):
        pass

    def init(self):
        if RZCONTROL.hDevice != INVALID_HANDLE_VALUE:
            kernel32.CloseHandle(RZCONTROL.hDevice)
        found, name = find_sym_link("\\GLOBAL??", "RZCONTROL")
        if not found:
            print("Não foi possível encontrar o link simbólico.")
            return False
        sym_link = "\\\\?\\" + name
        RZCONTROL.hDevice = kernel32.CreateFileW(
            sym_link, 0, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_EXISTING, 0, 0
        )
        if RZCONTROL.hDevice == INVALID_HANDLE_VALUE:
            print(f"Falha ao abrir o dispositivo. Código de erro: {GetLastError()}")
        return RZCONTROL.hDevice != INVALID_HANDLE_VALUE

    def impl_mouse_ioctl(self, ioctl):
        if ioctl:
            p_ioctl = pointer(ioctl)
            junk = c_ulong()
            bResult = kernel32.DeviceIoControl(
                RZCONTROL.hDevice,
                IOCTL_MOUSE,
                p_ioctl,
                sizeof(RZCONTROL_IOCTL_STRUCT),
                0,
                0,
                byref(junk),
                0,
            )
            if not bResult:
                print(f"Erro ao enviar comando: {GetLastError()}")
                self.init()
            return bResult
        return False

    def mouse_move(self, x, y, speed, from_start_point):
        # Validate the speed
        if speed <= 0:
            raise ValueError("Speed must be greater than zero.")

        screen_width, screen_height = get_screen_resolution()

        # Ensure x and y are within the screen bounds
        if not from_start_point:
            max_val = max(screen_width, screen_height)
            if x < 1:
                x = 1
            if x > screen_width:
                x = screen_width
            if y < 1:
                y = 1
            if y > screen_height:
                y = screen_height
        else:
            max_val = 0

        # Parameters for movement
        x_current = 0.0
        y_current = 0.0
        overflow_x = 0.0
        overflow_y = 0.0

        # Define the movement increments
        u_x = (x - x_current) / speed
        u_y = (y - y_current) / speed

        for i in range(1, int(speed) + 1):
            xI = i * u_x
            yI = i * u_y

            # Handle overflow
            xI, overflow_x = self.add_overflow(xI, overflow_x)
            yI, overflow_y = self.add_overflow(yI, overflow_y)

            final_x = int(xI - x_current)
            final_y = int(yI - y_current)

            if final_x != 0 or final_y != 0:
                # Create and send the mouse movement request
                mm = RZCONTROL_IOCTL_STRUCT(0, RZCONTROL_MOUSE, max_val, 0, 0, final_x, final_y, 0)
                self.impl_mouse_ioctl(mm)

            # Update current position
            x_current = xI
            y_current = yI

    def add_overflow(self, Input, Overflow):
        Integral = 0.0
        Overflow, Integral = math.modf(Input + Overflow)

        if Overflow > 1.0:
            Overflow, Integral = math.modf(Overflow)
            Input += Integral
        return Input, Overflow

    def mouse_click(self, click_mask):
        """
        Args:
            click_mask (MOUSE_CLICK):
        """
        mm = RZCONTROL_IOCTL_STRUCT(
            0,
            RZCONTROL_MOUSE,
            0,
            click_mask,
            0,
            0,
            0,
            0,
        )
        self.impl_mouse_ioctl(mm)

    def keyboard_input(self, scan_code, up_down):
        """
        Args:
            scan_code (short): https://www.millisecond.com/support/docs/current/html/language/scancodes.htm
            up_down (KEYBOARD_INPUT_TYPE): _description_
        """
        mm = RZCONTROL_IOCTL_STRUCT(
            0,
            RZCONTROL_KEYBOARD,
            (int(scan_code) << 16),
            up_down,
            0,
            0,
            0,
            0,
        )
        self.impl_mouse_ioctl(mm)
