import re
import common
from functools import reduce
import time


class CPU():
    def __init__(self, pkgName ,deviceId):
        self.pkgName = pkgName
        self.deviceId = deviceId

    def getprocessCpuStat(self):
        """获取某个时刻的某个进程的cpu损耗"""
        pid = common.Devices.getPid(pkgName=self.pkgName,deviceId=self.deviceId)
        cmd = f'cat /proc/{pid}/stat'
        result = common.Adb.shell(cmd)
        r = re.compile("\\s+")
        toks = r.split(result)
        processCpu = float(int(toks[13]) + int(toks[14]));
        return processCpu

    def getTotalCpuStat(self):
        """获取某个时刻的总cpu损耗"""
        cmd = f'cat /proc/stat |grep ^cpu\ '
        result = common.Adb.shell(cmd)
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(result)
        idleCpu = float(toks[3])
        totalCpu = float(reduce(lambda x, y: int(x) + int(y), toks));
        return totalCpu

    def getSingCpuRate(self):
        """获取进程损耗cpu的占比%"""
        processCpuTime_1 = self.getprocessCpuStat()
        totalCpuTime_1 = self.getTotalCpuStat()
        time.sleep(0.5)
        processCpuTime_2 = self.getprocessCpuStat()
        totalCpuTime_2 = self.getTotalCpuStat()
        cpuRate = int((processCpuTime_2 - processCpuTime_1) / (totalCpuTime_2 - totalCpuTime_1) * 100)
        return cpuRate

class MEM():
    def __init__(self, pkgName ,deviceId):
        self.pkgName = pkgName
        self.deviceId = deviceId

    def getProcessMem(self):
        """获取进程内存Total\NativeHeap\NativeHeap;单位：MB"""
        pid = common.Devices.getPid(pkgName=self.pkgName,deviceId=self.deviceId)
        cmd = f'adb shell dumpsys meminfo {pid}'
        output = common.Adb.shell(cmd)
        m = re.search(r'TOTAL\s*(\d+)', output)
        m1 = re.search(r'Native Heap\s*(\d+)', output)
        m2 = re.search(r'Dalvik Heap\s*(\d+)', output)
        PSS = round(float(float(m.group(1))) / 1024, 2)
        NativeHeap = round(float(float(m1.group(1))) / 1024, 2)
        DalvikHeap = round(float(float(m2.group(1))) / 1024, 2)
        return PSS, NativeHeap, DalvikHeap