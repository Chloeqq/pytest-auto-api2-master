#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2022/3/30 14:12
# @Author : 余少琪
import json
import os
import time

import allure
import pytest
import requests

from Enums.yamlData_enum import YAMLDate
from common.setting import ConfigHandler
from utils.cacheUtils.cacheControl import Cache
from utils.logUtils.logControl import WARNING, INFO, ERROR
from utils.otherUtils.allureDate.allure_tools import allure_step, allure_step_no
from utils.readFilesUtils.get_all_files_path import get_all_files
from utils.readFilesUtils.get_yaml_data_analysis import CaseData
from utils.readFilesUtils.yamlControl import GetYamlData
from utils.requestsUtils.encryption_algorithm_control import md5_encryption


@pytest.fixture(scope="session", autouse=False)
def clear_report():
    try:
        for one in os.listdir(ConfigHandler.report_path + '/tmp'):
            if 'json' in one:
                os.remove(ConfigHandler.report_path + f'/tmp/{one}')
            if 'txt' in one:
                os.remove(ConfigHandler.report_path + f'/tmp/{one}')
    except Exception as e:
        print("allure数据清除失败", e)

    yield


@pytest.fixture(scope="session", autouse=True)
def write_case_process():
    """
    获取所有用例，写入用例池中
    :return:
    """

    case_data = {}
    # 循环拿到所有存放用例的文件路径
    for i in get_all_files(file_path=ConfigHandler.data_path, yaml_data_switch=True):
        # 循环读取文件中的数据
        case_process = CaseData(i).case_process(case_id_switch=True)
        # 转换数据类型
        for case in case_process:
            for k, v in case.items():
                # 判断 case_id 是否已存在
                case_id_exit = k in case_data.keys()
                # 如果case_id 不存在，则将用例写入缓存池中
                if case_id_exit is False:
                    case_data[k] = v
                # 当 case_id 为 True 存在时，则跑出异常
                elif case_id_exit is True:
                    raise ValueError(f"case_id: {k} 存在重复项, 请修改case_id\n"
                                     f"文件路径: {i}")

    Cache('case_process').set_caches(case_data)


@pytest.fixture(scope="session", autouse=True)
def work_login_init():
    """
    获取登录的cookie
    :return:
    """
    url = "http://acgi.internal.jianke.com/passport/account/login/v2"
    data = json.dumps({
        "loginName": 13544529580,  # 15557188338
        "password": '12345Jk#',
        "platform": 3
    })
    headers = {'Content-Type': 'application/json'}
    # 请求登录接口
    res = requests.post(url=url, data=data, verify=True, headers=headers).json()
    token = res["token_type"] + " " + res["access_token"]
    # print(token)
    Cache("token").set_caches(token)

@pytest.fixture(scope="session", autouse=True)
def get_x_jk_x():
    t = time.time()  # 当前时间的时间戳
    now_time = int(round(t * 1000))  # 转化为毫秒级别的时间戳
    t1 = str((now_time - 1500000000000) % 999983)
    t2 = str((now_time - 1500000000000) % 9973)
    x_jk_udid = GetYamlData(ConfigHandler.config_path).get_yaml_data()['x-jk-udid']
    versionCode = str(GetYamlData(ConfigHandler.config_path).get_yaml_data()['versionCode'])
    x1 = md5_encryption( x_jk_udid + t1 + versionCode)
    x2 = md5_encryption(x1 + t2 + versionCode)
    x_jk_x = t1 + '#' + x2 + '#' + t2 + '#' + versionCode
    Cache('x_jk_x').set_caches(x_jk_x)



def pytest_collection_modifyitems(items):
    """
    测试用例收集完成时，将收集到的 item 的 name 和 node_id 的中文显示在控制台上
    :return:
    """
    for item in items:
        item.name = item.name.encode("utf-8").decode("unicode_escape")
        item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")


# 定义单个标签
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "smoke"
    )


@pytest.fixture(scope="function", autouse=True)
def case_skip(in_data):
    """处理跳过用例"""
    if in_data['is_run'] is False:
        allure.dynamic.title(in_data[YAMLDate.DETAIL.value])
        allure_step_no(f"请求URL: {in_data[YAMLDate.IS_RUN.value]}")
        allure_step_no(f"请求方式: {in_data[YAMLDate.METHOD.value]}")
        allure_step("请求头: ", in_data[YAMLDate.HEADER.value])
        allure_step("请求数据: ", in_data[YAMLDate.DATA.value])
        allure_step("依赖数据: ", in_data[YAMLDate.DEPENDENCE_CASE_DATA.value])
        allure_step("预期数据: ", in_data[YAMLDate.ASSERT.value])
        pytest.skip()


def pytest_terminal_summary(terminalreporter):
    """
    收集测试结果
    """

    _PASSED = len([i for i in terminalreporter.stats.get('passed', []) if i.when != 'teardown'])
    _ERROR = len([i for i in terminalreporter.stats.get('error', []) if i.when != 'teardown'])
    _FAILED = len([i for i in terminalreporter.stats.get('failed', []) if i.when != 'teardown'])
    _SKIPPED = len([i for i in terminalreporter.stats.get('skipped', []) if i.when != 'teardown'])
    _TOTAL = terminalreporter._numcollected
    _TIMES = time.time() - terminalreporter._sessionstarttime

    INFO.logger.info(f"成功用例数: {_PASSED}")
    ERROR.logger.error(f"异常用例数: {_ERROR}")
    ERROR.logger.error(f"失败用例数: {_FAILED}")
    WARNING.logger.warning(f"跳过用例数: {_SKIPPED}")
    INFO.logger.info("用例执行时长: %.2f" % _TIMES + " s")

    try:
        _RATE = round(_PASSED / _TOTAL * 100, 2)
        INFO.logger.info("用例成功率: %.2f" % _RATE + " %")
    except ZeroDivisionError:
        INFO.logger.info("用例成功率: 0.00 %")
