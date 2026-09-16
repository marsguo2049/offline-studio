from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from urllib.parse import unquote, urlparse

from comfyui_py_workflow.studio import OfflineStudio
from comfyui_py_workflow.batch_studio import MAX_FILE_BYTES, BatchStudio
from comfyui_py_workflow.comic_studio import ComicStudio


WEB_ROOT = Path(__file__).with_name("web")


from comfyui_py_workflow.local_ui import StudioRequestHandler as BatchRequestHandler
from comfyui_py_workflow.local_ui import WEB_ROOT as COMFY_WEB


class CreativeRequestHandler(BatchRequestHandler):
    studio: OfflineStudio
    batch: BatchStudio
    comic: ComicStudio
    server_version = "OfflineStudio/0.2"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith(("/api/batch/", "/batch-media/")):
            return super().do_GET()
        try:
            if parsed.path == "/":
                self._send_file(WEB_ROOT / "creative.html", cache=False)
                return
            if parsed.path.startswith("/static/"):
                name = Path(parsed.path).name
                if name in {"app.js", "comic.js", "navigation.js"}:
                    root = WEB_ROOT
                elif name in {"batch.js", "style.css"}:
                    root = COMFY_WEB
                else:
                    self.send_error(HTTPStatus.NOT_FOUND, "Unknown asset")
                    return
                self._send_file(root / name, cache=False)
                return
            if parsed.path == "/api/projects":
                self._send_json({"projects": self.studio.list_projects()})
                return
            if parsed.path == "/api/comic/jobs":
                self._send_json({"jobs": self.comic.list_jobs()})
                return
            if parsed.path == "/api/comic/job":
                self._send_json(self.comic.get(self._query(parsed, "id")))
                return
            if parsed.path.startswith("/comic-media/"):
                parts = parsed.path.split("/", 3)
                if len(parts) != 4:
                    raise ValueError("Invalid comic media URL")
                self._send_media_file(self.comic.media_path(unquote(parts[2]), unquote(parts[3])))
                return
            if parsed.path == "/api/project":
                project_id = self._query(parsed, "id")
                self._send_json(self.studio.project_payload(project_id))
                return
            if parsed.path == "/api/status":
                lm_url = self._query(parsed, "lm", "http://127.0.0.1:1234/v1")
                comfy_url = self._query(parsed, "comfy", "http://127.0.0.1:8188")
                self._send_json(self.studio.service_status(lm_url, comfy_url))
                return
            if parsed.path.startswith("/media/"):
                parts = parsed.path.split("/", 3)
                if len(parts) != 4:
                    raise ValueError("Invalid media URL")
                project_id = unquote(parts[2])
                relative = unquote(parts[3])
                self._send_media_file(self.studio.media_path(project_id, relative))
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_error(exc)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith(("/api/batch/", "/batch-media/")):
            return super().do_POST()
        try:
            self._check_origin()
            if parsed.path == "/api/comic/file":
                self._send_json(self.comic.create(filename=self._query(parsed, "filename"),
                    data=self._read_body(max_bytes=100 * 1024 * 1024)), status=201)
                return
            if parsed.path == "/api/comic/reference":
                self._send_json(self.comic.attach_reference(self._query(parsed, "id"),
                    self._read_body(max_bytes=MAX_FILE_BYTES)), status=201)
                return
            if parsed.path == "/api/project/file":
                filename = self._query(parsed, "filename")
                data = self._read_body(max_bytes=100 * 1024 * 1024)
                self._send_json(self.studio.create_file_project(filename, data), status=201)
                return
            if parsed.path == "/api/project/reference-image":
                project_id = self._query(parsed, "project_id")
                filename = self._query(parsed, "filename")
                data = self._read_body(max_bytes=25 * 1024 * 1024)
                self._send_json(
                    self.studio.attach_reference_image(project_id, filename, data),
                    status=201,
                )
                return

            body = self._read_json()
            if parsed.path == "/api/comic/create":
                self._send_json(self.comic.create(str(body.get("text", ""))), status=201)
            elif parsed.path == "/api/comic/plan":
                self._send_json(self.comic.plan(str(body["id"]), body), status=202)
            elif parsed.path == "/api/comic/save-plan":
                self._send_json(self.comic.save_plan(str(body["id"]), body.get("plan"), int(body["revision"])))
            elif parsed.path == "/api/comic/start":
                self._send_json(self.comic.start(str(body["id"]), body), status=202)
            elif parsed.path == "/api/comic/cancel":
                self._send_json(self.comic.cancel(str(body["id"])))
            elif parsed.path == "/api/comic/open-folder":
                self.comic.open_folder(str(body["id"]))
                self._send_json({"ok": True})
            elif parsed.path == "/api/project/text":
                result = self.studio.create_text_project(
                    str(body.get("text", "")),
                    str(body.get("filename", "story.md")),
                )
                self._send_json(result, status=201)
            elif parsed.path == "/api/analyze":
                self._send_json(self.studio.analyze(
                    str(body["project_id"]),
                    lm_studio_url=str(body.get("lm_studio_url", "http://127.0.0.1:1234/v1")),
                    model=str(body.get("model") or "") or None,
                    output_language=str(body.get("output_language", "Chinese")),
                ))
            elif parsed.path == "/api/plan":
                self._send_json(self.studio.create_plan(
                    str(body["project_id"]),
                    duration_seconds=int(body["duration_seconds"]),
                    aspect_ratio=str(body.get("aspect_ratio", "16:9")),
                    style=str(body.get("style") or "") or None,
                    dialogue_mode=str(body.get("dialogue_mode", "auto")),
                    lm_studio_url=str(body.get("lm_studio_url", "http://127.0.0.1:1234/v1")),
                    model=str(body.get("model") or "") or None,
                    output_language=str(body.get("output_language", "Chinese")),
                ))
            elif parsed.path == "/api/save-plan":
                plan = body.get("plan")
                if not isinstance(plan, dict):
                    raise ValueError("plan must be a JSON object")
                self._send_json(self.studio.save_plan(str(body["project_id"]), plan))
            elif parsed.path == "/api/generate":
                self._send_json(self.studio.start_generation(
                    str(body["project_id"]),
                    comfyui_url=str(body.get("comfyui_url", "http://127.0.0.1:8188")),
                    base_seed=int(body.get("base_seed", 1000)),
                ), status=202)
            elif parsed.path == "/api/cancel":
                self._send_json(self.studio.cancel_generation(str(body["project_id"])))
            elif parsed.path == "/api/open-folder":
                path = self.studio.open_project_folder(str(body["project_id"]))
                self._send_json({"ok": True, "path": path})
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_error(exc)

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith(("/api/batch/", "/batch-media/")):
            return super().do_HEAD()
        try:
            if parsed.path.startswith("/comic-media/"):
                parts = parsed.path.split("/", 3)
                if len(parts) != 4:
                    raise ValueError("Invalid comic media URL")
                self._send_media_file(self.comic.media_path(unquote(parts[2]), unquote(parts[3])), head_only=True)
                return
            if parsed.path.startswith("/media/"):
                parts = parsed.path.split("/", 3)
                if len(parts) != 4:
                    raise ValueError("Invalid media URL")
                project_id = unquote(parts[2])
                relative = unquote(parts[3])
                self._send_media_file(
                    self.studio.media_path(project_id, relative),
                    head_only=True,
                )
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_error(exc)
