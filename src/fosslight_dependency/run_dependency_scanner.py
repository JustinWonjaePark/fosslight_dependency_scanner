#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import argparse
import pkg_resources
import warnings
from datetime import datetime
import logging
import fosslight_dependency.constant as const
from fosslight_util.set_log import init_log
import fosslight_util.constant as constant
from fosslight_dependency._help import print_help_msg
from fosslight_dependency._analyze_dependency import analyze_dependency
from fosslight_util.output_format import check_output_format, write_output_file

# Package Name
_PKG_NAME = "fosslight_dependency"
logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_sheet_name = "SRC_FL_Dependency"


def find_package_manager():
    ret = True
    manifest_file_name = list(set(list(const.SUPPORT_PACKAE.values())))

    found_manifest_file = []
    for f in manifest_file_name:
        if os.path.isfile(f):
            found_manifest_file.append(f)

    found_package_manager = []
    for f_idx in found_manifest_file:
        for key, value in const.SUPPORT_PACKAE.items():
            if value == f_idx:
                found_package_manager.append(key)

    if len(found_package_manager) >= 1:
        logger.info("Found the manifest file(" + ','.join(found_manifest_file) + ")automatically.")
        logger.warning("### Set Package Manager = " + ', '.join(found_package_manager))
    else:
        ret = False
        logger.error("Cannot find the manifest file.")
        logger.error("Please run with '-m' option to append the package manager name to be analzyed.")

    return ret, found_package_manager


def run_dependency_scanner(package_manager='', input_dir='', output_dir_file='', pip_activate_cmd='', pip_deactivate_cmd='',
                           output_custom_dir='', app_name=const.default_app_name, github_token='', format=''):
    global logger

    ret = True
    sheet_list = {}
    sheet_list[_sheet_name] = []
    _json_ext = ".json"
    _start_time = datetime.now().strftime('%y%m%d_%H%M%S')

    success, msg, output_path, output_file, output_extension = check_output_format(output_dir_file, format)
    if success:
        if output_path == "":
            output_path = os.getcwd()
        else:
            output_path = os.path.abspath(output_path)

        if output_file == "":
            if output_extension == _json_ext:
                output_file = "Opossum_input_" + _start_time
            else:
                output_file = "FOSSLight-Report_" + _start_time

    logger, _result_log = init_log(os.path.join(output_path, "fosslight_dependency_log_" + _start_time + ".txt"),
                                   True, logging.INFO, logging.DEBUG, _PKG_NAME)

    logger.info("Tool Info : " + _result_log["Tool Info"])

    if not success:
        logger.error(msg)
        return False, sheet_list

    autodetect = True
    if package_manager:
        autodetect = False
        support_packagemanager = list(const.SUPPORT_PACKAE.keys())

        if package_manager not in support_packagemanager:
            logger.error("You entered the unsupported package manager(" + package_manager + ").")
            logger.error("Please enter the supported package manager({0}) with '-m' option."
                         .format(", ".join(support_packagemanager)))
            return False, sheet_list

    if input_dir:
        if os.path.isdir(input_dir):
            os.chdir(input_dir)
            input_dir = os.getcwd()
        else:
            logger.error("You entered the wrong input path(" + input_dir + ") to run the script.")
            logger.error("Please enter the existed input path with '-p' option.")
            return False, sheet_list
    else:
        input_dir = os.getcwd()
        os.chdir(input_dir)

    found_package_manager = []
    if autodetect:
        try:
            ret, found_package_manager = find_package_manager()
        except Exception as e:
            logger.error(str(e))
            ret = False
        finally:
            if not ret:
                logger.error("Failed to detect package manager automatically.")
                return False, sheet_list
    else:
        found_package_manager.append(package_manager)

    for pm in found_package_manager:
        ret, package_sheet_list = analyze_dependency(pm, input_dir, output_path, pip_activate_cmd, pip_deactivate_cmd,
                                                     output_custom_dir, app_name, github_token)
        if ret:
            sheet_list[_sheet_name].extend(package_sheet_list)

    if sheet_list is not None:
        output_file_without_ext = os.path.join(output_path, output_file)
        success_to_write, writing_msg = write_output_file(output_file_without_ext, output_extension,
                                                          sheet_list)
        if success_to_write:
            logger.info("Writing Output file(" + output_file + output_extension + "):" + str(success_to_write) + " "
                                               + writing_msg)
        else:
            ret = False
            logger.error("Fail to generate result file. msg:()" + writing_msg)
    else:
        logger.error("Analyzing result is empty.")

    logger.warning("### FINISH ###")
    return ret, sheet_list


def main():
    package_manager = ''
    input_dir = ''
    output_dir = ''
    pip_activate_cmd = ''
    pip_deactivate_cmd = ''
    output_custom_dir = ''
    app_name = const.default_app_name
    github_token = ''
    format = ''

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action='store_true', required=False)
    parser.add_argument('-v', '--version', action='store_true', required=False)
    parser.add_argument('-m', '--manager', nargs=1, type=str, default='', required=False)
    parser.add_argument('-p', '--path', nargs=1, type=str, required=False)
    parser.add_argument('-o', '--output', nargs=1, type=str, required=False)
    parser.add_argument('-a', '--activate', nargs=1, type=str, default='', required=False)
    parser.add_argument('-d', '--deactivate', nargs=1, type=str, default='', required=False)
    parser.add_argument('-c', '--customized', nargs=1, type=str, required=False)
    parser.add_argument('-n', '--appname', nargs=1, type=str, required=False)
    parser.add_argument('-t', '--token', nargs=1, type=str, required=False)
    parser.add_argument('-f', '--format', nargs=1, type=str, required=False)

    args = parser.parse_args()

    if args.help:  # -h option
        print_help_msg()

    if args.version:  # -v option
        cur_version = pkg_resources.get_distribution(_PKG_NAME).version
        print('FOSSLight Dependency Scanner Version : ' + cur_version)
        sys.exit(0)

    if args.manager:  # -m option
        package_manager = ''.join(args.manager)
    if args.path:  # -p option
        input_dir = ''.join(args.path)
    if args.output:  # -o option
        output_dir = ''.join(args.output)
    if args.activate:  # -a option
        pip_activate_cmd = ''.join(args.activate)
    if args.deactivate:  # -d option
        pip_deactivate_cmd = ''.join(args.deactivate)
    if args.customized:  # -c option
        output_custom_dir = ''.join(args.customized)
    if args.appname:  # -n option
        app_name = ''.join(args.appname)
    if args.token:  # -t option
        github_token = ''.join(args.token)
    if args.format:  # -f option
        format = ''.join(args.format)

    run_dependency_scanner(package_manager, input_dir, output_dir, pip_activate_cmd, pip_deactivate_cmd,
                           output_custom_dir, app_name, github_token, format)


if __name__ == '__main__':
    main()
