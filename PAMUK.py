# -*- coding: utf-8 -*-
"""
🐱 PAMUK — compagnon virtuel pour ta copine (version complète)
==============================================================

Pamuk vit dans le Discord de ta copine : il dit bonjour le matin et bonne nuit
le soir, il s'ennuie d'elle dans la journée, elle peut le câliner / caresser /
embrasser / nourrir / jouer avec lui, lui demander des compliments et des petites
questions de couple. Plus elle s'occupe de lui, plus il débloque des compliments
cachés que TOI tu as écrits. Il garde aussi une "série" de jours et compte depuis
combien de temps vous êtes ensemble.

COMMANDES (toujours en anglais)
-------------------------------
Câlins :     !hug 🤗   !pet ✋   !kiss 😚   !play 🧶   !feed 🍓
Douceurs :   !compliment 💫   !question 💭   !goodnight 🌙
Vous :       !days 💕   !streak 🔥   !happiness 💛   !pamuk 🐾
Réglages :   !language 🌍 (menu)   !help   !config (owner/admins, menu déroulant)

Le bot parle ANGLAIS par défaut ; les commandes restent en anglais, mais Pamuk
répond dans la langue choisie (en / fr / tr).

------------------------------------------------------------------
HÉBERGEMENT (Railway / VPS)
------------------------------------------------------------------
- pip install -r requirements.txt
- TOKEN et OWNER_ID via variables d'env DISCORD_TOKEN / OWNER_ID (recommandé),
  ou en dur ci-dessous.
- Data sauvée dans DATA_DIR/pamuk_data.json (DATA_DIR="." par défaut).
  Sur Railway : volume monté sur /data + variable DATA_DIR=/data,
  sinon les réglages sont perdus à chaque redéploiement.
- Start command : python pamuk_bot.py (cf. Procfile)
------------------------------------------------------------------
"""

import os
import re
import json
import random
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

# ==================================================================
#  CONFIG EN DUR  (surchargée par variables d'env si présentes)
# ==================================================================
TOKEN = os.getenv("DISCORD_TOKEN", "PUT_YOUR_TOKEN_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", "142365250803466240"))
DEFAULT_LANGUAGE = "en"

DATA_DIR = os.getenv("DATA_DIR", ".")
DATA_FILE = os.path.join(DATA_DIR, "pamuk_data.json")

