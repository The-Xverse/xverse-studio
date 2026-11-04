"""Documented Windows handle operations for managed files (native verification open).

No DLL is loaded on import. Every relative open is a single validated component;
existing objects are opened as reparse points and checked before use. Directory
handles omit FILE_SHARE_DELETE and remain held by the caller during traversal.
Only fixed local NTFS volumes with persistent ACLs are admitted. No privilege is
enabled and no path-based fallback is provided.
"""

from contextlib import contextmanager
import ctypes as c
from functools import lru_cache
import os
import sys

from .windows_paths import component


# Fixed-width fields matter: ctypes.c_ulong/wchar have different widths on Linux.
DWORD, WORD, BYTE = c.c_uint32, c.c_uint16, c.c_uint8
HANDLE, PVOID, ULONG_PTR = c.c_void_p, c.c_void_p, c.c_size_t
BOOL, NTSTATUS = c.c_int32, c.c_int32
SYNCHRONIZE = 0x100000
READ_ATTRIBUTES, DELETE = 0x80, 0x10000
READ, WRITE = 0x80000000, 0x40000000
DIRECTORY, REPARSE = 0x10, 0x400


class UnicodeString(c.Structure):
    _fields_ = [("Length", WORD), ("MaximumLength", WORD), ("Buffer", PVOID)]


class ObjectAttributes(c.Structure):
    _fields_ = [
        ("Length", DWORD),
        ("RootDirectory", HANDLE),
        ("ObjectName", c.POINTER(UnicodeString)),
        ("Attributes", DWORD),
        ("SecurityDescriptor", PVOID),
        ("SecurityQualityOfService", PVOID),
    ]


class IOStatus(c.Structure):
    _fields_ = [("Status", PVOID), ("Information", ULONG_PTR)]


class AttributeTag(c.Structure):
    _fields_ = [("FileAttributes", DWORD), ("ReparseTag", DWORD)]


class RenameInfo(c.Structure):
    _fields_ = [
        ("ReplaceIfExists", BYTE),
        ("RootDirectory", HANDLE),
        ("FileNameLength", DWORD),
        ("FileName", WORD * 1),
    ]


class DirectoryInfo(c.Structure):
    _fields_ = [
        ("NextEntryOffset", DWORD),
        ("FileIndex", DWORD),
        ("CreationTime", c.c_int64),
        ("LastAccessTime", c.c_int64),
        ("LastWriteTime", c.c_int64),
        ("ChangeTime", c.c_int64),
        ("EndOfFile", c.c_int64),
        ("AllocationSize", c.c_int64),
        ("FileAttributes", DWORD),
        ("FileNameLength", DWORD),
        ("EaSize", DWORD),
        ("ShortNameLength", BYTE),
        ("ShortName", WORD * 12),
        ("FileId", c.c_int64),
        ("FileName", WORD * 1),
    ]


def rename_buffer(parent, name, replace):
    """Build the length-delimited native ABI, including a zeroed terminator."""
    encoded = component(name).encode("utf-16-le")
    buffer = c.create_string_buffer(
        max(c.sizeof(RenameInfo), RenameInfo.FileName.offset + len(encoded) + 2)
    )
    info = RenameInfo.from_buffer(buffer)
    info.ReplaceIfExists = bool(replace)
    info.RootDirectory = parent
    info.FileNameLength = len(encoded)
    c.memmove(c.addressof(buffer) + RenameInfo.FileName.offset, encoded, len(encoded))
    return buffer


def directory_names(data):
    """Decode a bounded native enumeration page without trusting entry offsets."""
    offset, names = 0, []
    start = DirectoryInfo.FileName.offset
    while True:
        if offset + start > len(data):
            raise ValueError("UNSAFE_PATH")
        # Header has tail padding; a last entry need not include that padding.
        next_offset = int.from_bytes(data[offset : offset + 4], "little")
        length = int.from_bytes(
            data[
                offset + DirectoryInfo.FileNameLength.offset : offset
                + DirectoryInfo.FileNameLength.offset
                + 4
            ],
            "little",
        )
        end = offset + start + length
        if length % 2 or not length or length > 510 or end > len(data):
            raise ValueError("UNSAFE_PATH")
        name = data[offset + start : end].decode("utf-16-le")
        if name not in {".", ".."}:
            names.append(component(name))
        if next_offset == 0:
            return names
        if (
            next_offset % 8
            or next_offset < start + length
            or offset + next_offset >= len(data)
        ):
            raise ValueError("UNSAFE_PATH")
        offset += next_offset


