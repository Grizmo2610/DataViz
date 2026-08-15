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

SUBCOMMAND_ROOTS = {"config", "session", "cache", "tool-gen"}


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
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print detailed debug log for every pipeline step.")

    add_subcommand_parsers(parser)

    return parser


def build_subcommand_parser() -> argparse.ArgumentParser:
    """Build a parser for command-style subcommands only.

    Returns:
        A parser that accepts config/session/cache/tool-gen subcommands.
    """

    parser = argparse.ArgumentParser(
        prog="dataviz",
        description="Automated data visualization CLI.",
    )
    add_subcommand_parsers(parser)
    return parser


def add_subcommand_parsers(parser: argparse.ArgumentParser) -> None:
    """Attach DataViz subcommand parsers to a parser.

    Args:
        parser: Parser that should receive the subcommands.
    """

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


def handle_config_set(args: argparse.Namespace) -> int:
    """Create or update provider config values (used by both ``set`` and ``update`` sub-commands).

    Args:
        args: Parsed config arguments.  ``args.key`` may be ``None`` for the
            ``update`` sub-command, in which case only the supplied fields are
            changed.

    Returns:
        Process exit code.
    """

    update_provider_config(args.provider, api_key=args.key, model=args.model, base_url=args.base_url)
    print(f"Config for provider '{args.provider}' saved.")
    return 0


