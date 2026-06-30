# -*- coding: utf-8 -*-
"""
🐱 PAMUK — petit compagnon virtuel (version hébergeable + panneau !config)
==========================================================================

Pamuk vit dans le Discord de ta copine : il dit bonjour le matin, il s'ennuie
d'elle dans la journée, elle peut le câliner / le nourrir, et plus elle s'occupe
de lui, plus il débloque des compliments cachés que TOI tu as écrits.

COMMANDES (toujours en anglais) :
    !hug         -> câlin
    !feed        -> nourrir
    !happiness   -> niveau de bonheur
    !language    -> en / fr / tr (elle change la langue parlée par Pamuk)
    !help        -> aide (en/fr/tr selon la langue choisie)
    !config      -> PANNEAU DE CONFIG (owner/admins seulement) : ouvre un menu
                    déroulant pour tout régler sans toucher au code.

Le bot parle ANGLAIS par défaut ; les commandes restent en anglais, mais Pamuk
répond dans la langue choisie.

------------------------------------------------------------------
HÉBERGEMENT (Railway / VPS)
------------------------------------------------------------------
- pip install -r requirements.txt
- Renseigne TOKEN et OWNER_ID ci-dessous (ou via variables d'environnement
  DISCORD_TOKEN / OWNER_ID -> recommandé sur Railway pour ne pas exposer le token).
- La data est sauvée dans  DATA_DIR/pamuk_data.json  (DATA_DIR = "." par défaut).
  Sur Railway, ajoute un VOLUME monté sur /data et mets la variable DATA_DIR=/data,
  sinon les réglages sont perdus à chaque redéploiement.
- Start command : python pamuk_bot.py   (cf. Procfile fourni)
------------------------------------------------------------------
"""

import os
import json
import random
from datetime import time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

# ==================================================================
#  CONFIG EN DUR  (surchargée par variables d'env si présentes)
# ==================================================================
TOKEN = os.getenv("DISCORD_TOKEN", "PUT_YOUR_TOKEN_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", "142365250803466240"))  # ton ID Discord
DEFAULT_LANGUAGE = "en"

