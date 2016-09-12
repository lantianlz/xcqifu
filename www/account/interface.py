# -*- coding: utf-8 -*-

import datetime
import logging
import time
from django.db import transaction
from django.utils.encoding import smart_unicode
from django.conf import settings

from common import utils, debug, validators, cache, raw_sql
from www.misc.decorators import cache_required
from www.misc import consts
from www.tasks import async_send_email, async_send_invite_success_template_msg
from www.tasks import async_send_verfy_info_notification_template_msg, async_send_verfy_result_template_msg
from www.account.models import User, Profile, LastActive, ActiveDay, ExternalToken, InviteQrcode, UserInvite, VerifyInfo
from www.weixin.interface import WeixinBase

dict_err = {
    10100: u'邮箱重复',
    10101: u'昵称重复',
    10102: u'手机号重复',
    10103: u'被逮到了，无效的性别值',
    10104: u'这么奇葩的生日怎么可能',
    10105: u'两次输入密码不相同',
    10106: u'当前密码错误',
    10107: u'新密码和老密码不能相同',
    10108: u'登陆密码验证失败',
    10109: u'新邮箱和老邮箱不能相同',
    10110: u'邮箱验证码错误或者已过期，请重新验证',
    10111: u'该邮箱尚未注册',
    10112: u'code已失效，请重新执行重置密码操作',
    10113: u'没有找到对象',
    10114: u'已经提交审核，请耐心等待审核结果',
}
dict_err.update(consts.G_DICT_ERROR)

ACCOUNT_DB = 'account'


