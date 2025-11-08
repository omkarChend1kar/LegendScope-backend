from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

from app.schemas import Item, ItemCreate


@dataclass
class ItemStore:
    _lock: Lock = field(default_factory=Lock)
    _items: dict[int, Item] = field(default_factory=dict)
    _next_id: int = 1

    def list_items(self) -> list[Item]:
        with self._lock:
            return list(self._items.values())

    def get_item(self, item_id: int) -> Item | None:
        with self._lock:
            return self._items.get(item_id)

    def create_item(self, item_in: ItemCreate) -> Item:
        with self._lock:
            item = Item(
                id=self._next_id,
                name=item_in.name,
                description=item_in.description,
                price=item_in.price,
                created_at=datetime.utcnow(),
            )
            self._items[self._next_id] = item
            self._next_id += 1
            return item

    def delete_item(self, item_id: int) -> bool:
        with self._lock:
            if item_id not in self._items:
                return False
            del self._items[item_id]
            return True


store = ItemStore()