# Dossier de sauvegarde (mets DATA_DIR=/data sur Railway avec un volume)
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
        "hugs": [
            "mmm 🥰 I'm hugging you so tight, I don't want to let go.",
            "I'm so glad you're here 💛 everything feels better when I hug you.",
            "meow 🐱 there... my heart is pounding.",
        ],
        "feed": [
            "mmm that was delicious, thank you 🍓",
            "my tummy's full 🥹 now I just want to cuddle you.",
            "I love you even more for feeding me 💛",
        ],
        "spontaneous": [
            "I'm a little bored without you... what are you up to? 🥺",
            "you just crossed my mind 💭 I love you so much, you know?",
            "did you take care of yourself today? did you drink water? 💧",
            "I wish I were next to you right now, you'd rest your head on my shoulder 🥹",
        ],
        "happiness_low": "🐱 meow... I could use a little attention.",
        "happiness_mid": "😺 I'm doing good today, thanks to you!",
        "happiness_high": "😻 I'm the happiest cat in the world because you're here 💛",
        "happiness_label": "happiness",
        "lang_changed": "✅ I'll talk to you in English now! 💛",
        "lang_invalid": "I only speak `en`, `fr` and `tr` 🥺  try `!language tr`",
        "help": (
            "🐱 Hi, I'm Pamuk! Here's what we can do together:\n"
            "`!hug` — give me a hug 🤗\n"
            "`!feed` — feed me 🍓\n"
            "`!happiness` — see how happy I am 💛\n"
            "`!language` — open the language menu 🌍\n"
            "`!help` — show this message\n"
            "_The commands stay in English, but I'll talk to you in your language!_"
        ),
    },
    "fr": {
        "morning": [
            "*bâille* ...bonjour {name} 🌙 j'ai rêvé de toi toute la nuit.",
            "bonjour mon unique ☀️ dès le réveil j'ai pensé à toi.",
            "miaou~ bonjour 💛 j'aurais aimé me réveiller à tes côtés aujourd'hui aussi.",
        ],
        "hugs": [
            "mmm 🥰 je te serre très fort, je ne veux pas te lâcher.",
            "heureusement que tu es là 💛 tout est plus beau quand je te fais un câlin.",
            "miaou 🐱 voilà... mon cœur bat fort.",
        ],
        "feed": [
            "mmm c'était délicieux, merci 🍓",
            "j'ai le ventre plein 🥹 maintenant je veux juste te faire un câlin.",
            "je t'aime encore plus de m'avoir nourri 💛",
        ],
        "spontaneous": [
            "je m'ennuie un peu sans toi... tu fais quoi ? 🥺",
            "tu m'es venue à l'esprit 💭 je t'aime très fort, tu sais ?",
            "tu as pris soin de toi aujourd'hui ? tu as bu de l'eau ? 💧",
            "j'aimerais être près de toi là, tu poserais ta tête sur mon épaule 🥹",
        ],
        "happiness_low": "🐱 miaou... j'aurais besoin d'un peu d'attention.",
        "happiness_mid": "😺 je vais bien aujourd'hui, grâce à toi !",
        "happiness_high": "😻 je suis le chat le plus heureux du monde parce que tu es là 💛",
        "happiness_label": "bonheur",
        "lang_changed": "✅ Je te parlerai en français maintenant ! 💛",
        "lang_invalid": "je parle seulement `en`, `fr` et `tr` 🥺  essaie `!language tr`",
        "help": (
            "🐱 Coucou, c'est Pamuk ! Voilà ce qu'on peut faire ensemble :\n"
            "`!hug` — fais-moi un câlin 🤗\n"
            "`!feed` — nourris-moi 🍓\n"
            "`!happiness` — vois à quel point je suis heureux 💛\n"
            "`!language` — ouvre le menu des langues 🌍\n"
            "`!help` — affiche ce message\n"
            "_Les commandes restent en anglais, mais je te parlerai dans ta langue !_"
        ),
    },
    "tr": {
        "morning": [
            "*esner* ...günaydın {name} 🌙 bütün gece seni rüyamda gördüm.",
            "günaydın bir tanem ☀️ gözümü açar açmaz aklıma sen geldin.",
            "mırnav~ günaydın 💛 bugün de senin yanında uyanmak isterdim.",
        ],
        "hugs": [
            "mmm 🥰 sana sımsıkı sarılıyorum, bırakmak istemiyorum.",
            "iyi ki varsın 💛 sana sarılınca her şey daha güzel.",
            "mırnav 🐱 işte böyle... kalbim küt küt atıyor.",
        ],
        "feed": [
            "mmm çok lezzetliydi, teşekkür ederim 🍓",
            "karnım doydu 🥹 şimdi sadece sana sarılmak istiyorum.",
            "beni beslediğin için seni daha çok sevdim 💛",
        ],
        "spontaneous": [
            "sensiz biraz sıkıldım... ne yapıyorsun? 🥺",
            "aklıma geldin de 💭 seni çok seviyorum, biliyor musun?",
            "bugün kendine iyi baktın mı? su içtin mi? 💧",
            "keşke şu an yanında olsam, başını omzuma yaslardın 🥹",
        ],
        "happiness_low": "🐱 mırnav... biraz ilgiye ihtiyacım var.",
        "happiness_mid": "😺 bugün iyiyim, sayende!",
        "happiness_high": "😻 dünyanın en mutlu kedisiyim çünkü sen varsın 💛",
        "happiness_label": "mutluluk",
        "lang_changed": "✅ Artık seninle Türkçe konuşacağım! 💛",
        "lang_invalid": "sadece `en`, `fr` ve `tr` biliyorum 🥺  `!language tr` dene",
        "help": (
            "🐱 Selam, ben Pamuk! Birlikte neler yapabiliriz:\n"
            "`!hug` — bana sarıl 🤗\n"
            "`!feed` — beni besle 🍓\n"
            "`!happiness` — ne kadar mutlu olduğumu gör 💛\n"
            "`!language` — dil menüsünü aç 🌍\n"
            "`!help` — bu mesajı göster\n"
            "_Komutlar İngilizce kalır ama seninle senin dilinde konuşurum!_"
        ),
    },
}

# ==================================================================
#  DATA (sauvegardée en JSON)
# ==================================================================
DEFAULT_DATA = {
    "name": "my love",
    "language": DEFAULT_LANGUAGE,
    "channel_id": None,
    "morning_hour": 8,
    "morning_minute": 0,
    "timezone": "Europe/Istanbul",
    "spontaneous_enabled": True,
    "spontaneous_hours": 3,
    "happiness": 0,
    "unlocked": [],
    "admins": [],
    "compliments": {
        "10": "psst... <your name> told me: your smile is his favorite thing 💫",
        "25": "<your name> said: 'everything is easier with her, I love her so much' 💛",
        "50": "<your name> shared a secret: he's dreaming of a future with you 🌍",
    },
}


