import sys
import ctypes
from ctypes import *
from ctypes.wintypes import *

ntdll = windll.ntdll
kernel32 = windll.kernel32

NTSTATUS = c_long
STATUS_SUCCESS = NTSTATUS(0x00000000).value
STATUS_UNSUCCESSFUL = NTSTATUS(0xC0000001).value
STATUS_BUFFER_TOO_SMALL = NTSTATUS(0xC0000023).value
PVOID = c_void_p
PWSTR = c_wchar_p
DIRECTORY_QUERY = 0x0001
OBJ_CASE_INSENSITIVE = 0x00000040
INVALID_HANDLE_VALUE = -1
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3


class UNICODE_STRING(Structure):
    _fields_ = [("Length", USHORT), ("MaximumLength", USHORT), ("Buffer", PWSTR)]


class OBJECT_ATTRIBUTES(Structure):
    _fields_ = [
        ("Length", ULONG),
        ("RootDirectory", HANDLE),
        ("ObjectName", POINTER(UNICODE_STRING)),
        ("Attributes", ULONG),
        ("SecurityDescriptor", PVOID),
        ("SecurityQualityOfService", PVOID),
    ]


class OBJECT_DIRECTORY_INFORMATION(Structure):
    _fields_ = [("Name", UNICODE_STRING), ("TypeName", UNICODE_STRING)]


def InitializeObjectAttributes(
    InitializedAttributes, ObjectName, Attributes, RootDirectory, SecurityDescriptor
):
    memset(addressof(InitializedAttributes), 0, sizeof(InitializedAttributes))
    InitializedAttributes.Length = sizeof(InitializedAttributes)
    InitializedAttributes.ObjectName = ObjectName
    InitializedAttributes.Attributes = Attributes
    InitializedAttributes.RootDirectory = RootDirectory
    InitializedAttributes.SecurityDescriptor = SecurityDescriptor
    InitializedAttributes.SecurityQualityOfService = None


def RtlInitUnicodeString(DestinationString, Src):
    memset(addressof(DestinationString), 0, sizeof(DestinationString))
    DestinationString.Buffer = cast(Src, PWSTR)
    DestinationString.Length = sizeof(Src) - 2
    DestinationString.MaximumLength = DestinationString.Length
    return STATUS_SUCCESS


def open_directory(root_handle, dir, desired_access):
    status = STATUS_UNSUCCESSFUL
    dir_handle = c_void_p()
    us_dir = UNICODE_STRING()
    p_us_dir = None
    if dir:
        w_dir = create_unicode_buffer(dir)
        us_dir = UNICODE_STRING()
        status = RtlInitUnicodeString(us_dir, w_dir)
        p_us_dir = pointer(us_dir)
        if status != STATUS_SUCCESS:
            print("RtlInitUnicodeString failed.")
            sys.exit(0)
    obj_attr = OBJECT_ATTRIBUTES()
    InitializeObjectAttributes(
        obj_attr, p_us_dir, OBJ_CASE_INSENSITIVE, root_handle, None
    )
    status = ntdll.NtOpenDirectoryObject(
        byref(dir_handle), desired_access, byref(obj_attr)
    )
    if status != STATUS_SUCCESS:
        print("NtOpenDirectoryObject failed.")
        sys.exit(0)
    return dir_handle


def find_sym_link(dir, name):
    dir_handle = open_directory(None, "\\GLOBAL??", DIRECTORY_QUERY)
    if not dir_handle:
        sys.exit(0)
    status = STATUS_UNSUCCESSFUL
    query_context = ULONG(0)
    length = ULONG()
    objinf = OBJECT_DIRECTORY_INFORMATION()
    found = False
    out = None
    while True:
        status = ntdll.NtQueryDirectoryObject(
            dir_handle, 0, 0, True, False, byref(query_context), byref(length)
        )
        if status != STATUS_BUFFER_TOO_SMALL:
            print("NtQueryDirectoryObject failed.")
            sys.exit(0)
        p_objinf = pointer(objinf)
        status = ntdll.NtQueryDirectoryObject(
            dir_handle,
            p_objinf,
            length,
            True,
            False,
            byref(query_context),
            byref(length),
        )
        if status != STATUS_SUCCESS:
            print("NtQueryDirectoryObject failed.")
            sys.exit(0)
        _name = objinf.Name.Buffer
        if name in _name:
            found = True
            out = _name
            break
    ntdll.NtClose(dir_handle)
    return found, out