class UserBase(object):

    def __init__(self):
        from common import password_hashers
        self.hasher = password_hashers.MD5PasswordHasher()

    def set_password(self, raw_password):
        assert raw_password
        self.password = self.hasher.make_password(raw_password)
        return self.password

    def check_password(self, raw_password, password):
        return self.hasher.check_password(raw_password, getattr(self, 'password', password))

    def set_profile_login_att(self, profile, user):
        for key in ['email', 'mobilenumber', 'username', 'last_login', 'password', 'state']:
            setattr(profile, key, getattr(user, key))
        # profile.is_staff = lambda:user.is_staff()
        setattr(profile, 'user_login', user)

    def get_user_login_by_id(self, id):
        try:
            user = User.objects.get(id=id, state__gt=0)
            return user
        except User.DoesNotExist:
            return None

    @cache_required(cache_key='user_%s', expire=3600, cache_config=cache.CACHE_USER)
    def get_user_by_id(self, id, state=[1, 2], must_update_cache=False):
        try:
            profile = Profile.objects.get(id=id)
            user = User.objects.get(id=profile.id, state__in=state)
            self.set_profile_login_att(profile, user)
            return profile
        except (Profile.DoesNotExist, User.DoesNotExist):
            return ''

    def get_user_by_nick(self, nick, state=[1, 2]):
        try:
            profile = Profile.objects.get(nick=nick)
            user = User.objects.get(id=profile.id, state__in=state)
            self.set_profile_login_att(profile, user)
            return profile
        except (Profile.DoesNotExist, User.DoesNotExist):
            return None

    def get_user_by_email(self, email):
        try:
            user = User.objects.get(email=email, state__gt=0)
            profile = Profile.objects.get(id=user.id)
            self.set_profile_login_att(profile, user)
            return profile
        except (Profile.DoesNotExist, User.DoesNotExist):
            return None

    def get_user_by_mobilenumber(self, mobilenumber):
        try:
            if mobilenumber:
                user = User.objects.get(mobilenumber=mobilenumber, state__gt=0)
                profile = Profile.objects.get(id=user.id)
                self.set_profile_login_att(profile, user)
                return profile
        except (Profile.DoesNotExist, User.DoesNotExist):
            return None

    def check_user_info(self, email, nick, password, mobilenumber):
        try:
            validators.vemail(email)
            validators.vnick(nick)
            validators.vpassword(password)
        except Exception, e:
            return 99900, smart_unicode(e)

        if self.get_user_by_email(email):
            return 10100, dict_err.get(10100)
        if self.get_user_by_nick(nick):
            return 10101, dict_err.get(10101)
        if self.get_user_by_mobilenumber(mobilenumber):
            return 10102, dict_err.get(10102)
        return 0, dict_err.get(0)

    def check_gender(self, gender):
        if not str(gender) in ('0', '1', '2'):
            return 10103, dict_err.get(10103)
        return 0, dict_err.get(0)

    def check_birthday(self, birthday):
        try:
            birthday = datetime.datetime.strptime(birthday, '%Y-%m-%d')
            now = datetime.datetime.now()
            assert (now + datetime.timedelta(days=100 * 365)) > birthday > (now - datetime.timedelta(days=100 * 365))
        except:
            return 10104, dict_err.get(10104)
        return 0, dict_err.get(0)

    @transaction.commit_manually(using=ACCOUNT_DB)
    def regist_user_with_transaction(self, email, nick, password, re_password, ip, mobilenumber=None, username=None,
                                     source=0, gender=0, invitation_code=None):
        try:
            errcode, errmsg = self.regist_user(email, nick, password, re_password, ip, mobilenumber, username,
                                               source, gender, invitation_code)
            if errcode == 0:
                transaction.commit(using=ACCOUNT_DB)
            else:
                transaction.rollback(using=ACCOUNT_DB)
            return errcode, errmsg
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            transaction.rollback(using=ACCOUNT_DB)
            return 99900, dict_err.get(99900)

    def regist_user(self, email, nick, password, re_password, ip, mobilenumber=None, username=None,
                    source=0, gender=0, invitation_code=None):
        '''
        @note: 注册
        '''
        try:
            if not (email and nick and password):
                return 99800, dict_err.get(99800)

            if password != re_password:
                return 10105, dict_err.get(10105)

            errcode, errmsg = self.check_user_info(email, nick, password, mobilenumber)
            if errcode != 0:
                return errcode, errmsg

            id = utils.uuid_without_dash()
            now = datetime.datetime.now()

            user = User.objects.create(id=id, email=email, mobilenumber=mobilenumber, last_login=now,
                                       password=self.set_password(password))
            profile = Profile.objects.create(id=id, nick=nick, ip=ip, source=source, gender=gender)
            self.set_profile_login_att(profile, user)

            # 发送验证邮件
            # self.send_confirm_email(user)

            return 0, profile
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

    def change_profile(self, user, nick, gender, birthday, email, mobilenumber, des=None, state=None):
        '''
        @note: 资料修改
        '''
        user_id = user.id
        if not (user_id and nick and gender and birthday and email):
            return 99800, dict_err.get(99800)

        try:
            validators.vnick(nick)
        except Exception, e:
            return 99900, smart_unicode(e)

        if user.nick != nick and self.get_user_by_nick(nick):
            return 10101, dict_err.get(10101)

        errcode, errmsg = self.check_gender(gender)
        if errcode != 0:
            return errcode, errmsg

        errcode, errmsg = self.check_birthday(birthday)
        if errcode != 0:
            return errcode, errmsg

        temp = self.get_user_by_email(email)
        if temp and temp.id != user.id:
            return 10100, dict_err.get(10100)

        temp = self.get_user_by_mobilenumber(mobilenumber)
        if temp and temp.id != user.id:
            return 10102, dict_err.get(10102)

        user = self.get_user_by_id(user_id)
        user.nick = nick
        user.gender = int(gender)
        user.birthday = birthday
        if des:
            user.des = utils.filter_script(des)[:128]
        user.save()

        user_login = self.get_user_login_by_id(user.id)
        user_login.email = email
        user_login.mobilenumber = mobilenumber or None
        if state is not None:
            user_login.state = state
        user_login.save()

        # 更新缓存
        self.get_user_by_id(user.id, must_update_cache=True)
        return 0, user

    def change_pwd(self, user, old_password, new_password_1, new_password_2):
        '''
        @note: 密码修改
        '''
        if not all((old_password, new_password_1, new_password_2)):
            return 99800, dict_err.get(99800)

        if new_password_1 != new_password_2:
            return 10105, dict_err.get(10105)
        if not self.check_password(old_password, user.password):
            return 10106, dict_err.get(10106)
        if old_password == new_password_1:
            return 10107, dict_err.get(10107)
        try:
            validators.vpassword(new_password_1)
        except Exception, e:
            return 99900, smart_unicode(e)

        user_login = self.get_user_login_by_id(user.id)
        user_login.password = self.set_password(new_password_1)
        user_login.save()

        # 更新缓存
        self.get_user_by_id(user.id, must_update_cache=True)
        return 0, dict_err.get(0)

    def change_email(self, user, email, password):
        '''
        @note: 邮箱修改
        '''
        if not all((email, password)):
            return 99800, dict_err.get(99800)

        if not self.check_password(password, user.password):
            return 10108, dict_err.get(10108)

        if user.email == email:
            return 10109, dict_err.get(10109)

        try:
            validators.vemail(email)
        except Exception, e:
            return 99900, smart_unicode(e)

        if user.email != email and self.get_user_by_email(email):
            return 10100, dict_err.get(10100)

        user_login = self.get_user_login_by_id(user.id)
        user_login.email = email
        user_login.save()

        # 更新缓存
        self.get_user_by_id(user.id, must_update_cache=True)

        # 发送验证邮件
        self.send_confirm_email(user)

        return 0, dict_err.get(0)

    def send_confirm_email(self, user):
        '''
        @note: 发送验证邮件
        '''
        cache_obj = cache.Cache()
        key = u'confirm_email_code_%s' % user.id
        code = cache_obj.get(key)
        if not code:
            code = utils.uuid_without_dash()
            cache_obj.set(key, code, time_out=1800)

        if not cache_obj.get_time_is_locked(key, 60):
            context = {'verify_url': '%s/account/user_settings/verify_email?code=%s' % (settings.MAIN_DOMAIN, code), }
            async_send_email(user.email, u'小橙企服邮箱验证', utils.render_email_template('email/verify_email.html', context), 'html')

    def check_email_confim_code(self, user, code):
        '''
        @note: 确认邮箱
        '''
        if not code:
            return 99800, dict_err.get(99800)

        cache_obj = cache.Cache()
        key = u'confirm_email_code_%s' % user.id
        cache_code = cache_obj.get(key)

        if cache_code != code:
            return 10110, dict_err.get(10110)

        user.email_verified = True
        user.save()

        # 更新缓存
        self.get_user_by_id(user.id, must_update_cache=True)
        return 0, user

    def send_forget_password_email(self, email):
        '''
        @note: 发送密码找回邮件
        '''
        if not email:
            return 99800, dict_err.get(99800)

        user = self.get_user_by_email(email)
        if not user:
            return 10111, dict_err.get(10111)
        cache_obj = cache.Cache()
        key = u'forget_password_email_code_%s' % email
        code = cache_obj.get(key)
        if not code:
            code = utils.uuid_without_dash()
            cache_obj.set(key, code, time_out=1800)
            cache_obj.set(code, user, time_out=1800)

        if not cache_obj.get_time_is_locked(key, 60):
            context = {'reset_url': '%s/reset_password?code=%s' % (settings.MAIN_DOMAIN, code), }
            async_send_email(email, u'小橙企服找回密码', utils.render_email_template('email/reset_password.html', context), 'html')
        return 0, dict_err.get(0)

    def get_user_by_code(self, code):
        cache_obj = cache.Cache()
        return cache_obj.get(code)

    def reset_password_by_code(self, code, new_password_1, new_password_2):
        user = self.get_user_by_code(code)
        if not user:
            return 10112, dict_err.get(10112)

        if new_password_1 != new_password_2:
            return 10105, dict_err.get(10105)
        try:
            validators.vpassword(new_password_1)
        except Exception, e:
            return 99900, smart_unicode(e)

        user_login = self.get_user_login_by_id(user.id)
        user_login.password = self.set_password(new_password_1)
        user_login.save()

        # 更新缓存
        self.get_user_by_id(user.id, must_update_cache=True)

        cache_obj = cache.Cache()
        key = u'forget_password_email_code_%s' % user.email
        cache_obj.delete(key)
        cache_obj.delete(code)
        return 0, user_login

    def update_user_last_active_time(self, user_id, ip=None, last_active_source=0):
        '''
        @note: 更新用户最后活跃时间
        '''
        cache_obj = cache.Cache()
        # 一小时更新一次
        if not cache_obj.get_time_is_locked(key=u'last_active_time_%s' % user_id, time_out=3600):
            try:
                la = LastActive.objects.get(user_id=user_id)
                la.ip = ip
                la.last_active_source = last_active_source
                la.last_active_time = datetime.datetime.now()
                la.save()
            except LastActive.DoesNotExist:
                LastActive.objects.create(user_id=user_id, last_active_time=datetime.datetime.now(),
                                          ip=ip, last_active_source=last_active_source)
            now_date = datetime.datetime.now().date()
            try:
                ActiveDay.objects.get(user_id=user_id, active_day=now_date)
            except ActiveDay.DoesNotExist:
                ActiveDay.objects.create(user_id=user_id, active_day=now_date)

    def update_user_last_login_time(self, user_id, ip=None, last_active_source=0):
        user_login = self.get_user_login_by_id(user_id)
        user_login.last_login = datetime.datetime.now()
        user_login.save()
        self.update_user_last_active_time(user_id, ip, last_active_source)

    def get_all_users(self):
        '''
        '''
        return User.objects.all()

    def format_user_full_info(self, user_id):
        '''
        格式化完整用户信息
        '''
        format_user = self.get_user_by_id(user_id)

        # 是否管理员
        from www.admin.interface import PermissionBase
        if PermissionBase().get_user_permissions(user_id):
            format_user.is_admin = True
        else:
            format_user.is_admin = False

        # 活跃时间
        la = LastActive.objects.filter(user_id=user_id)
        if la:
            la = la[0]
            format_user.last_active = la.last_active_time
            format_user.last_active_ip = la.ip
            format_user.last_active_source = la.last_active_source
        else:
            format_user.last_active = format_user.create_time
            format_user.last_active_ip = format_user.ip
            format_user.last_active_source = ''

        # 注册来源
        format_user.source_display = u"直接注册"
        format_user.is_sub_weixin = 0
        if format_user.source > 0:
            ets = list(ExternalToken.objects.filter(user_id=user_id))
            if ets:
                format_user.source_display = ets[0].get_source_display()
                format_user.is_sub_weixin = ets[0].is_sub_weixin

        # 邀请人信息
        ui = UserInvite.objects.filter(to_user_id=user_id)
        if ui:
            invite_user = self.get_user_by_id(ui[0].from_user_id)
            format_user.invite_user_id = invite_user.id
            format_user.invite_user_nick = invite_user.nick

        return format_user

    def get_active_users(self, date):

        return LastActive.objects.filter(last_active_time__gte=date)

    def get_users_by_range_date(self, start_date, end_date):
        return User.objects.filter(create_time__range=(start_date, end_date))

    def search_users(self, nick):
        if not nick:
            return []
        return Profile.objects.filter(nick__icontains=nick)[:200]

    @transaction.commit_manually(using=ACCOUNT_DB)
    def get_user_by_external_info(self, source, access_token, external_user_id,
                                  refresh_token, nick, ip, expire_time,
                                  user_url='', gender=0, app_id=None, is_sub_weixin=True):
        try:
            assert all((source, access_token, external_user_id, nick))

            expire_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time()) + int(expire_time)))
            et = self.get_external_user(source, access_token, external_user_id, refresh_token, expire_time)
            if et:
                flag, result = True, self.get_user_by_id(et.user_id)
                ExternalTokenBase().update_is_sub_weixin(external_user_id, is_sub_weixin)
            else:
                email = '%s_%s@mrxcqifu.com' % (source, int(time.time() * 1000))
                nick = self.generate_nick_by_external_nick(nick)
                if not nick:
                    flag, result = False, u'生成名称异常'
                else:
                    errcode, result = self.regist_user(email=email, nick=nick, password=email, re_password=email, ip=ip, source=1, gender=gender)
                    if errcode == 0:
                        user = result
                        ExternalToken.objects.create(source=source, external_user_id=external_user_id,
                                                     access_token=access_token, refresh_token=refresh_token, user_url=user_url,
                                                     nick=nick, user_id=user.id, expire_time=expire_time, app_id=app_id
                                                     )
                        flag, result = True, user
                    else:
                        flag, result = False, result

            if flag:
                transaction.commit(using=ACCOUNT_DB)
            else:
                transaction.rollback(using=ACCOUNT_DB)
            return flag, result
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            transaction.rollback(using=ACCOUNT_DB)
            return False, dict_err.get(99900)

    def generate_nick_by_external_nick(self, nick, user_id=None):
        exist_user = self.get_user_by_nick(nick)
        if (not exist_user) or (exist_user.id == user_id):
            return nick
        else:
            for i in xrange(3):
                new_nick = '%s_%s' % (nick, i)
                if not self.get_user_by_nick(new_nick):
                    return new_nick
            for i in xrange(10):
                return '%s_%s' % (nick,  str(int(time.time() * 1000))[-3:])

    def get_external_user(self, source, access_token, external_user_id, refresh_token, expire_time):
        assert all((source, access_token, external_user_id))

        et = None
        ets = list(ExternalToken.objects.filter(source=source, external_user_id=external_user_id))
        if ets:
            et = ets[0]
            if et.access_token != access_token:
                et.access_token = access_token
                et.refresh_token = refresh_token
                et.expire_time = expire_time
                et.save()
        else:
            ets = list(ExternalToken.objects.filter(source=source, access_token=access_token))
            if ets:
                et = ets[0]
                if et.external_user_id != external_user_id:
                    et.external_user_id = external_user_id
                    et.refresh_token = refresh_token
                    et.expire_time = expire_time
                    et.save()
        return et

    def change_user_city(self, user_id, city_id):
        '''
        @note: 修改城市信息
        '''
        user = self.get_user_by_id(user_id)
        user.city_id = city_id
        user.save()

        # 更新缓存
        self.get_user_by_id(user.id, must_update_cache=True)
        return 0, user

    def get_user_for_admin(self, user_nick="", des=""):
        objs = Profile.objects.all()

        # if user_nick:
        #     objs = self.get_user_by_nick(user_nick)
        #     objs = [objs] if objs else []
        # elif email:
        #     objs = self.get_user_by_email(email)
        #     objs = [objs] if objs else []
        # else:
        #     objs = User.objects.all()

        if user_nick:
            objs = objs.filter(nick__icontains=user_nick)

        if des:
            objs = objs.filter(des__icontains=des)

        return objs

    def change_profile_from_weixin(self, user, app_key, openid, qrscene=""):
        '''
        @note: 通过微信资料修改
        '''
        try:
            import urllib2
            from www.misc import qiniu_client
            from www.weixin.interface import dict_weixin_app, WeixinBase

            if user.nick.startswith("weixin_"):
                user_id = user.id
                app_id = dict_weixin_app[app_key]["app_id"]

                weixin_user_info = WeixinBase().get_user_info(app_key, openid)
                if weixin_user_info:
                    nick = weixin_user_info["nickname"]
                    gender = weixin_user_info["sex"]
                    errcode, errmsg = self.check_gender(gender)
                    if errcode != 0:
                        return errcode, errmsg

                    weixin_img_url = weixin_user_info.get("headimgurl")
                    user_avatar = ''
                    if weixin_img_url:
                        # 上传图片

                        flag, img_name = qiniu_client.upload_img(urllib2.urlopen(weixin_img_url, timeout=20), img_type='weixin_avatar')
                        if flag:
                            user_avatar = '%s/%s' % (settings.IMG0_DOMAIN, img_name)
                        else:
                            logging.error(u'转换微信图片失败，weixin_img_url is %s' % weixin_img_url)

                    ets = list(ExternalToken.objects.filter(app_id=app_id, external_user_id=openid, source="weixin"))
                    if ets:
                        et = ets[0]
                        et.nick = nick
                        et.save()

                    nick = self.generate_nick_by_external_nick(nick, user.id)
                    user = self.get_user_by_id(user_id)
                    user.nick = nick
                    user.avatar = user_avatar
                    user.gender = int(gender)
                    user.save()

                    # 更新缓存
                    self.get_user_by_id(user.id, must_update_cache=True)

                    # 录入用户邀请信息
                    if qrscene:
                        try:
                            UserInviteBase().create_ui(qrscene, user.id)
                        except Exception, e:
                            debug.get_debug_detail_and_send_email(e)
            return 0, user
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)

    def regist_by_weixin(self, openid, app_key, qrscene="", ip=None, expire_time=0):
        """
        @note: 通过微信注册用户
        """
        assert openid and app_key
        from www.weixin.interface import dict_weixin_app
        from www.tasks import async_change_profile_from_weixin

        user_info = dict(nick=u"weixin_%s" % int(time.time() * 1000), url="", gender=0)
        flag, result = self.get_user_by_external_info(source='weixin', access_token="access_token_%s" % openid, external_user_id=openid,
                                                      refresh_token=None, nick=user_info['nick'], ip=ip, expire_time=expire_time,
                                                      user_url=user_info['url'], gender=user_info['gender'],
                                                      app_id=dict_weixin_app[app_key]["app_id"])
        user = None
        if flag:
            user = result
            UserBase().update_user_last_login_time(user.id, ip=ip, last_active_source=2)

            # 更新用户资料
            if settings.LOCAL_FLAG:
                async_change_profile_from_weixin(user, app_key, openid, qrscene)
            else:
                async_change_profile_from_weixin.delay(user, app_key, openid, qrscene)
        return user, result

    def login_by_weixin_qr_code(self, ticket, openid, app_key):
        """
        @note: 通过微信二维码扫码登陆
        """
        assert ticket and openid and app_key
        user, result = self.regist_by_weixin(openid, app_key)

        if user:
            errcode, errmsg = 0, u"扫码登陆网站成功"
        else:
            errcode, errmsg = -1, result

        # 设置缓存
        cache_obj = cache.Cache()
        key = u'weixin_login_state_%s' % ticket
        user_id = user.id if errcode == 0 else ""
        cache_obj.set(key, [errcode, errmsg, user_id], time_out=300)

        return errcode, errmsg

    def change_pwd_by_admin(self, user_id, pwd):

        try:

            try:
                validators.vpassword(pwd)
            except Exception, e:
                return 99900, smart_unicode(e)

            user = self.get_user_login_by_id(user_id)
            user.password = self.set_password(pwd)
            user.save()

            # 更新缓存
            self.get_user_by_id(user.id, must_update_cache=True)
        except Exception:
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)

    def get_count_group_by_create_time(self, count=360):
        '''
        查询用户数量 按创建时间分组
        数据格式：
        [2014-01-01, 15], [2014-01-02, 23]
        '''
        sql = """
            SELECT DATE_FORMAT(create_time, "%%Y-%%m-%%d"), COUNT(*)
            FROM account_xcqifu.account_user
            GROUP BY DATE_FORMAT(create_time, "%%Y-%%m-%%d")
            LIMIT 0, %s
        """

        return raw_sql.exec_sql(sql, [count], 'account')

    def get_toady_count_group_by_create_time(self):
        '''
        查询当天用户数量 按创建时间分组
        数据格式：
        [09, 15], [10, 23]
        '''
        sql = """
            SELECT DATE_FORMAT(create_time, "%%H"), COUNT(*)
            FROM account_xcqifu.account_user
            WHERE %s <= create_time AND create_time <= %s
            GROUP BY DATE_FORMAT(create_time, "%%H")
        """
        now = datetime.datetime.now().strftime('%Y-%m-%d')

        return raw_sql.exec_sql(sql, [now + ' 00:00:00', now + ' 23:59:59'], 'account')