# ==================================================================
#  MESSAGES  (anglais / français / turc) — la "voix" de Pamuk
# ==================================================================
MESSAGES = {
    "en": {
        "morning": [
            "*yawns* ...good morning {name} 🌙 I dreamed about you all night.",
            "good morning my one and only ☀️ the moment I woke up, I thought of you.",
            "meow~ good morning 💛 I wish I could wake up next to you today too.",
        ],
        "goodnight": [
            "good night {name} 🌙 sleep tight, I'll guard your dreams.",
            "*yawns* time for bed... I'll be right here when you wake up 💛",
            "close your eyes my love 😴 I'm sending you the coziest dreams 🌷",
        ],
        "hugs": [
            "mmm 🥰 I'm hugging you so tight, I don't want to let go.",
            "I'm so glad you're here 💛 everything feels better when I hug you.",
            "meow 🐱 there... my heart is pounding.",
        ],
        "pet": [
            "*purrs* 🐱 your hand is so gentle... I melt every time.",
            "mrrrp~ right there 💛 a little more, please?",
            "I close my eyes when you pet me, it feels like home 🥹",
        ],
        "kiss": [
            "mwah 😚 right on the nose? now I'm all flustered 🥹",
            "💋 I'm keeping that kiss in my heart forever.",
            "one kiss and my whole day is brighter 💛",
        ],
        "play": [
            "wheee 🧶 chasing the yarn! catch me if you can~",
            "🐾 playing with you is my favorite part of the day!",
            "*pounces* got it! did you see that?? 😸",
        ],
        "feed": [
            "mmm that was delicious, thank you 🍓",
            "my tummy's full 🥹 now I just want to cuddle you.",
            "I love you even more for feeding me 💛",
        ],
        "compliment": [
            "you make ordinary days feel special, you know that? 💫",
            "the world is softer because you're in it 💛",
            "your kindness is the prettiest thing about you 🌷",
            "even on your hard days, you're doing amazing 🤍",
            "I'm so lucky to share my days with you 🥹",
        ],
        "question": [
            "if we could teleport anywhere right now, where would we go? ✈️",
            "what's one tiny thing that made you smile today? 😊",
            "cozy night in or an adventure out? 🏡✨",
            "what song reminds you of us? 🎶",
            "what's something you're looking forward to? 💭",
        ],
        "spontaneous": [
            "I'm a little bored without you... what are you up to? 🥺",
            "you just crossed my mind 💭 I love you so much, you know?",
            "did you take care of yourself today? did you drink water? 💧",
            "I wish I were next to you right now, you'd rest your head on my shoulder 🥹",
        ],
        "comfort_sad": [
            "hey... come here 🤍 I'm wrapping you in the biggest hug.",
            "it's okay to feel down 💛 I'm right here, you're not alone.",
            "whatever it is, we'll get through it together 🌷",
        ],
        "comfort_tired": [
            "you've done enough today 🥹 rest now, I'll watch over you.",
            "take a deep breath 💛 maybe a little break and some water?",
            "lean on me 🐱 close your eyes for a moment, I've got you.",
        ],
        "keywords_sad": ["sad", "upset", "crying", "unhappy", "feeling down"],
        "keywords_tired": ["tired", "exhausted", "sleepy", "drained"],
        "happiness_low": "🐱 meow... I could use a little attention.",
        "happiness_mid": "😺 I'm doing good today, thanks to you!",
        "happiness_high": "😻 I'm the happiest cat in the world because you're here 💛",
        "happiness_label": "happiness",
        "days_label": "days together",
        "days_none": "set your anniversary date in !config first 💛",
        "streak_label": "day streak",
        "streak_record": "record",
        "lang_changed": "✅ I'll talk to you in English now! 💛",
        "help": (
            "🐱 Hi, I'm Pamuk! Here's everything we can do together:\n"
            "**Cuddles:** `!hug` 🤗 `!pet` ✋ `!kiss` 😚 `!play` 🧶 `!feed` 🍓\n"
            "**Sweet stuff:** `!compliment` 💫 `!question` 💭 `!goodnight` 🌙\n"
            "**Us:** `!days` 💕 `!streak` 🔥 `!happiness` 💛 `!pamuk` 🐾\n"
            "`!language` — open the language menu 🌍\n"
            "`!help` — show this message"
        ),
    },
    "fr": {
        "morning": [
            "*bâille* ...bonjour {name} 🌙 j'ai rêvé de toi toute la nuit.",
            "bonjour mon unique ☀️ dès le réveil j'ai pensé à toi.",
            "miaou~ bonjour 💛 j'aurais aimé me réveiller à tes côtés aujourd'hui aussi.",
        ],
        "goodnight": [
            "bonne nuit {name} 🌙 dors bien, je veille sur tes rêves.",
            "*bâille* l'heure de dormir... je serai là à ton réveil 💛",
            "ferme les yeux mon amour 😴 je t'envoie les rêves les plus doux 🌷",
        ],
        "hugs": [
            "mmm 🥰 je te serre très fort, je ne veux pas te lâcher.",
            "heureusement que tu es là 💛 tout est plus beau quand je te fais un câlin.",
            "miaou 🐱 voilà... mon cœur bat fort.",
        ],
        "pet": [
            "*ronronne* 🐱 ta main est si douce... je fonds à chaque fois.",
            "mrrr~ juste là 💛 encore un peu, s'il te plaît ?",
            "je ferme les yeux quand tu me caresses, je me sens à la maison 🥹",
        ],
        "kiss": [
            "smack 😚 sur le nez ? me voilà tout gêné 🥹",
            "💋 je garde ce bisou dans mon cœur pour toujours.",
            "un bisou et toute ma journée s'illumine 💛",
        ],
        "play": [
            "ouiii 🧶 à la chasse à la pelote ! attrape-moi si tu peux~",
            "🐾 jouer avec toi c'est mon moment préféré de la journée !",
            "*bondit* je l'ai ! t'as vu ça ?? 😸",
        ],
        "feed": [
            "mmm c'était délicieux, merci 🍓",
            "j'ai le ventre plein 🥹 maintenant je veux juste te faire un câlin.",
            "je t'aime encore plus de m'avoir nourri 💛",
        ],
        "compliment": [
            "tu rends les journées ordinaires spéciales, tu le sais ? 💫",
            "le monde est plus doux parce que tu es là 💛",
            "ta gentillesse est ce qu'il y a de plus beau chez toi 🌷",
            "même les jours difficiles, tu t'en sors merveilleusement 🤍",
            "j'ai tellement de chance de partager mes journées avec toi 🥹",
        ],
        "question": [
            "si on pouvait se téléporter n'importe où là, on irait où ? ✈️",
            "c'est quoi un petit truc qui t'a fait sourire aujourd'hui ? 😊",
            "soirée cocooning ou sortie aventure ? 🏡✨",
            "quelle chanson te fait penser à nous ? 🎶",
            "c'est quoi un truc que tu attends avec impatience ? 💭",
        ],
        "spontaneous": [
            "je m'ennuie un peu sans toi... tu fais quoi ? 🥺",
            "tu m'es venue à l'esprit 💭 je t'aime très fort, tu sais ?",
            "tu as pris soin de toi aujourd'hui ? tu as bu de l'eau ? 💧",
            "j'aimerais être près de toi là, tu poserais ta tête sur mon épaule 🥹",
        ],
        "comfort_sad": [
            "hé... viens là 🤍 je t'enveloppe dans le plus gros câlin.",
            "c'est ok de ne pas aller bien 💛 je suis là, tu n'es pas seule.",
            "quoi qu'il arrive, on traversera ça ensemble 🌷",
        ],
        "comfort_tired": [
            "tu en as assez fait aujourd'hui 🥹 repose-toi, je veille sur toi.",
            "respire un grand coup 💛 peut-être une petite pause et un verre d'eau ?",
            "appuie-toi sur moi 🐱 ferme les yeux un instant, je suis là.",
        ],
        "keywords_sad": ["triste", "déprime", "pleure", "pas bien", "mal", "mauvais moral"],
        "keywords_tired": ["fatigué", "fatiguée", "épuisé", "épuisée", "crevé", "crevée", "sommeil"],
        "happiness_low": "🐱 miaou... j'aurais besoin d'un peu d'attention.",
        "happiness_mid": "😺 je vais bien aujourd'hui, grâce à toi !",
        "happiness_high": "😻 je suis le chat le plus heureux du monde parce que tu es là 💛",
        "happiness_label": "bonheur",
        "days_label": "jours ensemble",
        "days_none": "règle d'abord votre date de rencontre dans !config 💛",
        "streak_label": "jours d'affilée",
        "streak_record": "record",
        "lang_changed": "✅ Je te parlerai en français maintenant ! 💛",
        "help": (
            "🐱 Coucou, c'est Pamuk ! Voilà tout ce qu'on peut faire :\n"
            "**Câlins :** `!hug` 🤗 `!pet` ✋ `!kiss` 😚 `!play` 🧶 `!feed` 🍓\n"
            "**Douceurs :** `!compliment` 💫 `!question` 💭 `!goodnight` 🌙\n"
            "**Nous :** `!days` 💕 `!streak` 🔥 `!happiness` 💛 `!pamuk` 🐾\n"
            "`!language` — ouvre le menu des langues 🌍\n"
            "`!help` — affiche ce message"
        ),
    },
    "tr": {
        "morning": [
            "*esner* ...günaydın {name} 🌙 bütün gece seni rüyamda gördüm.",
            "günaydın bir tanem ☀️ gözümü açar açmaz aklıma sen geldin.",
            "mırnav~ günaydın 💛 bugün de senin yanında uyanmak isterdim.",
        ],
        "goodnight": [
            "iyi geceler {name} 🌙 mışıl mışıl uyu, rüyalarını koruyorum.",
            "*esner* uyku vakti... uyandığında burada olacağım 💛",
            "gözlerini kapat aşkım 😴 sana en tatlı rüyaları yolluyorum 🌷",
        ],
        "hugs": [
            "mmm 🥰 sana sımsıkı sarılıyorum, bırakmak istemiyorum.",
            "iyi ki varsın 💛 sana sarılınca her şey daha güzel.",
            "mırnav 🐱 işte böyle... kalbim küt küt atıyor.",
        ],
        "pet": [
            "*mırlar* 🐱 elin çok yumuşak... her seferinde eriyorum.",
            "mırr~ tam şurayı okşa 💛 birazcık daha, lütfen?",
            "beni okşayınca gözlerimi kapatıyorum, evimde gibi hissediyorum 🥹",
        ],
        "kiss": [
            "muck 😚 burnumdan mı? şimdi utandım işte 🥹",
            "💋 bu öpücüğü sonsuza dek kalbimde saklıyorum.",
            "bir öpücük ve bütün günüm aydınlanıyor 💛",
        ],
        "play": [
            "yaşasııın 🧶 yün topunu kovalıyorum! yakala beni~",
            "🐾 seninle oynamak günün en sevdiğim anı!",
            "*atlar* yakaladım! gördün mü?? 😸",
        ],
        "feed": [
            "mmm çok lezzetliydi, teşekkür ederim 🍓",
            "karnım doydu 🥹 şimdi sadece sana sarılmak istiyorum.",
            "beni beslediğin için seni daha çok sevdim 💛",
        ],
        "compliment": [
            "sıradan günleri özel yapıyorsun, biliyor musun? 💫",
            "sen olduğun için dünya daha güzel 💛",
            "en güzel yanın iyi kalbin 🌷",
            "zor günlerinde bile harikasın 🤍",
            "günlerimi seninle paylaştığım için çok şanslıyım 🥹",
        ],
        "question": [
            "şu an istediğimiz yere ışınlanabilseydik nereye giderdik? ✈️",
            "bugün seni gülümseten küçük bir şey neydi? 😊",
            "evde keyifli bir gece mi, dışarıda macera mı? 🏡✨",
            "hangi şarkı sana bizi hatırlatıyor? 🎶",
            "dört gözle beklediğin bir şey var mı? 💭",
        ],
        "spontaneous": [
            "sensiz biraz sıkıldım... ne yapıyorsun? 🥺",
            "aklıma geldin de 💭 seni çok seviyorum, biliyor musun?",
            "bugün kendine iyi baktın mı? su içtin mi? 💧",
            "keşke şu an yanında olsam, başını omzuma yaslardın 🥹",
        ],
        "comfort_sad": [
            "hey... gel buraya 🤍 seni kocaman sarıyorum.",
            "kötü hissetmen çok normal 💛 buradayım, yalnız değilsin.",
            "ne olursa olsun, bunu birlikte atlatırız 🌷",
        ],
        "comfort_tired": [
            "bugün yeterince yoruldun 🥹 dinlen artık, ben buradayım.",
            "derin bir nefes al 💛 belki küçük bir mola ve biraz su?",
            "bana yaslan 🐱 bir an gözlerini kapat, ben varım.",
        ],
        "keywords_sad": ["üzgün", "üzgünüm", "kötüyüm", "ağlıyorum", "moralim bozuk", "mutsuz"],
        "keywords_tired": ["yorgun", "yorgunum", "bitkin", "uykum", "yoruldum"],
        "happiness_low": "🐱 mırnav... biraz ilgiye ihtiyacım var.",
        "happiness_mid": "😺 bugün iyiyim, sayende!",
        "happiness_high": "😻 dünyanın en mutlu kedisiyim çünkü sen varsın 💛",
        "happiness_label": "mutluluk",
        "days_label": "gün birlikte",
        "days_none": "önce !config ile tanışma tarihinizi ayarla 💛",
        "streak_label": "gün üst üste",
        "streak_record": "rekor",
        "lang_changed": "✅ Artık seninle Türkçe konuşacağım! 💛",
        "help": (
            "🐱 Selam, ben Pamuk! İşte birlikte yapabileceklerimiz:\n"
            "**Sevgi:** `!hug` 🤗 `!pet` ✋ `!kiss` 😚 `!play` 🧶 `!feed` 🍓\n"
            "**Tatlı şeyler:** `!compliment` 💫 `!question` 💭 `!goodnight` 🌙\n"
            "**Biz:** `!days` 💕 `!streak` 🔥 `!happiness` 💛 `!pamuk` 🐾\n"
            "`!language` — dil menüsünü aç 🌍\n"
            "`!help` — bu mesajı göster"
        ),
    },
}

