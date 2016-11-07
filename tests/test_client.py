# coding: utf-8
import re
import unittest
from flask import url_for, request
from app import create_app, db
from app.models import User, Role


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        '''在每个测试前运行, 初始化测试环境'''
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)  # Flask测试客户端对象

    def tearDown(self):
        '''在每个测试后运行, 清理测试环境'''
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        '''测试主页'''
        response = self.client.get(url_for('main.index'))
        self.assertTrue(b'Copyright' in response.data)

    def test_register_and_login(self):
        '''测试新用户注册, 确认账户, 登录功能'''
        # register a new account
        response = self.client.post(url_for('auth.register'), data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat',
            'password2': 'cat'
        })
        self.assertTrue(response.status_code == 302)  # 注册成功, 返回重定向

        # login with the new account
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat'
        }, follow_redirects=True)  # 自动重定向, 返回 GET 请求的响应
        self.assertTrue(re.search(b'Hello,\s+john!', response.data))
        self.assertTrue(b'You have not confirmed your account yet' in response.data)

        # send a confirmation token
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()  # 还可以通过解析邮件获取 token
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        self.assertTrue(b'You have confirmed your account' in response.data)

        # log out
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue(b'You have been logged out' in response.data)