def user_profile_required(func):
    '''
    @note: 访问用户控件装饰器
    '''
    def _decorator(request, user_id, *args, **kwargs):
        from www.timeline.interface import UserFollowBase
        from django.shortcuts import render_to_response
        from django.template import RequestContext

        ufb = UserFollowBase()
        ub = UserBase()
        if not user_id:
            user = request.user
        else:
            user = ub.get_user_by_id(user_id)
            if not user:
                err_msg = u'用户不存在'
                return render_to_response('error.html', locals(), context_instance=RequestContext(request))
        request.is_me = (request.user == user)
        if not request.is_me:
            request.is_follow = ufb.check_is_follow(request.user.id, user.id)

        return func(request, user, *args, **kwargs)
    return _decorator


class ExternalTokenBase(object):

    def get_ets_by_user_id(self, user_id, source=None):
        ps = dict(user_id=user_id)
        if source is not None:
            ps.update(dict(source=source))
        return ExternalToken.objects.filter(**ps)

    def get_weixin_openid_by_user_id(self, user_id):
        ets = list(self.get_ets_by_user_id(user_id, source="weixin"))
        if ets:
            return ets[0].external_user_id

    def get_external_for_admin(self, s_date, e_date, nick=''):

        # objs = ExternalToken.objects.filter(create_time__range=(s_date, e_date))
        objs = ExternalToken.objects.all()

        if nick:
            objs = objs.filter(nick=nick)
        return objs

    def update_is_sub_weixin(self, external_user_id, is_sub_weixin):
        """
        @note: 更新是否关注微信状态
        """
        et = ExternalToken.objects.get(external_user_id=external_user_id, source="weixin")
        et.is_sub_weixin = is_sub_weixin
        et.save()


