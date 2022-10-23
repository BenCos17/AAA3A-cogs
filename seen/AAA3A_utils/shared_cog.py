from redbot.core import commands  # isort:skip
import discord  # isort:skip
import typing  # isort:skip

import datetime
import os
import platform
import sys
import traceback
from io import StringIO
from pathlib import Path

import pip
from redbot import version_info as red_version_info
from redbot.cogs.downloader.converters import InstalledCog
from redbot.cogs.downloader.repo_manager import Repo
from redbot.core import Config
from redbot.core._diagnoser import IssueDiagnoser
from redbot.core.bot import Red
from redbot.core.data_manager import basic_config, config_file, instance_name, storage_type
from redbot.core.utils.chat_formatting import (
    bold,
    box,
    humanize_list,
    humanize_timedelta,
    pagify,
    text_to_file,
)  # NOQA
from rich.console import Console
from rich.table import Table

__all__ = ["SharedCog"]


def _(untranslated: str):
    return untranslated


def no_colour_rich_markup(*objects: typing.Any, lang: str = "") -> str:
    """
    Slimmed down version of rich_markup which ensure no colours (/ANSI) can exist
    https://github.com/Cog-Creators/Red-DiscordBot/pull/5538/files (Kowlin)
    """
    temp_console = Console(  # Prevent messing with STDOUT's console
        color_system=None,
        file=StringIO(),
        force_terminal=True,
        width=80,
    )
    temp_console.print(*objects)
    return box(temp_console.file.getvalue(), lang=lang)  # type: ignore


class StrConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str):
        return arg


