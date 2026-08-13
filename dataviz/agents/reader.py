from __future__ import annotations

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext
from dataviz.readers import get_reader
from dataviz.tools.loader import ToolRegistry


class ReaderAgent(BaseAgent):
    """Load sample data and schema information."""

    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        """Initialize the reader agent."""

        super().__init__(tool_registry=tool_registry)

    def run(self, context: PipelineContext) -> AgentResult:
        """Read the first file and return sample metadata."""

        file_path = context.file_paths[0]
        reader = get_reader(file_path, sheet_name=context.extra.get("sheet"))
        sample = reader.read_sample(file_path, n_rows=20)
        schema = self.call_tool("detect_schema", sample)
        stats = reader.read_full_stats(file_path)
        return AgentResult(output={"sample_rows": len(sample)}, context_updates={"schema": schema, "stats": stats, "sample_df": sample})
