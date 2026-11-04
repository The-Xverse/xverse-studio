/** Optional contributor hardware isolation proof; not an application requirement. */
import type { FullConfig } from "@playwright/test";
import { existsSync, readdirSync, readlinkSync, writeFileSync } from "node:fs";

export default async function setup(config: FullConfig) {
  if (process.env.STUDIO_BROWSER_CPU_ONLY !== "1") return;
  const target = process.env.STUDIO_BROWSER_DEVICE_PROOF;
  const hostNamespace = process.env.STUDIO_BROWSER_HOST_MOUNT_NS;
  const allowed = new Set([
    "core", "fd", "full", "null", "ptmx", "pts", "random", "shm",
    "stderr", "stdin", "stdout", "tty", "urandom", "zero",
  ]);
  const devices = readdirSync("/dev").sort();
  const namespace = readlinkSync("/proc/self/ns/mnt");
  const flags = config.projects[0].use.launchOptions?.args ?? [];
  const displaysUnset = ["DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS"]
    .every(name => !process.env[name]);
  if (!target || !hostNamespace || namespace === hostNamespace ||
      devices.some(name => !allowed.has(name)) || !displaysUnset ||
      existsSync("/tmp/.X11-unix") ||
      !flags.includes("--disable-gpu") || !flags.includes("--disable-gpu-rasterization")) {
    throw new Error("BROWSER_DEVICE_ISOLATION_UNVERIFIED");
  }
  writeFileSync(target, JSON.stringify({
    scope: "Linux contributor browser only; original backend outside namespace",
    uid: process.getuid?.(), devices, namespace, hostNamespace,
    displaysUnset, xSocketVisible: false, flags, nodePid: process.pid,
  }, null, 2), { mode: 0o600 });
}