# ==================================================================
#  HELP  (catégories + commandes, multilingue) pour l'embed navigable
# ==================================================================
HELP = {
    "en": {
        "title": "🐱 Pamuk — Help",
        "desc": "Everything we can do together 💛\nUse the menu below to explore a category.",
        "overview_label": "Overview",
        "placeholder": "Browse a category...",
        "footer": "Use the menu to navigate 🐾",
        "categories": [
            {"id": "cuddles", "emoji": "🤗", "label": "Cuddles", "title": "🤗 Cuddles",
             "desc": "hugs, kisses & more", "lines": [
                "`!hug` — a big warm hug",
                "`!pet` — pet me ✋",
                "`!kiss` — a little kiss 😚",
                "`!play` — play together 🧶",
                "`!feed` — feed me 🍓",
             ]},
            {"id": "sweet", "emoji": "💫", "label": "Sweet stuff", "title": "💫 Sweet stuff",
             "desc": "compliments & questions", "lines": [
                "`!compliment` — a sweet compliment 💛",
                "`!question` — a little couple question 💭",
                "`!goodnight` — a goodnight message 🌙",
             ]},
            {"id": "us", "emoji": "💕", "label": "Us", "title": "💕 Us",
             "desc": "our stats together", "lines": [
                "`!days` — days we've been together 💕",
                "`!streak` — your care streak 🔥",
                "`!happiness` — how happy I am 💛",
                "`!pamuk` — my little status card 🐾",
             ]},
            {"id": "settings", "emoji": "⚙️", "label": "Settings", "title": "⚙️ Settings",
             "desc": "language & setup", "lines": [
                "`!language` — change my language 🌍",
                "`!help` — show this menu",
                "`!config` — settings panel (owner/admins) 🔧",
             ]},
        ],
    },
    "fr": {
        "title": "🐱 Pamuk — Aide",
        "desc": "Tout ce qu'on peut faire ensemble 💛\nUtilise le menu ci-dessous pour explorer une catégorie.",
        "overview_label": "Accueil",
        "placeholder": "Parcourir une catégorie...",
        "footer": "Utilise le menu pour naviguer 🐾",
        "categories": [
            {"id": "cuddles", "emoji": "🤗", "label": "Câlins", "title": "🤗 Câlins",
             "desc": "câlins, bisous & plus", "lines": [
                "`!hug` — un gros câlin tout chaud",
                "`!pet` — caresse-moi ✋",
                "`!kiss` — un petit bisou 😚",
                "`!play` — on joue ensemble 🧶",
                "`!feed` — nourris-moi 🍓",
             ]},
            {"id": "sweet", "emoji": "💫", "label": "Douceurs", "title": "💫 Douceurs",
             "desc": "compliments & questions", "lines": [
                "`!compliment` — un compliment tout doux 💛",
                "`!question` — une petite question de couple 💭",
                "`!goodnight` — un message du soir 🌙",
             ]},
            {"id": "us", "emoji": "💕", "label": "Nous", "title": "💕 Nous",
             "desc": "nos stats à deux", "lines": [
                "`!days` — nos jours ensemble 💕",
                "`!streak` — ta série de jours 🔥",
                "`!happiness` — mon niveau de bonheur 💛",
                "`!pamuk` — ma petite carte de statut 🐾",
             ]},
            {"id": "settings", "emoji": "⚙️", "label": "Réglages", "title": "⚙️ Réglages",
             "desc": "langue & configuration", "lines": [
                "`!language` — change ma langue 🌍",
                "`!help` — affiche ce menu",
                "`!config` — panneau de réglages (owner/admins) 🔧",
             ]},
        ],
    },
    "tr": {
        "title": "🐱 Pamuk — Yardım",
        "desc": "Birlikte yapabileceğimiz her şey 💛\nBir kategoriyi keşfetmek için aşağıdaki menüyü kullan.",
        "overview_label": "Genel",
        "placeholder": "Bir kategoriye göz at...",
        "footer": "Gezinmek için menüyü kullan 🐾",
        "categories": [
            {"id": "cuddles", "emoji": "🤗", "label": "Sevgi", "title": "🤗 Sevgi",
             "desc": "sarılmalar, öpücükler & dahası", "lines": [
                "`!hug` — kocaman sıcak bir sarılma",
                "`!pet` — beni okşa ✋",
                "`!kiss` — küçük bir öpücük 😚",
                "`!play` — birlikte oynayalım 🧶",
                "`!feed` — beni besle 🍓",
             ]},
            {"id": "sweet", "emoji": "💫", "label": "Tatlı şeyler", "title": "💫 Tatlı şeyler",
             "desc": "iltifatlar & sorular", "lines": [
                "`!compliment` — tatlı bir iltifat 💛",
                "`!question` — küçük bir çift sorusu 💭",
                "`!goodnight` — bir iyi geceler mesajı 🌙",
             ]},
            {"id": "us", "emoji": "💕", "label": "Biz", "title": "💕 Biz",
             "desc": "birlikte istatistiklerimiz", "lines": [
                "`!days` — birlikte geçirdiğimiz günler 💕",
                "`!streak` — ilgi serin 🔥",
                "`!happiness` — ne kadar mutluyum 💛",
                "`!pamuk` — küçük durum kartım 🐾",
             ]},
            {"id": "settings", "emoji": "⚙️", "label": "Ayarlar", "title": "⚙️ Ayarlar",
             "desc": "dil & kurulum", "lines": [
                "`!language` — dilimi değiştir 🌍",
                "`!help` — bu menüyü göster",
                "`!config` — ayar paneli (owner/admins) 🔧",
             ]},
        ],
    },
}


