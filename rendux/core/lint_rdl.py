"""RDL layout linter — validates views.yaml layout trees against widget contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from rendux.core.contracts import (
    CONTRACTS_ROOT,
    load_grammar,
    load_profiles,
    load_widget_registry,
    canonical_prop_names,
)

_CTX_RE = re.compile(r"^\$ctx\.(.+)$")
_ITEM_RE = re.compile(r"^\$item\.(.+)$")

LintLevel = Literal["error", "warning", "note"]


@dataclass(frozen=True)
class LintIssue:
    level: LintLevel
    path: str
    message: str


class RdlLinter:
  def __init__(self, *, strict: bool = True) -> None:
      self.strict = strict
      self.grammar = load_grammar()
      self.registry = load_widget_registry()
      self.profiles = load_profiles()
      self.issues: list[LintIssue] = []

  def lint_views_config(self, config: dict[str, Any]) -> list[LintIssue]:
      self.issues = []
      views = config.get("views", {})
      if not isinstance(views, dict):
          self._add("error", "views", "views must be a mapping")
          return self.issues

      for view_id, view in views.items():
          if not isinstance(view, dict):
              continue
          workspace = view.get("workspace", {})
          if not isinstance(workspace, dict):
              continue
          layout = workspace.get("layout")
          if layout is None:
              continue
          static_data = view.get("data", {})
          if not isinstance(static_data, dict):
              static_data = {}
          self._lint_nodes(
              layout if isinstance(layout, list) else [layout],
              path=f"views.{view_id}.workspace.layout",
              static_data=static_data,
          )
      return self.issues

  def lint_views_file(self, path: Path) -> list[LintIssue]:
      data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
      if not isinstance(data, dict):
          return [LintIssue("error", str(path), "root must be a mapping")]
      return self.lint_views_config(data)

  def has_errors(self) -> bool:
      return any(i.level == "error" for i in self.issues)

  # ── internal ─────────────────────────────────────────────────────────────

  def _add(self, level: LintLevel, path: str, message: str) -> None:
      self.issues.append(LintIssue(level, path, message))

  def _lint_nodes(
      self,
      nodes: list[Any],
      *,
      path: str,
      static_data: dict[str, Any],
      in_each: bool = False,
  ) -> None:
      if not isinstance(nodes, list):
          self._add("error", path, "layout must be a list of nodes")
          return
      for idx, node in enumerate(nodes):
          self._lint_node(node, path=f"{path}[{idx}]", static_data=static_data, in_each=in_each)

  def _lint_node(
      self,
      node: Any,
      *,
      path: str,
      static_data: dict[str, Any],
      in_each: bool,
  ) -> None:
      if not isinstance(node, dict):
          self._add("error", path, "node must be a mapping")
          return

      if "when" in node:
          self._lint_when(node["when"], path=f"{path}.when", static_data=static_data, in_each=in_each)

      if node.get("divider") is True:
          return
      if "heading" in node:
          return
      if "widget" in node:
          self._lint_widget(node, path=path, static_data=static_data, in_each=in_each)
          return
      if "type" in node:
          self._lint_container(node, path=path, static_data=static_data, in_each=in_each)
          return

      self._add("error", path, "node must be widget, container, divider, or heading")

  def _lint_when(
      self,
      value: Any,
      *,
      path: str,
      static_data: dict[str, Any],
      in_each: bool,
  ) -> None:
      if isinstance(value, str) and value.startswith("$ctx."):
          self._lint_ctx_ref(value, path=path, static_data=static_data, in_each=in_each)

  def _lint_widget(
      self,
      node: dict[str, Any],
      *,
      path: str,
      static_data: dict[str, Any],
      in_each: bool,
  ) -> None:
      name = node.get("widget")
      if not isinstance(name, str) or not name:
          self._add("error", f"{path}.widget", "widget name must be a non-empty string")
          return

      contract = self.registry.get(name)
      if contract is None:
          self._add("error", f"{path}.widget", f"unknown widget: {name!r}")
          return

      if contract.get("status") != "verified":
          self._add(
              "note",
              path,
              f"widget {name!r} contract is unverified — prop checks skipped",
          )
          self._lint_children_after_each(node, path, static_data)
          return

      reserved = set(self.grammar.get("reserved_widget_keys", []))
      alias_map = canonical_prop_names(contract)
      known_props = set(contract.get("props", {}))
      known_aliases = set(alias_map.keys())

      props_on_node = {k: v for k, v in node.items() if k not in reserved}

      # Required props
      for prop_name, spec in contract.get("props", {}).items():
          if not spec.get("required"):
              continue
          if prop_name in props_on_node:
              continue
          has_alias = any(
              alias in props_on_node and alias_map.get(alias) == prop_name
              for alias in spec.get("aliases", [])
          )
          if not has_alias:
              self._add("error", path, f"widget {name!r} missing required prop {prop_name!r}")

      # Unknown props
      for key in props_on_node:
          if key in known_props or key in known_aliases:
              if key in known_aliases and alias_map[key] != key:
                  self._add(
                      "warning",
                      f"{path}.{key}",
                      f"deprecated alias {key!r} — use {alias_map[key]!r}",
                  )
              continue
          level: LintLevel = "error" if self.strict else "warning"
          self._add(level, f"{path}.{key}", f"unknown prop {key!r} on widget {name!r}")

      # Enum validation on literals
      for key, value in props_on_node.items():
          canonical = alias_map.get(key, key)
          spec = contract.get("props", {}).get(canonical)
          if not spec or spec.get("type") != "enum":
              continue
          if isinstance(value, str) and not value.startswith("$"):
              allowed = spec.get("enum", [])
              if value not in allowed:
                  self._add(
                      "error",
                      f"{path}.{key}",
                      f"invalid {canonical}={value!r} — expected one of {allowed}",
                  )

      has_each = "each" in node

      # Static $ctx resolution
      for key, value in props_on_node.items():
          if isinstance(value, str) and value.startswith("$ctx."):
              self._lint_ctx_ref(value, path=f"{path}.{key}", static_data=static_data, in_each=in_each or has_each)
          elif isinstance(value, str) and value.startswith("$item."):
              if not in_each and not has_each:
                  self._add(
                      "warning",
                      f"{path}.{key}",
                      f"{value!r} outside each: block (runtime resolves to empty string)",
                  )

      # Item schema when static list is available
      self._lint_static_collection(node, contract, path, static_data)

      # Interaction profile
      self._lint_interaction(name, contract, props_on_node, path)

      self._lint_children_after_each(node, path, static_data)

  def _lint_children_after_each(
      self,
      node: dict[str, Any],
      path: str,
      static_data: dict[str, Any],
  ) -> None:
      if "each" in node:
          each_val = node["each"]
          if isinstance(each_val, str) and each_val.startswith("$ctx."):
              self._lint_ctx_ref(
                  each_val,
                  path=f"{path}.each",
                  static_data=static_data,
                  in_each=False,
                  expect_list=True,
              )

  def _lint_interaction(
      self,
      name: str,
      contract: dict[str, Any],
      props: dict[str, Any],
      path: str,
  ) -> None:
      profile_name = contract.get("interaction", {}).get("profile", "static")
      profile = self.profiles.get(profile_name)
      if profile is None:
          self._add("error", path, f"widget {name!r} references unknown profile {profile_name!r}")
          return
      for req in profile.get("requires", []):
          if req not in props:
              self._add(
                  "error",
                  path,
                  f"widget {name!r} (profile {profile_name}) missing required prop {req!r}",
              )

  def _lint_static_collection(
      self,
      node: dict[str, Any],
      contract: dict[str, Any],
      path: str,
      static_data: dict[str, Any],
  ) -> None:
      item_schema = contract.get("item_schema")
      if not item_schema:
          return

      collection_key = None
      for candidate in ("items", "events"):
          if candidate in node:
              collection_key = candidate
              break
      if collection_key is None:
          return

      value = node[collection_key]
      if isinstance(value, str) and value.startswith("$ctx."):
          m = _CTX_RE.match(value)
          if not m:
              return
          resolved = _resolve_path(static_data, m.group(1))
          if resolved is None:
              return  # already reported or dynamic
          if not isinstance(resolved, list):
              return
          items = resolved
      elif isinstance(value, list):
          items = value
      else:
          return

      for i, item in enumerate(items):
          self._lint_item_schema(item, item_schema, f"{path}.{collection_key}[{i}]")

  def _lint_item_schema(self, item: Any, schema: dict[str, Any], path: str) -> None:
      if not isinstance(item, dict):
          self._add("warning", path, "collection item must be a mapping")
          return
      for req, spec in schema.get("required", {}).items():
          if req not in item:
              self._add("error", path, f"item missing required field {req!r}")
          elif spec.get("type") == "enum" and item[req] not in spec.get("enum", []):
              self._add("error", path, f"item field {req}={item[req]!r} not in enum")
      for key in item:
          if key in schema.get("required", {}) or key in schema.get("optional", {}):
              continue
          level: LintLevel = "warning" if self.strict else "note"
          self._add(level, f"{path}.{key}", f"unknown item field {key!r}")

  def _lint_container(
      self,
      node: dict[str, Any],
      *,
      path: str,
      static_data: dict[str, Any],
      in_each: bool,
  ) -> None:
      ctype = node.get("type")
      known = set(self.grammar.get("container_types", []))
      if ctype not in known:
          self._add("error", f"{path}.type", f"unknown container type {ctype!r}")

      if ctype == "grid":
          cols = node.get("columns", "auto")
          allowed = self.grammar.get("grid_columns", [])
          if cols not in allowed:
              self._add("error", f"{path}.columns", f"invalid columns {cols!r}")

      gap = node.get("gap")
      if gap is not None and gap not in self.grammar.get("gap_values", []):
          self._add("error", f"{path}.gap", f"invalid gap {gap!r}")

      space = node.get("space")
      if space is not None and space not in self.grammar.get("space_values", self.grammar.get("gap_values", [])):
          self._add("error", f"{path}.space", f"invalid space {space!r}")

      if ctype == "split":
          for slot in ("primary", "secondary"):
              children = node.get(slot, [])
              self._lint_nodes(
                  children if isinstance(children, list) else [],
                  path=f"{path}.{slot}",
                  static_data=static_data,
                  in_each=in_each,
              )
      else:
          children = node.get("children", [])
          self._lint_nodes(
              children if isinstance(children, list) else [],
              path=f"{path}.children",
              static_data=static_data,
              in_each=in_each,
          )

  def _lint_ctx_ref(
      self,
      ref: str,
      *,
      path: str,
      static_data: dict[str, Any],
      in_each: bool,
      expect_list: bool = False,
  ) -> None:
      m = _CTX_RE.match(ref)
      if not m:
          return
      if not static_data:
          self._add(
              "note",
              path,
              f"{ref!r} — no static data: block; cannot verify path statically",
          )
          return
      resolved = _resolve_path(static_data, m.group(1))
      if resolved is None:
          self._add("error", path, f"{ref!r} does not resolve in view data:")
          return
      if expect_list and not isinstance(resolved, list):
          self._add("error", path, f"{ref!r} must resolve to a list for each:")


def _resolve_path(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def lint_views_file(path: Path, *, strict: bool = True) -> list[LintIssue]:
    return RdlLinter(strict=strict).lint_views_file(path)


def contracts_root() -> Path:
    return CONTRACTS_ROOT
