# _*_ coding : UTF-8 _*_
# 开发人员： Xiaoqiang
# 微信公众号: xiaoqiangclub
# 开发时间： 2024/5/27 17:48
# 文件名称： test_updater.py
# 项目描述： 测试
# 开发工具： PyCharm
import unittest
from updater import updater


class TestUpdater(unittest.TestCase):
    def test_run_command(self):
        updater()


if __name__ == '__main__':
    unittest.main()
