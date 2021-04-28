from datetime import datetime
from lib.handlers.device_config_handler import ConfigHandler
from lib.targets_parser import TargetParser
from lib.var_parser import VarParser
import json
from loguru import logger
import sys
import os
import click
from gevent.monkey import patch_all

patch_all()



@click.group()
def cli():
    pass


@cli.command(help="run generic config template")
@click.argument('targets', required=True, type=click.Path(exists=True))
@click.argument('config', required=True, type=click.Path(exists=True))
@click.option('--variables', help="variables file path", required=False, type=click.Path(exists=True))
@click.option('--output', help="output file path", required=False, default=f"vrp_multi_exec-{datetime.now().timestamp()}.txt", type=click.Path(dir_okay=True))
@click.option('--sequential', help="execute sequentially", required=False, default=False, is_flag=True)
@click.option('--password-prompt', help="prompt to enter password", required=False, default=False, is_flag=True)
@click.option('--timeout', help="timeout for shell output", required=False, default=1, type=int)
@click.option('--keyfile', help="private key file path", required=False, type=click.Path(exists=True))
@click.option('--loglevel', help="execution log level", required=False, default="info", type=click.Choice(["info", "debug", "error", "critical"]))
def config(targets, config, variables=None, output=None, sequential=False, password_prompt=False, timeout=2, keyfile=None, loglevel="info"):
    logger.add(sys.stderr, colorize=True, format="<green>{time}</green> <level>{message}</level>", filter="vrp_multi_exec", level=loglevel.upper(), backtrace=True, diagnose=True)
    if password_prompt:
        password = click.prompt('Please input the password', hide_input=True)
    else:
        password = None
    target_groups = get_target_groups(targets, password, keyfile)
    var_tree = get_complete_variables(variables, target_groups) if variables else {}
    handler = ConfigHandler(logger, config)
    result = handler.execute_config(target_groups, out_file=output, var_tree=var_tree, sequential=sequential, timeout=timeout)
    with open("multi_exec.json", "w") as result_json:
        json.dump(result, result_json, indent=4)



def get_target_groups(targets_path, password, key_filename):
    if not os.path.exists(targets_path):
        logger.error(f"{targets_path} doesn't exist")
        exit(1)
    with open(targets_path) as targets_file:
        targets_text = "\n".join(targets_file.readlines())
    target_parser = TargetParser()
    target_groups = target_parser.parse(targets_text, password, key_filename)
    return target_groups

def get_complete_variables(variables_path, target_groups):
    if not os.path.exists(variables_path):
        logger.error(f"{variables_path} doesn't exist")
        exit(1)
    var_parser = VarParser(variables_path)
    var_tree = var_parser.build_var_tree(target_groups)
    return var_tree


if __name__ == "__main__":
    cli()
