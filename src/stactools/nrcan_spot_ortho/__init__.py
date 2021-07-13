import stactools.core

stactools.core.use_fsspec()


def register_plugin(registry):
    """Register subcommands"""
    from stactools.nrcan_spot_ortho import commands

    registry.register_subcommand(commands.create_spot_command)


__version__ = '0.1.0'
"""Library version"""