class InviteQrcodeBase(object):

    def generate_unique_code(self):
        last_qrs = InviteQrcode.objects.all().order_by("-id")
        num = 0
        prefix = "invite"
        if last_qrs:
            last_qr = last_qrs[0]
            num = int(last_qr.unique_code.split("_")[1]) + 1
        return u"%s_%s" % (prefix, num)

    def create_user_qrcode(self, user_id):
        wb = WeixinBase()

        user = UserBase().get_user_by_id(user_id)
        if not user:
            return 99600, dict_err.get(99600)
        if InviteQrcode.objects.filter(user_id=user_id):
            return 99802, dict_err.get(99802)

        unique_code = self.generate_unique_code()
        ticket_info = wb.get_qr_code_ticket(wb.init_app_key(), is_limit=True, scene_str=unique_code)

        if not ticket_info:
            raise Exception, u"获取推广二维码异常"
        ticket = ticket_info["ticket"]
        name = u"个人码_%s" % user.nick

        qrcode = InviteQrcode.objects.create(name=name, user_id=user_id, unique_code=unique_code, ticket=ticket, state=0)

        return 0, qrcode

    def create_channel_qrcode(self, name):
        wb = WeixinBase()
        unique_code = self.generate_unique_code()

        try:
            assert all([name, ])
        except Exception, e:
            return 99800, dict_err.get(99800)

        if InviteQrcode.objects.filter(name=name):
            return 99802, dict_err.get(99802)

        ticket_info = wb.get_qr_code_ticket(wb.init_app_key(), is_limit=True, scene_str=unique_code)

        if not ticket_info:
            raise Exception, u"获取推广二维码异常"
        ticket = ticket_info["ticket"]
        qrcode = InviteQrcode.objects.create(name=name, unique_code=unique_code, ticket=ticket, state=1)

        return 0, qrcode

    def get_qrcode_by_code(self, unique_code):
        try:
            return InviteQrcode.objects.get(unique_code=unique_code)
        except InviteQrcode.DoesNotExist:
            return None

    def get_qrcode_by_id(self, qrcode_id):
        try:
            return InviteQrcode.objects.get(id=qrcode_id)
        except InviteQrcode.DoesNotExist:
            return None

    def get_or_create_user_qrcode(self, user_id):
        qrcodes = list(InviteQrcode.objects.filter(user_id=user_id))
        if qrcodes:
            return qrcodes[0]
        else:
            try:
                return self.create_user_qrcode(user_id)[1]
            except:
                return InviteQrcode.objects.get(user_id=user_id)    # 访问频率太快重新请求

    def search_person_qrcodes_for_admin(self, name, is_sort=0):
        '''
        个人二维码
        '''
        return self.search_qrcodes_for_admin(name, is_sort, 0)

    def search_channel_qrcodes_for_admin(self, name, is_sort=0):
        '''
        渠道二维码
        '''
        return self.search_qrcodes_for_admin(name, is_sort, 1)

    def search_qrcodes_for_admin(self, name, is_sort=0, state=0):
        objs = InviteQrcode.objects.filter(state=state)

        if name:
            objs = objs.filter(name__icontains=name)

        if is_sort:
            objs = objs.order_by('-user_count')

        return objs

    def modify_qrcode(self, qrcode_id, name):
        try:
            assert all([name, ])
        except Exception, e:
            return 99800, dict_err.get(99800)

        obj = self.get_qrcode_by_id(qrcode_id)
        if not obj:
            return 99800, dict_err.get(99800)

        try:
            obj.name = name
            obj.save()
        except Exception, e:
            return 99800, dict_err.get(99800)

        return 0, dict_err.get(0)