def load_data():
    base = json.loads(json.dumps(DEFAULT_DATA))  # copie profonde
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


def morning_time_obj():
    return time(
        hour=int(data["morning_hour"]),
        minute=int(data["morning_minute"]),
        tzinfo=ZoneInfo(data["timezone"]),
    )

# ==================================================================
#  BOT
# ==================================================================
intents = discord.Intents.default()
intents.message_content = True
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
@tasks.loop(time=time(hour=0))  # reconfiguré dans on_ready
async def morning_message():
    channel = get_channel()
    if channel:
        await channel.send(fill(random.choice(m("morning"))))


@tasks.loop(hours=3)
async def spontaneous_message():
    if not data.get("spontaneous_enabled", True):
        return
    channel = get_channel()
    if channel and random.random() < 0.5:
        await channel.send(fill(random.choice(m("spontaneous"))))


async def _wait_ready():
    await bot.wait_until_ready()

morning_message.before_loop(_wait_ready)
spontaneous_message.before_loop(_wait_ready)


def reconfigure_morning():
    try:
        morning_message.change_interval(time=morning_time_obj())
    except Exception as e:
        print("⚠️ reconfigure_morning:", e)


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
    reconfigure_spontaneous()
    if data.get("spontaneous_enabled", True) and not spontaneous_message.is_running():
        spontaneous_message.start()

# ==================================================================
#  COMMANDES "MIGNONNES"
# ==================================================================
@bot.command(name="hug")
async def hug(ctx):
    await ctx.send(fill(random.choice(m("hugs"))))
    await add_happiness(ctx.channel, 3)


@bot.command(name="feed")
async def feed(ctx):
    await ctx.send(fill(random.choice(m("feed"))))
    await add_happiness(ctx.channel, 2)


@bot.command(name="happiness")
async def happiness(ctx):
    h = data["happiness"]
    if h < 10:
        face = m("happiness_low")
    elif h < 30:
        face = m("happiness_mid")
    else:
        face = m("happiness_high")
    await ctx.send(f"{fill(face)}\n({m('happiness_label')}: {h})")


@bot.command(name="language", aliases=["langue", "lang", "dil"])
async def set_language(ctx):
    await ctx.send(
        content="🌍 Choose a language / Choisis une langue / Bir dil seç :",
        view=LanguageView(),
    )


@bot.command(name="help")
async def help_command(ctx):
    await ctx.send(fill(m("help")))

# ==================================================================
#  PANNEAU DE CONFIGURATION  (!config)
# ==================================================================
def build_config_embed():
    ch = f"<#{data['channel_id']}>" if data.get("channel_id") else "❌ non défini"
    sp = ("✅ activé" if data["spontaneous_enabled"] else "❌ désactivé") + \
         f" (toutes les {data['spontaneous_hours']}h)"
    admins = ", ".join(f"<@{a}>" for a in data.get("admins", [])) or "—"
    embed = discord.Embed(
        title="🐱 Pamuk — Configuration",
        description="Choisis un réglage dans le menu ci-dessous.",
        color=0xF7B5CA,
    )
    embed.add_field(name="Surnom", value=data["name"], inline=True)
    embed.add_field(name="Langue", value=data["language"], inline=True)
    embed.add_field(name="Salon", value=ch, inline=True)
    embed.add_field(
        name="Heure du matin",
        value=f"{data['morning_hour']:02d}:{data['morning_minute']:02d}",
        inline=True,
    )
    embed.add_field(name="Fuseau", value=data["timezone"], inline=True)
    embed.add_field(name="Messages spontanés", value=sp, inline=True)
    embed.add_field(name="Admins supplémentaires", value=admins, inline=False)
    embed.set_footer(text="Owner & admins uniquement")
    return embed


async def refresh(view):
    """Reconstruit le menu (remet le select à zéro) et met à jour l'embed."""
    msg = getattr(view, "message", None)
    if not msg:
        return
    new_view = ConfigView(getattr(view, "author_id", OWNER_ID))
    new_view.message = msg
    try:
        await msg.edit(embed=build_config_embed(), view=new_view)
    except Exception as e:
        print("⚠️ refresh:", e)


