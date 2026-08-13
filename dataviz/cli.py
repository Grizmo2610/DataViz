from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

from dataviz import __version__
from dataviz.cache import clear_cache
from dataviz.config import (
    format_config_summary,
    load_config,
    update_provider_config,
)
from dataviz.agents.base import PipelineContext
from dataviz.agents.orchestrator import Orchestrator
from dataviz.exporters import get_exporter
from dataviz.tools.join_tools import infer_join_key, join_files
from dataviz.readers import MissingDependencyError, UnsupportedFormatError, get_reader
from dataviz.session import list_sessions, open_session
from dataviz.tool_gen import discard_pending_tools, list_pending_tools, run_pending_tools
from dataviz.tui import DatavizApp


def should_launch_tui(no_tui: bool) -> bool:
    """Determine whether the TUI should launch.

    Args:
        no_tui: Whether the user disabled the TUI.

    Returns:
        True when the TUI can launch.
    """

    if no_tui:
        return False
    return sys.stdout.isatty()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        A configured argparse parser for the DataViz CLI.
    """

    parser = argparse.ArgumentParser(
        prog="dataviz",
        description="Automated data visualization CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="*", help="Input files to analyze.")
    parser.add_argument("--output", default=None, choices=["html", "md", "pdf", "notebook"], help="Output format.")
    parser.add_argument("--out-dir", default=None, help="Output directory.")
    parser.add_argument("--lang", default=None, choices=["en", "vi", "auto"], help="Report language.")
    parser.add_argument("--fast", action="store_true", help="Use fast analysis mode.")
    parser.add_argument("--deep", action="store_true", help="Use deep analysis mode.")
    parser.add_argument("--interactive", action="store_true", help="Open interactive Q&A after report generation.")
    parser.add_argument("--focus", default=None, help="Analysis focus hint.")
    parser.add_argument("--sheet", default=None, help="XLSX sheet name.")
    parser.add_argument("--join-on", default=None, help="Join key for multi-file analysis.")
    parser.add_argument("--join-type", default=None, choices=["inner", "left", "outer"], help="Join strategy.")
    parser.add_argument("--provider", default=None, help="Override the default provider.")
    parser.add_argument("--model", default=None, help="Override the provider model.")
    parser.add_argument("--no-cache", action="store_true", help="Skip cache usage.")
    parser.add_argument("--session", default=None, help="Save the run as a named session.")
    parser.add_argument("--no-tui", action="store_true", help="Skip the TUI.")
    parser.add_argument("--template", default=None, help="Dashboard template name.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    config_parser = subparsers.add_parser("config", help="Manage config files.")
    config_subparsers = config_parser.add_subparsers(dest="config_command")

    config_set_parser = config_subparsers.add_parser("set", help="Set a provider config.")
    config_set_parser.add_argument("--provider", required=True, help="Provider name.")
    config_set_parser.add_argument("--key", required=True, help="API key.")
    config_set_parser.add_argument("--model", default=None, help="Model name.")
    config_set_parser.add_argument("--base-url", default=None, help="Provider base URL.")
    config_set_parser.set_defaults(handler=handle_config_set)

    config_update_parser = config_subparsers.add_parser("update", help="Update a provider config.")
    config_update_parser.add_argument("--provider", required=True, help="Provider name.")
    config_update_parser.add_argument("--key", default=None, help="API key.")
    config_update_parser.add_argument("--model", default=None, help="Model name.")
    config_update_parser.add_argument("--base-url", default=None, help="Provider base URL.")
    config_update_parser.set_defaults(handler=handle_config_update)

    config_show_parser = config_subparsers.add_parser("show", help="Show the current config.")
    config_show_parser.set_defaults(handler=handle_config_show)

    session_parser = subparsers.add_parser("session", help="Manage saved sessions.")
    session_subparsers = session_parser.add_subparsers(dest="session_command")

    session_list_parser = session_subparsers.add_parser("list", help="List saved sessions.")
    session_list_parser.set_defaults(handler=handle_session_list)

    session_open_parser = session_subparsers.add_parser("open", help="Open a saved session.")
    session_open_parser.add_argument("name", help="Session name.")
    session_open_parser.set_defaults(handler=handle_session_open)

    cache_parser = subparsers.add_parser("cache", help="Manage the local cache.")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command")

    cache_clear_parser = cache_subparsers.add_parser("clear", help="Clear the cache.")
    cache_clear_parser.set_defaults(handler=handle_cache_clear)

    tool_gen_parser = subparsers.add_parser("tool-gen", help="Manage pending tool generation requests.")
    tool_gen_subparsers = tool_gen_parser.add_subparsers(dest="tool_gen_command")

    tool_gen_list_parser = tool_gen_subparsers.add_parser("list", help="List pending tool requests.")
    tool_gen_list_parser.set_defaults(handler=handle_tool_gen_list)

    tool_gen_run_parser = tool_gen_subparsers.add_parser("run", help="Run pending tool generation requests.")
    tool_gen_run_parser.add_argument("--name", default=None, help="Optional request name.")
    tool_gen_run_parser.set_defaults(handler=handle_tool_gen_run)

    tool_gen_discard_parser = tool_gen_subparsers.add_parser("discard", help="Discard pending tool requests.")
    tool_gen_discard_parser.add_argument("--name", default=None, help="Optional request name.")
    tool_gen_discard_parser.set_defaults(handler=handle_tool_gen_discard)

    return parser


def handle_config_set(args: argparse.Namespace) -> int:
    """Create or update provider config values.

    Args:
        args: Parsed config set arguments.

    Returns:
        Process exit code.
    """

    update_provider_config(args.provider, api_key=args.key, model=args.model, base_url=args.base_url)
    print(f"Saved config for provider '{args.provider}'.")
    return 0


def handle_config_update(args: argparse.Namespace) -> int:
    """Update provider config values without changing the command shape.

    Args:
        args: Parsed config update arguments.

    Returns:
        Process exit code.
    """

    update_provider_config(args.provider, api_key=args.key, model=args.model, base_url=args.base_url)
    print(f"Updated config for provider '{args.provider}'.")
    return 0


def handle_config_show(args: argparse.Namespace) -> int:
    """Display the merged configuration.

    Args:
        args: Parsed config show arguments.

    Returns:
        Process exit code.
    """

    print(format_config_summary(load_config()))
    return 0


def handle_session_list(args: argparse.Namespace) -> int:
    """List saved sessions.

    Args:
        args: Parsed session list arguments.

    Returns:
        Process exit code.
    """

    sessions = list_sessions()
    if not sessions:
        print("No sessions found.")
        return 0

    for session in sessions:
        print(f"{session.get('session_name', '(unnamed)')}\t{session.get('created_at', '(unknown)')}")
    return 0


def handle_session_open(args: argparse.Namespace) -> int:
    """Show the metadata for a saved session.

    Args:
        args: Parsed session open arguments.

    Returns:
        Process exit code.
    """

    session = open_session(args.name)
    if not session:
        print(f"Session '{args.name}' was not found.")
        return 1
    print(session)
    return 0


def handle_cache_clear(args: argparse.Namespace) -> int:
    """Clear the local cache directory.

    Args:
        args: Parsed cache clear arguments.

    Returns:
        Process exit code.
    """

    cleared = clear_cache()
    print(f"Cleared cache at {cleared}.")
    return 0


def handle_tool_gen_list(args: argparse.Namespace) -> int:
    """List queued tool generation requests.

    Args:
        args: Parsed tool-gen list arguments.

    Returns:
        Process exit code.
    """

    pending = list_pending_tools()
    if not pending:
        print("No pending tool requests.")
        return 0
    for item in pending:
        print(f"{item.get('id', '(no id)')}\t{item.get('agent', '(no agent)')}\t{item.get('status', '(unknown)')}")
    return 0


def handle_tool_gen_run(args: argparse.Namespace) -> int:
    """Report pending tool requests without generating code yet.

    Args:
        args: Parsed tool-gen run arguments.

    Returns:
        Process exit code.
    """

    pending = run_pending_tools()
    if args.name is not None:
        pending = [item for item in pending if item.get("id") == args.name]
    print(f"Tool generation is not implemented in phase 0. Pending requests: {len(pending)}.")
    return 0


def handle_tool_gen_discard(args: argparse.Namespace) -> int:
    """Discard queued tool generation requests.

    Args:
        args: Parsed tool-gen discard arguments.

    Returns:
        Process exit code.
    """

    discard_pending_tools()
    print("Discarded pending tool requests.")
    return 0


def handle_main_command(args: argparse.Namespace) -> int:
    """Handle the default analysis command path.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.
    """

    if not args.files:
        return 0

    config = load_config(
        {
            "output": args.output,
            "out_dir": args.out_dir,
            "lang": args.lang,
            "focus": args.focus,
            "provider": args.provider,
            "model": args.model,
            "session": args.session,
            "template": args.template,
            "join_on": args.join_on,
            "join_type": args.join_type,
            "sheet": args.sheet,
            "fast": args.fast,
            "deep": args.deep,
            "interactive": args.interactive,
            "no_cache": args.no_cache,
            "no_tui": args.no_tui,
        }
    )

    print(format_config_summary(config))

    if len(args.files) == 1:
        file_path = args.files[0]
        try:
            reader = get_reader(file_path, sheet_name=args.sheet)
            sample = reader.read_sample(file_path, n_rows=20)
            stats = reader.read_full_stats(file_path)
            print(f"\nFile: {file_path}")
            print(f"Sample rows: {len(sample)}")
            print(f"Columns: {len(sample.columns)}")
            print(f"Full rows: {stats.get('row_count', 0)}")
            print(f"Read strategy: {stats.get('read_strategy', 'full')}")
        except UnsupportedFormatError as exc:
            print(f"\nFile: {file_path}")
            print(f"Error: {exc}")
        except MissingDependencyError as exc:
            print(f"\nFile: {file_path}")
            print(f"Error: {exc}")
    else:
        try:
            frames = [get_reader(file_path, sheet_name=args.sheet).read_sample(file_path, n_rows=10_000) for file_path in args.files]
            join_key = args.join_on or infer_join_key(frames)
            if join_key is None:
                print("\nUnable to infer a join key. Use --join-on.")
                return 1
            merged = join_files(args.files, join_on=join_key, join_type=args.join_type or "inner", sheet_name=args.sheet)
            print(f"\nMulti-file join key: {join_key}")
            print(f"Merged rows: {len(merged)}")
            print(f"Merged columns: {len(merged.columns)}")
        except UnsupportedFormatError as exc:
            print(f"\nError: {exc}")
            return 1
        except MissingDependencyError as exc:
            print(f"\nError: {exc}")
            return 1

    if should_launch_tui(args.no_tui):
        app = DatavizApp(
            context=PipelineContext(
                file_paths=list(args.files),
                output_format=config.get("output", "html"),
                mode="deep" if args.deep else "default",
                lang=config.get("lang", "auto"),
                extra={"out_dir": config.get("out_dir", "./dataviz_output")},
            )
        )
        print("\n" + app.dashboard().render())
    else:
        print("\nTUI skipped.")

    exporter = get_exporter(config.get("output", "html"))
    output_path = exporter.write(
        [
            exporter.render_section(
                {"id": "summary", "title": "Summary"},
                f"Analyzed {len(args.files)} file(s).",
            )
        ],
        config.get("out_dir", "./dataviz_output"),
    )
    print(f"\nExported report: {output_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the DataViz CLI.

    Args:
        argv: Optional command-line arguments.

    Returns:
        Process exit code.
    """

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    handler = getattr(args, "handler", None)
    if handler is not None:
        return handler(args)

    if getattr(args, "command", None) is None and not args.files:
        parser.print_help()
        return 0

    return handle_main_command(args)
