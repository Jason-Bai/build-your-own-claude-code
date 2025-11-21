"""Logging query commands"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from .base import Command, CLIContext
from ..logging import get_action_logger
from ..logging.constants import DEFAULT_LOG_DIR
from ..logging.maintenance import LogMaintenance


class LogCommand(Command):
    """Query and display action logs"""

    @property
    def name(self) -> str:
        return "log"

    @property
    def description(self) -> str:
        return "Query and manage logs: /log [filters|stats|cleanup|help]"

    @property
    def aliases(self):
        return ["logs"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        """
        Query logs with filters or manage log files:

        Query:
        - /log : Show last 10 logs
        - /log --today : Show today's logs
        - /log --last 20 : Show last 20 logs
        - /log --action-type TOOL_CALL : Filter by action type
        - /log --session <session_id> : Filter by session

        Maintenance:
        - /log stats : Show disk usage statistics
        - /log cleanup : Run maintenance (compress + delete old logs)
        - /log help : Show detailed help
        """
        # Check for maintenance subcommands first
        args_stripped = args.strip().lower() if args else ""

        if args_stripped == "help":
            return self._show_help()
        elif args_stripped == "stats":
            return self._show_stats(context)
        elif args_stripped == "cleanup":
            return self._run_cleanup(context)

        # Otherwise, treat as log query
        filters = self._parse_args(args)
        log_dir = Path(context.config.get("logging", {}).get("log_dir", DEFAULT_LOG_DIR)).expanduser()
        logs = self._read_logs(log_dir, filters)

        if not logs:
            if filters["format"] == "json":
                return json.dumps({"logs": [], "count": 0})
            return "📋 No logs found matching the filters"

        # Format output based on format parameter
        if filters["format"] == "json":
            return json.dumps({"logs": logs, "count": len(logs)}, indent=2, ensure_ascii=False)
        else:
            return self._format_logs(logs, filters)

    def _parse_args(self, args: str) -> Dict:
        """Parse command arguments into filters"""
        filters = {
            "limit": 10,
            "today": False,
            "action_type": None,
            "session_id": None,
            "status": None,
            "keyword": None,
            "format": "text"
        }

        if not args:
            return filters

        parts = args.strip().split()
        i = 0
        while i < len(parts):
            if parts[i] == "--today":
                filters["today"] = True
                i += 1
            elif parts[i] == "--last" and i + 1 < len(parts):
                try:
                    filters["limit"] = int(parts[i + 1])
                    i += 2
                except ValueError:
                    i += 1
            elif parts[i] == "--action-type" and i + 1 < len(parts):
                filters["action_type"] = parts[i + 1]
                i += 2
            elif parts[i] == "--session" and i + 1 < len(parts):
                filters["session_id"] = parts[i + 1]
                i += 2
            elif parts[i] == "--status" and i + 1 < len(parts):
                filters["status"] = parts[i + 1]
                i += 2
            elif parts[i] == "--keyword" and i + 1 < len(parts):
                filters["keyword"] = parts[i + 1]
                i += 2
            elif parts[i] == "--format" and i + 1 < len(parts):
                filters["format"] = parts[i + 1]
                i += 2
            else:
                i += 1

        return filters

    def _read_logs(self, log_dir: Path, filters: Dict) -> List[Dict]:
        """Read and filter log files"""
        logs = []

        if not log_dir.exists():
            return logs

        # Determine which files to read
        if filters["today"]:
            # Only read today's file
            today_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
            log_files = [today_file] if today_file.exists() else []
        else:
            # Read all log files, sorted by date (newest first)
            log_files = sorted(log_dir.glob("*.jsonl"), reverse=True)

        # Read logs from files
        for log_file in log_files:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line)

                            # Apply filters
                            if filters["action_type"] and log_entry.get("action_type") != filters["action_type"]:
                                continue
                            if filters["session_id"] and log_entry.get("session_id") != filters["session_id"]:
                                continue
                            if filters["status"] and log_entry.get("status") != filters["status"]:
                                continue
                            if filters["keyword"]:
                                # Search keyword in all string fields
                                found = False
                                for key, value in log_entry.items():
                                    if isinstance(value, str) and filters["keyword"].lower() in value.lower():
                                        found = True
                                        break
                                if not found:
                                    continue

                            logs.append(log_entry)

                            # Stop if we have enough logs
                            if len(logs) >= filters["limit"] * 2:  # Read more than limit for filtering
                                break
                        except json.JSONDecodeError:
                            continue

                # Stop if we have enough logs
                if len(logs) >= filters["limit"] * 2:
                    break
            except Exception:
                continue

        # Return limited number of logs (reversed for chronological order)
        return logs[-filters["limit"]:]

    def _format_logs(self, logs: List[Dict], filters: Dict) -> str:
        """Format logs for display"""
        output = ["📋 Action Logs", ""]

        # Show filters
        filter_info = []
        if filters["today"]:
            filter_info.append("today only")
        if filters["action_type"]:
            filter_info.append(f"type={filters['action_type']}")
        if filters["session_id"]:
            filter_info.append(f"session={filters['session_id'][:8]}...")

        if filter_info:
            output.append(f"Filters: {', '.join(filter_info)}")
            output.append("")

        output.append(f"Showing last {len(logs)} logs:")
        output.append("")

        # Display logs
        for log in logs:
            timestamp = log.get("timestamp", "?")
            action_type = log.get("action_type", "?")
            session_id = log.get("session_id", "?")[:8]
            action_num = log.get("action_number", "?")
            status = log.get("status", "?")

            # Format header
            output.append(f"[{timestamp}] #{action_num} {action_type} (session: {session_id}) - {status}")

            # Format key details based on action type
            details = []
            if action_type == "TOOL_CALL":
                tool_name = log.get("tool_name", "?")
                details.append(f"  Tool: {tool_name}")
            elif action_type == "TOOL_RESULT":
                tool_name = log.get("tool_name", "?")
                output_preview = str(log.get("output", ""))[:100]
                details.append(f"  Tool: {tool_name}")
                details.append(f"  Output: {output_preview}...")
            elif action_type == "TOOL_ERROR":
                tool_name = log.get("tool_name", "?")
                error = log.get("error", "?")
                details.append(f"  Tool: {tool_name}")
                details.append(f"  Error: {error}")
            elif action_type == "TOOL_PERMISSION":
                tool_name = log.get("tool_name", "?")
                permission_level = log.get("permission_level", "?")
                user_decision = log.get("user_decision", "?")
                decision_type = log.get("decision_type", "?")
                details.append(f"  Tool: {tool_name} ({permission_level})")
                details.append(f"  Decision: {user_decision} ({decision_type})")
            elif action_type == "LLM_REQUEST":
                provider = log.get("provider", "?")
                model = log.get("model", "?")
                msg_count = log.get("messages_count", "?")
                details.append(f"  {provider}/{model} ({msg_count} messages)")
            elif action_type == "LLM_RESPONSE":
                input_tokens = log.get("input_tokens", 0)
                output_tokens = log.get("output_tokens", 0)
                stop_reason = log.get("stop_reason", "?")
                details.append(f"  Tokens: {input_tokens} in / {output_tokens} out")
                details.append(f"  Stop: {stop_reason}")
            elif action_type == "AGENT_STATE_CHANGE":
                from_state = log.get("from_state", "?")
                to_state = log.get("to_state", "?")
                details.append(f"  {from_state} → {to_state}")
            elif action_type == "AGENT_THINKING":
                msg_count = log.get("message_count", 0)
                tool_count = log.get("tool_count", 0)
                details.append(f"  Messages: {msg_count}, Tools: {tool_count}")
            elif action_type == "SESSION_START":
                project = log.get("project_name", "?")
                details.append(f"  Project: {project}")
            elif action_type == "SESSION_END":
                duration = log.get("duration_seconds", 0)
                details.append(f"  Duration: {duration:.2f}s")
            elif action_type == "SESSION_PAUSE":
                reason = log.get("reason", "unknown")
                pause_time = log.get("pause_time", "?")
                details.append(f"  Reason: {reason}")
                details.append(f"  Paused at: {pause_time}")
            elif action_type == "SESSION_RESUME":
                resume_time = log.get("resume_time", "?")
                details.append(f"  Resumed at: {resume_time}")
            elif action_type == "LLM_ERROR":
                provider = log.get("provider", "?")
                model = log.get("model", "?")
                error = log.get("error", "?")
                error_type = log.get("error_type", "?")
                details.append(f"  {provider}/{model}")
                details.append(f"  Error: {error_type}: {error}")
            elif action_type == "SYSTEM_ERROR":
                error = log.get("error", "?")
                error_type = log.get("error_type", "?")
                context = log.get("context", "")
                details.append(f"  Error: {error_type}: {error}")
                if context:
                    details.append(f"  Context: {context}")
            elif action_type == "SYSTEM_WARNING":
                warning = log.get("warning", log.get("error", "?"))
                context = log.get("context", "")
                details.append(f"  Warning: {warning}")
                if context:
                    details.append(f"  Context: {context}")

            output.extend(details)
            output.append("")

        return "\n".join(output)

    def _show_help(self) -> str:
        """Show comprehensive help message"""
        return """📚 Log Command Help