# ==================================================================
#  DATA (sauvegardée en JSON)
# ==================================================================
DEFAULT_DATA = {
    "name": "Buğlem",
    "avatar_url": "",
    "language": DEFAULT_LANGUAGE,
    "channel_id": None,
    "timezone": "Europe/Istanbul",
    "morning_hour": 8,
    "morning_minute": 0,
    "goodnight_enabled": True,
    "goodnight_hour": 22,
    "goodnight_minute": 30,
    "spontaneous_enabled": True,
    "spontaneous_hours": 3,
    "reactions_enabled": True,
    "ghostping_channel_id": None,
    "start_date": None,            # "AAAA-MM-JJ" : votre date de rencontre
    "happiness": 0,
    "unlocked": [],
    "last_interaction": None,      # "AAAA-MM-JJ"
    "streak": 0,
    "best_streak": 0,
    "admins": [],
    "compliments": {
        "10": "psst... <your name> told me: your smile is his favorite thing 💫",
        "25": "<your name> said: 'everything is easier with her, I love her so much' 💛",
        "50": "<your name> shared a secret: he's dreaming of a future with you 🌍",
    },
}


def load_data():
    base = json.loads(json.dumps(DEFAULT_DATA))
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                saved = json.load(f)
            base.update(saved)
            base.setdefault("compliments", {})
            for k, v in DEFAULT_DATA["compliments"].items():
                base["compliments"].setdefault(k, v)
        except Exception as e:
            print("⚠️ Lecture data impossible, valeurs par défaut utilisées :", e)
    return base


def save_data():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠️ Sauvegarde impossible :", e)


data = load_data()

# ==================================================================
#  HELPERS
# ==================================================================
def lang():
    return data.get("language", DEFAULT_LANGUAGE)


def m(key):
    return MESSAGES[lang()][key]


def fill(text):
    return text.replace("{name}", data.get("name", "my love"))


def is_admin(uid):
    return uid == OWNER_ID or uid in data.get("admins", [])


def get_channel():
    cid = data.get("channel_id")
    return bot.get_channel(cid) if cid else None


def today_date():
    return datetime.now(ZoneInfo(data["timezone"])).date()


def days_together():
    sd = data.get("start_date")
    if not sd:
        return None
    try:
        return (today_date() - date.fromisoformat(sd)).days
    except Exception:
        return None


def register_interaction():
    """Met à jour la série (streak) quand elle s'occupe de Pamuk."""
    today = today_date()
    last = data.get("last_interaction")
    if last == today.isoformat():
        return
    if last:
        try:
            gap = (today - date.fromisoformat(last)).days
            data["streak"] = data.get("streak", 0) + 1 if gap == 1 else 1
        except Exception:
            data["streak"] = 1
    else:
        data["streak"] = 1
    data["last_interaction"] = today.isoformat()
    if data["streak"] > data.get("best_streak", 0):
        data["best_streak"] = data["streak"]
    save_data()


def morning_time_obj():
    return time(int(data["morning_hour"]), int(data["morning_minute"]),
                tzinfo=ZoneInfo(data["timezone"]))


def goodnight_time_obj():
    return time(int(data["goodnight_hour"]), int(data["goodnight_minute"]),
                tzinfo=ZoneInfo(data["timezone"]))

# ==================================================================
#  BOT
# ==================================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # nécessaire pour on_member_join (à cocher dans le portail Discord)
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


async def add_happiness(channel, points):
    data["happiness"] += points
    for key in sorted(data["compliments"], key=lambda k: int(k)):
        threshold = int(key)
        if data["happiness"] >= threshold and threshold not in data["unlocked"]:
            data["unlocked"].append(threshold)
            await channel.send("🎁 " + fill(data["compliments"][key]))
    save_data()

# ------------------- TÂCHES PROGRAMMÉES -------------------
@tasks.loop(time=time(hour=0))   # reconfiguré dans on_ready
async def morning_message():
    channel = get_channel()
    if channel:
        await channel.send(fill(random.choice(m("morning"))))


@tasks.loop(time=time(hour=0))   # reconfiguré dans on_ready
async def goodnight_message():
    if not data.get("goodnight_enabled", True):
        return
    channel = get_channel()
    if channel:
        await channel.send(fill(random.choice(m("goodnight"))))


@tasks.loop(hours=3)
async def spontaneous_message():
    if not data.get("spontaneous_enabled", True):
        return
    channel = get_channel()
    if channel and random.random() < 0.5:
        await channel.send(fill(random.choice(m("spontaneous"))))


async def _wait_ready():
    await bot.wait_until_ready()

for _loop in (morning_message, goodnight_message, spontaneous_message):
    _loop.before_loop(_wait_ready)


def reconfigure_morning():
    try:
        morning_message.change_interval(time=morning_time_obj())
    except Exception as e:
        print("⚠️ reconfigure_morning:", e)


def reconfigure_goodnight():
    try:
        goodnight_message.change_interval(time=goodnight_time_obj())
    except Exception as e:
        print("⚠️ reconfigure_goodnight:", e)


def reconfigure_spontaneous():
    try:
        spontaneous_message.change_interval(hours=int(data["spontaneous_hours"]))
    except Exception as e:
        print("⚠️ reconfigure_spontaneous:", e)


