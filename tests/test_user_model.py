# coding: utf-8
import time
from datetime import datetime
from flask_testing import TestCase
from app import create_app, db
from app.models import User, AnonymousUser, Role, Permission, Follow


class UserModelTestCase(TestCase):
    def create_app(self):
        '''创建 app'''
        return create_app('testing')

    def setUp(self):
        '''在每个测试前运行, 初始化测试环境'''
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        '''在每个测试后运行, 清理测试环境'''
        db.session.remove()
        db.drop_all()

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

    def test_roles_and_permissions(self):
        '''测试角色和权限'''
        u = User(email='john@example.com', password='cat')
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_anonymous_user(self):
        '''测试匿名用户权限'''
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))

    def test_timestamps(self):
        '''测试时间戳'''
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        self.assertTrue(
            (datetime.utcnow() - u.member_since).total_seconds() < 3)
        self.assertTrue(
            (datetime.utcnow() - u.last_seen).total_seconds() < 3)

    def test_ping(self):
        '''测试更新访问时间'''
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)

    def test_gravatar(self):
        '''测试 Gravatar 头像 URL'''
        u = User(email='john@example.com', password='cat')
        with self.app.test_request_context('/'):
            gravatar = u.gravatar()
            gravatar_256 = u.gravatar(size=256)
            gravatar_pg = u.gravatar(rating='pg')
            gravatar_retro = u.gravatar(default='retro')
        with self.app.test_request_context('/', base_url='https://example.com'):
            gravatar_ssl = u.gravatar()
        self.assertTrue('http://cn.gravatar.com/avatar/' +
                        'd4c74594d841139328695756648b6bd6'in gravatar)
        self.assertTrue('s=256' in gravatar_256)
        self.assertTrue('r=pg' in gravatar_pg)
        self.assertTrue('d=retro' in gravatar_retro)
        self.assertTrue('https://cn.gravatar.com/avatar/' +
                        'd4c74594d841139328695756648b6bd6' in gravatar_ssl)

    def test_follows(self):
        '''测试关注功能'''
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        db.session.add_all([u1, u2])
        db.session.commit()
        self.assertFalse(u1.is_following(u2))  # u1 未关注 u2
        self.assertFalse(u1.is_followed_by(u2))  # u1 未被 u2 关注
        timestamp_before = datetime.utcnow()
        u1.follow(u2)
        db.session.add(u1)
        db.session.commit()
        timestamp_after = datetime.utcnow()
        self.assertTrue(u1.is_following(u2))  # u1 关注 u2
        self.assertFalse(u1.is_followed_by(u2))  # u1 未被 u2 关注
        self.assertTrue(u2.is_followed_by(u1))  # u2 被 u1 关注
        self.assertTrue(u1.followed.count() == 2)  # u1 关注列表
        self.assertTrue(u2.followers.count() == 2)  # 关注 u2 的列表
        f = u1.followed.all()[-1]
        self.assertTrue(f.followed == u2)
        self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
        f = u2.followers.all()[-1]
        self.assertTrue(f.follower == u1)
        u1.unfollow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)
        u2.follow(u1)
        db.session.add_all([u1, u2])
        db.session.commit()
        db.session.delete(u2)  # 删除 u2
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)

    def test_to_json(self):
        '''测试生成 JSON'''
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        json_user = u.to_json()
        expect_keys = ['url', 'username', 'email', 'member_since', 'last_seen',
                       'posts', 'followed_posts', 'post_count']
        self.assertEqual(sorted(json_user.keys()), sorted(expect_keys))
        self.assertTrue('/api/v1.0/users/' in json_user['url'])