class UserInviteBase(object):

    def create_ui(self, unique_code, to_user_id):
        qrcode = InviteQrcodeBase().get_qrcode_by_code(unique_code)

        to_user = UserBase().get_user_by_id(to_user_id)
        if qrcode.user_id == to_user_id or (not to_user):
            return 99800, dict_err.get(99800)

        if UserInvite.objects.filter(qrcode=qrcode, to_user_id=to_user_id):
            return 99802, dict_err.get(99802)
        else:
            ui = UserInvite.objects.create(from_user_id=qrcode.user_id, to_user_id=to_user_id, qrcode=qrcode)

            # 更新计数器
            qrcode.user_count += 1
            qrcode.save()

            # 个人邀请的，发送模板消息通知邀请人
            if qrcode.user_id:
                openid = ExternalTokenBase().get_weixin_openid_by_user_id(qrcode.user_id)
                # openid = "okQdow-Svk_sI4LEHf0LbUAUoK2A"
                if openid:
                    async_send_invite_success_template_msg.delay(openid, to_user.nick, to_user.get_gender_display(), to_user.create_time)

            return 0, ui

    def get_user_invites(self, from_user_id):
        return UserInvite.objects.filter(from_user_id=from_user_id)

    def get_user_invite_count(self, from_user_id):
        return UserInvite.objects.filter(from_user_id=from_user_id).count()

    def search_invite_for_admin(self, state, name):
        objs = UserInvite.objects.filter(qrcode__state=state)

        # 个人二维码
        if state == 0:
            user = UserBase().get_user_by_nick(name)
            if user:
                objs = objs.filter(from_user_id=user.id)

        # 渠道二维码
        if state == 1:
            objs = objs.filter(qrcode__name__icontains=name)

        return objs


