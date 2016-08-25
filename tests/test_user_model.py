# coding: utf-8
import unittest
import time
from app import create_app, db
from app.models import User


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        '''初始化测试环境'''
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        '''清理测试环境'''
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        '''测试可生成Hash'''
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        '''测试不可读取密码'''
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        '''测试验证密码'''
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        '''测试盐值随机性'''
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        '''测试有效的确认令牌'''
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self):
        '''测试无效的确认令牌'''
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add_all([u1, u2])
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expired_confirmation_token(self):
        '''测试过期确认令牌'''
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_valid_reset_token(self):
        '''测试有效的重置令牌'''
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertTrue(u.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_invalid_reset_token(self):
        '''测试无效的重置令牌'''
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add_all([u1, u2])
        db.session.commit()
        token = u1.generate_reset_token()
        self.assertFalse(u2.reset_password(token, 'horse'))
        self.assertTrue(u2.verify_password('dog'))

    def test_valid_email_change_token(self):
        '''测试有效的邮箱修改令牌'''
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token('susan@example.com')
        self.assertTrue(u.change_email(token))
        self.assertTrue(u.email == 'susan@example.com')

    def test_invalid_email_change_token(self):
        '''测试无效的邮箱修改令牌'''
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        db.session.add_all([u1, u2])
        db.session.commit()
        token = u1.generate_email_change_token('david@example.com')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'susan@example.org')

    def test_duplicate_email_change_token(self):
        '''测试重复的邮箱修改令牌'''
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        db.session.add_all([u1, u2])
        db.session.commit()
        token = u2.generate_email_change_token('john@example.com')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'susan@example.org')
