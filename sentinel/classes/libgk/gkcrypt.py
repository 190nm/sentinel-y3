#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
import os
import subprocess


class gk:
    gk_bin = ['qemu-i386', os.path.join(os.path.dirname(os.path.realpath(__file__)),'gk')]

    ODF = 'odf'
    LHB = 'lhb'
    NO_IV = '--no-iv'

    KR_ALL = '-a'
    KR_IGARASHI = '-i'
    KR_TAKESHI = '-t'

    @staticmethod
    def decrypt(input, container, key=None, iv=None):
        args = ['-d']
        if container == 'odf': args.append('-o')
        elif container == 'lhb': args.append('-l')

        if key: args += ['-k', key]
        if iv == '--no-iv': args += ['--no-iv']
        elif iv: args += ['-v', iv]

        cmd = gk.gk_bin + ['-a'] + args

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        data, _ = proc.communicate(input=input)
        if proc.returncode != 0:
            raise Exception("gk decrypt error error {}. cmd: {}\nstdout\n{}".format(proc.returncode, " ".join(cmd), data))
        
        return data

    @staticmethod
    def encrypt(input, container, keyrequest, key=None, iv=None):
        args = ['-e']
        if container == 'odf': args.append('-o')
        elif container == 'lhb': args.append('-l')

        if key: args += ['-k', key]
        if iv == '--no-iv': args += ['--no-iv']
        elif iv: args += ['-v', iv]

        if not keyrequest in [gk.KR_ALL, gk.KR_IGARASHI, gk.KR_TAKESHI]:
            raise Exception("invalid keyrequest")

        args += [keyrequest]

        cmd = gk.gk_bin + args

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        data, _ = proc.communicate(input=input)
        if proc.returncode != 0:
            raise Exception("gk encrypt error {}. cmd: {}\nstdout\n{}".format(proc.returncode, " ".join(cmd),data))
        
        return data
