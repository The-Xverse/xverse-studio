"""Private child session for autoverse_orca_browser.py; never a host desktop helper."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

OUT = Path(sys.argv[1])
C = json.loads((OUT / "context.private.json").read_bytes())
STATE = Path(__file__).resolve().parent
assert os.readlink("/proc/self/ns/mnt") != C["hostMount"]
assert os.readlink("/proc/self/ns/pid") != C["hostPid"]
assert os.readlink("/proc/self/ns/ipc") != C["hostIpc"]
assert not any(
    k in os.environ
    for k in (
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XAUTHORITY",
        "PULSE_SERVER",
        "PIPEWIRE_REMOTE",
    )
)
assert not any(
    p.name in ("dri", "snd") or p.name.startswith("nvidia")
    for p in Path("/dev").iterdir()
)
assert not Path("/tmp/.X11-unix").exists()
R = Path("/run/user") / str(os.getuid())
assert os.environ["DBUS_SESSION_BUS_ADDRESS"] and os.environ["XDG_RUNTIME_DIR"] == str(
    R
)
for name in ("config", "cache", "data"):
    (R / name).mkdir(mode=0o700)
env = dict(
    os.environ,
    DISPLAY=":71",
    XAUTHORITY=str(R / "authority"),
    SPEECHD_ADDRESS="unix_socket:" + str(R / "speechd.sock"),
)
children = []


def spawn(name, argv):
    log = (OUT / (name + ".log")).open("xb")
    p = subprocess.Popen(
        argv, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT
    )
    fd = os.pidfd_open(p.pid)
    children.append((name, p, fd, log))
    return p


def until(read, predicate, seconds=12):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = read()
        if predicate(value):
            return value
        time.sleep(0.1)
    raise AssertionError("Isolated prerequisite readiness deadline")


def stop(sig, frame):
    raise KeyboardInterrupt("Owned AT test interrupted")


signal.signal(signal.SIGTERM, stop)
status = {
    "namespaces": {n: os.readlink("/proc/self/ns/" + n) for n in ("mnt", "pid", "ipc")},
    "devices": sorted(p.name for p in Path("/dev").iterdir()),
    "ownSessionBus": os.environ["DBUS_SESSION_BUS_ADDRESS"],
    "scope": "Private process/mount/IPC namespace, CPU framebuffer, real eSpeak NG with ALSA null sink; original host backend outside",
}
exit_code = 1
try:
    import secrets

    subprocess.run(
        [
            "/usr/bin/xauth",
            "-f",
            env["XAUTHORITY"],
            "add",
            env["DISPLAY"],
            "MIT-MAGIC-COOKIE-1",
            secrets.token_hex(16),
        ],
        env=env,
        check=True,
        capture_output=True,
    )
    xvfb = Path(C["xvfb"])
    display = spawn(
        "display",
        [
            str(xvfb),
            env["DISPLAY"],
            "-auth",
            env["XAUTHORITY"],
            "-nolisten",
            "tcp",
            "-nolisten",
            "local",
            "-screen",
            "0",
            "1440x900x24",
            "-noreset",
        ],
    )

    def ready():
        assert display.poll() is None
        return subprocess.run(
            ["/usr/bin/xdpyinfo"], env=env, capture_output=True, timeout=2
        ).returncode

    until(ready, lambda x: x == 0)
    conf = R / "speech-config"
    conf.mkdir()
    (conf / "speechd.conf").write_text(
        'CommunicationMethod "unix_socket"\nSocketPath "'
        + str(R / "speechd.sock")
        + '"\nLogLevel 5\nLogDir "'
        + str(OUT / "speech-logs")
        + '"\nAudioOutputMethod "alsa"\nAudioALSADevice "null"\nAddModule "espeak-ng" "sd_espeak-ng" "/etc/speech-dispatcher/modules/espeak-ng.conf"\nDefaultModule "espeak-ng"\nDisableAutoSpawn\n'
    )
    (OUT / "speech-logs").mkdir()
    speech = spawn(
        "speech-dispatcher",
        [
            "/usr/bin/speech-dispatcher",
            "--run-single",
            "--config-dir",
            str(conf),
            "--module-dir",
            "/usr/lib/speech-dispatcher-modules",
            "--pid-file",
            str(R / "speech.pid"),
            "--timeout",
            "0",
        ],
    )
    until(
        lambda: (speech.poll(), (R / "speechd.sock").exists()),
        lambda x: x == (None, True),
    )
    import speechd

    client = speechd.SSIPClient(
        "StudioATPrerequisite", address=env["SPEECHD_ADDRESS"], autospawn=False
    )
    status["speechModules"] = client.list_output_modules()
    assert tuple(status["speechModules"]) == ("espeak-ng",)
    status["defaultSpeechModule"] = client.get_output_module()
    assert status["defaultSpeechModule"] == "espeak-ng"
    client.close()
    prefs = OUT / "orca-prefs"
    prefs.mkdir()
    (prefs / "user-settings.conf").write_text(
        json.dumps(
            {
                "general": {
                    "enableBraille": False,
                    "enableSpeech": True,
                    "enableKeyEcho": False,
                    "speechServerInfo": ["espeak-ng", "espeak-ng"],
                    "startingProfile": ["Default", "default"],
                },
                "profiles": {
                    "default": {
                        "profile": ["Default", "default"],
                        "pronunciations": {},
                        "keybindings": {},
                    }
                },
                "pronunciations": {},
                "keybindings": {},
            }
        )
    )
    orca_argv = [
        "/usr/bin/orca",
        "--user-prefs",
        str(prefs),
        "--debug-file",
        str(OUT / "orca-debug.private.log"),
    ]
    orca = spawn("orca", orca_argv)
    # Orca's debug file is buffered. Confirm its actual Speech Dispatcher
    # connection and successful first SPEAK rather than polling unflushed text.
    until(
        lambda: (OUT / "speech-logs/speech-dispatcher.log").read_text(errors="replace"),
        lambda x: "CLIENT_NAME unknown:Orca:espeak-ng" in x and "200 OK SPEAKING" in x,
        20,
    )
    assert orca.poll() is None
    inspector = spawn(
        "inspector",
        ["/usr/bin/python3", "-I", str(STATE / "autoverse_orca_inspect.py"), str(OUT)],
    )
    until(lambda: (OUT / "atspi-ready.json").exists(), bool)
    node = C["node"]
    script = {
        "retained-results": "autoverse-orca.cjs",
        "scenario-conditions": "autoverse-orca-authoring.cjs",
        "lab-inventory": "autoverse-orca-lab.cjs",
    }[C["suite"]]
    browser = spawn("browser", [node, str(STATE / script), str(OUT)])
    exit_code = browser.wait(timeout=115)
    assert orca.poll() is None and inspector.poll() is None and speech.poll() is None
    status["browserExit"] = exit_code
finally:
    terminals = []
    for name, p, fd, log in reversed(children):
        if p.poll() is None:
            signal.pidfd_send_signal(fd, signal.SIGTERM, None, 0)
        try:
            p.wait(timeout=8)
        except subprocess.TimeoutExpired:
            signal.pidfd_send_signal(fd, signal.SIGKILL, None, 0)
            p.wait(timeout=3)
        terminals.append({"name": name, "pid": p.pid, "exit": p.returncode})
        os.close(fd)
        log.close()
    status["terminals"] = terminals
    (OUT / "isolation.private.json").write_text(json.dumps(status, indent=2) + "\n")
raise SystemExit(exit_code)
