from __future__ import annotations

from typing import Any


class DataMapper:
    """Decouples external raw JSON/dict payloads from internal UI primitives by mapping fields declaratively."""

    @staticmethod
    def resolve_path(data: Any, path: str) -> Any:
        if not path or path == "$":
            return data
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    @classmethod
    def map_list(cls, raw_data: Any, mappings: dict[str, Any]) -> list[dict[str, Any]]:
        items_path = mappings.get("items_path", "$")
        raw_items = cls.resolve_path(raw_data, items_path)

        if not isinstance(raw_items, list):
            if isinstance(raw_items, dict):
                raw_items = [raw_items]
            else:
                return []

        mapped_items = []
        for item in raw_items:
            mapped_item: dict[str, Any] = {}

            mapped_item["id"] = str(cls.resolve_path(item, mappings.get("id", "id")) or "")
            mapped_item["title"] = str(cls.resolve_path(item, mappings.get("title", "title")) or "")

            if "description" in mappings:
                desc = cls.resolve_path(item, mappings["description"])
                mapped_item["description"] = str(desc) if desc is not None else None
            else:
                mapped_item["description"] = None

            if "meta" in mappings:
                meta = cls.resolve_path(item, mappings["meta"])
                mapped_item["meta"] = str(meta) if meta is not None else None
            else:
                mapped_item["meta"] = None

            if "subtext" in mappings:
                sub = cls.resolve_path(item, mappings["subtext"])
                mapped_item["subtext"] = str(sub) if sub is not None else None
            else:
                mapped_item["subtext"] = None

            if "open_url" in mappings:
                ou = cls.resolve_path(item, mappings["open_url"])
                mapped_item["open_url"] = str(ou) if ou is not None else None
            else:
                mapped_item["open_url"] = None

            data_attrs: dict[str, str] = {}
            for key, attr_path in mappings.get("data_attrs", {}).items():
                val = cls.resolve_path(item, attr_path)
                if val is not None:
                    data_attrs[key] = str(val)
            mapped_item["data_attrs"] = data_attrs

            tags = []
            for tag_mapping in mappings.get("tags", []):
                if not isinstance(tag_mapping, dict):
                    continue
                tag_path = tag_mapping.get("path")
                tag_label = tag_mapping.get("label", "")
                if tag_path:
                    val = cls.resolve_path(item, tag_path)
                    if val is not None:
                        tags.append({"name": tag_label, "value": str(val)})
            mapped_item["tags"] = tags

            mapped_items.append(mapped_item)

        return mapped_items

    @classmethod
    def map_grid(cls, raw_data: Any, mappings: dict[str, Any]) -> list[dict[str, Any]]:
        groups_path = mappings.get("groups_path", "$")
        raw_groups = cls.resolve_path(raw_data, groups_path)

        if not isinstance(raw_groups, list):
            if isinstance(raw_groups, dict):
                raw_groups = [raw_groups]
            else:
                return []

        mapped_groups = []
        for group in raw_groups:
            group_id = str(cls.resolve_path(group, mappings.get("group_id", "id")) or "")
            group_label = str(cls.resolve_path(group, mappings.get("group_label", "label")) or "")

            items_path = mappings.get("items_path", "items")
            raw_items = cls.resolve_path(group, items_path)
            if not isinstance(raw_items, list):
                raw_items = []

            mapped_items = []
            for item in raw_items:
                item_id = str(cls.resolve_path(item, mappings.get("item_id", "id")) or "")
                item_label = str(cls.resolve_path(item, mappings.get("item_label", "label")) or "")

                desc = None
                if "item_description" in mappings:
                    desc_val = cls.resolve_path(item, mappings["item_description"])
                    if desc_val is not None:
                        desc = str(desc_val)

                subtext = None
                if "item_subtext" in mappings:
                    subtext_val = cls.resolve_path(item, mappings["item_subtext"])
                    if subtext_val is not None:
                        subtext = str(subtext_val)

                open_url = None
                if "item_open_url" in mappings:
                    open_url_val = cls.resolve_path(item, mappings["item_open_url"])
                    if open_url_val is not None:
                        open_url = str(open_url_val)

                status_tags = []
                for tag_mapping in mappings.get("item_status_tags", []):
                    if not isinstance(tag_mapping, dict):
                        continue
                    tag_path = tag_mapping.get("path")
                    tag_name = tag_mapping.get("name", "")
                    if tag_path:
                        val = cls.resolve_path(item, tag_path)
                        if val is not None:
                            status_tags.append({"name": tag_name, "value": str(val)})

                data_attrs = {}
                for key, attr_path in mappings.get("item_data_attrs", {}).items():
                    val = cls.resolve_path(item, attr_path)
                    if val is not None:
                        data_attrs[key] = str(val)

                mapped_items.append({
                    "id": item_id,
                    "label": item_label,
                    "description": desc,
                    "subtext": subtext,
                    "status_tags": status_tags,
                    "open_url": open_url,
                    "has_details": bool(mappings.get("has_details", True)),
                    "data_attrs": data_attrs,
                })

            mapped_groups.append({
                "id": group_id,
                "label": group_label,
                "items": mapped_items,
            })

        return mapped_groups

    @classmethod
    def map_detail_list(cls, raw_data: Any, mappings: dict[str, Any]) -> list[dict[str, Any]]:
        detail_items = []
        for item_mapping in mappings.get("items", []):
            if not isinstance(item_mapping, dict):
                continue
            label = item_mapping.get("label", "")
            path = item_mapping.get("path", "")
            data_attr = item_mapping.get("data_attr", "")

            val = cls.resolve_path(raw_data, path) if path else None
            detail_item: dict[str, Any] = {
                "label": label,
                "value": str(val) if val is not None else None,
            }
            if data_attr:
                detail_item["data_attr"] = data_attr
            detail_items.append(detail_item)

        return detail_items