Query Logs:
  /log                              Show last 10 logs
  /log --today                      Show today's logs only
  /log --last N                     Show last N logs (e.g., /log --last 20)
  /log --action-type TYPE           Filter by action type
  /log --session SESSION_ID         Filter by session ID
  /log --status STATUS              Filter by status (success/error/pending)
  /log --keyword KEYWORD            Search for keyword in all fields
  /log --format json                Output in JSON format

  Action Types:
    USER_INPUT, USER_COMMAND, SESSION_START, SESSION_END,
    SESSION_PAUSE, SESSION_RESUME, AGENT_STATE_CHANGE, AGENT_THINKING,
    TOOL_CALL, TOOL_RESULT, TOOL_ERROR, TOOL_PERMISSION,
    LLM_REQUEST, LLM_RESPONSE, LLM_ERROR,
    SYSTEM_ERROR, SYSTEM_WARNING

Manage Logs:
  /log stats                        Show disk usage statistics
  /log cleanup                      Run maintenance (compress + delete old logs)
  /log help                         Show this help message

Examples:
  /log --last 50
  /log --action-type TOOL_CALL
  /log --today --action-type LLM_REQUEST
  /log stats
  /log cleanup
"""

    def _show_stats(self, context: CLIContext) -> str:
        """Show disk usage statistics"""
        log_config = context.config.get("logging", {})
        log_dir = Path(log_config.get("log_dir", DEFAULT_LOG_DIR)).expanduser()
        maint_config = log_config.get("maintenance", {})

        maintenance = LogMaintenance(
            log_dir=log_dir,
            retention_days=maint_config.get("retention_days", 30),
            max_size_mb=maint_config.get("max_size_mb", 1000),
            compress_after_days=maint_config.get("compress_after_days", 7),
            enabled=maint_config.get("enabled", True)
        )

        stats = maintenance.get_disk_usage_stats()

        output = ["📊 Log Disk Usage Statistics", ""]
        output.append(f"Log Directory: {maintenance.log_dir}")
        output.append("")
        output.append(f"Total Files: {stats['total_files']}")
        output.append(f"  • Uncompressed: {stats['uncompressed_files']} (.jsonl)")
        output.append(f"  • Compressed: {stats['compressed_files']} (.jsonl.gz)")
        output.append("")
        output.append(f"Total Size: {stats['total_size_mb']:.2f} MB")
        output.append(f"Max Size Limit: {maintenance.max_size_mb} MB")

        if stats['oldest_log']:
            output.append("")
            output.append(f"Oldest Log: {stats['oldest_log']}")
            output.append(f"Newest Log: {stats['newest_log']}")

        output.append("")
        output.append("Maintenance Settings:")
        output.append(f"  • Retention: {maintenance.retention_days} days")
        output.append(f"  • Compress after: {maintenance.compress_after_days} days")
        output.append(f"  • Enabled: {maintenance.enabled}")

        return "\n".join(output)

    def _run_cleanup(self, context: CLIContext) -> str:
        """Run maintenance cleanup"""
        log_config = context.config.get("logging", {})
        log_dir = Path(log_config.get("log_dir", DEFAULT_LOG_DIR)).expanduser()
        maint_config = log_config.get("maintenance", {})

        maintenance = LogMaintenance(
            log_dir=log_dir,
            retention_days=maint_config.get("retention_days", 30),
            max_size_mb=maint_config.get("max_size_mb", 1000),
            compress_after_days=maint_config.get("compress_after_days", 7),
            enabled=maint_config.get("enabled", True)
        )

        if not maintenance.enabled:
            return "❌ Log maintenance is disabled in settings"

        output = ["🧹 Running Log Maintenance...", ""]

        try:
            stats = maintenance.run_maintenance()

            if "error" in stats:
                output.append(f"❌ Error: {stats['error']}")
            else:
                output.append("✓ Maintenance completed successfully")
                output.append("")
                output.append(f"Compressed: {stats['compressed_files']} files")
                output.append(f"Deleted: {stats['deleted_files']} files")
                output.append(f"Space Freed: {stats['space_freed_mb']:.2f} MB")
                output.append(f"Total Size: {stats['total_size_mb']:.2f} MB")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Maintenance failed: {str(e)}"
