import subprocess


def shutdown():
    subprocess.run(["doas", "shutdown", "-h", "now"])


def restart():
    subprocess.run(["doas", "shutdown", "-r", "now"])


def suspend_mem():
    subprocess.run(["doas", "zzz", "-z"])


def suspend_freeze():
    subprocess.run(["doas", "zzz", "-S"])


def suspend_disk():
    subprocess.run(["doas", "zzz", "-Z"])
