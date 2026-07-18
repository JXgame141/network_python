import asyncio
import threading

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

app = FastAPI()

ITEMS: dict[int, dict] = {}
NEXT_ID = 1
COUNTER = 0
ITEMS_LOCK = threading.RLock()
COUNTER_LOCK = threading.Lock()


class ItemCreate(BaseModel):
    name: str


class ItemUpdate(BaseModel):
    name: str = ""


@app.get("/items")
def list_items():
    with ITEMS_LOCK:
        return {"items": list(ITEMS.values())}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    with ITEMS_LOCK:
        item = ITEMS.get(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return item


@app.post("/items", status_code=201)
def create_item(item: ItemCreate):
    global NEXT_ID

    with ITEMS_LOCK:
        item_id = NEXT_ID
        NEXT_ID += 1
        created = {"id": item_id, "name": item.name}
        ITEMS[item_id] = created
        return created


@app.get("/items/{item_id}/counter")
def get_counter(item_id: int):
    global COUNTER

    with ITEMS_LOCK:
        if item_id not in ITEMS:
            raise HTTPException(status_code=404, detail="Item not found")

    with COUNTER_LOCK:
        COUNTER += 1
        return {"counter": COUNTER}


@app.put("/items/{item_id}")
def update_item(item_id: int, update: ItemUpdate):
    with ITEMS_LOCK:
        if item_id not in ITEMS:
            raise HTTPException(status_code=404, detail="Item not found")
        updated = {"id": item_id, "name": update.name}
        ITEMS[item_id] = updated
        return updated


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    with ITEMS_LOCK:
        if item_id not in ITEMS:
            raise HTTPException(status_code=404, detail="Item not found")
        del ITEMS[item_id]
    return Response(status_code=204)


@app.get("/divide")
def divide(a: int, b: int):
    if b == 0:
        raise HTTPException(status_code=400, detail="Division by zero")
    return {"result": a / b}


@app.get("/slow-sync")
async def slow_sync():
    await asyncio.sleep(0.5)
    return {"status": "done"}
