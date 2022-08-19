#!/usr/bin/env python
# -*- coding: utf-8 -*-


import allure
import pytest

from common.setting import ConfigHandler
from utils.assertUtils.assertControl import Assert
from utils.readFilesUtils.get_yaml_data_analysis import CaseData
from utils.readFilesUtils.regularControl import regular
from utils.requestsUtils.requestControl import RequestControl
from utils.requestsUtils.teardownControl import TearDownHandler

TestData = CaseData(ConfigHandler.data_path + r'JkSettle/jkrxRule_settings.yaml').case_process()
re_data = regular(str(TestData))


@allure.epic("开发平台接口")
@allure.feature("结算模块")
class TestJkrxruleSettings:

    @allure.story("用药人信息")
    @pytest.mark.parametrize('in_data', eval(re_data), ids=[i['detail'] for i in TestData])
    def test_jkrxRule_settings(self, in_data, case_skip):
        """
        :param :
        :return:
        """
        res = RequestControl().http_request(in_data)
        TearDownHandler().teardown_handle(res)
        Assert(in_data['assert']).assert_equality(response_data=res['response_data'],
                                                  sql_data=res['sql_data'], status_code=res['status_code'])


if __name__ == '__main__':
    pytest.main(['test_jkrxRule_settings.py', '-s', '-W', 'ignore:Module already imported:pytest.PytestWarning'])
