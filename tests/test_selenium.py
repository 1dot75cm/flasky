# coding: utf-8
from __future__ import print_function
import os
import re
import time
import threading
import unittest
from selenium import webdriver
from app import create_app, db
from app.models import Role, User, Post, Category
from config import datadir, bindir, logdir


def download_webdriver():
    '''下载浏览器驱动'''
    import requests
    from lxml import etree
    from subprocess import call

    resp = requests.get('https://github.com/mozilla/geckodriver/releases')
    tree = etree.HTML(resp.content)
    url = tree.xpath('//div[contains(@class, "label-latest")]//a[contains(@href, "linux64")]/@href')[0]

    tgz_fname = url.split('/')[-1]
    tgz_fpath = os.path.join(datadir, tgz_fname)
    if not os.path.exists(tgz_fpath):
        print('Download webdriver...')
        tgz_file_content = requests.get('https://github.com' + url).content
        with open(tgz_fpath, 'wb') as f:
            f.write(tgz_file_content)

    fname = tgz_fname.split('-')[0]
    fpath = os.path.join(bindir, fname)
    if not os.path.exists(fpath):
        print('Extract webdriver...')
        call('tar -xf {} -C {}'.format(tgz_fpath, bindir).split())

    return fpath


class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        '''在所有测试前运行, 初始化测试环境'''
        # 启动 Firefox
        try:
            cls.client = webdriver.Firefox(
                executable_path=download_webdriver(),  # 下载第三方 Driver
                log_path=os.path.join(logdir, 'geckodriver.log'),
                timeout=30)
            cls.client.set_page_load_timeout(30)
        except:
            pass

        # 如果无法启动浏览器, 则跳过这些测试
        if cls.client:
            # 创建应用程序
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # 禁止日志, 保持输出简洁
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # 创建数据库, 并使用一些虚拟数据填充
            db.create_all()
            Role.insert_roles()
            Category.insert_category()
            User.generate_fake(10)
            Post.generate_fake(10)

            # 添加管理员
            admin_role = Role.query.filter_by(permissions=0xff).first()
            admin = User(email='john@example.com',
                         username='john', password='cat',
                         role=admin_role, confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # 在线程中启动 Flask 服务器
            threading.Thread(target=cls.app.run).start()

            # 等待 1s 确保服务器已启动
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        '''在所有测试后运行, 清理测试环境'''
        if cls.client:
            # 关闭 Flask 服务器和浏览器
            cls.client.get('http://127.0.0.1:5000/shutdown')
            #cls.client.close()  # 关闭当前窗口
            cls.client.quit()  # 关闭所有关联窗口

            # 销毁数据库
            db.drop_all()
            db.session.remove()

            # 删除程序上下文
            cls.app_context.pop()

    def setUp(self):
        '''在每个测试前运行, 初始化测试环境'''
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        '''在每个测试后运行, 清理测试环境'''
        pass

    def test_admin_home_page(self):
        '''测试主页, 用户页'''
        # 进入首页
        self.client.get('http://127.0.0.1:5000/')
        self.assertTrue(re.search('Copyright', self.client.page_source))

        # 进入登录页面
        self.client.find_element_by_link_text('Log In').click()  # 查找元素，并点击
        time.sleep(1)
        self.assertTrue('<h1>Login</h1>' in self.client.page_source)

        # 登录
        self.client.find_element_by_name('email').send_keys('john@example.com')
        self.client.find_element_by_name('password').send_keys('cat')  # 查找元素，并输入
        self.client.find_element_by_name('submit').click()
        time.sleep(5)
        self.assertTrue(re.search('Hello,\s+john.', self.client.page_source))

        # 进入用户个人资料页
        self.client.find_element_by_link_text('john').click()
        self.client.find_element_by_link_text('Profile').click()
        time.sleep(1)
        self.assertTrue('<h1>john</h1>' in self.client.page_source)  # 测试用户资料页
