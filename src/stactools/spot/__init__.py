import stactools.core

stactools.core.use_fsspec()


def register_plugin(registry):
    """Register subcommands"""
    from stactools.spot import commands

    registry.register_subcommand(commands.create_spot_command)


__version__ = '0.1.5'
"""Library version"""