class VerifyInfoBase(object):

    def add_verfy_info(self, user_id, name, mobile, title, company_name):
        try:
            assert all([user_id, name, mobile, title, company_name])
        except Exception, e:
            return 99800, dict_err.get(99800)

        try:
            verfy_info, is_created = VerifyInfo.objects.get_or_create(user_id=user_id)

            # 防止重复提交
            # if not is_created and verfy_info.state == 0:
            # return 10114, dict_err.get(10114)

            verfy_info.name = name
            verfy_info.mobile = mobile
            verfy_info.title = title
            verfy_info.company_name = company_name
            verfy_info.state = 0
            verfy_info.save()

            # 发送模板消息通知给内部成员
            from www.weixin.weixin_config import staff_open_ids
            create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for openid in staff_open_ids:
                async_send_verfy_info_notification_template_msg.delay(openid=openid, name=name, mobile=mobile,
                                                                      create_time=create_time, info=u"%s %s" % (company_name, title))

        except Exception, e:

            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, verfy_info

    def get_info_by_user_id(self, user_id):
        try:
            return VerifyInfo.objects.get(user_id=user_id)
        except VerifyInfo.DoesNotExist:
            return None

    def get_info_by_id(self, info_id):
        try:
            return VerifyInfo.objects.get(id=info_id)
        except VerifyInfo.DoesNotExist:
            return None

    def search_infos_for_admin(self, name, state=None):
        objs = VerifyInfo.objects.all()

        if state:
            objs = objs.filter(state=state)

        if name:
            objs = objs.filter(name__icontains=name)

        return objs

    def modify_info(self, obj_id, name, mobile, title, company_name, company_short_name="",
                    state=0):

        if not (obj_id and name and mobile and title and company_name):
            return 99800, dict_err.get(99800)

        obj = self.get_info_by_id(obj_id)
        if not obj:
            return 20201, dict_err.get(20201)

        try:
            pre_state = obj.state
            state = int(state)

            obj.name = name
            obj.mobile = mobile
            obj.title = title
            obj.company_name = company_name
            obj.company_short_name = company_short_name
            obj.state = state
            obj.save()

            # 发送模板消息通知给用户
            if pre_state == 0 and state > 0:
                openid = ExternalTokenBase().get_weixin_openid_by_user_id(obj.user_id)
                des = u"亲爱的%s，恭喜，在小橙你可是通过认证的有身份的用户了" if state == 1 else u"亲爱的%s，你提交的认证资料未能通过火眼金睛的审核人员的审查"
                des = des % name
                result = u"审核通过" if state == 1 else u"审核未通过"
                reason = u"漂亮的审核资料" if state == 1 else u"请检查姓名、电话、职位信息后重新提交"
                remark = u"点击查看认证信息"

                async_send_verfy_result_template_msg.delay(openid, des, result, reason, remark)

        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)


class LastActiveBase(object):

    def get_active_user(self, start_date, end_date):
        return LastActive.objects.filter(last_active_time__range=(start_date, end_date))
