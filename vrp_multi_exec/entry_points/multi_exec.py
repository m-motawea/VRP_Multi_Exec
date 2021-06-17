from gevent.monkey import patch_all

patch_all()

from datetime import datetime
from vrp_multi_exec.lib.handlers.device_config_handler import ConfigHandler, CommandHandler
from vrp_multi_exec.lib.parsers.targets import TargetParserFactory
from vrp_multi_exec.lib.parsers.vars import VarParserFactory
import json
from loguru import logger
import os
import click
from vrp_multi_exec.lib.logging import GlobalLogger


@click.group()
def cli():
    pass


@cli.command(help="run generic config template")
@click.argument("targets", required=True, type=click.Path(exists=True))
@click.argument("config", required=True, type=click.Path(exists=True))
@click.option(
    "--group",
    help="targets group to execute on. if not specified will execute on all",
    required=False,
    default="",
    type=str,
)
@click.option(
    "--variables",
    help="variables file path",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--output",
    help="output file path",
    required=False,
    default=f"vrp_multi_exec-{datetime.now().timestamp()}.txt",
    type=click.Path(dir_okay=True),
)
@click.option(
    "--sequential",
    help="execute sequentially",
    required=False,
    default=False,
    is_flag=True,
)
@click.option(
    "--password-prompt",
    help="prompt to enter password",
    required=False,
    default=False,
    is_flag=True,
)
@click.option(
    "--timeout", help="timeout for shell output", required=False, default=1, type=int
)
@click.option(
    "--keyfile",
    help="private key file path",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--loglevel",
    help="execution log level",
    required=False,
    default="info",
    type=click.Choice(["info", "debug", "error", "critical"]),
)
def config(
    targets,
    config,
    group=None,
    variables=None,
    output=None,
    sequential=False,
    password_prompt=False,
    timeout=1,
    keyfile=None,
    loglevel="info",
):
    logger = GlobalLogger(loglevel).logger
    if password_prompt:
        password = click.prompt("Please input the password", hide_input=True)
    else:
        password = None
    target_groups = get_target_groups(targets, password, keyfile)
    var_tree = get_complete_variables(variables, target_groups) if variables else {}
    handler = ConfigHandler(config, group=group)
    result = handler.execute_config(
        target_groups,
        out_file=output,
        var_tree=var_tree,
        sequential=sequential,
        timeout=timeout,
    )
    with open("multi_exec.json", "w") as result_json:
        json.dump(result, result_json, indent=4)


@cli.command(help="run generic ad-hoc commands")
@click.argument("targets", required=True, type=click.Path(exists=True))
@click.argument("command", required=True, type=str)
@click.option(
    "--group",
    help="targets group to execute on. if not specified will execute on all",
    required=False,
    default="",
    type=str,
)
@click.option(
    "--variables",
    help="variables file path",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--sequential",
    help="execute sequentially",
    required=False,
    default=False,
    is_flag=True,
)
@click.option(
    "--password-prompt",
    help="prompt to enter password",
    required=False,
    default=False,
    is_flag=True,
)
@click.option(
    "--timeout", help="timeout for shell output", required=False, default=1, type=int
)
@click.option(
    "--keyfile",
    help="private key file path",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--loglevel",
    help="execution log level",
    required=False,
    default="info",
    type=click.Choice(["info", "debug", "error", "critical"]),
)
@click.option(
    "--output",
    help="output file path",
    required=False,
    default="",
    type=click.Path(dir_okay=True),
)
def exec(
    targets,
    command,
    group="",
    variables=None,
    sequential=False,
    password_prompt=False,
    timeout=1,
    keyfile=None,
    loglevel="info",
    output="",
):
    logger = GlobalLogger(loglevel).logger
    if password_prompt:
        password = click.prompt("Please input the password", hide_input=True)
    else:
        password = None
    target_groups = get_target_groups(targets, password, keyfile)
    handler = CommandHandler(command, group)
    var_tree = get_complete_variables(variables, target_groups) if variables else {}
    result = handler.execute_config(
        target_groups,
        var_tree=var_tree,
        sequential=sequential,
        timeout=timeout,
        out_file=output,
        write_result=True if output else False,
    )
    with open("multi_exec.json", "w") as result_json:
        json.dump(result, result_json, indent=4)


def get_target_groups(targets_path, password, key_filename, content=""):
    if not os.path.exists(targets_path):
        logger.error(f"{targets_path} doesn't exist")
        exit(1)
    parser_factory = TargetParserFactory(targets_path, content)
    target_parser = parser_factory.parser
    target_groups = target_parser.parse(password, key_filename)
    return target_groups


def get_complete_variables(variables_path, target_groups):
    if not os.path.exists(variables_path):
        logger.error(f"{variables_path} doesn't exist")
        exit(1)
    parser_factory = VarParserFactory(variables_path)
    var_parser = parser_factory.parser
    var_tree = var_parser.parse(target_groups)
    return var_tree


if __name__ == "__main__":
    cli()