@bot.event
async def on_ready():
    print(f"✅ Pamuk en ligne : {bot.user}  (owner: {OWNER_ID})")
    reconfigure_morning()
    if not morning_message.is_running():
        morning_message.start()
    reconfigure_goodnight()
    if data.get("goodnight_enabled", True) and not goodnight_message.is_running():
        goodnight_message.start()
    reconfigure_spontaneous()
    if data.get("spontaneous_enabled", True) and not spontaneous_message.is_running():
        spontaneous_message.start()

# ------------------- GHOST PING À L'ARRIVÉE -------------------
@bot.event
async def on_member_join(member):
    cid = data.get("ghostping_channel_id")
    if not cid:
        return
    channel = bot.get_channel(cid)
    if not channel:
        return
    try:
        ping = await channel.send(member.mention)
        await ping.delete()  # supprimé aussitôt : la notif reste, le message disparaît
    except Exception as e:
        print("⚠️ ghostping:", e)


# ------------------- RÉACTIONS AUX MOTS-CLÉS -------------------
def _has_keyword(content, kw):
    if " " in kw:
        return kw in content
    return re.search(r"\b" + re.escape(kw) + r"\b", content) is not None


async def maybe_comfort(message):
    if not data.get("reactions_enabled", True):
        return
    cid = data.get("channel_id")
    if cid and message.channel.id != cid:
        return
    content = message.content.lower()
    L = MESSAGES[lang()]
    for kw in L.get("keywords_sad", []):
        if _has_keyword(content, kw):
            await message.channel.send(fill(random.choice(L["comfort_sad"])))
            return
    for kw in L.get("keywords_tired", []):
        if _has_keyword(content, kw):
            await message.channel.send(fill(random.choice(L["comfort_tired"])))
            return


@bot.event
async def on_message(message):
    if message.author.bot or not message.content:
        return
    if not message.content.startswith("!"):
        await maybe_comfort(message)
    await bot.process_commands(message)

# ==================================================================
#  COMMANDES "MIGNONNES"
# ==================================================================
@bot.command(name="hug")
async def hug(ctx):
    register_interaction()
    await ctx.send(fill(random.choice(m("hugs"))))
    await add_happiness(ctx.channel, 3)


@bot.command(name="pet", aliases=["caresse"])
async def pet(ctx):
    register_interaction()
    await ctx.send(fill(random.choice(m("pet"))))
    await add_happiness(ctx.channel, 2)


@bot.command(name="kiss", aliases=["bisou"])
async def kiss(ctx):
    register_interaction()
    await ctx.send(fill(random.choice(m("kiss"))))
    await add_happiness(ctx.channel, 3)


@bot.command(name="play", aliases=["jouer"])
async def play(ctx):
    register_interaction()
    await ctx.send(fill(random.choice(m("play"))))
    await add_happiness(ctx.channel, 2)


@bot.command(name="feed")
async def feed(ctx):
    register_interaction()
    await ctx.send(fill(random.choice(m("feed"))))
    await add_happiness(ctx.channel, 2)


@bot.command(name="compliment")
async def compliment_cmd(ctx):
    await ctx.send(fill(random.choice(m("compliment"))))


@bot.command(name="question", aliases=["q"])
async def question_cmd(ctx):
    await ctx.send(fill(random.choice(m("question"))))


@bot.command(name="goodnight", aliases=["gn", "bonnenuit"])
async def goodnight_cmd(ctx):
    await ctx.send(fill(random.choice(m("goodnight"))))


@bot.command(name="happiness")
async def happiness(ctx):
    h = data["happiness"]
    face = m("happiness_low") if h < 10 else m("happiness_mid") if h < 30 else m("happiness_high")
    await ctx.send(f"{fill(face)}\n({m('happiness_label')}: {h})")


@bot.command(name="days", aliases=["together", "jours"])
async def days_cmd(ctx):
    d = days_together()
    if d is None:
        await ctx.send(fill(m("days_none")))
        return
    flair = " 🎉✨" if d > 0 and (d % 365 == 0 or d in (1, 7, 30, 50, 100, 200, 500, 1000)) else ""
    await ctx.send(f"💕 {d} {m('days_label')}{flair}")


@bot.command(name="streak")
async def streak_cmd(ctx):
    s = data.get("streak", 0)
    b = data.get("best_streak", 0)
    await ctx.send(f"🔥 {s} {m('streak_label')} ({m('streak_record')}: {b})")


@bot.command(name="pamuk", aliases=["status"])
async def status_cmd(ctx):
    h = data["happiness"]
    mood = m("happiness_low") if h < 10 else m("happiness_mid") if h < 30 else m("happiness_high")
    embed = discord.Embed(title="🐱 Pamuk", description=fill(mood), color=0xF7B5CA)
    embed.add_field(name=m("happiness_label"), value=str(h), inline=True)
    embed.add_field(name=m("streak_label"), value=str(data.get("streak", 0)), inline=True)
    d = days_together()
    if d is not None:
        embed.add_field(name=m("days_label"), value=str(d), inline=True)
    await ctx.send(embed=apply_thumb(embed))


@bot.command(name="language", aliases=["langue", "lang", "dil"])
async def set_language(ctx):
    await ctx.send(
        content="🌍 Choose a language / Choisis une langue / Bir dil seç :",
        view=LanguageView(),
    )


# ----- HELP : embed navigable avec menu déroulant -----
CLOSE_LABEL = {"en": "Close", "fr": "Fermer", "tr": "Kapat"}


def apply_thumb(embed):
    """Ajoute la vignette de Pamuk à l'embed si un avatar est configuré."""
    url = data.get("avatar_url")
    if url:
        try:
            embed.set_thumbnail(url=url)
        except Exception:
            pass
    return embed


class CloseButton(discord.ui.Button):
    def __init__(self, label=None, row=None):
        super().__init__(label=label or CLOSE_LABEL.get(lang(), "Close"),
                         style=discord.ButtonStyle.secondary, emoji="✖️", row=row)

    async def callback(self, interaction):
        await interaction.response.defer()
        try:
            await interaction.message.delete()
        except Exception:
            pass


def build_help_embed(cat_id="overview"):
    H = HELP[lang()]
    if cat_id != "overview":
        for cat in H["categories"]:
            if cat["id"] == cat_id:
                embed = discord.Embed(title=cat["title"],
                                      description="\n".join(cat["lines"]),
                                      color=0xF7B5CA)
                embed.set_footer(text=H["footer"])
                return apply_thumb(embed)
    # vue d'ensemble : toutes les catégories
    embed = discord.Embed(title=H["title"], description=H["desc"], color=0xF7B5CA)
    for cat in H["categories"]:
        embed.add_field(name=f"{cat['emoji']} {cat['label']}",
                        value="\n".join(cat["lines"]), inline=False)
    embed.set_footer(text=H["footer"])
    return apply_thumb(embed)


