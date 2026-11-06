from .topic import Topic
from ._load import native

kModel = "SR_3588"
kDefaultRobotIp = "192.168.5.2"
kAlgsRpcPort = 51234

kTopicLowerState = Topic("rt/lower/state", "LowerState_")
kTopicUpperState = Topic("rt/upper/state", "UpperState_")
kTopicLowerCmd = Topic("rt/lower/cmd", "LowerCmd_")
kTopicUpperCmd = Topic("rt/upper/cmd", "UpperCmd_")
kTopicStandCmd = Topic("rt/stand/cmd", "StandingControl_")
kTopicPelvisImu = Topic("rt/pelvis/imu/data", "IMUState_")
kTopicTorsoImu = Topic("rt/torso/imu/data", "IMUState_")
kTopicGamepadState = Topic("rt/gamepad/state", "GamepadState_")
kTopicMainNodesState = Topic("rt/main/nodes/state", "MainNodesState_")
kTopicMcuBmsCommon = Topic("Mcu/BmsCommon", "BmsCommon_")
kTopicMcuBmsUncommon = Topic("Mcu/BmsUncommon", "BmsUncommon_")
kTopicMcuHeartbeat = Topic("Mcu/Heartbeat", "Heartbeat_")
kTopicMcuEstop = Topic("Mcu/Estop", "Estop_")
kTopicMcuAdc = Topic("Mcu/Adc", "Adc_")
kTopicMcuTemp = Topic("Mcu/Temp", "Temp_")
kTopicMcuInit = Topic("Mcu/Init", "McuInit_")
kTopicMcuFault = Topic("Mcu/Fault", "Fault_")
kTopicEnableMotors = Topic("rt/enable/motors", "EnableMotors_")
kTopicClearErrors = Topic("rt/clear/errors", "ClearErrors_")
kTopicGoHome = Topic("rt/go/home", "GoHome_")
kTopicSetCalibrationFlag = Topic("rt/set/calibration/flag", "SetCalibrationFlag_")
kTopicSetFsmId = Topic("rt/set/fsm/id", "SetFsmId_")
kTopicRemoteControl = Topic("rt/remote/control", "RemoteControl_")
kTopicDiagnosticReport = Topic("rt/diagnostic/report", "DiagnosticReport_")
kTopicLocomotionAlarm = Topic("rt/locomotion/alarm/state", "LocomotionAlarmState_")
kTopicWifiStatus = Topic("rt/wifi/status", "WifiStatus_")
kTopicPerfFault = Topic("dobot_perf_fault", "FaultInfo_")
kTopicVoiceCommand = Topic("rt/voice/command", "VoiceCommand_")
kTopicVoiceVadEvent = Topic("rt/voice/vad_event", "VADEvent_")
kTopicVoiceTtsRequest = Topic("rt/voice/tts_request", "TTSRequest_")
kTopicVoiceAckRequest = Topic("rt/voice/ack_request", "AckRequest_")
kTopicVoiceControl = Topic("rt/voice/control", "VoiceControl_")
kTopicVoiceOutputEvent = Topic("rt/voice/output_event", "VoiceOutputEvent_")
kTopicHeadEyeEffectCmd = Topic("rt/head/eye_effect_cmd", "HeadEyeEffectCmd_")
kTopicHeadInfoRequest = Topic("rt/head/info_request", "HeadInfoRequest_")
kTopicHeadState = Topic("rt/head/state", "HeadState_")
kTopicHeadTouchEvent = Topic("rt/head/touch_event", "HeadTouchEvent_")
kTopicHeadErrorEvent = Topic("rt/head/error_event", "HeadErrorEvent_")


def Profile():
    return native().sr_3588_profile()
