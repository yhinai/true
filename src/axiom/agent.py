from __future__ import annotations

import asyncio
from pathlib import Path
import traceback
import uuid
from dataclasses import dataclass, field

import acp

from .pipeline import AxiomPipeline, PipelineInput
from .prompt_parser import GUIDANCE, load_prompt_paths, parse_prompt

LOG_PATH = Path("/Users/alhinai/Desktop/TRUE/.axiom_acp.log")


@dataclass
class SessionState:
    cwd: str
    session_id: str
    history: list[str] = field(default_factory=list)


class AxiomAgent:
    def __init__(self) -> None:
        self.client = None
        self.sessions: dict[str, SessionState] = {}
        self.pipeline = AxiomPipeline()

    def on_connect(self, conn) -> None:
        self.client = conn

    async def initialize(self, protocol_version: int, client_capabilities=None, client_info=None, **kwargs):
        return acp.InitializeResponse(
            protocolVersion=protocol_version,
            agentInfo=acp.schema.Implementation(name="Axiom", version="0.1.0"),
            availableModes=[],
            availableModels=[],
        )

    async def new_session(self, cwd: str, mcp_servers=None, **kwargs):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = SessionState(cwd=cwd, session_id=session_id)
        return acp.NewSessionResponse(sessionId=session_id)

    async def load_session(self, cwd: str, session_id: str, mcp_servers=None, **kwargs):
        self.sessions.setdefault(session_id, SessionState(cwd=cwd, session_id=session_id))
        return acp.LoadSessionResponse(sessionId=session_id)

    async def list_sessions(self, cursor=None, cwd=None, **kwargs):
        return acp.schema.ListSessionsResponse(items=[], nextCursor=None)

    async def set_session_mode(self, mode_id: str, session_id: str, **kwargs):
        return acp.SetSessionModeResponse(modeId=mode_id)

    async def set_session_model(self, model_id: str, session_id: str, **kwargs):
        return acp.SetSessionModelResponse(modelId=model_id)

    async def set_config_option(self, config_id: str, session_id: str, value, **kwargs):
        return acp.SetSessionConfigOptionResponse()

    async def authenticate(self, method_id: str, **kwargs):
        return acp.AuthenticateResponse()

    async def prompt(self, prompt, session_id: str, message_id=None, **kwargs):
        try:
            text = "\n".join(block.text for block in prompt if hasattr(block, "text"))
            self._log(f"prompt start session={session_id} message_id={message_id!r} text={text!r}")
            self.sessions.setdefault(session_id, SessionState(cwd=".", session_id=session_id)).history.append(text)
            ledger = self._handle_prompt(text)
            self._log(f"prompt result session={session_id} ledger={ledger!r}")
            if self.client is not None:
                await self.client.session_update(
                    session_id=session_id,
                    update=acp.update_agent_message_text(ledger),
                )
            return acp.PromptResponse(stopReason="end_turn", userMessageId=message_id)
        except Exception as exc:
            error_text = f"Axiom ACP error: {exc}"
            self._log(error_text)
            self._log(traceback.format_exc())
            if self.client is not None:
                await self.client.session_update(
                    session_id=session_id,
                    update=acp.update_agent_message_text(error_text),
                )
            return acp.PromptResponse(stopReason="end_turn", userMessageId=message_id)

    async def fork_session(self, cwd: str, session_id: str, mcp_servers=None, **kwargs):
        new_session_id = str(uuid.uuid4())
        self.sessions[new_session_id] = SessionState(cwd=cwd, session_id=new_session_id)
        return acp.schema.ForkSessionResponse(sessionId=new_session_id)

    async def resume_session(self, cwd: str, session_id: str, mcp_servers=None, **kwargs):
        self.sessions.setdefault(session_id, SessionState(cwd=cwd, session_id=session_id))
        return acp.schema.ResumeSessionResponse(sessionId=session_id)

    async def close_session(self, session_id: str, **kwargs):
        self.sessions.pop(session_id, None)
        return acp.schema.CloseSessionResponse()

    async def cancel(self, session_id: str, **kwargs) -> None:
        return None

    async def ext_method(self, method: str, params: dict[str, object]) -> dict[str, object]:
        return {}

    async def ext_notification(self, method: str, params: dict[str, object]) -> None:
        return None

    def _handle_prompt(self, text: str) -> str:
        try:
            parsed = load_prompt_paths(parse_prompt(text))
        except (FileNotFoundError, ValueError) as exc:
            return f"{exc}\n\n{GUIDANCE}"

        if parsed.bug_path:
            return self.pipeline.run_and_render(
                PipelineInput(
                    bug_source_path=parsed.bug_path,
                    test_path=parsed.test_path,
                    bug_text=parsed.error_info or parsed.context,
                )
            )
        if parsed.is_actionable:
            return self.pipeline.run_and_render(
                PipelineInput(
                    function_source=parsed.function_source,
                    bug_text=parsed.error_info or parsed.context,
                    run_tests=False,
                )
            )
        return f"Axiom ACP agent is live.\n\n{GUIDANCE}"

    @staticmethod
    def _log(message: str) -> None:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n")


async def _main() -> None:
    await acp.run_agent(AxiomAgent())


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