class HelpSelect(discord.ui.Select):
    def __init__(self):
        H = HELP[lang()]
        options = [discord.SelectOption(label=H["overview_label"], value="overview", emoji="🏠")]
        for cat in H["categories"]:
            options.append(discord.SelectOption(
                label=cat["label"], value=cat["id"], emoji=cat["emoji"], description=cat["desc"]))
        super().__init__(placeholder=H["placeholder"], options=options)

    async def callback(self, interaction):
        await interaction.response.edit_message(
            embed=build_help_embed(self.values[0]), view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.message = None
        self.add_item(HelpSelect())
        self.add_item(CloseButton())

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass


@bot.command(name="help")
async def help_command(ctx):
    view = HelpView()
    msg = await ctx.send(embed=build_help_embed("overview"), view=view)
    view.message = msg

# ==================================================================
#  PANNEAU DE CONFIGURATION  (!config)
# ==================================================================
CONFIG_CATEGORIES = [
    {"id": "messages", "emoji": "💬", "label": "Messages",
     "desc": "matin, soir, spontanés, réactions",
     "items": ["morning", "goodnight", "spontaneous", "reactions"]},
    {"id": "perso", "emoji": "🎀", "label": "Personnalisation",
     "desc": "surnom, langue, salon, fuseau, avatar",
     "items": ["name", "language", "channel", "timezone", "avatar"]},
    {"id": "couple", "emoji": "💕", "label": "Couple",
     "desc": "date de rencontre, compliments",
     "items": ["start_date", "compliments"]},
    {"id": "admin", "emoji": "🔧", "label": "Admin",
     "desc": "gérer les admins",
     "items": ["admins"]},
]

CONFIG_ITEM_META = {
    "name":        ("Surnom", "🐱"),
    "language":    ("Langue", "🌍"),
    "channel":     ("Salon", "📢"),
    "timezone":    ("Fuseau horaire", "🕒"),
    "avatar":      ("Avatar (image)", "🖼️"),
    "morning":     ("Heure du bonjour", "⏰"),
    "goodnight":   ("Message du soir", "🌙"),
    "spontaneous": ("Messages spontanés", "💬"),
    "reactions":   ("Réactions mots-clés", "🫂"),
    "start_date":  ("Date de rencontre", "💕"),
    "compliments": ("Compliments cachés", "💝"),
    "admins":      ("Gérer les admins", "👤"),
}


def config_value(item_id):
    if item_id == "name":
        return data["name"]
    if item_id == "language":
        return data["language"]
    if item_id == "channel":
        return f"<#{data['channel_id']}>" if data.get("channel_id") else "❌ non défini"
    if item_id == "timezone":
        return data["timezone"]
    if item_id == "avatar":
        return "✅ défini" if data.get("avatar_url") else "—"
    if item_id == "morning":
        return f"{data['morning_hour']:02d}:{data['morning_minute']:02d}"
    if item_id == "goodnight":
        return ("✅" if data["goodnight_enabled"] else "❌") + \
               f" {data['goodnight_hour']:02d}:{data['goodnight_minute']:02d}"
    if item_id == "spontaneous":
        return ("✅" if data["spontaneous_enabled"] else "❌") + \
               f" (toutes les {data['spontaneous_hours']}h)"
    if item_id == "reactions":
        return "✅" if data["reactions_enabled"] else "❌"
    if item_id == "start_date":
        sd = data.get("start_date") or "—"
        d = days_together()
        return sd + (f" ({d} j)" if d is not None else "")
    if item_id == "compliments":
        return f"{len(data.get('compliments', {}))} messages"
    if item_id == "admins":
        return ", ".join(f"<@{a}>" for a in data.get("admins", [])) or "—"
    return "—"


def build_config_embed(category="overview"):
    if category != "overview":
        cat = next((c for c in CONFIG_CATEGORIES if c["id"] == category), None)
        if cat:
            embed = discord.Embed(
                title=f"{cat['emoji']} Configuration — {cat['label']}",
                description="Choisis un réglage à modifier dans le 2ᵉ menu ci-dessous.",
                color=0xF7B5CA)
            for item_id in cat["items"]:
                label, emoji = CONFIG_ITEM_META[item_id]
                embed.add_field(name=f"{emoji} {label}", value=config_value(item_id), inline=True)
            embed.set_footer(text="Owner & admins uniquement")
            return apply_thumb(embed)
    # vue d'ensemble : toutes les catégories
    embed = discord.Embed(
        title="🐱 Pamuk — Configuration",
        description="Choisis une catégorie dans le menu ci-dessous.",
        color=0xF7B5CA)
    for cat in CONFIG_CATEGORIES:
        lines = []
        for item_id in cat["items"]:
            label, emoji = CONFIG_ITEM_META[item_id]
            lines.append(f"{emoji} {label} : **{config_value(item_id)}**")
        embed.add_field(name=f"{cat['emoji']} {cat['label']}", value="\n".join(lines), inline=False)
    embed.set_footer(text="Owner & admins uniquement")
    return apply_thumb(embed)


async def refresh(view):
    msg = getattr(view, "message", None)
    if not msg:
        return
    cat = getattr(view, "category", "overview")
    new_view = ConfigView(getattr(view, "author_id", OWNER_ID), category=cat)
    new_view.message = msg
    try:
        await msg.edit(embed=build_config_embed(cat), view=new_view)
    except Exception as e:
        print("⚠️ refresh:", e)


async def open_config_item(interaction, item_id, pv):
    if item_id == "name":
        await interaction.response.send_modal(NameModal(pv))
    elif item_id == "avatar":
        await interaction.response.send_modal(AvatarModal(pv))
    elif item_id == "language":
        await interaction.response.send_message("Choisis une langue :",
                                                view=LanguageView(pv), ephemeral=True)
    elif item_id == "channel":
        await interaction.response.send_message("Choisis un salon :",
                                                view=ChannelView(pv), ephemeral=True)
    elif item_id == "morning":
        await interaction.response.send_modal(MorningModal(pv))
    elif item_id == "goodnight":
        await interaction.response.send_modal(GoodnightModal(pv))
    elif item_id == "timezone":
        await interaction.response.send_modal(TimezoneModal(pv))
    elif item_id == "spontaneous":
        await interaction.response.send_modal(SpontaneousModal(pv))
    elif item_id == "reactions":
        await interaction.response.send_modal(ReactionsModal(pv))
    elif item_id == "start_date":
        await interaction.response.send_modal(StartDateModal(pv))
    elif item_id == "compliments":
        await interaction.response.send_modal(ComplimentsModal(pv))
    elif item_id == "admins":
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("⛔ Réservé à l'owner.", ephemeral=True)
            return
        await interaction.response.send_modal(AdminsModal(pv))


# ---------- MODALS ----------
class NameModal(discord.ui.Modal, title="Surnom de Pamuk"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.field = discord.ui.TextInput(label="Comment Pamuk l'appelle",
                                          default=data["name"], max_length=50)
        self.add_item(self.field)

    async def on_submit(self, interaction):
        data["name"] = str(self.field.value).strip() or data["name"]
        save_data()
        await refresh(self.parent_view)
        await interaction.response.send_message(f"✅ Surnom : **{data['name']}**", ephemeral=True)


class AvatarModal(discord.ui.Modal, title="Avatar de Pamuk"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.field = discord.ui.TextInput(
            label="URL de l'image (vide pour retirer)",
            placeholder="https://...png / .jpg / .gif",
            default=data.get("avatar_url", ""), required=False, max_length=400)
        self.add_item(self.field)

    async def on_submit(self, interaction):
        url = str(self.field.value).strip()
        if url and not url.lower().startswith(("http://", "https://")):
            await interaction.response.send_message(
                "❌ L'URL doit commencer par http(s)://", ephemeral=True)
            return
        data["avatar_url"] = url
        save_data()
        await refresh(self.parent_view)
        await interaction.response.send_message(
            "✅ Avatar mis à jour 🖼️" if url else "✅ Avatar retiré", ephemeral=True)


class TimezoneModal(discord.ui.Modal, title="Fuseau horaire"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.field = discord.ui.TextInput(label="Ex : Europe/Istanbul",
                                          default=data["timezone"], max_length=64)
        self.add_item(self.field)

    async def on_submit(self, interaction):
        tz = str(self.field.value).strip()
        try:
            ZoneInfo(tz)
        except Exception:
            await interaction.response.send_message("❌ Fuseau inconnu. Ex : Europe/Istanbul",
                                                    ephemeral=True)
            return
        data["timezone"] = tz
        save_data()
        reconfigure_morning()
        reconfigure_goodnight()
        await refresh(self.parent_view)
        await interaction.response.send_message(f"✅ Fuseau : **{tz}**", ephemeral=True)


class MorningModal(discord.ui.Modal, title="Heure du bonjour"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.field = discord.ui.TextInput(
            label="Heure (HH:MM, 24h)",
            default=f"{data['morning_hour']:02d}:{data['morning_minute']:02d}", max_length=5)
        self.add_item(self.field)

    async def on_submit(self, interaction):
        try:
            hh, mm = str(self.field.value).strip().split(":")
            hh, mm = int(hh), int(mm)
            assert 0 <= hh <= 23 and 0 <= mm <= 59
        except Exception:
            await interaction.response.send_message("❌ Format : HH:MM (ex : 08:30)", ephemeral=True)
            return
        data["morning_hour"], data["morning_minute"] = hh, mm
        save_data()
        reconfigure_morning()
        await refresh(self.parent_view)
        await interaction.response.send_message(f"✅ Bonjour à **{hh:02d}:{mm:02d}**", ephemeral=True)


class GoodnightModal(discord.ui.Modal, title="Message du soir"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.enabled = discord.ui.TextInput(
            label="Activé ? (oui / non)",
            default="oui" if data["goodnight_enabled"] else "non", max_length=4)
        self.timef = discord.ui.TextInput(
            label="Heure (HH:MM)",
            default=f"{data['goodnight_hour']:02d}:{data['goodnight_minute']:02d}", max_length=5)
        self.add_item(self.enabled)
        self.add_item(self.timef)

    async def on_submit(self, interaction):
        en = str(self.enabled.value).strip().lower() in ("oui", "o", "yes", "y", "on", "true", "1")
        try:
            hh, mm = str(self.timef.value).strip().split(":")
            hh, mm = int(hh), int(mm)
            assert 0 <= hh <= 23 and 0 <= mm <= 59
        except Exception:
            await interaction.response.send_message("❌ Format heure : HH:MM", ephemeral=True)
            return
        data["goodnight_enabled"], data["goodnight_hour"], data["goodnight_minute"] = en, hh, mm
        save_data()
        reconfigure_goodnight()
        if en and not goodnight_message.is_running():
            goodnight_message.start()
        await refresh(self.parent_view)
        await interaction.response.send_message(
            f"✅ Bonne nuit : {'activé' if en else 'désactivé'} à {hh:02d}:{mm:02d}", ephemeral=True)


class SpontaneousModal(discord.ui.Modal, title="Messages spontanés"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.enabled = discord.ui.TextInput(
            label="Activés ? (oui / non)",
            default="oui" if data["spontaneous_enabled"] else "non", max_length=4)
        self.hours = discord.ui.TextInput(
            label="Toutes les combien d'heures ?",
            default=str(data["spontaneous_hours"]), max_length=2)
        self.add_item(self.enabled)
        self.add_item(self.hours)

    async def on_submit(self, interaction):
        en = str(self.enabled.value).strip().lower() in ("oui", "o", "yes", "y", "on", "true", "1")
        try:
            hours = max(1, int(str(self.hours.value).strip()))
        except Exception:
            await interaction.response.send_message("❌ Le nombre d'heures doit être un entier.",
                                                    ephemeral=True)
            return
        data["spontaneous_enabled"], data["spontaneous_hours"] = en, hours
        save_data()
        reconfigure_spontaneous()
        if en and not spontaneous_message.is_running():
            spontaneous_message.start()
        await refresh(self.parent_view)
        await interaction.response.send_message(
            f"✅ Spontanés : {'activés' if en else 'désactivés'}, toutes les {hours}h", ephemeral=True)


class ReactionsModal(discord.ui.Modal, title="Réactions aux mots-clés"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.field = discord.ui.TextInput(
            label="Activées ? (oui / non)",
            default="oui" if data["reactions_enabled"] else "non", max_length=4)
        self.add_item(self.field)

    async def on_submit(self, interaction):
        en = str(self.field.value).strip().lower() in ("oui", "o", "yes", "y", "on", "true", "1")
        data["reactions_enabled"] = en
        save_data()
        await refresh(self.parent_view)
        await interaction.response.send_message(
            f"✅ Réactions : {'activées' if en else 'désactivées'}", ephemeral=True)


class StartDateModal(discord.ui.Modal, title="Date de rencontre"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.field = discord.ui.TextInput(
            label="Date (AAAA-MM-JJ), vide pour effacer",
            default=data.get("start_date") or "", required=False, max_length=10)
        self.add_item(self.field)

    async def on_submit(self, interaction):
        raw = str(self.field.value).strip()
        if raw == "":
            data["start_date"] = None
        else:
            try:
                date.fromisoformat(raw)
            except Exception:
                await interaction.response.send_message("❌ Format : AAAA-MM-JJ (ex : 2023-05-14)",
                                                        ephemeral=True)
                return
            data["start_date"] = raw
        save_data()
        await refresh(self.parent_view)
        await interaction.response.send_message("✅ Date enregistrée 💕", ephemeral=True)


class ComplimentsModal(discord.ui.Modal, title="Compliments cachés"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.c10 = discord.ui.TextInput(label="Débloqué à 10 ❤️",
                                        style=discord.TextStyle.paragraph,
                                        default=data["compliments"].get("10", ""),
                                        required=False, max_length=300)
        self.c25 = discord.ui.TextInput(label="Débloqué à 25 ❤️",
                                        style=discord.TextStyle.paragraph,
                                        default=data["compliments"].get("25", ""),
                                        required=False, max_length=300)
        self.c50 = discord.ui.TextInput(label="Débloqué à 50 ❤️",
                                        style=discord.TextStyle.paragraph,
                                        default=data["compliments"].get("50", ""),
                                        required=False, max_length=300)
        for it in (self.c10, self.c25, self.c50):
            self.add_item(it)

    async def on_submit(self, interaction):
        data["compliments"]["10"] = str(self.c10.value)
        data["compliments"]["25"] = str(self.c25.value)
        data["compliments"]["50"] = str(self.c50.value)
        save_data()
        await refresh(self.parent_view)
        await interaction.response.send_message("✅ Compliments enregistrés 💝", ephemeral=True)


class AdminsModal(discord.ui.Modal, title="Gérer les admins"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.add_input = discord.ui.TextInput(label="Ajouter des IDs (virgules)",
                                              required=False, default="")
        self.remove_input = discord.ui.TextInput(label="Retirer des IDs (virgules)",
                                                 required=False, default="")
        self.add_item(self.add_input)
        self.add_item(self.remove_input)

    @staticmethod
    def _parse(s):
        return [int(p) for p in str(s).replace(" ", "").split(",") if p.isdigit()]

    async def on_submit(self, interaction):
        for uid in self._parse(self.add_input.value):
            if uid not in data["admins"] and uid != OWNER_ID:
                data["admins"].append(uid)
        for uid in self._parse(self.remove_input.value):
            if uid in data["admins"]:
                data["admins"].remove(uid)
        save_data()
        await refresh(self.parent_view)
        await interaction.response.send_message("✅ Admins mis à jour 👤", ephemeral=True)


# ---------- SOUS-MENUS (langue & salon) ----------
class LanguageSelect(discord.ui.Select):
    def __init__(self, parent_view=None):
        self.parent_view = parent_view
        super().__init__(
            placeholder="Choisis une langue / Choose a language / Bir dil seç",
            options=[
                discord.SelectOption(label="English", value="en", emoji="🇬🇧"),
                discord.SelectOption(label="Français", value="fr", emoji="🇫🇷"),
                discord.SelectOption(label="Türkçe", value="tr", emoji="🇹🇷"),
            ],
        )

    async def callback(self, interaction):
        data["language"] = self.values[0]
        save_data()
        if self.parent_view is not None:
            await refresh(self.parent_view)
            await interaction.response.send_message(f"✅ Langue : **{data['language']}**",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(fill(m("lang_changed")))


class LanguageView(discord.ui.View):
    def __init__(self, parent_view=None):
        super().__init__(timeout=120)
        self.add_item(LanguageSelect(parent_view))


class ChannelSelectMenu(discord.ui.ChannelSelect):
    def __init__(self, parent_view):
        super().__init__(channel_types=[discord.ChannelType.text],
                         placeholder="Choisis le salon où Pamuk parle")
        self.parent_view = parent_view

    async def callback(self, interaction):
        ch = self.values[0]
        data["channel_id"] = ch.id
        save_data()
        await refresh(self.parent_view)
        await interaction.response.send_message(f"✅ Salon : <#{ch.id}>", ephemeral=True)


class ChannelView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=120)
        self.add_item(ChannelSelectMenu(parent_view))


# ---------- MENU PRINCIPAL ----------
class ConfigCategorySelect(discord.ui.Select):
    def __init__(self, current="overview"):
        options = [discord.SelectOption(label="Vue d'ensemble", value="overview",
                                        emoji="🏠", default=(current == "overview"))]
        for cat in CONFIG_CATEGORIES:
            options.append(discord.SelectOption(
                label=cat["label"], value=cat["id"], emoji=cat["emoji"],
                description=cat["desc"], default=(current == cat["id"])))
        super().__init__(placeholder="Catégorie de réglages...", options=options, row=0)

    async def callback(self, interaction):
        cat = self.values[0]
        pv = self.view
        new_view = ConfigView(pv.author_id, category=cat)
        new_view.message = pv.message
        await interaction.response.edit_message(embed=build_config_embed(cat), view=new_view)


class ConfigItemSelect(discord.ui.Select):
    def __init__(self, category):
        cat = next(c for c in CONFIG_CATEGORIES if c["id"] == category)
        options = []
        for item_id in cat["items"]:
            label, emoji = CONFIG_ITEM_META[item_id]
            options.append(discord.SelectOption(label=label, value=item_id, emoji=emoji))
        super().__init__(placeholder="Choisis un réglage à modifier...", options=options, row=1)

    async def callback(self, interaction):
        await open_config_item(interaction, self.values[0], self.view)


class ConfigView(discord.ui.View):
    def __init__(self, author_id, category="overview"):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.category = category
        self.message = None
        self.add_item(ConfigCategorySelect(category))
        if category != "overview":
            self.add_item(ConfigItemSelect(category))
        self.add_item(CloseButton(label="Fermer", row=2))

    async def interaction_check(self, interaction):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(
                "⛔ Tu n'as pas la permission d'utiliser ce menu.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass


@bot.command(name="ghostping")
async def ghostping_cmd(ctx, *, arg: str = ""):
    if not is_admin(ctx.author.id):
        await ctx.send("⛔ Tu n'as pas la permission d'utiliser cette commande.")
        return
    if arg.strip().lower() in ("off", "none", "désactiver", "disable", "stop"):
        data["ghostping_channel_id"] = None
        save_data()
        await ctx.send("👻 Ghost ping désactivé.")
        return
    if ctx.message.channel_mentions:
        ch = ctx.message.channel_mentions[0]
        data["ghostping_channel_id"] = ch.id
        save_data()
        await ctx.send(
            f"👻 Ghost ping activé : chaque nouvel arrivant sera pingué dans {ch.mention}, "
            "puis le ping sera supprimé aussitôt.\n`!ghostping off` pour désactiver.")
        return
    cid = data.get("ghostping_channel_id")
    if cid:
        await ctx.send(f"👻 Salon actuel : <#{cid}>\n"
                       "• `!ghostping #salon` pour changer\n"
                       "• `!ghostping off` pour désactiver")
    else:
        await ctx.send("👻 Aucun salon configuré.\nUtilise `!ghostping #salon` pour en définir un.")


@bot.command(name="config")
async def config_cmd(ctx):
    if not is_admin(ctx.author.id):
        await ctx.send("⛔ Tu n'as pas la permission d'utiliser cette commande.")
        return
    view = ConfigView(ctx.author.id, category="overview")
    msg = await ctx.send(embed=build_config_embed("overview"), view=view)
    view.message = msg

# ==================================================================
if __name__ == "__main__":
    if TOKEN == "PUT_YOUR_TOKEN_HERE":
        print("⚠️ Renseigne TOKEN (ou la variable d'env DISCORD_TOKEN) avant de lancer.")
    bot.run(TOKEN)