# ---------- MODALS (saisie de texte) ----------
class NameModal(discord.ui.Modal, title="Surnom de Pamuk"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.field = discord.ui.TextInput(
            label="Comment Pamuk l'appelle",
            default=data["name"], max_length=50,
        )
        self.add_item(self.field)

    async def on_submit(self, interaction):
        data["name"] = str(self.field.value).strip() or data["name"]
        save_data()
        await refresh(self.parent_view)
        await interaction.response.send_message(
            f"✅ Surnom : **{data['name']}**", ephemeral=True
        )


class TimezoneModal(discord.ui.Modal, title="Fuseau horaire"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.field = discord.ui.TextInput(
            label="Ex : Europe/Istanbul", default=data["timezone"], max_length=64
        )
        self.add_item(self.field)

    async def on_submit(self, interaction):
        tz = str(self.field.value).strip()
        try:
            ZoneInfo(tz)
        except Exception:
            await interaction.response.send_message(
                "❌ Fuseau inconnu. Exemple : Europe/Istanbul", ephemeral=True
            )
            return
        data["timezone"] = tz
        save_data()
        reconfigure_morning()
        await refresh(self.parent_view)
        await interaction.response.send_message(f"✅ Fuseau : **{tz}**", ephemeral=True)


class MorningModal(discord.ui.Modal, title="Heure du message du matin"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.field = discord.ui.TextInput(
            label="Heure (HH:MM, 24h)",
            default=f"{data['morning_hour']:02d}:{data['morning_minute']:02d}",
            max_length=5,
        )
        self.add_item(self.field)

    async def on_submit(self, interaction):
        raw = str(self.field.value).strip()
        try:
            hh, mm = raw.split(":")
            hh, mm = int(hh), int(mm)
            assert 0 <= hh <= 23 and 0 <= mm <= 59
        except Exception:
            await interaction.response.send_message(
                "❌ Format attendu : HH:MM (ex : 08:30)", ephemeral=True
            )
            return
        data["morning_hour"], data["morning_minute"] = hh, mm
        save_data()
        reconfigure_morning()
        await refresh(self.parent_view)
        await interaction.response.send_message(
            f"✅ Bonjour du matin à **{hh:02d}:{mm:02d}**", ephemeral=True
        )


class SpontaneousModal(discord.ui.Modal, title="Messages spontanés"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.enabled = discord.ui.TextInput(
            label="Activés ? (oui / non)",
            default="oui" if data["spontaneous_enabled"] else "non",
            max_length=4,
        )
        self.hours = discord.ui.TextInput(
            label="Toutes les combien d'heures ?",
            default=str(data["spontaneous_hours"]), max_length=2,
        )
        self.add_item(self.enabled)
        self.add_item(self.hours)

    async def on_submit(self, interaction):
        en = str(self.enabled.value).strip().lower() in (
            "oui", "o", "yes", "y", "on", "true", "1"
        )
        try:
            hours = max(1, int(str(self.hours.value).strip()))
        except Exception:
            await interaction.response.send_message(
                "❌ Le nombre d'heures doit être un entier.", ephemeral=True
            )
            return
        data["spontaneous_enabled"] = en
        data["spontaneous_hours"] = hours
        save_data()
        reconfigure_spontaneous()
        if en and not spontaneous_message.is_running():
            spontaneous_message.start()
        await refresh(self.parent_view)
        await interaction.response.send_message(
            f"✅ Spontanés : {'activés' if en else 'désactivés'}, toutes les {hours}h",
            ephemeral=True,
        )


class ComplimentsModal(discord.ui.Modal, title="Compliments cachés"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.c10 = discord.ui.TextInput(
            label="Débloqué à 10 ❤️", style=discord.TextStyle.paragraph,
            default=data["compliments"].get("10", ""), required=False, max_length=300,
        )
        self.c25 = discord.ui.TextInput(
            label="Débloqué à 25 ❤️", style=discord.TextStyle.paragraph,
            default=data["compliments"].get("25", ""), required=False, max_length=300,
        )
        self.c50 = discord.ui.TextInput(
            label="Débloqué à 50 ❤️", style=discord.TextStyle.paragraph,
            default=data["compliments"].get("50", ""), required=False, max_length=300,
        )
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
        self.add_input = discord.ui.TextInput(
            label="Ajouter des IDs (séparés par des virgules)",
            required=False, default="",
        )
        self.remove_input = discord.ui.TextInput(
            label="Retirer des IDs (séparés par des virgules)",
            required=False, default="",
        )
        self.add_item(self.add_input)
        self.add_item(self.remove_input)

    @staticmethod
    def _parse(s):
        out = []
        for part in str(s).replace(" ", "").split(","):
            if part.isdigit():
                out.append(int(part))
        return out

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
            # ouvert depuis le panneau !config : on rafraîchit l'embed
            await refresh(self.parent_view)
            await interaction.response.send_message(
                f"✅ Langue : **{data['language']}**", ephemeral=True
            )
        else:
            # ouvert depuis !language : Pamuk confirme dans la nouvelle langue
            await interaction.response.send_message(fill(m("lang_changed")))


class LanguageView(discord.ui.View):
    def __init__(self, parent_view=None):
        super().__init__(timeout=120)
        self.add_item(LanguageSelect(parent_view))


class ChannelSelectMenu(discord.ui.ChannelSelect):
    def __init__(self, parent_view):
        super().__init__(
            channel_types=[discord.ChannelType.text],
            placeholder="Choisis le salon où Pamuk parle",
        )
        self.parent_view = parent_view

    async def callback(self, interaction):
        ch = self.values[0]
        data["channel_id"] = ch.id
        save_data()
        await refresh(self.parent_view)
        await interaction.response.send_message(
            f"✅ Salon : <#{ch.id}>", ephemeral=True
        )


class ChannelView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=120)
        self.add_item(ChannelSelectMenu(parent_view))


# ---------- MENU PRINCIPAL ----------
class ConfigSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Surnom", value="name", emoji="🐱",
                                 description="Comment Pamuk l'appelle"),
            discord.SelectOption(label="Langue", value="language", emoji="🌍",
                                 description="en / fr / tr"),
            discord.SelectOption(label="Salon", value="channel", emoji="📢",
                                 description="Où Pamuk parle"),
            discord.SelectOption(label="Heure du matin", value="morning", emoji="⏰",
                                 description="Bonjour quotidien"),
            discord.SelectOption(label="Fuseau horaire", value="timezone", emoji="🕒",
                                 description="ex : Europe/Istanbul"),
            discord.SelectOption(label="Messages spontanés", value="spontaneous", emoji="💬",
                                 description="Activer / fréquence"),
            discord.SelectOption(label="Compliments cachés", value="compliments", emoji="💝",
                                 description="Tes messages secrets"),
            discord.SelectOption(label="Gérer les admins", value="admins", emoji="👤",
                                 description="Owner uniquement"),
        ]
        super().__init__(placeholder="Que veux-tu configurer ?", options=options)

    async def callback(self, interaction):
        v = self.values[0]
        pv = self.view
        if v == "name":
            await interaction.response.send_modal(NameModal(pv))
        elif v == "language":
            await interaction.response.send_message(
                "Choisis une langue :", view=LanguageView(pv), ephemeral=True
            )
        elif v == "channel":
            await interaction.response.send_message(
                "Choisis un salon :", view=ChannelView(pv), ephemeral=True
            )
        elif v == "morning":
            await interaction.response.send_modal(MorningModal(pv))
        elif v == "timezone":
            await interaction.response.send_modal(TimezoneModal(pv))
        elif v == "spontaneous":
            await interaction.response.send_modal(SpontaneousModal(pv))
        elif v == "compliments":
            await interaction.response.send_modal(ComplimentsModal(pv))
        elif v == "admins":
            if interaction.user.id != OWNER_ID:
                await interaction.response.send_message(
                    "⛔ Réservé à l'owner.", ephemeral=True
                )
                return
            await interaction.response.send_modal(AdminsModal(pv))


class ConfigView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.message = None
        self.add_item(ConfigSelect())

    async def interaction_check(self, interaction):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(
                "⛔ Tu n'as pas la permission d'utiliser ce menu.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass


@bot.command(name="config")
async def config_cmd(ctx):
    if not is_admin(ctx.author.id):
        await ctx.send("⛔ Tu n'as pas la permission d'utiliser cette commande.")
        return
    view = ConfigView(ctx.author.id)
    msg = await ctx.send(embed=build_config_embed(), view=view)
    view.message = msg

# ==================================================================
if __name__ == "__main__":
    if TOKEN == "PUT_YOUR_TOKEN_HERE":
        print("⚠️ Renseigne TOKEN (ou la variable d'env DISCORD_TOKEN) avant de lancer.")
    bot.run(TOKEN)