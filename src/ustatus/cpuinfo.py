def get_core_per_cpu():
    cpuinfo = open("/proc/cpuinfo", "r").read().strip().split("\n\n")
    cores = []
    for cpu in cpuinfo:
        [core] = [
            int(s.split(":")[1].strip())
            for s in cpu.splitlines()
            if s.startswith("core id")
        ]
        cores.append(core)
    return cores