class SharedCog(commands.Cog, name="AAA3A_utils"):
    """Commands to manage all the cogs in AAA3A-cogs repo!"""

    def __init__(self, bot: Red, CogsUtils):
        self.bot: Red = bot

        self.config: Config = Config.get_conf(
            self,
            identifier=205192943327321000143939875896557571750,
            force_registration=True,
            cog_name=self.qualified_name,
        )
        self.AAA3A_utils_global = {
            "cogs_with_slash": [],
        }
        self.config.register_global(**self.AAA3A_utils_global)

        self.cogsutils = CogsUtils(cog=self)
        self.cogsutils._setup()

    async def check_if_slash(self, cog: commands.Cog):
        if not self.cogsutils.is_dpy2:
            return False
        if cog.qualified_name not in self.cogsutils.get_all_repo_cogs_objects():
            return False
        return cog.qualified_name in await self.config.cogs_with_slash()

    @commands.is_owner()
    @commands.group(hidden=True)
    async def AAA3A_utils(self, ctx: commands.Context):
        """All commands to manage all the cogs in AAA3A-cogs repo."""
        pass

    @commands.is_owner()
    @AAA3A_utils.command()
    async def addslash(self, ctx: commands.Context, cogs: commands.Greedy[StrConverter]):
        """Add slash commands for repo cogs."""
        if not self.cogsutils.is_dpy2:
            await ctx.send(_("Slash commands do not work under dpy1. Wait for Red 3.5."))
            return
        async with ctx.typing():
            result = {
                "not_installed_or_loaded": [],
                "not_from_AAA3A-cogs": [],
                "already": [],
                "failed": [],
            }
            config = await self.config.cogs_with_slash()
            for cog_name in list(set(cogs)):
                cog = ctx.bot.get_cog(cog_name)
                if cog is None:
                    result["not_installed_or_loaded"].append(cog_name)
                    continue
                if cog.qualified_name not in self.cogsutils.get_all_repo_cogs_objects():
                    result["not_from_AAA3A-cogs"].append(cog.qualified_name)
                    continue
                if cog.qualified_name in config:
                    result["already"].append(cog.qualified_name)
                    continue
                try:
                    await self.cogsutils.add_hybrid_commands(cog=cog)
                except Exception as e:
                    self.log.error(
                        f"Error when adding slash (hybrids) commands from the {cog.qualified_name} cog.",
                        exc_info=e,
                    )
                    result["failed"].append(cog.qualified_name)
                    continue
                config.append(cog.qualified_name)
            await self.config.cogs_with_slash.set(config)
        if result == {
            "not_installed_or_loaded": [],
            "not_from_AAA3A-cogs": [],
            "already": [],
            "failed": [],
        }:
            await ctx.tick(message="Done.")
        else:
            message = ""
            if not result["not_installed_or_loaded"] == []:
                items = result["not_installed_or_loaded"]
                s = "s" if len(items) > 1 else ""
                message += f"\n{bold(f'Cog{s} not installed or loaded')}: {humanize_list(items)}"
            if not result["not_from_AAA3A-cogs"] == []:
                items = result["not_from_AAA3A-cogs"]
                s = "s" if len(items) > 1 else ""
                message += f"\n{bold(f'Cog{s} not from AAA3A-cogs')}: {humanize_list(items)}"
            if not result["already"] == []:
                items = result["already"]
                s = "s" if len(items) > 1 else ""
                message += f"\n{bold(f'Cog{s} with slash commands already loaded')} (If they don't appear in Discord, you may have forgotten to sync.): {humanize_list(items)}"
            if not result["failed"] == []:
                items = result["failed"]
                s = "s" if len(items) > 1 else ""
                message += (
                    f"\n{bold(f'Failed cog{s}')} (Check the bot console.): {humanize_list(items)}"
                )
            await ctx.send(message)

    @commands.is_owner()
    @AAA3A_utils.command()
    async def removeslash(self, ctx: commands.Context, cogs: commands.Greedy[StrConverter]):
        """Remove slash commands for repo cogs."""
        if not self.cogsutils.is_dpy2:
            await ctx.send(_("Slash commands do not work under dpy1. Wait for Red 3.5."))
            return
        async with ctx.typing():
            result = {
                "not_installed_or_loaded": [],
                "not_from_AAA3A-cogs": [],
                "already": [],
                "failed": [],
            }
            config = await self.config.cogs_with_slash()
            for cog_name in list(set(cogs)):
                cog = ctx.bot.get_cog(cog_name)
                if cog is None:
                    result["not_installed_or_loaded"].append(cog_name)
                    continue
                if cog.qualified_name not in self.cogsutils.get_all_repo_cogs_objects():
                    result["not_from_AAA3A-cogs"].append(cog.qualified_name)
                    continue
                if cog.qualified_name not in config:
                    result["already"].append(cog.qualified_name)
                    continue
                try:
                    await self.cogsutils.remove_hybrid_commands(cog=cog)
                except Exception as e:
                    self.log.error(
                        f"Error when removing slash (hybrids) commands from the {cog.qualified_name} cog.",
                        exc_info=e,
                    )
                    result["failed"].append(cog.qualified_name)
                config.remove(cog.qualified_name)
            await self.config.cogs_with_slash.set(config)
        if result == {
            "not_installed_or_loaded": [],
            "not_from_AAA3A-cogs": [],
            "already": [],
            "failed": [],
        }:
            await ctx.tick(message="Done.")
        else:
            message = ""
            if not result["not_installed_or_loaded"] == []:
                items = result["not_installed_or_loaded"]
                s = "s" if len(items) > 1 else ""
                message += f"\n{bold(f'Cog{s} not installed or loaded')}: {humanize_list(items)}"
            if not result["not_from_AAA3A-cogs"] == []:
                items = result["not_from_AAA3A-cogs"]
                s = "s" if len(items) > 1 else ""
                message += f"\n{bold(f'Cog{s} not from AAA3A-cogs')}: {humanize_list(items)}"
            if not result["already"] == []:
                items = result["already"]
                s = "s" if len(items) > 1 else ""
                message += f"\n{bold(f'Cog{s} with slash commands already unloaded')} (If they appear in Discord, you may have forgotten to sync.): {humanize_list(items)}"
            if not result["failed"] == []:
                items = result["failed"]
                s = "s" if len(items) > 1 else ""
                message += (
                    f"\n{bold(f'Failed cog{s}')} (Check the bot console.): {humanize_list(items)}"
                )
            await ctx.send(message)

    @commands.is_owner()
    @AAA3A_utils.command()
    async def clearslash(self, ctx: commands.Context):
        """Remove slash commands for all repo cogs."""
        if not self.cogsutils.is_dpy2:
            await ctx.send(_("Slash commands do not work under dpy1. Wait for Red 3.5."))
            return
        config = await self.config.cogs_with_slash()
        for cog in self.cogsutils.get_all_repo_cogs_objects():
            if cog.qualified_name in config:
                await self.cogsutils.remove_hybrid_commands(cog=cog)
        config.clear()
        await self.config.cogs_with_slash.set(config)
        await self.cogsutils.remove_hybrid_commands(cog=cog)
        await ctx.tick(message="Done")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Record all exceptions generated by commands by cog and by command in `bot.last_exceptions_cogs`.
        All my cogs will add this listener if it doesn't exist, so I need to record this in a common variable. Also, this may be useful to others.
        """
        try:
            IGNORED_ERRORS = (
                commands.UserInputError,
                commands.DisabledCommand,
                commands.CommandNotFound,
                commands.CheckFailure,
                commands.NoPrivateMessage,
                commands.CommandOnCooldown,
                commands.MaxConcurrencyReached,
                commands.BadArgument,
                commands.BadBoolArgument,
            )
            if ctx.cog is not None:
                cog = ctx.cog.qualified_name
            else:
                cog = "None"
            if ctx.command is None:
                return
            if isinstance(error, IGNORED_ERRORS):
                return
            if not hasattr(self.bot, "last_exceptions_cogs"):
                self.bot.last_exceptions_cogs = {}
            if "global" not in self.bot.last_exceptions_cogs:
                self.bot.last_exceptions_cogs["global"] = []
            if error in self.bot.last_exceptions_cogs["global"]:
                return
            self.bot.last_exceptions_cogs["global"].append(error)
            if isinstance(error, commands.CommandError):
                traceback_error = "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )
            else:
                traceback_error = f"Traceback (most recent call last): {error}"
            traceback_error = self.replace_var_paths(traceback_error)
            if cog not in self.bot.last_exceptions_cogs:
                self.bot.last_exceptions_cogs[cog] = {}
            if ctx.command.qualified_name not in self.bot.last_exceptions_cogs[cog]:
                self.bot.last_exceptions_cogs[cog][ctx.command.qualified_name] = []
            self.bot.last_exceptions_cogs[cog][ctx.command.qualified_name].append(traceback_error)
        except Exception:
            pass

    @commands.is_owner()
    @AAA3A_utils.command()
    async def getallfor(
        self,
        ctx: commands.Context,
        all: typing.Optional[typing.Literal["all", "ALL"]] = None,
        page: typing.Optional[int] = None,
        repo: typing.Optional[typing.Union[Repo, typing.Literal["AAA3A", "aaa3a"]]] = None,
        check_updates: typing.Optional[bool] = False,
        cog: typing.Optional[InstalledCog] = None,
        command: typing.Optional[str] = None,
    ):
        """Get all the necessary information to get support on a bot/repo/cog/command.
        With a html file.
        """
        if all is not None:
            repo = None
            cog = None
            command = None
            check_updates = False
        if repo is not None:
            _repos = [repo]
        else:
            _repos = [None]
        if cog is not None:
            _cogs = [cog]
        else:
            _cogs = [None]
        if command is not None:
            _commands = [command]
        else:
            _commands = [None]
        if command is not None:
            object_command = ctx.bot.get_command(_commands[0])
            if object_command is None:
                await ctx.send(_("The command `{command}` does not exist.").format(**locals()))
                return
            _commands = [object_command]
        downloader = ctx.bot.get_cog("Downloader")
        if downloader is None:
            if self.cogsutils.ConfirmationAsk(
                ctx,
                _(
                    "The cog downloader is not loaded. I can't continue. Do you want me to do it?"
                ).format(**locals()),
            ):
                await ctx.invoke(ctx.bot.get_command("load"), "downloader")
                downloader = ctx.bot.get_cog("Downloader")
            else:
                return
        installed_cogs = await downloader.config.installed_cogs()
        loaded_cogs = [c.lower() for c in ctx.bot.cogs]
        if repo is not None:
            rp = _repos[0]
            if not isinstance(rp, Repo) and not "AAA3A".lower() in rp.lower():
                await ctx.send(_("Repo by the name `{rp}` does not exist.").format(**locals()))
                return
            if not isinstance(repo, Repo):
                found = False
                for r in await downloader.config.installed_cogs():
                    if "AAA3A".lower() in str(r).lower():
                        _repos = [downloader._repo_manager.get_repo(str(r))]
                        found = True
                        break
                if not found:
                    await ctx.send(_("Repo by the name `{rp}` does not exist.").format(**locals()))
                    return
            if check_updates:
                cogs_to_check, failed = await downloader._get_cogs_to_check(repos={_repos[0]})
                cogs_to_update, libs_to_update = await downloader._available_updates(cogs_to_check)
                cogs_to_update, filter_message = downloader._filter_incorrect_cogs(cogs_to_update)
                to_update_cogs = [c.name.lower() for c in cogs_to_update]

        if all is not None:
            _repos = []
            for r in installed_cogs:
                _repos.append(downloader._repo_manager.get_repo(str(r)))
            _cogs = []
            for r in installed_cogs:
                for c in installed_cogs[r]:
                    _cogs.append(await InstalledCog.convert(ctx, str(c)))
            _commands = []
            for c in ctx.bot.all_commands:
                cmd = ctx.bot.get_command(str(c))
                if cmd.cog is not None:
                    _commands.append(cmd)
            repo = True
            cog = True
            command = True

        IS_WINDOWS = os.name == "nt"
        IS_MAC = sys.platform == "darwin"
        IS_LINUX = sys.platform == "linux"
        if IS_LINUX:
            import distro  # pylint: disable=import-error
        python_executable = sys.executable
        python_version = ".".join(map(str, sys.version_info[:3]))
        pyver = f"{python_version} ({platform.architecture()[0]})"
        pipver = pip.__version__
        redver = red_version_info
        dpy_version = discord.__version__
        if IS_WINDOWS:
            os_info = platform.uname()
            osver = f"{os_info.system} {os_info.release} (version {os_info.version})"
        elif IS_MAC:
            os_info = platform.mac_ver()
            osver = f"Mac OSX {os_info[0]} {os_info[2]}"
        elif IS_LINUX:
            osver = f"{distro.name()} {distro.version()}".strip()
        else:
            osver = "Could not parse OS, report this on Github."
        driver = storage_type()
        data_path_original = Path(basic_config["DATA_PATH"])
        data_path = Path(self.cogsutils.replace_var_paths(str(data_path_original)))
        _config_file = Path(self.cogsutils.replace_var_paths(str(config_file)))
        python_executable = Path(self.cogsutils.replace_var_paths(str(python_executable)))
        disabled_intents = (
            ", ".join(
                intent_name.replace("_", " ").title()
                for intent_name, enabled in ctx.bot.intents
                if not enabled
            )
            or "None"
        )
        uptime = humanize_timedelta(timedelta=datetime.datetime.utcnow() - ctx.bot.uptime)

        async def can_run(command):
            try:
                await command.can_run(ctx, check_all_parents=True, change_permission_state=False)
            except Exception:
                return False
            else:
                return True

        def get_aliases(command, original):
            if alias := list(command.aliases):
                if original in alias:
                    alias.remove(original)
                    alias.append(command.name)
                return alias

        def get_perms(command):
            final_perms = ""

            def neat_format(x):
                return " ".join(i.capitalize() for i in x.replace("_", " ").split())

            user_perms = []
            if perms := getattr(command.requires, "user_perms"):
                user_perms.extend(neat_format(i) for i, j in perms if j)
            if perms := command.requires.privilege_level:
                if perms.name != "NONE":
                    user_perms.append(neat_format(perms.name))
            if user_perms:
                final_perms += "User Permission(s): " + ", ".join(user_perms) + "\n"
            if perms := getattr(command.requires, "bot_perms"):
                if perms_list := ", ".join(neat_format(i) for i, j in perms if j):
                    final_perms += "Bot Permission(s): " + perms_list
            return final_perms

        def get_cooldowns(command):
            cooldowns = []
            if s := command._buckets._cooldown:
                txt = f"{s.rate} time{'s' if s.rate>1 else ''} in {humanize_timedelta(seconds=s.per)}"
                try:
                    txt += f" per {s.type.name.capitalize()}"
                # This is to avoid custom bucketype erroring out stuff (eg:licenseinfo)
                except AttributeError:
                    pass
                cooldowns.append(txt)
            if s := command._max_concurrency:
                cooldowns.append(f"Max concurrent uses: {s.number} per {s.per.name.capitalize()}")
            return cooldowns

        async def get_diagnose(ctx, command):
            issue_diagnoser = IssueDiagnoser(ctx.bot, ctx, ctx.channel, ctx.author, command)
            await issue_diagnoser._prepare()
            diagnose_result = []
            result = await issue_diagnoser._check_until_fail(
                "",
                (
                    issue_diagnoser._check_global_call_once_checks_issues,
                    issue_diagnoser._check_disabled_command_issues,
                    issue_diagnoser._check_can_run_issues,
                ),
            )
            if result.success:
                diagnose_result.append(_("All checks passed and no issues were detected."))
            else:
                diagnose_result.append(_("The bot has been able to identify the issue."))
            details = issue_diagnoser._get_details_from_check_result(result)
            if details:
                diagnose_result.append(bold(_("Detected issue: ")) + details)
            if result.resolution:
                diagnose_result.append(bold(_("Solution: ")) + result.resolution)
            diagnose_result.extend(issue_diagnoser._get_message_from_check_result(result))
            return diagnose_result

        async def get_all_config(cog: commands.Cog):
            config = {}
            if not hasattr(cog, "config"):
                return config
            try:
                config["global"] = await cog.config.all()
                config["users"] = await cog.config.all_users()
                config["guilds"] = await cog.config.all_guilds()
                config["members"] = await cog.config.all_members()
                config["roles"] = await cog.config.all_roles()
                config["channels"] = await cog.config.all_channels()
            except Exception:
                return config
            return config

        use_emojis = False
        check_emoji = "✅" if use_emojis else True
        cross_emoji = "❌" if use_emojis else False

        ##################################################
        os_table = Table("Key", "Value", title="Host machine informations")
        os_table.add_row("OS version", str(osver))
        os_table.add_row("Python executable", str(python_executable))
        os_table.add_row("Python version", str(pyver))
        os_table.add_row("Pip version", str(pipver))
        raw_os_table_str = no_colour_rich_markup(os_table)
        ##################################################
        red_table = Table("Key", "Value", title="Red instance informations")
        red_table.add_row("Red version", str(redver))
        red_table.add_row("Discord.py version", str(dpy_version))
        red_table.add_row("Instance name", str(instance_name))
        red_table.add_row("Storage type", str(driver))
        red_table.add_row("Disabled intents", str(disabled_intents))
        red_table.add_row("Data path", str(data_path))
        red_table.add_row("Metadata file", str(_config_file))
        red_table.add_row("Uptime", str(uptime))
        red_table.add_row(
            "Global prefixe(s)",
            str(await ctx.bot.get_valid_prefixes()).replace(f"{ctx.bot.user.id}", "{bot_id}"),
        )
        if ctx.guild is not None:
            if not await ctx.bot.get_valid_prefixes() == await ctx.bot.get_valid_prefixes(
                ctx.guild
            ):
                red_table.add_row(
                    "Guild prefixe(s)",
                    str(await ctx.bot.get_valid_prefixes(ctx.guild)).replace(
                        f"{ctx.bot.user.id}", "{bot_id}"
                    ),
                )
        raw_red_table_str = no_colour_rich_markup(red_table)
        ##################################################
        context_table = Table("Key", "Value", title="Context")
        context_table.add_row("Channel type", str(f"discord.{ctx.channel.__class__.__name__}"))
        context_table.add_row(
            "Bot permissions value (guild)",
            str(
                ctx.guild.me.guild_permissions.value
                if ctx.guild is not None
                else "Not in a guild."
            ),
        )
        context_table.add_row(
            "Bot permissions value (channel)",
            str(
                ctx.channel.permissions_for(ctx.guild.me).value
                if ctx.guild is not None
                else ctx.channel.permissions_for(ctx.bot.user).value
            ),
        )
        context_table.add_row(
            "User permissions value (guild)",
            str(
                ctx.author.guild_permissions.value if ctx.guild is not None else "Not in a guild."
            ),
        )
        context_table.add_row(
            "User permissions value (channel)", str(ctx.channel.permissions_for(ctx.author).value)
        )
        raw_context_table_str = no_colour_rich_markup(context_table)
        ##################################################
        if repo is not None:
            raw_repo_table_str = []
            for repo in _repos:
                if not check_updates:
                    cogs_table = Table(
                        "Name",
                        "Commit",
                        "Loaded",
                        "Pinned",
                        title=f"Cogs installed for {repo.name}",
                    )
                else:
                    cogs_table = Table(
                        "Name",
                        "Commit",
                        "Loaded",
                        "Pinned",
                        "To update",
                        title=f"Cogs installed for {repo.name}",
                    )
                for _cog in installed_cogs[repo.name]:
                    _cog = await InstalledCog.convert(ctx, _cog)
                    if not check_updates:
                        cogs_table.add_row(
                            str(_cog.name),
                            str(_cog.commit),
                            str(check_emoji if _cog.name in loaded_cogs else cross_emoji),
                            str(check_emoji if _cog.pinned else cross_emoji),
                        )
                    else:
                        cogs_table.add_row(
                            str(_cog.name),
                            str(_cog.commit),
                            str(check_emoji if _cog.name in loaded_cogs else cross_emoji),
                            str(check_emoji if _cog.pinned else cross_emoji),
                            str(check_emoji if _cog.name in to_update_cogs else cross_emoji),
                        )
                raw_repo_table_str.append(no_colour_rich_markup(cogs_table))
        else:
            raw_repo_table_str = None
        ##################################################
        if cog is not None:
            raw_cogs_table_str = []
            for cog in _cogs:
                cog_table = Table("Key", "Value", title=f"Cog {cog.name}")
                cog_table.add_row("Name", str(cog.name))
                cog_table.add_row("Repo name", str(cog.repo_name))
                cog_table.add_row("Hidden", str(check_emoji if cog.hidden else cross_emoji))
                cog_table.add_row("Disabled", str(check_emoji if cog.disabled else cross_emoji))
                cog_table.add_row("Required cogs", str([r for r in cog.required_cogs]))
                cog_table.add_row("Requirements", str([r for r in cog.requirements]))
                cog_table.add_row("Short", str(cog.short))
                cog_table.add_row("Min bot version", str(cog.min_bot_version))
                cog_table.add_row("Max bot version", str(cog.max_bot_version))
                cog_table.add_row("Min python version", str(cog.min_python_version))
                cog_table.add_row("Author", str([a for a in cog.author]))
                cog_table.add_row("Commit", str(cog.commit))
                raw_cog_table_str = no_colour_rich_markup(cog_table)
                raw_cogs_table_str.append(raw_cog_table_str)
        else:
            raw_cogs_table_str = None
        ##################################################
        if command is not None:
            raw_commands_table_str = []
            for command in _commands:
                command_table = Table("Key", "Value", title=f"Command {command.qualified_name}")
                command_table.add_row("Qualified name", str(command.qualified_name))
                command_table.add_row("Cog name", str(command.cog_name))
                command_table.add_row("Short description", str(command.short_doc))
                command_table.add_row(
                    "Syntax",
                    str(f"{ctx.clean_prefix}{command.qualified_name} {command.signature}"),
                )
                command_table.add_row("Hidden", str(command.hidden))
                command_table.add_row(
                    "Parents",
                    str(command.full_parent_name if not command.full_parent_name == "" else None),
                )
                command_table.add_row("Can see", str(await command.can_see(ctx)))
                command_table.add_row("Can run", str(await can_run(command)))
                command_table.add_row("Params", str(command.clean_params))
                command_table.add_row("Aliases", str(get_aliases(command, command.qualified_name)))
                command_table.add_row("Requires", str(get_perms(command)))
                command_table.add_row("Cooldowns", str(get_cooldowns(command)))
                command_table.add_row("Is on cooldown", str(command.is_on_cooldown(ctx)))
                if ctx.guild is not None:
                    diagnose_result = await get_diagnose(ctx, command)
                    c = 0
                    for x in diagnose_result:
                        c += 1
                        if c == 1:
                            command_table.add_row("Issue Diagnose", str(x))
                        else:
                            command_table.add_row("", str(x).replace("✅", "").replace("❌", ""))
                raw_command_table_str = no_colour_rich_markup(command_table)
                raw_commands_table_str.append(raw_command_table_str)
                cog = command.cog.qualified_name if command.cog is not None else "None"
                if (
                    hasattr(ctx.bot, "last_exceptions_cogs")
                    and cog in ctx.bot.last_exceptions_cogs
                    and command.qualified_name in ctx.bot.last_exceptions_cogs[cog]
                ):
                    raw_errors_table = []
                    error_table = Table("Last error recorded for this command")
                    error_table.add_row(
                        str(
                            ctx.bot.last_exceptions_cogs[cog][command.qualified_name][
                                len(ctx.bot.last_exceptions_cogs[cog][command.qualified_name]) - 1
                            ]
                        )
                    )
                    raw_errors_table.append(no_colour_rich_markup(error_table))
                else:
                    raw_errors_table = None
        else:
            raw_commands_table_str = None
            raw_errors_table = None
        ##################################################
        if _cogs is not None and len(_cogs) == 1 and _cogs[0] is not None:
            cog = None
            for name, value in ctx.bot.cogs.items():
                if name.lower() == _cogs[0].name.lower():
                    cog = value
                    break
            if cog is not None:
                config_table = Table(f"All Config for {cog.qualified_name}")
                config_table.add_row(str(await get_all_config(cog)))
                raw_config_table_str = no_colour_rich_markup(config_table)
            else:
                raw_config_table_str = None
        else:
            raw_config_table_str = None
        ##################################################

        response = [raw_os_table_str, raw_red_table_str, raw_context_table_str]
        for x in [
            raw_repo_table_str,
            raw_cogs_table_str,
            raw_commands_table_str,
            raw_errors_table,
            raw_config_table_str,
        ]:
            if x is not None:
                if isinstance(x, typing.List):
                    for y in x:
                        response.append(y)
                elif isinstance(x, str):
                    response.append(x)
        to_html = (
            to_html_getallfor.replace(
                "{AVATAR_URL}",
                str(ctx.bot.user.display_avatar)
                if self.cogsutils.is_dpy2
                else str(ctx.bot.user.avatar_url),
            )
            .replace("{BOT_NAME}", str(ctx.bot.user.name))
            .replace(
                "{REPO_NAME}", str(getattr(_repos[0], "name", None) if all is None else "All")
            )
            .replace("{COG_NAME}", str(getattr(_cogs[0], "name", None) if all is None else "All"))
            .replace(
                "{COMMAND_NAME}",
                str(getattr(_commands[0], "qualified_name", None) if all is None else "All"),
            )
        )
        message_html = message_html_getallfor
        end_html = end_html_getallfor
        try:
            if page is not None and page - 1 in [0, 1, 2, 3, 4, 5, 6, 7]:
                response = [response[page - 1]]
        except ValueError:
            pass
        for count_page, page in enumerate(response):
            if page is not None:
                if count_page == 1:
                    to_html += message_html.replace(
                        "{MESSAGE_CONTENT}",
                        str(page).replace("```", "").replace("<", "&lt;").replace("\n", "<br>"),
                    ).replace(
                        "{TIMESTAMP}", str(ctx.message.created_at.strftime("%b %d, %Y %I:%M %p"))
                    )
                else:
                    to_html += (
                        message_html.replace(
                            '    <div class="chatlog__messages">',
                            '            </div>            <div class="chatlog__message ">',
                        )
                        .replace(
                            "{MESSAGE_CONTENT}",
                            str(page)
                            .replace("```", "")
                            .replace("<", "&lt;")
                            .replace("\n", "<br>"),
                        )
                        .replace(
                            '<span class="chatlog__timestamp">{TIMESTAMP}</span>            ', ""
                        )
                    )
                if all is None and "Config" not in page:
                    for p in pagify(page):
                        p = p.replace("```", "")
                        p = box(p)
                        await ctx.send(p)
        to_html += end_html
        if self.cogsutils.check_permissions_for(
            channel=ctx.channel, user=ctx.me, check=["send_attachments"]
        ):
            await ctx.send(file=text_to_file(text=to_html, filename="diagnostic.html"))


to_html_getallfor = """
<!--
Thanks to @mahtoid for this transcript! It was retrieved from : https://github.com/mahtoid/DiscordChatExporterPy. Then all unnecessary elements were removed and the header was modified.
-->

