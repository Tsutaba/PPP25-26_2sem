from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from pydantic import BaseModel
from typing import Optional
import uvicorn


app = FastAPI(title = "ETL Data API")

# база данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./simple_etl.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args = {"check_same_thread": False})
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key = True)
    name = Column(String(50))
    items = relationship("Item", back_populates = "source")

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key = True)
    title = Column(String(100))
    price = Column(Float)
    source_id = Column(Integer, ForeignKey('sources.id'))
    source = relationship("Source", back_populates = "items")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    id = Column(Integer, primary_key = True)
    item_id = Column(Integer, ForeignKey('items.id'))
    old_price = Column(Float)
    new_price = Column(Float)

# создание таблиц
Base.metadata.create_all(bind=engine)

# схемы для ввода / вывода
class SourceCreate(BaseModel):
    name: str

class SourceResponse(SourceCreate):
    id: int
    class Config:
        from_attributes = True

class ItemCreate(BaseModel):
    title: str
    price: float
    source_id: int

class ItemResponse(ItemCreate):
    id: int
    source: SourceResponse
    class Config:
        from_attributes = True

class PriceHistoryCreate(BaseModel):
    item_id: int
    old_price: float
    new_price: float

class PriceHistoryResponse(PriceHistoryCreate):
    id: int
    class Config:
        from_attributes = True

# эндпоинты
# 1. GET (список источников)
@app.get("/sources")
def get_sources(db: Session = Depends(get_db)):
    return db.query(Source).all()

# 2. POST (создать источник)
@app.post("/sources")
def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    db_source = Source(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

# 3. GET (список товаров)
@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

# 4. GET (товар по id)
@app.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code = 404, detail = "Товар не найден")
    return item

# 5. POST (создать товар)
@app.post("/items")
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# 6. PUT (обновить товар полностью)
@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code = 404, detail = "Товар не найден")
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    db.commit()
    return db_item

# 7. PATCH (частично обновить товар)
@app.patch("/items/{item_id}")
def partial_update_item(item_id: int, title: Optional[str] = None, price: Optional[float] = None, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code = 404, detail = "Товар не найден")
    if title:
        db_item.title = title
    if price:
        db_item.price = price
    db.commit()
    return db_item

# 8. DELETE (удалить товар)
@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code = 404, detail = "Товар не найден")
    db.delete(db_item)
    db.commit()
    return {"message": "Товар удалён"}

# 9. POST (добавить историю цен)
@app.post("/price-history")
def add_price_history(history: PriceHistoryCreate, db: Session = Depends(get_db)):
    db_history = PriceHistory(**history.dict())
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history

# 10. GET (история цен для товара)
@app.get("/items/{item_id}/history")
def get_item_history(item_id: int, db: Session = Depends(get_db)):
    history = db.query(PriceHistory).filter(PriceHistory.item_id == item_id).all()
    if not history:
        raise HTTPException(status_code = 404, detail = "История цен не найдена")
    return history

if __name__ == "__main__":
    uvicorn.run(app, host = "0.0.0.0", port = 8000)
