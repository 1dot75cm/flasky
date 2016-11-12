# coding: utf-8
from flask import current_app
from flask_testing import TestCase
from app import create_app, db


class BasicsTestCase(TestCase):
    def create_app(self):
        '''创建 app'''
        return create_app('testing')

    def setUp(self):
        '''在每个测试前运行, 初始化测试环境'''
        db.create_all()

    def tearDown(self):
        '''在每个测试后运行, 清理测试环境'''
        db.session.remove()
        db.drop_all()

    def test_app_exists(self):
        '''测试应用实例存在'''
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        '''测试TESTING配置值'''
        self.assertTrue(current_app.config['TESTING'])
