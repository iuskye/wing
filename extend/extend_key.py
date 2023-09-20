#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @brief: 各类文件的签名信息
# @date:   2023.05.16 14:40:50

import sys, os, time, datetime

g_this_file = os.path.realpath(sys.argv[0])
g_this_path = os.path.dirname(g_this_file)
sys.path.append(os.path.dirname(g_this_path))

from utils.utils_cmn import CmnUtils
from utils.utils_cipher import CipherUtils
from utils.utils_logger import LoggerUtils
from utils.utils_file import FileUtils
from utils.utils_import import ImportUtils
from utils.utils_zip import ZipUtils
from basic.arguments import BasicArgumentsValue

g_env_path, g_this_file, g_this_path = ImportUtils.initEnv()
g_repo_path = ImportUtils.initPath(g_env_path)


# --------------------------------------------------------------------------------------------------------------------------
def doExportMobileProvision(tempPath, f):
    FileUtils.ensureDir(tempPath)

    global g_mp_file
    g_mp_file = None

    def doCallback(fullName, fileName):
        global g_mp_file
        if None != g_mp_file: return -1
        if fileName.endswith('embedded.mobileprovision'):
            g_mp_file = fullName
            return 1
        return 0

    ZipUtils.unzip2(f, tempPath, doCallback)
    return g_mp_file


def doList(envPath, f, pwd):
    if CmnUtils.isEmpty(f):
        LoggerUtils.error('Fail, not found file')
        return

    if CmnUtils.isRelativePath(f): f = envPath + os.sep + f
    # print(f)
    if f.endswith('.apk'):  # # "repo -key list com.demo.apk"
        ret = CmnUtils.doCmd('keytool -list -printcert -jarfile ' + CmnUtils.formatCmdArg(f))
        LoggerUtils.println(ret)
        return
    if f.endswith('.ipa'):  # # "repo -key list com.demo.ipa"
        tempPath = envPath + "/.cache/" + FileUtils.getTempName()
        try:
            mpf = doExportMobileProvision(tempPath, f)
            # print(mpf)
            ret = CmnUtils.doCmd('security cms -D -i ' + CmnUtils.formatCmdArg(mpf))
            LoggerUtils.println(ret)
        except Exception as e:
            LoggerUtils.exception(e)
        finally:
            FileUtils.remove(tempPath, True)
        return
    if f.endswith('.mobileprovision'):  # # "repo -key list embedded.mobileprovision"
        ret = CmnUtils.doCmd('security cms -D -i ' + CmnUtils.formatCmdArg(f))
        LoggerUtils.println(ret)
        return
    if f.endswith('.RSA') or f.endswith('.rsa'):  # # "repo -key list cert.RSA"
        ret = CmnUtils.doCmd('keytool -printcert -file ' + CmnUtils.formatCmdArg(f))
        LoggerUtils.println(ret)
        return
    if f.endswith('.keystore') or f.endswith('.jks'):  # # "repo -key list demo.keystore"
        if CmnUtils.isEmpty(pwd):
            ret = CmnUtils.doCmd('keytool -list -v -keystore ' + CmnUtils.formatCmdArg(f))
        else:
            ret = CmnUtils.doCmd(('keytool -list -v -storepass %s -keystore ' % (pwd)) + CmnUtils.formatCmdArg(f))
        LoggerUtils.println(ret)
        return
    LoggerUtils.error('UNsupport key list: ' + f)


def doCreate(envPath, _type, _mode):
    if 'rsa' == _type.lower():
        # openssl genrsa -out private.pem 2048
        # openssl rsa -in private.pem -pubout -out public.pem
        prvtFile = envPath + os.sep + FileUtils.getTempTimeName('private_', '.pem')
        mode = '2048' if CmnUtils.isEmpty(_mode) else _mode
        ret = CmnUtils.doCmdCall('openssl genrsa -out %s %s' % (prvtFile, mode))
        assert 0 == ret and os.path.isfile(prvtFile), 'openssl genrsa fail'

        pubFile = envPath + os.sep + FileUtils.getTempTimeName('public_', '.pem')
        ret = CmnUtils.doCmdCall('openssl rsa -in %s -pubout -out %s' % (prvtFile, pubFile))
        assert 0 == ret and os.path.isfile(prvtFile), 'openssl rsa fail'
        LoggerUtils.light('>>> ' + prvtFile[len(envPath) + 1:])
        LoggerUtils.light('>>> ' + pubFile[len(envPath) + 1:])
        return
    LoggerUtils.error('UNsupport key create: ' + ('none' if CmnUtils.isEmpty(_type) else _type) + ', ' + (
        'none' if CmnUtils.isEmpty(_mode) else _mode))


def doHash(str):
    h, f = CmnUtils.getHash(str)

    LoggerUtils.println('md5: ' + CipherUtils.md5String(str))
    LoggerUtils.println('sha256: ' + CipherUtils.sha256String(str))

    LoggerUtils.println('unique for long: 0x%x' % ((h << 32) | f))
    LoggerUtils.println('hash: 0x%x, flag: 0x%x' % (h, f))
    LoggerUtils.println('{ 0x%x, 0x%x }, // %s' % (h, f, str))


def run():
    '''
    repo -key
    '''
    argv = BasicArgumentsValue()
    envPath, cmd = argv.get(0), argv.get(1)

    # "repo -key list ${file} ${pwd}"
    if cmd == 'list': return doList(envPath, argv.get(2), argv.get(3))
    # "repo -key create ${type} ${mode}"
    if cmd == 'create': return doCreate(envPath, argv.get(2), argv.get(3))
    # "repo -key hash ${string}"
    if cmd == 'hash': return doHash(argv.get(2))
    LoggerUtils.error('UNsupport command: ' + cmd)


if __name__ == "__main__":
    run()
