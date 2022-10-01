import asyncio
import json


async def run(cmd):
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    match proc.returncode:
        case 0:
            pass
        case 1:
            raise Exception(f"swaymsg exception: {stderr.decode()}")
        case 2:
            raise Exception(f"sway exception: {stderr.decode()}")

    return json.loads(stdout.decode())


async def run_stream(cmd):
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)

    assert proc.stdout is not None

    buf = bytes()
    open_obj = 0
    open_lst = 0
    while True:
        # TODO: Make or find a more efficient buffer for this purpose
        c = await proc.stdout.read(n=1)
        if not c:
            break
        match c:
            case b"{":
                open_obj += 1
            case b"}":
                open_obj -= 1
            case b"[":
                open_lst += 1
            case b"]":
                open_lst -= 1
        buf += c
        if open_obj == 0 and open_lst == 0 and not c.isspace():
            yield json.loads(buf)
            buf = bytes()


async def get_workspaces():
    return await run(["swaymsg", "-t", "get_workspaces"])


async def get_outputs():
    return await run(["swaymsg", "-t", "get_outputs"])


async def sway_command(cmd: str):
    return await run(["swaymsg", cmd])


async def subscribe(event_types):
    async for event in run_stream(
        ["swaymsg", "--monitor", "-t", "subscribe", json.dumps(event_types)]
    ):
        yield event
