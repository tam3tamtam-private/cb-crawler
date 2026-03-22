from dataclasses import dataclass
from typing import Dict
import os
import yaml
from crawler import config


@dataclass(frozen=True)
class SiteConfig:
    campaign_card: str
    title: str
    reward: str
    link_selector: str
    link_attribute: str
    pagination_type: str
    pagination_selector: str
    scroll: bool
    source_path: str


def load_site_config(webpage_id: str) -> SiteConfig:
    path = os.path.join(config.SITE_CONFIG_DIR, f"{webpage_id}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Site config not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    link = data.get("link") or {}
    pagination = data.get("pagination") or {}

    campaign_card = data.get("campaign_card")
    title = data.get("title")
    reward = data.get("reward")
    link_selector = link.get("selector")
    link_attribute = link.get("attribute")
    pagination_type = pagination.get("type", "next_button")
    pagination_selector = pagination.get("selector", "")
    scroll = data.get("scroll")

    missing = []
    if not campaign_card:
        missing.append("campaign_card")
    if not title:
        missing.append("title")
    if not reward:
        missing.append("reward")
    if not link_selector:
        missing.append("link.selector")
    if not link_attribute:
        missing.append("link.attribute")

    if missing:
        raise ValueError(f"Missing required fields in {path}: {', '.join(missing)}")

    return SiteConfig(
        campaign_card=campaign_card,
        title=title,
        reward=reward,
        link_selector=link_selector,
        link_attribute=link_attribute,
        pagination_type=pagination_type,
        pagination_selector=pagination_selector,
        scroll=bool(scroll) if scroll is not None else False,
        source_path=path,
    )
