from zhinst.core import ziDAQServer

daq = ziDAQServer('localhost', 8004, 6)
daq.connectDevice('dev12247', '1GbE')   # or the device's serial + interface

# daq.sync()   # flush pending sets, invalidate cached gets
# daq.setInt('/dev12247/system/internaltrigger/repetitions', 100000)
# daq.setDouble('/dev12247/system/internaltrigger/holdoff', 1e-3)
# daq.sync()
# daq.setInt('/dev12247/system/internaltrigger/enable', 1)
# daq.sync()
# print(daq.getDouble('/dev12247/system/internaltrigger/progress'))

# daq.sync()
# print(daq.getInt('/dev12247/scopes/0/trigger/channel'))
# print(daq.getInt('/dev12247/scopes/0/trigger/enable'))
# print(daq.getInt('/dev12247/scopes/0/enable'))
# print(daq.getInt('/dev12247/scopes/0/single'))
# print(daq.getInt('/dev12247/scopes/0/segments/enable'),
#       daq.getInt('/dev12247/scopes/0/segments/count'))
# print(daq.getInt('/dev12247/scopes/0/averaging/enable'),
#       daq.getInt('/dev12247/scopes/0/averaging/count'))
# print(daq.getInt('/dev12247/scopes/0/channels/0/enable'))

dev = '/dev12247'

# # scope channel: on, and pointed at the QA input
# daq.setInt(f'{dev}/scopes/0/channels/0/enable', 1)
# daq.setInt(f'{dev}/scopes/0/channels/0/inputselect', 0)  # confirm via node_info

# daq.setInt(f'{dev}/scopes/0/length', 4096)
# daq.setInt(f'{dev}/scopes/0/segments/enable', 0)
# daq.setInt(f'{dev}/scopes/0/averaging/enable', 0)
# daq.setInt(f'{dev}/scopes/0/single', 1)

# # start untriggered to prove the capture path
# daq.setInt(f'{dev}/scopes/0/trigger/enable', 0)
# daq.sync()

# daq.setInt(f'{dev}/scopes/0/enable', 1)
# daq.sync()

# import time
# for _ in range(50):
#     if daq.getInt(f'{dev}/scopes/0/enable') == 0:
#         break
#     time.sleep(0.1)
# else:
#     print('scope never completed even untriggered')

# wave = daq.get(f'{dev}/scopes/0/channels/0/wave', flat=True)
# print(wave)

# print('input/on   :', daq.getInt(f'{dev}/qachannels/0/input/on'))
# print('input/range:', daq.getDouble(f'{dev}/qachannels/0/input/range'))
# print('rflfpath   :', daq.getInt(f'{dev}/qachannels/0/input/rflfpath'))
# print('output/on  :', daq.getInt(f'{dev}/qachannels/0/output/on'))
# print('mode       :', daq.getInt(f'{dev}/qachannels/0/mode'))

# info = device.scopes[0].channels[0].inputselect.node_info
# print(info)   # prints the named options

# import numpy as np
# for sel in range(16):
#     try:
#         daq.setInt(f'{dev}/scopes/0/channels/0/inputselect', sel)
#     except Exception:
#         continue
#     daq.setInt(f'{dev}/scopes/0/single', 1)
#     daq.sync()
#     daq.setInt(f'{dev}/scopes/0/enable', 1)
#     daq.sync()
#     for _ in range(50):
#         if daq.getInt(f'{dev}/scopes/0/enable') == 0:
#             break
#         time.sleep(0.05)
#     v = daq.get(f'{dev}/scopes/0/channels/0/wave', flat=True)
#     vec = v[f'{dev}/scopes/0/channels/0/wave'][0]['vector']
#     print(sel, len(vec), np.max(np.abs(vec)) if len(vec) else None)

# from zhinst.core import ziDAQServer
# import time

# daq = ziDAQServer('localhost', 8004, 6)
# daq.connectDevice('dev12247', '1GbE')

# daq.setInt('/dev12247/system/preset/index', 0)   # 0 = factory default
# daq.sync()
# daq.setInt('/dev12247/system/preset/load', 1)
# daq.sync()

# t0 = time.time()
# while daq.getInt('/dev12247/system/preset/busy') and time.time() - t0 < 60:
#     time.sleep(0.2)
# print('preset done, busy =', daq.getInt('/dev12247/system/preset/busy'))


import zhinst.core
import numpy as np
from zhinst.toolkit import Session as ZISession

zs = ZISession("localhost")

# d = "/dev12247"
# for n in [f"{d}/qachannels/0/mode",
#           f"{d}/qachannels/0/oscs/0/gain",
#           f"{d}/qachannels/0/spectroscopy/result/acquired",
#           f"{d}/qachannels/0/spectroscopy/result/enable",
#           f"{d}/qachannels/0/spectroscopy/length",
#           f"{d}/qachannels/0/output/on",
#           f"{d}/qachannels/0/input/on",
#           f"{d}/qachannels/0/output/rflfpath",
#           f"{d}/qachannels/0/input/rflfpath"]:
#     print(f"{n:58s}", zs.daq_server.getDouble(n))

node = "/dev12247/qachannels/0/spectroscopy/result/data/wave"
raw = zs.daq_server.get(node, flat=True)[node][0]["vector"]
print(type(raw), np.shape(raw))
print("device-side nonzero:", np.count_nonzero(raw))
print(raw[:5])