# ``update`` is an alias so existing scripts that use ``dataviz config update``
# continue to work without change.
handle_config_update = handle_config_set


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

    Runs the full Orchestrator pipeline (Reader → EDA → Viz → Report) and
    writes the report to disk.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.
    """
    if not args.files:
        return 0

    # -- Logging setup ---------------------------------------------------------
    import logging as _logging
    import datetime as _dt
    import os as _os

    # Always write full DEBUG log to a per-session file under out_dir/logs/
    _raw_out_dir = (args.out_dir or "./dataviz_output")
    _log_dir = _os.path.join(_raw_out_dir, "logs")
    _os.makedirs(_log_dir, exist_ok=True)
    _session_ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    _log_file = _os.path.join(_log_dir, f"session_{_session_ts}.log")

    _fmt = "%(asctime)s.%(msecs)03d  %(levelname)-5s  %(message)s"
    _datefmt = "%H:%M:%S"

    root_logger = _logging.getLogger()
    root_logger.setLevel(_logging.DEBUG)  # capture everything

    # File handler — always DEBUG
    _fh = _logging.FileHandler(_log_file, encoding="utf-8")
    _fh.setLevel(_logging.DEBUG)
    _fh.setFormatter(_logging.Formatter(_fmt, datefmt=_datefmt))
    root_logger.addHandler(_fh)

    # Console handler — DEBUG if --verbose, WARNING otherwise
    _ch = _logging.StreamHandler()
    _ch.setLevel(_logging.DEBUG if getattr(args, "verbose", False) else _logging.WARNING)
    _ch.setFormatter(_logging.Formatter(_fmt, datefmt=_datefmt))
    root_logger.addHandler(_ch)

    _logging.getLogger("dataviz").debug(
        "Session started  log=%s  args=%s", _log_file,
        {k: v for k, v in vars(args).items() if v is not None and v is not False}
    )

    config = load_config(
        {
            "output":     args.output,
            "out_dir":    args.out_dir,
            "lang":       args.lang,
            "focus":      args.focus,
            "provider":   args.provider,
            "model":      args.model,
            "session":    args.session,
            "template":   args.template,
            "join_on":    args.join_on,
            "join_type":  args.join_type,
            "sheet":      args.sheet,
            "fast":       args.fast,
            "deep":       args.deep,
            "interactive": args.interactive,
            "no_cache":   args.no_cache,
            "no_tui":     args.no_tui,
        }
    )

    output_format = config.get("output", "html")
    out_dir       = config.get("out_dir", "./dataviz_output")
    lang          = config.get("lang", "auto")
    mode          = "deep" if args.deep else ("fast" if args.fast else "default")

    # -- Resolve input: single file or multi-file join ------------------------
    file_paths = list(args.files)

    if len(file_paths) > 1:
        try:
            frames   = [get_reader(fp, sheet_name=args.sheet).read_sample(fp, n_rows=500) for fp in file_paths]
            join_key = args.join_on or infer_join_key(frames)
            if join_key is None:
                print("Unable to infer a join key from shared columns. Use --join-on.")
                return 1
            print(f"Joining {len(file_paths)} files on '{join_key}' ({args.join_type or 'inner'}) …")
            import tempfile, os
            merged_df = join_files(
                file_paths,
                join_on=join_key,
                join_type=args.join_type or "inner",
                sheet_name=args.sheet,
            )
            # Write merged frame to a temp CSV so ReaderAgent can read it normally
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
            merged_df.to_csv(tmp, index=False)
            tmp.close()
            file_paths = [tmp.name]
            print(f"Merged: {len(merged_df):,} rows × {len(merged_df.columns)} columns")
        except (UnsupportedFormatError, MissingDependencyError, KeyError) as exc:
            print(f"Error: {exc}")
            return 1

    # -- Build provider -------------------------------------------------------
    from dataviz.providers import get_provider
    try:
        provider = get_provider(config)
    except Exception as exc:
        print(f"\n  X Provider error: {exc}")
        print("    Run: dataviz config set --provider <name> --key <key>")
        return 1

    if not provider or not getattr(provider, "api_key", ""):
        print("\n  X No API key configured — cannot run without a provider.")
        print("    Run: dataviz config set --provider <name> --key <key>")
        return 1

    # -- Run Orchestrator pipeline --------------------------------------------
    from dataviz.agents.orchestrator import Orchestrator
    from dataviz.tools.loader import ToolRegistry

    context = PipelineContext(
        file_paths=file_paths,
        output_format=output_format,
        mode=mode,
        focus=args.focus,
        lang=lang,
        extra={
            "out_dir":    out_dir,
            "sheet":      args.sheet,
            "template":   args.template or "default",
            "no_cache":   args.no_cache,
        },
    )

    # -- Print run header -----------------------------------------------------
    files_label = args.files[0] + (f" (+{len(args.files)-1} more)" if len(args.files) > 1 else "")
    provider_label = f"{type(provider).__name__} / {provider.model}"
    print()
    print(f"  File      : {files_label}")
    print(f"  Output    : {output_format}  ->  {out_dir}")
    print(f"  Provider  : {provider_label}")
    print(f"  Mode      : {mode}")
    print()

    # -- Instrumented pipeline run ---------------------------------------------
    import time as _time

    STAGE_LABELS = {
        "reader": "Reading file & schema detection",
        "eda":    "EDA  (stats, nulls, outliers, time-series)",
        "viz":    "Rendering charts",
        "report": "Writing report",
    }

    class _VerboseOrch(Orchestrator):
        def run(self, ctx):
            from dataviz.agents.eda import EDAAgent
            from dataviz.agents.reader import ReaderAgent
            from dataviz.agents.report import ReportAgent
            from dataviz.agents.viz import VizAgent
            from dataviz.agents.orchestrator import PipelineState

            results = {}
            for stage_name, agent_cls in [
                ("reader", ReaderAgent),
                ("eda",    EDAAgent),
                ("viz",    VizAgent),
                ("report", ReportAgent),
            ]:
                label = STAGE_LABELS.get(stage_name, stage_name)
                print(f"  [{stage_name.upper():6}] {label} ...", end="", flush=True)
                t0 = _time.monotonic()
                agent = self._make_agent(agent_cls)
                result = agent.run(ctx)
                elapsed = _time.monotonic() - t0
                ctx.extra.update(result.context_updates)

                # Stage-specific detail line
                if stage_name == "reader":
                    rows = ctx.extra.get("stats", {}).get("row_count", "?")
                    cols = ctx.extra.get("schema", {}).get("column_count", "?")
                    detail = f"{rows:,} rows x {cols} cols" if isinstance(rows, int) else str(rows)
                elif stage_name == "eda":
                    detail = "done"
                elif stage_name == "viz":
                    charts = result.output.get("charts", [])
                    ok = sum(1 for c in charts if c.get("vega_spec") and not c.get("error"))
                    detail = f"{ok}/{len(charts)} charts OK"
                elif stage_name == "report":
                    detail = "agent"
                else:
                    detail = ""

                print(f" {elapsed:.1f}s  {detail}")
                results[stage_name] = result.output

            return PipelineState(context=ctx, results=results)

    try:
        orch  = _VerboseOrch(provider=provider, tool_registry=ToolRegistry())
        state = orch.run(context)
    except Exception as exc:
        from dataviz.agents.base import LLMEmptyResponseError, LLMAPIError
        print()
        if isinstance(exc, LLMEmptyResponseError):
            print(f"  X LLM returned empty content  [{exc.reason}]")
            print(f"    {exc.detail}")
            print()
            print("  Possible fixes:")
            print("    • Check your API key:  dataviz config show")
            print("    • Check model name:    dataviz config set --provider <name> --model <model>")
            print("    • Check API quota / rate limit on your provider dashboard")
        elif isinstance(exc, LLMAPIError):
            print(f"  X LLM API error  [{exc.reason}]")
            print(f"    {exc.detail}")
        else:
            print(f"  X Pipeline error: {type(exc).__name__}: {exc}")
            import traceback as _tb; _tb.print_exc()
        return 1

    # -- Print brief terminal summary -----------------------------------------
    reader_out  = state.results.get("reader", {})
    report_out  = state.results.get("report", {})
    viz_out     = state.results.get("viz", {})

    n_rows    = state.context.extra.get("stats", {}).get("row_count", reader_out.get("sample_rows", "?"))
    n_cols    = state.context.extra.get("schema", {}).get("column_count", "?")
    n_charts  = len(viz_out.get("charts", []))
    out_path  = report_out.get("report", {}).get("output_path", "?")

    print(f"\n{'-'*50}")
    print(f"  Rows      : {n_rows:,}" if isinstance(n_rows, int) else f"  Rows      : {n_rows}")
    print(f"  Columns   : {n_cols}")
    print(f"  Charts    : {n_charts}")
    print(f"  Report    : {out_path}")
    print(f"{'-'*50}\n")

    # -- Optional TUI ---------------------------------------------------------
    if should_launch_tui(args.no_tui):
        try:
            app = DatavizApp(context=context)
            print(app.dashboard().render())
        except Exception:  # noqa: BLE001
            pass

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the DataViz CLI.

    Args:
        argv: Optional command-line arguments.

    Returns:
        Process exit code.
    """

    arg_list = list(argv) if argv is not None else sys.argv[1:]

    # Route to the correct parser.
    # Problem: argparse cannot distinguish positional file paths from subcommand
    # names when both are positional.  The fix: if the first token is a known
    # subcommand root, use the subcommand-only parser; otherwise collect any
    # leading non-flag tokens as file paths ourselves before handing the rest
    # to the main parser (which still has `files` for --help accuracy).
    if arg_list and arg_list[0] in SUBCOMMAND_ROOTS:
        parser = build_subcommand_parser()
        args = parser.parse_args(arg_list)
    else:
        # Separate file arguments (anything before the first flag or subcommand)
        # from the rest so argparse never sees them as a subcommand candidate.
        pre_files: list[str] = []
        rest: list[str] = []
        collecting_files = True
        for token in arg_list:
            if collecting_files and not token.startswith("-") and token not in SUBCOMMAND_ROOTS:
                pre_files.append(token)
            else:
                collecting_files = False
                rest.append(token)

        parser = build_parser()
        # Parse without the leading file tokens so subparsers never see them
        args = parser.parse_args(rest)
        # Merge pre_files with any --files already parsed (there won't be any,
        # but be defensive)
        existing = list(getattr(args, "files", None) or [])
        args.files = pre_files + existing

    handler = getattr(args, "handler", None)
    if handler is not None:
        return handler(args)

    if getattr(args, "command", None) is None and not args.files:
        parser.print_help()
        return 0

    return handle_main_command(args)