<!DOCTYPE html>
<html lang="en">

<head>
    <title>Diagnostic</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />

    <style>
        @font-face {
            font-family: Whitney;
            src: url(https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/whitney-300.woff);
            font-weight: 300;
        }

        @font-face {
            font-family: Whitney;
            src: url(https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/whitney-400.woff);
            font-weight: 400;
        }

        @font-face {
            font-family: Whitney;
            src: url(https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/whitney-500.woff);
            font-weight: 500;
        }

        @font-face {
            font-family: Whitney;
            src: url(https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/whitney-600.woff);
            font-weight: 600;
        }

        @font-face {
            font-family: Whitney;
            src: url(https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/whitney-700.woff);
            font-weight: 700;
        }

        body {
            font-family: "Whitney", "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 17px;
        }

        a {
            text-decoration: none;
        }

        .markdown {
            max-width: 100%;
            line-height: 1.3;
            overflow-wrap: break-word;
        }

        .preserve-whitespace {
            white-space: pre-wrap;
        }

        .pre {
            font-family: "Consolas", "Courier New", Courier, monospace;
        }

        .pre--multiline {
            margin-top: 0.25em;
            padding: 0.5em;
            border: 2px solid;
            border-radius: 5px;
        }

        .pre--inline {
            padding: 2px;
            border-radius: 3px;
            font-size: 0.85em;
        }

        .emoji {
            width: 1.25em;
            height: 1.25em;
            margin: 0 0.06em;
            vertical-align: -0.4em;
        }

        .emoji--small {
            width: 1em;
            height: 1em;
        }

        .emoji--large {
            width: 2.8em;
            height: 2.8em;
        }

        /* Chatlog */

        .chatlog {
            max-width: 100%;
        }

        .chatlog__message-group {
            display: grid;
            margin: 0 0.6em;
            padding: 0.9em 0;
            border-top: 1px solid;
            grid-template-columns: auto 1fr;
        }

        .chatlog__timestamp {
            margin-left: 0.3em;
            font-size: 0.75em;
        }

        /* General */

        body {
            background-color: #36393e;
            color: #dcddde;
        }

        a {
            color: #0096cf;
        }

        .pre {
            background-color: #2f3136 !important;
        }

        .pre--multiline {
            border-color: #282b30 !important;
            color: #b9bbbe !important;
        }

        /* Chatlog */

        .chatlog__message-group {
            border-color: rgba(255, 255, 255, 0.1);
        }

        .chatlog__timestamp {
            color: rgba(255, 255, 255, 0.2);
        }

        /* === INFO === */

        .info {
            display: flex;
            max-width: 100%;
            margin: 0 5px 10px 5px;
        }

        .info__bot-icon-container {
            flex: 0;
        }

        .info__bot-icon {
            max-width: 95px;
            max-height: 95px;
        }

        .info__metadata {
            flex: 1;
            margin-left: 10px;

    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/styles/solarized-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/highlight.min.js"></script>
    <script>
        <!--  Code Block Markdown (```lang```) -->
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('.pre--multiline').forEach((block) => {
                hljs.highlightBlock(block);
            });
        });
    </script>
</head>
<body>

<div class="info">
<div class="info__bot-icon-container">
    <img class="info__bot-icon" src="{AVATAR_URL}" />
</div>
<div class="info__metadata">
    <div class="info__report-name">Diagnostic</div>

    <div class="info__report-infos">Bot name: {BOT_NAME}</div>
    <div class="info__report-infos">Repo name: {REPO_NAME}</div>
    <div class="info__report-infos">Cog name: {COG_NAME}</div>
    <div class="info__report-infos">Command name: {COMMAND_NAME}</div>
</div>
</div>

<div class="chatlog">
<div class="chatlog__message-group">"""
message_html_getallfor = """    <div class="chatlog__messages">
    <span class="chatlog__timestamp">{TIMESTAMP}</span>            <div class="chatlog__message ">
            <div class="chatlog__content">
<div class="markdown">
    <span class="preserve-whitespace"><div class="pre pre--multiline nohighlight">{MESSAGE_CONTENT}</div></span>

</div>
</div>"""
end_html_getallfor = """

</div>
</div>

</body>
</html>"""
