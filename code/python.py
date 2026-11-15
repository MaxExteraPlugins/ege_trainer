# -*- coding: utf-8 -*-
__id__ = "ege_trainer"
__name__ = "ЕГЭ Тренер"
__description__ = "Решение заданий для подготовки к ЕГЭ с ege.sdamgia.ru, а также статистика"
__author__ = "@itNotMax - @MaxExteraPlugins"
__version__ = "1.4.0"
__min_version__ = "12.10.6"
__icon__ = "MaxExteraPluginsStickers/4"

__requirements__ = ["beautifulsoup4", "requests", "lxml"]

import random, re, json, requests, time
from bs4 import BeautifulSoup
from typing import Dict, Any, List

from base_plugin import BasePlugin, MenuItemData, MenuItemType
from android_utils import run_on_ui_thread, OnClickListener, OnLongClickListener
from client_utils import run_on_queue, get_last_fragment
from ui.alert import AlertDialogBuilder
from ui.settings import Header, Switch, Text, Divider
from java import jclass
from android.widget import (LinearLayout, TextView, EditText, Button,
    ScrollView, Toast)
from android.webkit import WebView
from android.view import Gravity, View, ViewGroup, MotionEvent
from android.graphics import Color, Typeface
from android.util import TypedValue
from org.telegram.messenger import AndroidUtilities
from org.telegram.ui.ActionBar import Theme

SUBJECTS = {
    "math":  {"name": "Математика (профиль)", "domain": "math-ege", "tasks": 19},
    "mathb": {"name": "Математика (база)",    "domain": "mathb-ege", "tasks": 22},
    "rus":   {"name": "Русский язык",         "domain": "rus-ege",   "tasks": 27},
    "phys":  {"name": "Физика",               "domain": "phys-ege",  "tasks": 26},
    "inf":   {"name": "Информатика",          "domain": "inf-ege",   "tasks": 27},
    "bio":   {"name": "Биология",             "domain": "bio-ege",   "tasks": 22},
    "chem":  {"name": "Химия",                "domain": "chem-ege",  "tasks": 28},
    "hist":  {"name": "История",              "domain": "hist-ege",  "tasks": 21},
    "soc":   {"name": "Обществознание",       "domain": "soc-ege",   "tasks": 25},
    "lit":   {"name": "Литература",           "domain": "lit-ege",   "tasks": 12},
    "geo":   {"name": "География",            "domain": "geo-ege",   "tasks": 22},
    "en":    {"name": "Английский язык",      "domain": "en-ege",    "tasks": 38},
}
_HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


class EgeActionBarHook:
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        try:
            if not self.plugin.get_setting("show_in_actionbar", False):
                return
            fragment = param.thisObject
            actionBar = fragment.getActionBar()
            if not actionBar:
                return
            menu = actionBar.createMenu()
            if menu.findViewById(7778) is not None:
                return
            R_drawable = jclass("org.telegram.messenger.R$drawable")
            item = menu.addItem(7778, R_drawable.msg_help)
            menu.removeView(item)
            menu.addView(item, menu.getChildCount() - 1)
            item.setOnClickListener(OnClickListener(lambda v: self.plugin._on_drawer(None)))
        except:
            pass



# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================

# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================
class AuthorChannelHelper:
    CONFIG_URL = "https://raw.githubusercontent.com/MaxExteraPlugins/config/main/links.json"

    DEFAULT_LINKS = {
        "channel_username": "MaxExteraPlugins",
        "channel_url": "https://t.me/MaxExteraPlugins",
        "trial_days": 7,
        "header": {"ru": "MaxExteraPlugins", "en": "MaxExteraPlugins"},
        "buttons": [
            {"title": {"ru": "Канал автора", "en": "Author's Channel"}, "icon": "msg_channel", "url": "https://t.me/MaxExteraPlugins"},
            {"title": {"ru": "Поддержать автора", "en": "Support author"}, "icon": "msg_share", "url": "https://t.me/itNotMax"},
            {"title": {"ru": "Сообщить о баге", "en": "Report a bug"}, "icon": "msg_help", "url": "https://t.me/itNotMax"}
        ]
    }

    _TEXTS = {
        "install_card_title": {"ru": "Спасибо за установку!", "en": "Thank you for installing!"},
        "install_card_msg": {
            "ru": "Надеемся, что плагин будет вам полезен!\n\nМы делаем плагины бесплатными и доступными для всех: пожалуйста, поддержите нас подпиской. Там будут только важные новости, обновления и розыгрыши.",
            "en": "We hope this plugin will be useful to you!\n\nWe keep our plugins free and open for everyone: please support us with a subscription. We only post key news, updates, and giveaways."
        },
        "subscribe_btn": {"ru": "Подписаться", "en": "Subscribe"},
        "remind_later_btn": {"ru": "Напомнить позже", "en": "Remind later"},
        "check_sub_btn": {"ru": "Проверить подписку", "en": "Check subscription"},
        "trial_expired_title": {"ru": "Пожалуйста, подпишитесь на канал", "en": "Please subscribe to the channel"},
        "trial_expired_msg": {
            "ru": "Пожалуйста, подпишитесь на наш официальный канал.\n\nМы делаем плагины бесплатно, ничего не требуя взамен. До подписки функции плагина временно приостановлены.",
            "en": "Please subscribe to our official channel.\n\nWe develop plugins for free and ask nothing in return. Plugin features are paused until you subscribe."
        },
        "sub_thank_you": {"ru": "Спасибо за подписку на наш канал!", "en": "Thank you for subscribing to our channel!"},
        "sub_thank_you_after_expired": {"ru": "Спасибо за подписку на наш канал!\nПлагин продолжит работу!", "en": "Thank you for subscribing to our channel!\nThe plugin will continue working!"},
        "sub_not_found": {"ru": "Подписка не обнаружена. Пожалуйста, подпишитесь на канал.", "en": "Subscription not found. Please subscribe to the channel."},
        "settings_channel": {"ru": "Канал автора", "en": "Author's Channel"},
        "settings_donate": {"ru": "Поддержать автора", "en": "Support author"},
        "settings_bug_report": {"ru": "Сообщить о баге", "en": "Report a bug"}
    }

    @classmethod
    def is_ru(cls) -> bool:
        try:
            from org.telegram.messenger import LocaleController
            cur = str(LocaleController.getInstance().getCurrentLocale().getLanguage() or "").lower()
            if cur.startswith(("ru", "uk", "be")): return True
            if cur: return False
        except Exception:
            pass
        try:
            from java.util import Locale
            code = str(Locale.getDefault().getLanguage() or "").lower()
            if code.startswith(("ru", "uk", "be")): return True
        except Exception:
            pass
        return False

    @classmethod
    def tr(cls, key: str) -> str:
        entry = cls._TEXTS.get(key, {})
        return entry.get("ru" if cls.is_ru() else "en", entry.get("en", key))

    def __init__(self, plugin, icon_sticker=None):
        self.plugin = plugin
        self.icon_sticker = icon_sticker or getattr(plugin, "__icon__", "MaxExteraPluginsStickers/1")
        self._stopped = False
        self._active_dialog = None
        self._last_known_sub = None

    def on_load(self):
        self._stopped = False
        self._active_dialog = None
        self._last_known_sub = None
        self._load_remote_links_async()
        self._check_initial_subscription_flow()
        self._start_subscription_watcher()

    def on_event(self, event_type):
        try:
            name = str(event_type).upper()
            if name.endswith("START") or name.endswith("RESUME"):
                self._check_subscription_change_instant()
        except Exception:
            pass

    def on_unload(self):
        self._stopped = True
        self._dismiss_active_dialog()

    def _get_links(self) -> dict:
        raw = self.plugin.get_setting("remote_links_cache", None)
        if raw:
            try:
                import json
                data = json.loads(raw)
                if isinstance(data, dict): return data
            except Exception:
                pass
        return self.DEFAULT_LINKS

    def _load_remote_links_async(self):
        def worker():
            try:
                import urllib.request, json
                req = urllib.request.Request(self.CONFIG_URL, headers={"User-Agent": "MaxExteraPlugins"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if isinstance(data, dict):
                            self.plugin.set_setting("remote_links_cache", json.dumps(data))
                            self._resolve_channel_in_telegram(data.get("channel_username", "MaxExteraPlugins"))
            except Exception:
                pass
        import threading
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _open_url(self, url: str, view=None):
        try:
            from org.telegram.messenger.browser import Browser
            from org.telegram.messenger import ApplicationLoader
            from client_utils import get_last_fragment
            ctx = None
            if view is not None:
                ctx = view.getContext()
            if ctx is None:
                frag = get_last_fragment()
                if frag is not None:
                    ctx = frag.getParentActivity()
            if ctx is None:
                ctx = ApplicationLoader.applicationContext
            Browser.openUrl(ctx, url)
        except Exception:
            pass

    def _resolve_channel_in_telegram(self, username: str):
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            from org.telegram.tgnet import TLRPC, ConnectionsManager, RequestDelegate
            clean_user = username.lstrip("@")
            acc = int(UserConfig.selectedAccount)
            mc = MessagesController.getInstance(acc)
            if not mc: return
            req = TLRPC.TL_contacts_resolveUsername()
            req.username = clean_user
            helper_ref = self
            class Delegate(RequestDelegate):
                def run(self, response, error):
                    if error is None and response is not None:
                        chats = getattr(response, "chats", None)
                        if chats is not None and chats.size() > 0:
                            mc.putChats(chats, False)
                            c = chats.get(0)
                            cid = getattr(c, "id", 0)
                            if cid > 0:
                                helper_ref.plugin.set_setting("resolved_channel_id", int(cid))
            ConnectionsManager.getInstance(acc).sendRequest(req, Delegate())
        except Exception:
            pass

    def is_subscribed(self) -> bool:
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            links = self._get_links()
            target = str(links.get("channel_username", "MaxExteraPlugins") or "MaxExteraPlugins").lower().lstrip("@")
            saved_cid = self.plugin.get_setting("resolved_channel_id", 0)

            for acc in range(UserConfig.MAX_ACCOUNT_COUNT):
                uconf = UserConfig.getInstance(acc)
                if not uconf.isClientActivated(): continue
                mc = MessagesController.getInstance(acc)
                if not mc: continue

                if saved_cid:
                    try:
                        from java.lang import Long as JLong
                        c = mc.getChat(JLong(int(saved_cid)))
                        if c is not None:
                            left = bool(getattr(c, "left", True))
                            kicked = bool(getattr(c, "kicked", False))
                            if not left and not kicked: return True
                    except Exception:
                        pass

                try:
                    chat = mc.getUserOrChat(target)
                    if chat is not None:
                        cid = getattr(chat, "id", 0)
                        if cid and not saved_cid:
                            self.plugin.set_setting("resolved_channel_id", int(cid))
                        left = bool(getattr(chat, "left", True))
                        kicked = bool(getattr(chat, "kicked", False))
                        if not left and not kicked: return True
                except Exception:
                    pass

                try:
                    dialogs = mc.allDialogs
                    if dialogs is not None:
                        limit = min(dialogs.size(), 300)
                        for i in range(limit):
                            d = dialogs.get(i)
                            did = getattr(d, "id", 0)
                            if did < 0:
                                from java.lang import Long as JLong
                                c = mc.getChat(JLong(-did))
                                if c is not None:
                                    uname = str(getattr(c, "username", "") or "").lower()
                                    if uname == target:
                                        cid = getattr(c, "id", 0)
                                        if cid and not saved_cid:
                                            self.plugin.set_setting("resolved_channel_id", int(cid))
                                        left = bool(getattr(c, "left", True))
                                        kicked = bool(getattr(c, "kicked", False))
                                        if not left and not kicked: return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def is_allowed(self) -> bool:
        import time
        if self.is_subscribed():
            if not self.plugin.get_setting("was_subscribed", False):
                was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                self.plugin.set_setting("was_subscribed", True)
                self.plugin.set_setting("was_expired_state", False)
                self._notify_subscribed(was_expired=was_exp)
            return True

        if self.plugin.get_setting("was_expired_state", False) or self.plugin.get_setting("was_subscribed", False):
            self.plugin.set_setting("was_subscribed", False)
            self.plugin.set_setting("was_expired_state", True)
            self._show_expired_card()
            return False

        now = time.time()
        install_time = float(self.plugin.get_setting("install_time", 0.0) or 0.0)
        if install_time <= 0:
            install_time = now
            self.plugin.set_setting("install_time", install_time)

        trial_days = float(self._get_links().get("trial_days", 7))
        trial_sec = trial_days * 86400.0

        if (now - install_time) < trial_sec:
            return True

        self.plugin.set_setting("was_expired_state", True)
        self._show_expired_card()
        return False

    def prepend_settings(self, original_items=None) -> list:
        from ui.settings import Header, Text, Divider

        # Prevent double-prepending
        if original_items and any(getattr(x, "text", "") == "MaxExteraPlugins" for x in original_items if type(x).__name__ == "Header"):
            return original_items

        links = self._get_links()
        buttons_config = links.get("buttons")

        author_items = []
        if isinstance(buttons_config, list):
            for btn in buttons_config:
                if not isinstance(btn, dict): continue
                url = str(btn.get("url") or "").strip()
                if not url: continue

                title_data = btn.get("title")
                if isinstance(title_data, dict):
                    title = title_data.get("ru" if self.is_ru() else "en") or title_data.get("en") or title_data.get("ru") or ""
                elif isinstance(title_data, str) and title_data:
                    title = title_data
                else:
                    title = btn.get("title_ru" if self.is_ru() else "title_en") or btn.get("title_ru") or btn.get("title_en") or ""

                if not title: continue
                icon = str(btn.get("icon") or "msg_channel").strip()

                def make_click(u):
                    return lambda v=None: self._open_url(u, v)

                author_items.append(Text(text=title, icon=icon, on_click=make_click(url)))
        else:
            for k, text_key, icon_name in [
                ("channel_url", "settings_channel", "msg_channel"),
                ("donate_url", "settings_donate", "msg_share"),
                ("bug_report_url", "settings_bug_report", "msg_help")
            ]:
                u = str(links.get(k) or "").strip()
                if u:
                    author_items.append(Text(text=self.tr(text_key), icon=icon_name, on_click=lambda v=None, target_u=u: self._open_url(target_u, v)))

        res = []
        if author_items:
            hdr = links.get("header") or "MaxExteraPlugins"
            if isinstance(hdr, dict):
                hdr_text = hdr.get("ru" if self.is_ru() else "en") or hdr.get("ru") or hdr.get("en") or "MaxExteraPlugins"
            else:
                hdr_text = str(hdr)
            res.append(Header(text=hdr_text))
            res.extend(author_items)
            res.append(Divider())

        # Clean original_items by removing any old "Информация" / "Information" category
        cleaned_items = []
        if original_items:
            skipping_info = False
            for item in original_items:
                item_cls = type(item).__name__
                if item_cls == "Header":
                    txt = str(getattr(item, "text", "") or getattr(item, "title", "") or "").lower()
                    if "информ" in txt or "inform" in txt:
                        skipping_info = True
                        continue
                    else:
                        skipping_info = False
                elif skipping_info and item_cls == "Divider":
                    skipping_info = False
                    continue

                if not skipping_info:
                    cleaned_items.append(item)

        res.extend(cleaned_items)
        return res

    def _dismiss_active_dialog(self):
        try:
            if self._active_dialog is not None:
                self._active_dialog.dismiss()
        except Exception:
            pass
        self._active_dialog = None

    def _is_dialog_active(self) -> bool:
        try:
            if self._active_dialog is not None:
                return bool(self._active_dialog.isShowing())
        except Exception:
            pass
        return False

    def _notify_subscribed(self, was_expired=False):
        self.plugin.set_setting("was_subscribed", True)
        from ui.bulletin import BulletinHelper
        msg_key = "sub_thank_you_after_expired" if was_expired else "sub_thank_you"
        BulletinHelper.show_success(self.tr(msg_key))

    def _check_subscription_change_instant(self):
        try:
            from android_utils import run_on_ui_thread
            cur_sub = self.is_subscribed()
            prev_sub = self._last_known_sub
            if prev_sub is not None and prev_sub != cur_sub:
                self._last_known_sub = cur_sub
                if cur_sub:
                    was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                    self.plugin.set_setting("was_subscribed", True)
                    self.plugin.set_setting("was_expired_state", False)
                    self._dismiss_active_dialog()
                    self._notify_subscribed(was_expired=was_exp)
                else:
                    self.plugin.set_setting("was_subscribed", False)
                    self.plugin.set_setting("was_expired_state", True)
                    self._dismiss_active_dialog()
                    self._show_expired_card()
            else:
                self._last_known_sub = cur_sub
        except Exception:
            pass

    def _start_subscription_watcher(self):
        def watcher_loop():
            import time
            from android_utils import run_on_ui_thread
            time.sleep(2.0)
            if self._stopped: return
            self._last_known_sub = self.is_subscribed()

            while not self._stopped:
                try:
                    time.sleep(2.0)
                    if self._stopped: break
                    cur_sub = self.is_subscribed()
                    prev_sub = self._last_known_sub

                    if prev_sub is not None and prev_sub != cur_sub:
                        self._last_known_sub = cur_sub
                        if cur_sub:
                            was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                            self.plugin.set_setting("was_subscribed", True)
                            self.plugin.set_setting("was_expired_state", False)
                            def on_sub():
                                self._dismiss_active_dialog()
                                self._notify_subscribed(was_expired=was_exp)
                            run_on_ui_thread(on_sub)
                        else:
                            self.plugin.set_setting("was_subscribed", False)
                            self.plugin.set_setting("was_expired_state", True)
                            def on_unsub():
                                self._dismiss_active_dialog()
                                self._show_expired_card()
                            run_on_ui_thread(on_unsub)
                    else:
                        self._last_known_sub = cur_sub
                except Exception:
                    pass
        import threading
        t = threading.Thread(target=watcher_loop, daemon=True)
        t.start()

    def _check_initial_subscription_flow(self):
        def flow():
            import time
            try:
                now = time.time()
                install_time = float(self.plugin.get_setting("install_time", 0.0) or 0.0)
                if install_time <= 0:
                    install_time = now
                    self.plugin.set_setting("install_time", install_time)

                is_sub = self.is_subscribed()
                self._last_known_sub = is_sub
                was_sub = bool(self.plugin.get_setting("was_subscribed", False))
                was_exp = bool(self.plugin.get_setting("was_expired_state", False))

                if is_sub:
                    if not was_sub:
                        self.plugin.set_setting("was_subscribed", True)
                        self.plugin.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=was_exp)
                    return

                if was_sub or was_exp:
                    self.plugin.set_setting("was_subscribed", False)
                    self.plugin.set_setting("was_expired_state", True)
                    self._show_expired_card()
                    return

                trial_days = float(self._get_links().get("trial_days", 7))
                trial_sec = trial_days * 86400.0
                last_remind = float(self.plugin.get_setting("last_remind_time", 0.0) or 0.0)

                if (now - install_time) < trial_sec:
                    if last_remind <= 0 or (now - last_remind) >= trial_sec:
                        self._show_welcome_card()
                else:
                    self.plugin.set_setting("was_expired_state", True)
                    self._show_expired_card()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(flow, 1500)

    def _create_card_content(self, act, title_text, message_text):
        try:
            from android.widget import LinearLayout, TextView
            from android.view import Gravity
            from android.graphics import Typeface
            from org.telegram.messenger import AndroidUtilities, UserConfig, MediaDataController
            from org.telegram.ui.ActionBar import Theme
            from org.telegram.ui.Components import BackupImageView

            dp = AndroidUtilities.dp
            layout = LinearLayout(act)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setGravity(Gravity.CENTER_HORIZONTAL)
            layout.setPadding(dp(24), dp(16), dp(24), dp(6))

            size = dp(76)
            iv = BackupImageView(act)
            iv.setRoundRadius(dp(18))
            lp_iv = LinearLayout.LayoutParams(size, size)
            lp_iv.gravity = Gravity.CENTER_HORIZONTAL
            lp_iv.setMargins(0, dp(4), 0, dp(16))
            iv.setLayoutParams(lp_iv)

            try:
                acc = int(UserConfig.selectedAccount)
                mdc = MediaDataController.getInstance(acc)
                raw_icon = str(self.icon_sticker)
                if "/" in raw_icon:
                    pack, idx_s = raw_icon.split("/", 1)
                    mdc.setPlaceholderImageByIndex(iv, pack, int(idx_s), "150_150")
            except Exception:
                pass
            layout.addView(iv)

            if title_text:
                tt = TextView(act)
                tt.setText(title_text)
                tt.setTextSize(19.0)
                tt.setTypeface(None, Typeface.BOLD)
                tt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                tt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_t = LinearLayout.LayoutParams(-1, -2)
                lp_t.setMargins(0, 0, 0, dp(12))
                tt.setLayoutParams(lp_t)
                layout.addView(tt)

            if message_text:
                mt = TextView(act)
                mt.setText(message_text)
                mt.setTextSize(15.0)
                mt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                mt.setLineSpacing(float(dp(3)), 1.0)
                mt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_m = LinearLayout.LayoutParams(-1, -2)
                mt.setLayoutParams(lp_m)
                layout.addView(mt)

            return layout
        except Exception:
            return None

    def _show_welcome_card(self):
        def show():
            try:
                if self._is_dialog_active(): return
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                from ui.alert import AlertDialogBuilder
                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, self.tr("install_card_title"), self.tr("install_card_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(self.tr("install_card_title"))
                    b.set_message(self.tr("install_card_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed():
                            self._notify_subscribed(was_expired=False)
                    from android_utils import run_on_ui_thread
                    run_on_ui_thread(check_after, 3000)

                def on_later(d, w):
                    import time
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("last_remind_time", time.time())

                b.set_positive_button(self.tr("subscribe_btn"), on_sub)
                b.set_negative_button(self.tr("remind_later_btn"), on_later)
                self._active_dialog = b.show()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)

    def _show_expired_card(self):
        def show():
            try:
                if self._is_dialog_active(): return
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                from ui.alert import AlertDialogBuilder
                from ui.bulletin import BulletinHelper
                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, self.tr("trial_expired_title"), self.tr("trial_expired_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(self.tr("trial_expired_title"))
                    b.set_message(self.tr("trial_expired_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed():
                            self.plugin.set_setting("was_subscribed", True)
                            self.plugin.set_setting("was_expired_state", False)
                            self._notify_subscribed(was_expired=True)
                    from android_utils import run_on_ui_thread
                    run_on_ui_thread(check_after, 3000)

                def on_check(d, w):
                    self._dismiss_active_dialog()
                    if self.is_subscribed():
                        self.plugin.set_setting("was_subscribed", True)
                        self.plugin.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=True)
                    else:
                        BulletinHelper.show_error(self.tr("sub_not_found"))
                        from android_utils import run_on_ui_thread
                        run_on_ui_thread(self._show_expired_card, 500)

                b.set_positive_button(self.tr("subscribe_btn"), on_sub)
                b.set_negative_button(self.tr("check_sub_btn"), on_check)
                self._active_dialog = b.show()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)


class SdamGIAPlugin(BasePlugin):
    def on_app_event(self, event_type):
        if hasattr(self, "_author_helper"):
            self._author_helper.on_event(event_type)

    def on_plugin_load(self):
        self._author_helper = AuthorChannelHelper(self, icon_sticker="MaxExteraPluginsStickers/4")
        self._author_helper.on_load()
        self._dlg = None; self._ldg = None
        if self.get_setting("show_in_drawer", True):
            self._add_drawer_item()
        try:
            clazz = jclass("org.telegram.ui.DialogsActivity")
            self.hook_all_methods(clazz.getClass(), "createView", EgeActionBarHook(self))
        except:
            pass

    def on_plugin_unload(self): pass

    def _add_drawer_item(self):
        self.add_menu_item(MenuItemData(
            menu_type=MenuItemType.DRAWER_MENU, text="ЕГЭ Тренер",
            on_click=self._on_drawer, icon="msg_help",
            subtext="Тренажёр заданий ЕГЭ", priority=50,
            item_id="ege_trainer_drawer"))

    def _remove_drawer_item(self):
        self.remove_menu_item("ege_trainer_drawer")

    def _on_drawer_toggle(self, enabled):
        if enabled:
            self._add_drawer_item()
        else:
            self._remove_drawer_item()

    def _on_profile_click(self, view):
        run_on_ui_thread(self._show_profile)

    def _on_start_click(self, view):
        run_on_ui_thread(self._pick_subject)

    def create_settings(self):
        try:
            items = self._inner_create_settings()
        except Exception:
            items = []
        if hasattr(self, '_author_helper'):
            return self._author_helper.prepend_settings(items)
        return items

    def _inner_create_settings(self):
        items = [
            Header(text="Быстрый доступ"),
            Text(text="Профиль", icon="msg_contacts",
                on_click=self._on_profile_click),
            Text(text="Выбор задания", icon="msg_help",
                on_click=self._on_start_click),
            Text(text="Открыть статистику", icon="msg_stats",
                on_click=self._on_stats_click),
            Divider(),
            Header(text="Отображение кнопки"),
            Switch(key="show_in_drawer", text="Боковое меню",
                default=True, subtext="Кнопка в боковом меню",
                icon="msg_menu", on_change=self._on_drawer_toggle),
            Switch(key="show_in_actionbar", text="Главный экран",
                default=False, subtext="Иконка на верхней панели главной страницы",
                icon="msg_header"),
            Divider(),
            Header(text="Общие"),
            Switch(key="show_solution", text="Показывать решение",
                default=True, subtext="После нажатия проверить/показать ответ"),
            Switch(key="light_theme", text="Светлая тема заданий",
                default=False),
            Switch(key="hide_input", text="Скрыть ввод ответа",
                default=False, subtext="Убрать поле ввода ответа"),
            Divider(),
            Header(text="Мои предметы"),
        ]
        for k, v in SUBJECTS.items():
            items.append(Switch(key="subj_" + k, text=v["name"],
                default=True, icon="msg_menu"))
        if hasattr(self, "_author_helper"):

            return self._author_helper.prepend_settings(items)

        return items

    def _on_stats_click(self, view):
        run_on_ui_thread(self._show_stats)

    def _get_stats(self):
        raw = self.get_setting("stats_data", "{}")
        try: return json.loads(raw)
        except: return {}

    def _save_stats(self, stats):
        self.set_setting("stats_data", json.dumps(stats, ensure_ascii=False))

    def _record(self, sk, tn, correct):
        stats = self._get_stats()
        if sk not in stats: stats[sk] = {}
        key = str(tn)
        if key not in stats[sk]: stats[sk][key] = {"ok": 0, "fail": 0}
        if correct:
            stats[sk][key]["ok"] += 1
        else:
            stats[sk][key]["fail"] += 1
        self._save_stats(stats)
        self._log_solve()

    def _show_stats(self):
        f = get_last_fragment()
        if not f: return
        a = f.getParentActivity()
        if not a: return
        stats = self._get_stats()
        if not stats:
            d = AlertDialogBuilder(a)
            d.set_title("Статистика")
            d.set_message("Пока нет данных. Решайте задания и отмечайте результат кнопками верно/неверно!")
            d.set_positive_button("OK", lambda b, w: b.dismiss()); d.show()
            return
        sk_list = [k for k in stats.keys() if k in SUBJECTS]
        if not sk_list:
            d = AlertDialogBuilder(a)
            d.set_title("Статистика")
            d.set_message("Нет данных.")
            d.set_positive_button("OK", lambda b, w: b.dismiss()); d.show()
            return
        names = [SUBJECTS[k]["name"] for k in sk_list]
        def on_pick(bld, idx):
            bld.dismiss()
            run_on_ui_thread(lambda s=sk_list[idx]: self._show_stats_subject(s))
        d = AlertDialogBuilder(a)
        d.set_title("Статистика по предметам")
        d.set_items(names, on_pick)
        d.set_negative_button("Закрыть", lambda b, w: b.dismiss())
        d.set_neutral_button("Сбросить",
            lambda b, w: (b.dismiss(), run_on_ui_thread(lambda: self._confirm_reset())))
        d.show()

    def _confirm_reset(self):
        f = get_last_fragment()
        if not f: return
        a = f.getParentActivity()
        if not a: return
        d = AlertDialogBuilder(a)
        d.set_title("Сброс статистики")
        d.set_message("Вы уверены? Все данные статистики будут удалены без возможности восстановления.")
        def do_reset(b, w):
            self._save_stats({})
            self.set_setting("solve_log", "[]")
            self.set_setting("active_days", "[]")
            b.dismiss()
            Toast.makeText(a, "Статистика сброшена", Toast.LENGTH_SHORT).show()
        d.set_positive_button("Сбросить", do_reset)
        d.set_negative_button("Отмена", lambda b, w: b.dismiss())
        d.show()

    def _show_stats_subject(self, sk):
        f = get_last_fragment()
        if not f: return
        a = f.getParentActivity()
        if not a: return
        stats = self._get_stats()
        tasks = stats.get(sk, {})
        info = SUBJECTS.get(sk, {})
        name = info.get("name", sk)
        force_light = self.get_setting("light_theme", False)
        if force_light:
            bg = "#ffffff"; fg = "#212121"; accent = "#1976d2"
        else:
            is_dark = Theme.isCurrentThemeDark()
            bg = "#1a1a1a" if is_dark else "#ffffff"
            fg = "#e0e0e0" if is_dark else "#212121"
            accent = "#64b5f6" if is_dark else "#1976d2"
        green = "#4CAF50"; red = "#F44336"
        rows = ""
        total_ok = 0; total_fail = 0
        for tn in sorted(tasks.keys(), key=lambda x: int(x)):
            d = tasks[tn]
            ok = d.get("ok", 0); fail = d.get("fail", 0)
            total = ok + fail
            total_ok += ok; total_fail += fail
            pct = str(int(ok * 100 / total)) + "%" if total > 0 else "—"
            rows += ("<tr>"
                "<td style='text-align:center;font-weight:700'>" + tn + "</td>"
                "<td style='text-align:center'>" + str(total) + "</td>"
                "<td style='text-align:center;color:" + green + "'>" + str(ok) + "</td>"
                "<td style='text-align:center;color:" + red + "'>" + str(fail) + "</td>"
                "<td style='text-align:center;font-weight:700;color:" + accent + "'>" + pct + "</td>"
                "</tr>")
        grand = total_ok + total_fail
        gpct = str(int(total_ok * 100 / grand)) + "%" if grand > 0 else "—"
        footer = ("<tr style='border-top:2px solid " + fg + "60'>"
            "<td style='font-weight:700'>Итого</td>"
            "<td style='text-align:center;font-weight:700'>" + str(grand) + "</td>"
            "<td style='text-align:center;font-weight:700;color:" + green + "'>" + str(total_ok) + "</td>"
            "<td style='text-align:center;font-weight:700;color:" + red + "'>" + str(total_fail) + "</td>"
            "<td style='text-align:center;font-weight:700;color:" + accent + "'>" + gpct + "</td>"
            "</tr>")
        table_html = ("<h3 style='margin:0 0 12px 0;color:" + accent + "'>" + name + "</h3>"
            "<table style='width:100%;border-collapse:collapse;font-size:14px'>"
            "<tr style='background:" + fg + "15'>"
            "<th style='padding:8px 6px;text-align:center;border-bottom:2px solid " + fg + "30'>№</th>"
            "<th style='padding:8px 6px;text-align:center;border-bottom:2px solid " + fg + "30'>Всего</th>"
            "<th style='padding:8px 6px;text-align:center;border-bottom:2px solid " + fg + "30'>Верно</th>"
            "<th style='padding:8px 6px;text-align:center;border-bottom:2px solid " + fg + "30'>Неверно</th>"
            "<th style='padding:8px 6px;text-align:center;border-bottom:2px solid " + fg + "30'>%</th>"
            "</tr>" + rows + footer + "</table>")
        wv = WebView(a)
        ws = wv.getSettings()
        ws.setJavaScriptEnabled(False); ws.setDefaultTextEncodingName("utf-8")
        wv.setBackgroundColor(Color.TRANSPARENT)
        wv.loadDataWithBaseURL(None, self._html(table_html, bg, fg, accent),
            "text/html", "utf-8", None)
        d = AlertDialogBuilder(a)
        d.set_title(name)
        d.set_view(wv, -2)
        d.set_positive_button("Назад",
            lambda b, w: (b.dismiss(), run_on_ui_thread(self._show_stats)))
        d.set_negative_button("Закрыть", lambda b, w: b.dismiss())
        d.show()

    def _today(self):
        return time.strftime("%Y-%m-%d")

    def _record_day(self):
        days = self.get_setting("active_days", "[]")
        try: days = json.loads(days)
        except: days = []
        today = self._today()
        if today not in days:
            days.append(today)
            if len(days) > 365: days = days[-365:]
            self.set_setting("active_days", json.dumps(days))

    def _get_streak(self):
        days = self.get_setting("active_days", "[]")
        try: days = json.loads(days)
        except: return 0
        if not days: return 0
        days_set = set(days)
        streak = 0
        cur = time.time()
        while True:
            ds = time.strftime("%Y-%m-%d", time.localtime(cur))
            if ds in days_set:
                streak += 1
                cur -= 86400
            else:
                if streak == 0:
                    cur -= 86400
                    ds2 = time.strftime("%Y-%m-%d", time.localtime(cur))
                    if ds2 in days_set:
                        streak += 1
                        cur -= 86400
                        continue
                break
        return streak

    def _get_totals(self):
        stats = self._get_stats()
        total = 0; ok = 0
        for sk, tasks in stats.items():
            for tn, d in tasks.items():
                total += d.get("ok", 0) + d.get("fail", 0)
                ok += d.get("ok", 0)
        return total, ok

    def _get_month_today(self):
        stats_log = self.get_setting("solve_log", "[]")
        try: log = json.loads(stats_log)
        except: log = []
        today = self._today()
        month = self._today()[:7]
        m_count = sum(1 for e in log if e.startswith(month))
        d_count = sum(1 for e in log if e == today)
        return m_count, d_count

    def _log_solve(self):
        stats_log = self.get_setting("solve_log", "[]")
        try: log = json.loads(stats_log)
        except: log = []
        log.append(self._today())
        if len(log) > 5000: log = log[-5000:]
        self.set_setting("solve_log", json.dumps(log))
        self._record_day()

    def _on_drawer(self, ctx): run_on_ui_thread(self._show_main_menu)

    def _show_main_menu(self):
        f = get_last_fragment()
        if not f: return
        a = f.getParentActivity()
        if not a: return
        items = ["Профиль", "Выбор предмета"]
        def cb(b, i):
            b.dismiss()
            if i == 0:
                run_on_ui_thread(self._show_profile)
            else:
                run_on_ui_thread(self._pick_subject)
        d = AlertDialogBuilder(a)
        d.set_title("ЕГЭ Тренер"); d.set_items(items, cb)
        d.set_negative_button("Закрыть", lambda b, w: b.dismiss())
        d.show(); d.set_cancelable(False)

    def _show_profile(self):
        f = get_last_fragment()
        if not f: return
        a = f.getParentActivity()
        if not a: return
        from org.telegram.messenger import UserConfig
        acc = UserConfig.getInstance(UserConfig.selectedAccount)
        user = acc.getCurrentUser()
        uname = ""
        if user:
            fn = user.first_name or ""
            ln = user.last_name or ""
            uname = (fn + " " + ln).strip()
        if not uname: uname = "Пользователь"
        streak = self._get_streak()
        total, ok = self._get_totals()
        pct = str(int(ok * 100 / total)) + "%" if total > 0 else "—"
        m_count, d_count = self._get_month_today()
        force_light = self.get_setting("light_theme", False)
        if force_light:
            bg = "#ffffff"; fg = "#212121"; accent = "#1976d2"
        else:
            is_dark = Theme.isCurrentThemeDark()
            bg = "#1a1a1a" if is_dark else "#ffffff"
            fg = "#e0e0e0" if is_dark else "#212121"
            accent = "#64b5f6" if is_dark else "#1976d2"
        fg2 = "#aaaaaa" if bg == "#1a1a1a" else "#888888"
        fire = str(streak) if streak > 0 else "0"
        html = ("<div style='text-align:center;padding:12px 0'>"
            "<div style='font-size:20px;font-weight:700;margin-bottom:4px'>"
            + uname + "</div>"
            "<div style='font-size:28px;margin-bottom:16px'>"
            + fire + " \U0001f525</div>"
            "<table style='width:100%;border-collapse:collapse;font-size:14px'>"
            "<tr>"
            "<td style='text-align:center;padding:12px 8px;border-right:1px solid " + fg + "20;border-bottom:1px solid " + fg + "20'>"
            "<div style='font-size:11px;color:" + fg2 + "'>Решено всего</div>"
            "<div style='font-size:22px;font-weight:700;color:" + accent + "'>" + str(total) + "</div></td>"
            "<td style='text-align:center;padding:12px 8px;border-bottom:1px solid " + fg + "20'>"
            "<div style='font-size:11px;color:" + fg2 + "'>Правильность</div>"
            "<div style='font-size:22px;font-weight:700;color:#4CAF50'>" + pct + "</div></td>"
            "</tr><tr>"
            "<td style='text-align:center;padding:12px 8px;border-right:1px solid " + fg + "20'>"
            "<div style='font-size:11px;color:" + fg2 + "'>За месяц</div>"
            "<div style='font-size:22px;font-weight:700;color:" + accent + "'>" + str(m_count) + "</div></td>"
            "<td style='text-align:center;padding:12px 8px'>"
            "<div style='font-size:11px;color:" + fg2 + "'>Сегодня</div>"
            "<div style='font-size:22px;font-weight:700;color:" + accent + "'>" + str(d_count) + "</div></td>"
            "</tr></table></div>")
        wv = WebView(a)
        ws = wv.getSettings()
        ws.setJavaScriptEnabled(False); ws.setDefaultTextEncodingName("utf-8")
        wv.setBackgroundColor(Color.TRANSPARENT)
        wv.loadDataWithBaseURL(None, self._html(html, bg, fg, accent), "text/html", "utf-8", None)
        sc = ScrollView(a); sc.setFillViewport(True)
        root = LinearLayout(a); root.setOrientation(LinearLayout.VERTICAL)
        pad = AndroidUtilities.dp(8); root.setPadding(pad, pad, pad, pad)
        wv_lp = LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, AndroidUtilities.dp(220))
        root.addView(wv, wv_lp)
        sb = Button(a); sb.setText("Открыть статистику"); sb.setAllCaps(False)
        sb.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14)
        sb_lp = LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, AndroidUtilities.dp(44))
        sb_lp.setMargins(0, AndroidUtilities.dp(8), 0, 0)
        root.addView(sb, sb_lp)
        sc.addView(root)
        def on_stats(v):
            if hasattr(self, '_prof_dlg') and self._prof_dlg:
                try: self._prof_dlg.dismiss()
                except: pass
            run_on_ui_thread(self._show_stats)
        sb.setOnClickListener(OnClickListener(on_stats))
        d = AlertDialogBuilder(a)
        d.set_title("Профиль")
        d.set_view(sc, -2)
        d.set_positive_button("Назад",
            lambda b, w: (b.dismiss(), run_on_ui_thread(self._show_main_menu)))
        d.set_negative_button("Закрыть", lambda b, w: b.dismiss())
        d.show(); d.set_cancelable(False)
        self._prof_dlg = d

    def _pick_subject(self):
        f = get_last_fragment()
        if not f: return
        a = f.getParentActivity()
        if not a: return
        keys = [k for k in SUBJECTS.keys() if self.get_setting("subj_" + k, True)]
        if not keys: keys = list(SUBJECTS.keys())
        names = [SUBJECTS[k]["name"] for k in keys]
        def cb(b, i):
            b.dismiss(); run_on_ui_thread(lambda k=keys[i]: self._pick_task(k))
        d = AlertDialogBuilder(a)
        d.set_title("Выберите предмет:"); d.set_items(names, cb)
        d.set_negative_button("Назад",
            lambda b, w: (b.dismiss(), run_on_ui_thread(self._show_main_menu)))
        d.show(); d.set_cancelable(False)

    def _pick_task(self, sk):
        f = get_last_fragment()
        if not f: return
        a = f.getParentActivity()
        if not a: return
        info = SUBJECTS[sk]
        items = ["Задание " + str(i+1) for i in range(info["tasks"])]
        def cb(b, i):
            b.dismiss(); self._load(sk, i+1)
        d = AlertDialogBuilder(a)
        d.set_title(info["name"]); d.set_items(items, cb)
        d.set_negative_button("Назад",
            lambda b, w: (b.dismiss(), run_on_ui_thread(self._pick_subject)))
        d.show(); d.set_cancelable(False)

    def _load(self, sk, tn):
        def spinner():
            f = get_last_fragment()
            if not f: return
            a = f.getParentActivity()
            if not a: return
            self._ldg = AlertDialogBuilder(a, AlertDialogBuilder.ALERT_TYPE_SPINNER)
            self._ldg.set_title("Загрузка..."); self._ldg.set_cancelable(False); self._ldg.show()
        run_on_ui_thread(spinner)
        def work():
            try:
                p = self._fetch(sk, tn)
                run_on_ui_thread(lambda pr=p, s=sk: (self._hld(), self._show(pr, s)))
            except Exception as exc:
                e = str(exc) or "Ошибка"
                run_on_ui_thread(lambda er=e, s=sk, t=tn: (self._hld(), self._err(er, s, t)))
        run_on_queue(work)

    def _hld(self):
        if self._ldg:
            try: self._ldg.dismiss()
            except: pass
            self._ldg = None

    def _err(self, msg, sk, tn):
        f = get_last_fragment()
        if not f: return
        a = f.getParentActivity()
        if not a: return
        d = AlertDialogBuilder(a); d.set_title("Ошибка"); d.set_message(msg)
        d.set_positive_button("Повторить", lambda b, w: (b.dismiss(), self._load(sk, tn)))
        d.set_negative_button("Закрыть", lambda b, w: b.dismiss()); d.show()

    def _base(self, sk):
        return "https://" + SUBJECTS[sk]["domain"] + ".sdamgia.ru"

    def _fetch(self, sk, tn):
        base = self._base(sk)
        s = requests.Session()
        s.headers.update(_HDR)

        catalog_url = base + "/prob_catalog"
        resp = s.get(catalog_url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        cat_id = self._find_category_for_task(soup, tn, base, s)

        if not cat_id:
            return self._fetch_via_test(sk, tn, s)

        problem_ids = self._get_problems_from_category(base, cat_id, s)

        if not problem_ids:
            return self._fetch_via_test(sk, tn, s)

        pid = random.choice(problem_ids)
        return self._get_problem_by_id(base, pid, tn, s)

    def _find_category_for_task(self, soup, tn, base, session):
        task_pattern = re.compile(r'[Зз]адани[ея]\s*' + str(tn) + r'\b', re.IGNORECASE)

        for link in soup.find_all('a', href=True):
            text = link.get_text()
            if task_pattern.search(text):
                href = link.get('href', '')
                m = re.search(r'theme=(\d+)', href)
                if m:
                    return m.group(1)
                m = re.search(r'category=(\d+)', href)
                if m:
                    return m.group(1)

        for div in soup.find_all(['div', 'span', 'td']):
            text = div.get_text()
            if task_pattern.search(text):
                for link in div.find_all('a', href=True):
                    href = link.get('href', '')
                    m = re.search(r'theme=(\d+)', href)
                    if m:
                        return m.group(1)
                    m = re.search(r'category=(\d+)', href)
                    if m:
                        return m.group(1)

        return None

    def _get_problems_from_category(self, base, cat_id, session):
        url = base + "/test?theme=" + cat_id
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            problem_ids = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                m = re.search(r'problem\?id=(\d+)', href)
                if m:
                    pid = m.group(1)
                    if pid not in problem_ids:
                        problem_ids.append(pid)

            return problem_ids[:50]
        except:
            return []

    def _get_problem_by_id(self, base, pid, tn, session):
        url = base + "/problem?id=" + str(pid)
        resp = session.get(url, timeout=20)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        cond_html = ""
        pbody = soup.find('div', class_='pbody')
        if pbody:
            for sol in pbody.find_all('div', class_='solution'):
                sol.decompose()
            cond_html = str(pbody)

        sol_html = ""
        solution = soup.find('div', class_='solution')
        if solution:
            sol_html = str(solution)

        answer = ""
        ans_div = soup.find('div', class_='answer')
        if ans_div:
            answer = ans_div.get_text(strip=True)
            answer = re.sub(r'^[Оо]твет[:\s]*', '', answer).strip().rstrip('.')

        if not answer and solution:
            text = solution.get_text()
            m = re.search(r'[Оо]твет[:\s]+([^\n]+)', text)
            if m:
                answer = m.group(1).strip().rstrip('.')

        if not answer:
            for tag in soup.find_all(['p', 'div', 'span']):
                text = tag.get_text()
                if 'Ответ' in text and len(text) < 200:
                    m = re.search(r'[Оо]твет[:\s]+(.+?)(?:\.|$)', text)
                    if m:
                        answer = m.group(1).strip()
                        break

        cond_html = self._fix_images(cond_html, base)
        sol_html = self._fix_images(sol_html, base)

        if not cond_html.strip():
            raise Exception("Не удалось извлечь условие задачи")

        return {
            "id": pid,
            "task_number": tn,
            "condition_html": cond_html,
            "solution_html": sol_html,
            "answer": answer,
            "url": url
        }

    def _fetch_via_test(self, sk, tn, session):
        base = self._base(sk)

        resp = session.post(
            base + "/test?a=generate",
            data={"prob" + str(tn): "1"},
            timeout=20,
            allow_redirects=True
        )
        resp.raise_for_status()

        tid = None
        if "id=" in resp.url:
            tid = resp.url.split("id=")[-1].split("&")[0].strip()
        if not tid:
            m = re.search(r'id=(\d+)', resp.text)
            if m:
                tid = m.group(1)

        if not tid:
            raise Exception("Сайт не вернул ID теста")

        test_url = base + "/test?id=" + tid
        resp = session.get(test_url, timeout=20)
        soup = BeautifulSoup(resp.text, "lxml")

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            m = re.search(r'problem\?id=(\d+)', href)
            if m:
                pid = m.group(1)
                return self._get_problem_by_id(base, pid, tn, session)

        raise Exception("Не удалось найти задачу в тесте")

    def _fix_images(self, html, base):
        if not html:
            return html
        soup = BeautifulSoup(html, "lxml")
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src.startswith("/"):
                img["src"] = base + src
            elif src and not src.startswith("http") and not src.startswith("data:"):
                img["src"] = base + "/" + src
        body = soup.find('body')
        if body:
            return body.decode_contents()
        return str(soup)

    def _show(self, p, sk):
        f = get_last_fragment()
        if not f: return
        act = f.getParentActivity()
        if not act: return
        ctx = act; info = SUBJECTS[sk]
        force_light = self.get_setting("light_theme", False)
        if force_light:
            bg = "#ffffff"; fg = "#212121"; fg2 = "#666666"
            accent = "#1976d2"; divider = "#e0e0e0"
        else:
            is_dark = Theme.isCurrentThemeDark()
            bg = "#1a1a1a" if is_dark else "#ffffff"
            fg = "#e0e0e0" if is_dark else "#212121"
            fg2 = "#aaaaaa" if is_dark else "#666666"
            accent = "#64b5f6" if is_dark else "#1976d2"
            divider = "#333333" if is_dark else "#e0e0e0"
        hide_input = self.get_setting("hide_input", False)
        sc = ScrollView(ctx); sc.setFillViewport(True)
        root = LinearLayout(ctx); root.setOrientation(LinearLayout.VERTICAL)
        pad = AndroidUtilities.dp(8); root.setPadding(pad, pad, pad, pad)
        wv = WebView(ctx)
        ws = wv.getSettings()
        ws.setJavaScriptEnabled(False); ws.setLoadWithOverviewMode(True)
        ws.setUseWideViewPort(True); ws.setBuiltInZoomControls(True)
        ws.setDisplayZoomControls(False); ws.setDefaultTextEncodingName("utf-8")
        wv.setBackgroundColor(Color.TRANSPARENT)
        wv.loadDataWithBaseURL(self._base(sk),
            self._html(p["condition_html"], bg, fg, accent), "text/html", "utf-8", None)
        wv_lp = LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, AndroidUtilities.dp(250))
        root.addView(wv, wv_lp)
        self._make_wv_scrollable(wv)
        dv = View(ctx); dv.setBackgroundColor(Color.parseColor(divider))
        dlp = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, AndroidUtilities.dp(1))
        dlp.setMargins(0, AndroidUtilities.dp(8), 0, AndroidUtilities.dp(8)); root.addView(dv, dlp)
        inp = None
        if not hide_input:
            self._tv(root, ctx, "Ваш ответ:", 14, True,
                Theme.getColor(Theme.key_dialogTextBlack), bottom=4)
            inp = EditText(ctx); inp.setHint("Введите ответ...")
            inp.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            inp.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            inp.setHintTextColor(Theme.getColor(Theme.key_dialogTextGray2))
            inp.setSingleLine(True)
            inp.setPadding(AndroidUtilities.dp(12),AndroidUtilities.dp(8),
                AndroidUtilities.dp(12),AndroidUtilities.dp(8))
            ilp = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT)
            ilp.setMargins(0,0,0,AndroidUtilities.dp(8)); root.addView(inp, ilp)
        btn_row = LinearLayout(ctx); btn_row.setOrientation(LinearLayout.HORIZONTAL)
        btn_row.setGravity(Gravity.CENTER)
        brlp = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT)
        brlp.setMargins(0,0,0,AndroidUtilities.dp(8))
        ckb = None
        if not hide_input:
            ckb = Button(ctx); ckb.setText("Проверить"); ckb.setAllCaps(False)
            ckb.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14)
            cb_lp = LinearLayout.LayoutParams(0, AndroidUtilities.dp(44), 1.0)
            cb_lp.setMargins(0,0,AndroidUtilities.dp(4),0); btn_row.addView(ckb, cb_lp)
        sab = Button(ctx); sab.setText("Ответ"); sab.setAllCaps(False)
        sab.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14)
        sa_lp = LinearLayout.LayoutParams(0, AndroidUtilities.dp(44), 1.0)
        if not hide_input:
            sa_lp.setMargins(AndroidUtilities.dp(4),0,0,0)
        btn_row.addView(sab, sa_lp)
        root.addView(btn_row, brlp)
        res = LinearLayout(ctx); res.setOrientation(LinearLayout.VERTICAL)
        res.setVisibility(View.GONE)
        res.setPadding(AndroidUtilities.dp(8),AndroidUtilities.dp(8),
            AndroidUtilities.dp(8),AndroidUtilities.dp(8))
        root.addView(res)
        nav = LinearLayout(ctx); nav.setOrientation(LinearLayout.HORIZONTAL)
        nav.setGravity(Gravity.CENTER)
        nlp = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT)
        nlp.setMargins(0,AndroidUtilities.dp(8),0,0)
        nb = Button(ctx); nb.setText("Следующее"); nb.setAllCaps(False)
        nb.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14)
        n1 = LinearLayout.LayoutParams(0, AndroidUtilities.dp(40), 1.0)
        n1.setMargins(0,0,AndroidUtilities.dp(4),0); nav.addView(nb, n1)
        wb = Button(ctx); wb.setText("На сайте"); wb.setAllCaps(False)
        wb.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14)
        n2 = LinearLayout.LayoutParams(0, AndroidUtilities.dp(40), 1.0)
        n2.setMargins(AndroidUtilities.dp(4),0,0,0); nav.addView(wb, n2)
        root.addView(nav, nlp)
        sc.addView(root)

        def _show_sol_and_mark(container):
            if self.get_setting("show_solution", True) and p.get("solution_html"):
                self._tv(container, ctx, "Решение:", 14, True,
                    Theme.getColor(Theme.key_dialogTextBlack), top=8, bottom=4)
                sw = WebView(ctx); sws = sw.getSettings()
                sws.setJavaScriptEnabled(False); sws.setDefaultTextEncodingName("utf-8")
                sws.setLoadWithOverviewMode(True); sws.setUseWideViewPort(True)
                sws.setBuiltInZoomControls(True); sws.setDisplayZoomControls(False)
                sw.setBackgroundColor(Color.TRANSPARENT)
                sw.loadDataWithBaseURL(self._base(sk),
                    self._html(p["solution_html"], bg, fg2, accent), "text/html", "utf-8", None)
                sw_lp = LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, AndroidUtilities.dp(300))
                container.addView(sw, sw_lp)
                self._make_wv_scrollable(sw)
            self._tv(container, ctx, "Оцените себя:", 13, False,
                Theme.getColor(Theme.key_dialogTextGray2), top=12, bottom=4)
            mark_row = LinearLayout(ctx); mark_row.setOrientation(LinearLayout.HORIZONTAL)
            mark_row.setGravity(Gravity.CENTER)
            mr_lp = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT)
            btn_ok = Button(ctx); btn_ok.setText("Верно"); btn_ok.setAllCaps(False)
            btn_ok.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14)
            ok_lp = LinearLayout.LayoutParams(0, AndroidUtilities.dp(40), 1.0)
            ok_lp.setMargins(0,0,AndroidUtilities.dp(4),0); mark_row.addView(btn_ok, ok_lp)
            btn_fail = Button(ctx); btn_fail.setText("Неверно"); btn_fail.setAllCaps(False)
            btn_fail.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14)
            fl_lp = LinearLayout.LayoutParams(0, AndroidUtilities.dp(40), 1.0)
            fl_lp.setMargins(AndroidUtilities.dp(4),0,0,0); mark_row.addView(btn_fail, fl_lp)
            container.addView(mark_row, mr_lp)
            def on_mark_ok(v):
                self._record(sk, p["task_number"], True)
                btn_ok.setEnabled(False); btn_fail.setEnabled(False)
                Toast.makeText(ctx, "Записано как верное", Toast.LENGTH_SHORT).show()
            def on_mark_fail(v):
                self._record(sk, p["task_number"], False)
                btn_ok.setEnabled(False); btn_fail.setEnabled(False)
                Toast.makeText(ctx, "Записано как неверное", Toast.LENGTH_SHORT).show()
            btn_ok.setOnClickListener(OnClickListener(on_mark_ok))
            btn_fail.setOnClickListener(OnClickListener(on_mark_fail))

        if ckb:
            def on_check(v):
                u = inp.getText().toString().strip()
                if not u:
                    Toast.makeText(ctx, "Введите ответ!", Toast.LENGTH_SHORT).show(); return
                c = p.get("answer", "")
                res.removeAllViews(); res.setVisibility(View.VISIBLE)
                def norm(s):
                    return (s.lower().replace(" ","").replace(",",".")
                        .replace("\u2212","-").replace("\u2013","-")
                        .replace("\u00a0","").replace("\u2010","-").strip())
                ok = norm(u) == norm(c) if c else False
                if ok:
                    self._tv(res, ctx, "Правильно!", 16, True,
                        Color.parseColor("#4CAF50"), bottom=4)
                else:
                    self._tv(res, ctx, "Неправильно", 16, True,
                        Color.parseColor("#F44336"), bottom=2)
                if c:
                    self._tv(res, ctx, "Правильный ответ: " + c, 14, True,
                        Theme.getColor(Theme.key_dialogTextBlue2), bottom=4)
                else:
                    self._tv(res, ctx, "Ответ не найден.", 13, False,
                        Color.parseColor("#FF9800"), bottom=4)
                _show_sol_and_mark(res)
            ckb.setOnClickListener(OnClickListener(on_check))

        def on_show_ans(v):
            c = p.get("answer", "")
            res.removeAllViews(); res.setVisibility(View.VISIBLE)
            if c:
                self._tv(res, ctx, "Ответ: " + c, 15, True,
                    Theme.getColor(Theme.key_dialogTextBlue2), bottom=4)
            else:
                self._tv(res, ctx, "Ответ не найден.", 13, False,
                    Color.parseColor("#FF9800"), bottom=4)
            _show_sol_and_mark(res)
        sab.setOnClickListener(OnClickListener(on_show_ans))

        def on_next(v):
            if self._dlg:
                try: self._dlg.dismiss()
                except: pass
                self._dlg = None
            self._load(sk, p["task_number"])
        nb.setOnClickListener(OnClickListener(on_next))

        def on_web(v):
            try:
                from android.content import Intent; from android.net import Uri
                ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(p["url"])))
            except: pass
        wb.setOnClickListener(OnClickListener(on_web))

        b = AlertDialogBuilder(ctx)
        b.set_title(info["name"] + " — Зад. " + str(p["task_number"]))
        b.set_view(sc, -2)
        b.set_negative_button("Закрыть", lambda b, w: b.dismiss())
        b.show(); b.set_cancelable(False); self._dlg = b

    def _html(self, body, bg, fg, accent):
        css = ("*{box-sizing:border-box;margin:0;padding:0}"
            "body{background:" + bg + ";color:" + fg + ";"
            "font-family:-apple-system,Roboto,sans-serif;"
            "font-size:15px;line-height:1.6;padding:8px;word-wrap:break-word}"
            "img{max-width:100%;height:auto;display:block;margin:8px auto}"
            "p{margin:6px 0}b,strong{font-weight:700}a{color:" + accent + "}"
            "center{text-align:center}"
            "sup{font-size:.75em;vertical-align:super}"
            "sub{font-size:.75em;vertical-align:sub}"
            "table{border-collapse:collapse;margin:8px 0;width:100%}"
            "td,th{border:1px solid " + fg + "40;padding:4px 8px;text-align:left}")
        return ("<!DOCTYPE html><html><head>"
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "<style>" + css + "</style></head><body>" + body + "</body></html>")

    def _tv(self, par, ctx, txt, sz, bold, col, top=0, bottom=0):
        tv = TextView(ctx); tv.setText(txt)
        tv.setTextSize(TypedValue.COMPLEX_UNIT_SP, sz)
        if bold: tv.setTypeface(Typeface.DEFAULT_BOLD)
        if isinstance(col, int): tv.setTextColor(col)
        else: tv.setTextColor(Color.parseColor(col))
        tv.setLineSpacing(AndroidUtilities.dp(2), 1.0)
        lp = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT)
        lp.setMargins(0, AndroidUtilities.dp(top), 0, AndroidUtilities.dp(bottom))
        par.addView(tv, lp)

    def _make_wv_scrollable(self, wv):
        from java import dynamic_proxy
        from android.view import View as V
        class TouchProxy(dynamic_proxy(V.OnTouchListener)):
            def onTouch(self_inner, view, event):
                a = event.getAction()
                if a == MotionEvent.ACTION_DOWN or a == MotionEvent.ACTION_MOVE:
                    view.getParent().requestDisallowInterceptTouchEvent(True)
                elif a == MotionEvent.ACTION_UP or a == MotionEvent.ACTION_CANCEL:
                    view.getParent().requestDisallowInterceptTouchEvent(False)
                return False
        wv.setOnTouchListener(TouchProxy())
