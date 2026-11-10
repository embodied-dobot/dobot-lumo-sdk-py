# dobot-sdk-py

给二开用的 Python SDK。需要 Python 3.12。这份目录里的扩展是按 3.12 编译的。

`dobot.__version__` 是 Python 包版本。`dobot.cpp_sdk_version` 是这份扩展编译时链上的 C++ SDK 版本。增加函数是次版本；修改已有函数的参数或返回值是主版本。

把本目录加入 `PYTHONPATH` 后：

```python
import dobot
from dobot import sr_3588

config = dobot.SessionConfig()
config.robot_ip = "192.168.5.2"
config.network_interface = "eth0"

session = dobot.Session()
ok, error = session.Init(sr_3588.Profile(), config)
if not ok:
    raise SystemExit(error)

code, fsm_id = session.motion().GetFsmId()
print(fsm_id, dobot.Motion.FsmIdToString(fsm_id))

lower = session.Subscribe(sr_3588.kTopicLowerState)
lower.WaitForData(5000)
sample = lower.Latest()
session.Shutdown()
```

`SR_thor` 换成 `dobot.sr_thor`，默认 IP 是 `172.16.20.2`。程序跑在机器人本机时把 `config.where` 设为 `dobot.RunWhere.kRobot`，并且不要填 `robot_ip`。

示例在 `example/`：

```bash
python3 example/motion_demo.py --model sr_3588 --ip 192.168.5.2
python3 example/dds_echo.py --model sr_3588 --nic eth0
python3 example/rpc_call.py --model sr_3588 --method ReloadArmSkillsData
python3 example/dds_publish_cmd.py --model sr_3588 --send --nic eth0
python3 example/dds_event.py --model sr_3588 --nic eth0
python3 example/state_gap.py --model sr_3588 --nic eth0 --duration 10
python3 example/upper_arm_swing.py --move --nic eth0
python3 example/walk_demo.py --model sr_3588 --run --nic eth0
```

x86_64 和 aarch64 的扩展、`libfastdds.so`、`libfastcdr.so`、`libdobot_log.so` 都在 `dobot/native/<架构>` 和 `dobot/lib/<架构>`。导入时按当前机器选择。

接口和 C++ SDK 对应：`Session.Init` / `Shutdown` / `Call` / `Subscribe` / `Publish`，`motion()` 上的模式、预设动作、舞蹈和速度，`rpc()` 上的薄 RPC。订阅有 `Latest`、`WaitForData`、`On`、`Matched`。同一消息类型一次会话只能订一个话题；骨盆 IMU 和躯干 IMU 都是 `IMUState_`，只能订一路。

`Init` 返回 `(成功, 错误字符串)`。运控方法成功返回 `0`，否则是 `RpcError` 的整数值。`GetFsmId` 和 `GetFsmList` 返回 `(错误码, 结果)`，失败时结果是 `None`。