class Native:
    def __init__(self):
        from .managed_io import SafeIOError

        if sys.platform != "win32":
            raise SafeIOError("SECURE_IO_UNAVAILABLE")
        import msvcrt

        self.crt = msvcrt
        try:
            self.kernel = c.WinDLL("kernel32", use_last_error=True)
            self.advapi = c.WinDLL("advapi32", use_last_error=True)
            self.ntdll = c.WinDLL("ntdll", use_last_error=True)
            self._bind()
        except (AttributeError, OSError):
            raise SafeIOError("SECURE_IO_UNAVAILABLE") from None

    def _bind(self):
        def bind(dll, name, result, *arguments):
            function = getattr(dll, name)
            function.restype, function.argtypes = result, list(arguments)
            setattr(self, name, function)

        bind(self.kernel, "CloseHandle", BOOL, HANDLE)
        bind(
            self.kernel,
            "CreateFileW",
            HANDLE,
            c.c_wchar_p,
            DWORD,
            DWORD,
            PVOID,
            DWORD,
            DWORD,
            HANDLE,
        )
        bind(self.kernel, "GetDriveTypeW", DWORD, c.c_wchar_p)
        bind(self.kernel, "GetFileType", DWORD, HANDLE)
        bind(
            self.kernel,
            "GetFileInformationByHandleEx",
            BOOL,
            HANDLE,
            c.c_int,
            PVOID,
            DWORD,
        )
        bind(
            self.kernel,
            "SetFileInformationByHandle",
            BOOL,
            HANDLE,
            c.c_int,
            PVOID,
            DWORD,
        )
        bind(
            self.kernel,
            "GetVolumeInformationByHandleW",
            BOOL,
            HANDLE,
            c.c_wchar_p,
            DWORD,
            c.POINTER(DWORD),
            c.POINTER(DWORD),
            c.POINTER(DWORD),
            c.c_wchar_p,
            DWORD,
        )
        bind(self.kernel, "GetCurrentProcess", HANDLE)
        bind(self.kernel, "LocalFree", PVOID, PVOID)
        bind(self.advapi, "OpenProcessToken", BOOL, HANDLE, DWORD, c.POINTER(HANDLE))
        bind(
            self.advapi,
            "GetTokenInformation",
            BOOL,
            HANDLE,
            c.c_int,
            PVOID,
            DWORD,
            c.POINTER(DWORD),
        )
        bind(self.advapi, "ConvertSidToStringSidW", BOOL, PVOID, c.POINTER(PVOID))
        bind(
            self.advapi,
            "ConvertStringSecurityDescriptorToSecurityDescriptorW",
            BOOL,
            c.c_wchar_p,
            DWORD,
            c.POINTER(PVOID),
            c.POINTER(DWORD),
        )
        bind(
            self.advapi,
            "GetSecurityDescriptorDacl",
            BOOL,
            PVOID,
            c.POINTER(BOOL),
            c.POINTER(PVOID),
            c.POINTER(BOOL),
        )
        bind(
            self.advapi,
            "GetSecurityDescriptorOwner",
            BOOL,
            PVOID,
            c.POINTER(PVOID),
            c.POINTER(BOOL),
        )
        bind(
            self.advapi,
            "GetSecurityDescriptorControl",
            BOOL,
            PVOID,
            c.POINTER(WORD),
            c.POINTER(DWORD),
        )
        bind(
            self.advapi,
            "GetSecurityInfo",
            DWORD,
            HANDLE,
            c.c_int,
            DWORD,
            c.POINTER(PVOID),
            PVOID,
            c.POINTER(PVOID),
            PVOID,
            c.POINTER(PVOID),
        )
        bind(self.advapi, "GetAce", BOOL, PVOID, DWORD, c.POINTER(PVOID))
        bind(self.advapi, "EqualSid", BOOL, PVOID, PVOID)
        bind(
            self.ntdll,
            "NtCreateFile",
            NTSTATUS,
            c.POINTER(HANDLE),
            DWORD,
            c.POINTER(ObjectAttributes),
            c.POINTER(IOStatus),
            PVOID,
            DWORD,
            DWORD,
            DWORD,
            DWORD,
            PVOID,
            DWORD,
        )
        bind(self.ntdll, "RtlNtStatusToDosError", DWORD, NTSTATUS)

    def fail(self, error=None):
        from .managed_io import SafeIOError

        error = c.get_last_error() if error is None else error
        code = {
            2: "FILE_MISSING",
            3: "FILE_MISSING",
            80: "TARGET_EXISTS",
            183: "TARGET_EXISTS",
            32: "SOURCE_CHANGED",
            33: "SOURCE_CHANGED",
            1: "SECURE_IO_UNAVAILABLE",
            50: "SECURE_IO_UNAVAILABLE",
            120: "SECURE_IO_UNAVAILABLE",
        }.get(error, "UNSAFE_PATH")
        raise SafeIOError(code)

    def handle(self, descriptor):
        return self.crt.get_osfhandle(descriptor)

    def descriptor(self, handle, *, writable=False):
        try:
            # Binary/non-inheritable CRT ownership; close exactly once via os.close.
            return self.crt.open_osfhandle(
                handle,
                os.O_BINARY
                | os.O_NOINHERIT
                | (os.O_WRONLY if writable else os.O_RDONLY),
            )
        except BaseException:
            self.CloseHandle(handle)
            raise

    def checked(self, descriptor, *, directory=None):
        from .managed_io import SafeIOError

        handle = self.handle(descriptor)
        attributes = AttributeTag()
        if self.GetFileType(handle) != 1:
            raise SafeIOError("UNSAFE_PATH")
        if not self.GetFileInformationByHandleEx(
            handle, 9, c.byref(attributes), c.sizeof(attributes)
        ):
            self.fail()
        if attributes.FileAttributes & REPARSE or attributes.ReparseTag:
            raise SafeIOError("UNSAFE_PATH")
        is_directory = bool(attributes.FileAttributes & DIRECTORY)
        if directory is not None and is_directory != directory:
            raise SafeIOError("UNSAFE_PATH")
        info = os.fstat(descriptor)
        if not is_directory and info.st_nlink != 1:
            raise SafeIOError("UNSAFE_PATH")
        return info

    def drive(self, root):
        from .managed_io import SafeIOError

        if self.GetDriveTypeW(str(root)) != 3:  # DRIVE_FIXED, never a network share.
            raise SafeIOError("SECURE_IO_UNAVAILABLE")
        handle = self.CreateFileW(
            "\\\\?\\" + str(root),
            1 | READ_ATTRIBUTES | SYNCHRONIZE,
            3,
            None,
            3,
            0x02200000,
            None,
        )
        if handle == c.c_void_p(-1).value:
            self.fail()
        descriptor = self.descriptor(handle)
        try:
            self.checked(descriptor, directory=True)
            filesystem, flags = c.create_unicode_buffer(32), DWORD()
            if not self.GetVolumeInformationByHandleW(
                handle, None, 0, None, None, c.byref(flags), filesystem, len(filesystem)
            ):
                self.fail()
            if filesystem.value != "NTFS" or not flags.value & 8:
                raise SafeIOError("SECURE_IO_UNAVAILABLE")
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    @contextmanager
    def private_security(self):
        """Protected owner-only DACL at creation, before any data is written."""
        token, sid_text, security = HANDLE(), PVOID(), PVOID()
        try:
            if not self.OpenProcessToken(self.GetCurrentProcess(), 8, c.byref(token)):
                self.fail()
            length = DWORD()
            self.GetTokenInformation(token, 1, None, 0, c.byref(length))
            if not 0 < length.value <= 65536:
                self.fail()
            user = c.create_string_buffer(length.value)
            if not self.GetTokenInformation(token, 1, user, len(user), c.byref(length)):
                self.fail()
            sid = c.cast(user, c.POINTER(PVOID))[0]
            if not self.ConvertSidToStringSidW(sid, c.byref(sid_text)):
                self.fail()
            owner = c.wstring_at(sid_text)
            if not self.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                f"O:{owner}D:P(A;OICI;FA;;;{owner})", 1, c.byref(security), None
            ):
                self.fail()
            yield security
        finally:
            if security.value:
                self.LocalFree(security)
            if sid_text.value:
                self.LocalFree(sid_text)
            if token.value:
                self.CloseHandle(token)

    def acquire(
        self,
        parent,
        name,
        *,
        directory=None,
        create=False,
        writable=False,
        delete=False,
    ):
        from .managed_io import SafeIOError

        self.checked(parent, directory=True)
        try:
            encoded = component(name).encode("utf-16-le")
        except ValueError:
            raise SafeIOError("UNSAFE_PATH") from None
        text = c.create_string_buffer(encoded + b"\0\0")
        unicode = UnicodeString(len(encoded), len(encoded) + 2, c.addressof(text))
        attributes = ObjectAttributes(
            c.sizeof(ObjectAttributes),
            self.handle(parent),
            c.pointer(unicode),
            0x40,
            None,
            None,
        )
        access = READ_ATTRIBUTES | SYNCHRONIZE | 0x20000  # READ_CONTROL for ACL checks.
        access |= WRITE if writable else (1 if directory else READ)
        access |= DELETE if delete else 0
        # Existing directory opens omit FILE_DIRECTORY_FILE: its documented
        # compatibility list excludes FILE_OPEN_REPARSE_POINT. Verify type after
        # acquisition. Exclusive directory creation cannot open an existing link.
        options = 0x20 | (1 if create and directory else 0x200000)
        handle, status = HANDLE(), IOStatus()

        def perform(security):
            attributes.SecurityDescriptor = security
            result = self.NtCreateFile(
                c.byref(handle),
                access,
                c.byref(attributes),
                c.byref(status),
                None,
                DIRECTORY if directory and create else 0x80,
                3 if directory else 1,
                2 if create else 1,
                options,
                None,
                0,
            )
            if result < 0:
                self.fail(self.RtlNtStatusToDosError(result))
            if not handle.value or handle.value == c.c_void_p(-1).value:
                self.fail(50)

        if create:
            with self.private_security() as security:
                perform(security)
        else:
            perform(None)
        descriptor = self.descriptor(handle.value, writable=writable)
        try:
            self.checked(descriptor, directory=directory)
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def verify_private(self, descriptor):
        """Require an owner-only protected ACL without rewriting descendants."""
        target, owner, dacl = PVOID(), PVOID(), PVOID()
        try:
            result = self.GetSecurityInfo(
                self.handle(descriptor),
                1,
                5,
                c.byref(owner),
                None,
                c.byref(dacl),
                None,
                c.byref(target),
            )
            if result:
                self.fail(result)
            control, revision = WORD(), DWORD()
            if not self.GetSecurityDescriptorControl(
                target, c.byref(control), c.byref(revision)
            ):
                self.fail()
            if not control.value & 0x1000 or not owner.value or not dacl.value:
                self.fail(5)
            # ACL header WORDs: revision/reserved, size, ACE count, reserved.
            if c.cast(dacl, c.POINTER(WORD))[2] != 1:
                self.fail(5)
            ace = PVOID()
            if not self.GetAce(dacl, 0, c.byref(ace)):
                self.fail()
            header = c.string_at(ace, 8)
            if (
                header[0] != 0
                or header[1] & 0x10
                or int.from_bytes(header[4:8], "little") != 0x1F01FF
            ):
                self.fail(5)
            with self.private_security() as expected:
                expected_owner, defaulted = PVOID(), BOOL()
                if not self.GetSecurityDescriptorOwner(
                    expected, c.byref(expected_owner), c.byref(defaulted)
                ):
                    self.fail()
                if not self.EqualSid(owner, expected_owner) or not self.EqualSid(
                    ace.value + 8, expected_owner
                ):
                    self.fail(5)
        finally:
            if target.value:
                self.LocalFree(target)

    def rename(self, descriptor, parent, name, *, replace=False):
        buffer = rename_buffer(self.handle(parent), name, replace)
        if not self.SetFileInformationByHandle(
            self.handle(descriptor), 3, buffer, len(buffer)
        ):
            self.fail()

    def discard(self, descriptor):
        delete = BYTE(1)
        if not self.SetFileInformationByHandle(
            self.handle(descriptor), 4, c.byref(delete), c.sizeof(delete)
        ):
            self.fail()

    def names(self, descriptor):
        buffer = c.create_string_buffer(65536)
        restart = True
        while True:
            if not self.GetFileInformationByHandleEx(
                self.handle(descriptor), 11 if restart else 10, buffer, len(buffer)
            ):
                if c.get_last_error() == 18:  # ERROR_NO_MORE_FILES
                    return
                self.fail()
            restart = False
            try:
                yield from directory_names(buffer.raw)
            except ValueError:
                self.fail(5)


@lru_cache(maxsize=1)
def native():
    return Native()
