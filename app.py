import os
import sys
import shutil
import sqlite3
import uuid
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.utils import secure_filename

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    DATA_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", DATA_DIR))
else:
    DATA_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = DATA_DIR

BASE_DIR = DATA_DIR
STATIC_DIR = DATA_DIR / "static"
TEMPLATE_DIR = RESOURCE_DIR / "templates"
PACKAGED_STATIC_DIR = RESOURCE_DIR / "static"

if IS_FROZEN and PACKAGED_STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PACKAGED_STATIC_DIR, STATIC_DIR, dirs_exist_ok=True)

DB_PATH = DATA_DIR / "museum.db"
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "pavlov-museum-change-me")
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
IMAGE_EXT = {"jpg", "jpeg", "png", "webp", "gif"}
AUDIO_EXT = {"mp3", "wav", "ogg", "m4a"}

DEFAULT_SECTIONS = [
    ("biography", "Биография", "", "Жизненный путь", "img/biography.svg", 10),
    ("autobiography", "Автобиография", "biography", "Биография", "img/biography.svg", 10),
    ("bibliography", "Библиография", "biography", "Биография", "img/archive.svg", 20),
    ("chronicle", "Летопись жизни и деятельности", "biography", "Биография", "img/biography.svg", 30),

    ("heritage", "Наследие", "", "Творчество и документы", "img/heritage.svg", 20),
    ("literary-works", "Литературные произведения", "heritage", "Наследие", "img/heritage.svg", 10),
    ("musical-works", "Музыкальные произведения", "heritage", "Наследие", "img/music.svg", 20),
    ("journalism", "Публицистика", "heritage", "Наследие", "img/archive.svg", 30),
    ("letters", "Письма", "heritage", "Наследие", "img/archive.svg", 40),
    ("archive", "Архивные материалы", "heritage", "Наследие", "img/archive.svg", 50),

    ("memory", "Память", "", "Павлов в культуре", "img/memory.svg", 30),
    ("in-art", "Фёдор Павлов в искусстве", "memory", "Память", "img/memory.svg", 10),
    ("in-music", "Фёдор Павлов в музыке", "memory", "Память", "img/music.svg", 20),
    ("in-literature", "Фёдор Павлов в литературе", "memory", "Память", "img/memory.svg", 30),

    ("contemporaries", "Современники", "", "Люди эпохи", "img/contemporaries.svg", 40),
    ("stepan-maksimov", "Степан Максимов", "contemporaries", "Современники", "img/contemporaries.svg", 10),
    ("vasiliy-vorobyev", "Василий Воробьёв", "contemporaries", "Современники", "img/contemporaries.svg", 20),
    ("iosif-lyublin", "Иосиф Люблин", "contemporaries", "Современники", "img/contemporaries.svg", 30),
    ("sigizmund-gaber", "Сигизмунд Габер", "contemporaries", "Современники", "img/contemporaries.svg", 40),
    ("vladimir-krivonosov", "Владимир Кривоносов", "contemporaries", "Современники", "img/contemporaries.svg", 50),
    ("vladimir-ivanishin", "Владимир Иванишин", "contemporaries", "Современники", "img/contemporaries.svg", 60),

    ("excursion", "Экскурсия", "", "Маршрут по музею", "img/excursion.svg", 50),
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS sections(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      slug TEXT NOT NULL UNIQUE,
      title TEXT NOT NULL,
      parent_slug TEXT DEFAULT '',
      eyebrow TEXT DEFAULT '',
      image TEXT DEFAULT '',
      sort_order INTEGER DEFAULT 0,
      visible INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS materials(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      section_slug TEXT NOT NULL,
      title TEXT NOT NULL,
      subtitle TEXT DEFAULT '',
      body TEXT DEFAULT '',
      image TEXT DEFAULT '',
      audio TEXT DEFAULT '',
      year TEXT DEFAULT '',
      sort_order INTEGER DEFAULT 0,
      featured INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS gallery(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      material_id INTEGER NOT NULL,
      image TEXT NOT NULL,
      caption TEXT DEFAULT '',
      sort_order INTEGER DEFAULT 0,
      FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE CASCADE
    );
    """)
    section_count = conn.execute("SELECT COUNT(*) n FROM sections").fetchone()["n"]
    if section_count == 0:
        conn.executemany(
            """INSERT INTO sections(slug,title,parent_slug,eyebrow,image,sort_order)
               VALUES(?,?,?,?,?,?)""", DEFAULT_SECTIONS
        )

    material_count = conn.execute("SELECT COUNT(*) n FROM materials").fetchone()["n"]
    if material_count == 0:
        seed_materials(conn)

    conn.commit()
    conn.close()

def seed_materials(conn):
    rows = [
      ("autobiography","Фёдор Павлович Павлов","Композитор, драматург, дирижёр, педагог и организатор культуры",
       "Фёдор Павлович Павлов родился 13 сентября 1892 года в селе Богатырёво Ядринского уезда. Он стал одним из основоположников чувашской драматургии и профессиональной музыки.\n\n"
       "В 1911 году Павлов окончил Симбирскую чувашскую учительскую школу, в 1916 году — Симбирскую духовную семинарию. В 1918–1919 годах учился в Северо-Восточном археологическом и этнографическом институте в Казани.\n\n"
       "Он преподавал пение, работал в системе народного образования, организовывал хоровую и театральную деятельность, руководил Чувашским национальным хором и преподавал в Чебоксарской музыкальной школе. С сентября 1930 года учился композиции в Ленинградской государственной консерватории в классе профессора М. О. Штейнберга. Учёба была прервана болезнью. Фёдор Павлов умер 2 июня 1931 года в Сочи.",
       "img/pavlov.svg","","1892–1931",10,1),
      ("chronicle","1892 — рождение","Село Богатырёво, Ядринский уезд",
       "13 сентября 1892 года родился Фёдор Павлович Павлов. Детство прошло в среде, где большое значение имели народные песни и музыкальная традиция.",
       "img/biography.svg","","1892",10,0),
      ("chronicle","1911 — окончание учительской школы","Симбирская чувашская учительская школа",
       "В 1911 году Павлов окончил Симбирскую чувашскую учительскую школу и некоторое время работал там учителем пения.",
       "img/biography.svg","","1911",20,0),
      ("chronicle","1916 — духовная семинария","Симбирск",
       "В 1916 году Павлов окончил Симбирскую духовную семинарию. В последующие годы работал учителем и участвовал в общественной жизни.",
       "img/biography.svg","","1916",30,0),
      ("chronicle","1918–1919 — Казань","Учёба и работа в сфере культуры",
       "Павлов учился в Северо-Восточном археологическом и этнографическом институте в Казани, а затем работал в учреждениях народного образования и искусства.",
       "img/heritage.svg","","1918–1919",40,0),
      ("chronicle","1920-е — Чебоксары","Музыкальная школа и национальный хор",
       "В 1920-е годы Павлов преподавал в Чебоксарской музыкальной школе, руководил Чувашским национальным хором, занимался собиранием и обработкой народной музыки.",
       "img/music.svg","","1920-е",50,0),
      ("chronicle","1930 — Ленинградская консерватория","Класс композиции М. О. Штейнберга",
       "С сентября 1930 года Павлов начал учиться в Ленинградской государственной консерватории. Обучение было прервано тяжёлой болезнью.",
       "img/biography.svg","","1930",60,0),
      ("chronicle","1931 — Сочи","Последний год жизни",
       "2 июня 1931 года Фёдор Павлов умер в Сочи. Его творческое и организационное наследие стало важной частью истории чувашской культуры.",
       "img/memory.svg","","1931",70,0),
      ("bibliography","Книги и исследования о Фёдоре Павлове","Библиографический каталог",
       "В этот раздел администратор может добавлять отдельные издания, исследования, статьи и каталоги. Для каждого материала доступны обложка, описание и галерея изображений.",
       "img/archive.svg","","",10,0),
      ("literary-works","«Сутра» («На суде»)","Комедия",
       "Комедия «Сутра» относится к ранним оригинальным произведениям чувашской драматургии. Работа над пьесой была завершена в 1919 году.",
       "img/heritage.svg","","1919",10,1),
      ("literary-works","«Ялта» («В деревне»)","Драма",
       "Драма «Ялта» была создана в начале 1920-х годов и вошла в литературное наследие Фёдора Павлова.",
       "img/heritage.svg","","1922",20,0),
      ("musical-works","«Ача-пача сасси»","Сборник детских песен и игр",
       "Сборник «Ача-пача сасси» («Голос детворы») был издан в 1921 году. В этом разделе можно разместить нотные материалы и современные аудиозаписи произведений.",
       "img/music.svg","","1921",10,1),
      ("musical-works","«Вӗлле хурчӗ»","Песня",
       "Песня «Вӗлле хурчӗ» («Пчёлка») создана Павловым на собственный текст. После загрузки аудиофайла через админ-панель запись можно слушать прямо на сенсорном столе.",
       "img/music.svg","","",20,1),
      ("musical-works","«Сарнай и палнай»","Музыкальная фантазия",
       "Произведение «Сарнай и палнай» связано с развитием профессиональной чувашской инструментальной музыки. В музейной карточке можно разместить запись исполнения, ноты и фотографии.",
       "img/music.svg","","1928",30,0),
      ("journalism","Публицистика и статьи о музыке","Тексты о культуре и фольклоре",
       "Павлов писал статьи о чувашской музыке, народных инструментах и песенном творчестве. Раздел предназначен для публикаций, сканов и расшифровок.",
       "img/archive.svg","","",10,0),
      ("letters","Письма Фёдора Павлова","Эпистолярное наследие",
       "Раздел предназначен для писем и рукописных документов. Для каждого письма можно загрузить несколько страниц в галерею и рядом разместить расшифровку.",
       "img/archive.svg","","",10,0),
      ("archive","Архивные материалы","Рукописи, фотографии, афиши, ноты",
       "Цифровой архив музея. Один материал может содержать основное изображение и целую галерею дополнительных сканов.",
       "img/archive.svg","","",10,1),
      ("in-art","Фёдор Павлов в изобразительном искусстве","Портреты, памятники и художественные образы",
       "Раздел собирает изображения и произведения искусства, связанные с памятью о Фёдоре Павлове.",
       "img/memory.svg","","",10,0),
      ("in-music","Память в музыке","Исполнения и посвящения",
       "Здесь размещаются современные исполнения, концертные записи и музыкальные посвящения.",
       "img/music.svg","","",10,0),
      ("in-literature","Фёдор Павлов в литературе","Исследования и воспоминания",
       "Раздел для воспоминаний, литературных произведений и исследовательских текстов о Павлове.",
       "img/memory.svg","","",10,0),
      ("excursion","Добро пожаловать в музей","Интерактивный маршрут",
       "Нажмите «Начать экскурсию», чтобы пройти последовательный маршрут: биография, летопись, литературное и музыкальное наследие, архив и память.",
       "img/excursion.svg","","",10,1)
    ]
    people = [
        ("stepan-maksimov","Степан Максимов"),("vasiliy-vorobyev","Василий Воробьёв"),
        ("iosif-lyublin","Иосиф Люблин"),("sigizmund-gaber","Сигизмунд Габер"),
        ("vladimir-krivonosov","Владимир Кривоносов"),("vladimir-ivanishin","Владимир Иванишин")
    ]
    for i,(slug,name) in enumerate(people,1):
        rows.append((slug,name,"Современник Фёдора Павлова",
          "Раздел подготовлен для музейного наполнения: биография, фотографии, документы и материалы о связи этого человека с эпохой Фёдора Павлова.",
          "img/contemporaries.svg","","",i*10,0))
    conn.executemany(
        """INSERT INTO materials(section_slug,title,subtitle,body,image,audio,year,sort_order,featured)
           VALUES(?,?,?,?,?,?,?,?,?)""", rows
    )

def get_sections():
    conn = db()
    rows = conn.execute("SELECT * FROM sections WHERE visible=1 ORDER BY sort_order,id").fetchall()
    conn.close()
    return rows

def get_main_groups():
    conn = db()
    parents = conn.execute(
        "SELECT * FROM sections WHERE visible=1 AND parent_slug='' AND slug!='excursion' ORDER BY sort_order,id"
    ).fetchall()
    result=[]
    for p in parents:
        children = conn.execute(
            "SELECT * FROM sections WHERE visible=1 AND parent_slug=? ORDER BY sort_order,id",
            (p["slug"],)
        ).fetchall()
        item=dict(p)
        item["children"]=[(c["slug"],c["title"]) for c in children]
        result.append(item)
    conn.close()
    return result

def all_sections():
    return [(r["slug"],r["title"]) for r in get_sections()]

def section_info(slug):
    conn = db()
    row = conn.execute("SELECT * FROM sections WHERE slug=? AND visible=1",(slug,)).fetchone()
    if not row:
        conn.close()
        return None
    children = conn.execute(
        "SELECT * FROM sections WHERE parent_slug=? AND visible=1 ORDER BY sort_order,id",(slug,)
    ).fetchall()
    parent = None
    if row["parent_slug"]:
        parent = conn.execute("SELECT * FROM sections WHERE slug=?",(row["parent_slug"],)).fetchone()
    conn.close()
    info=dict(row)
    info["children"]=[(c["slug"],c["title"]) for c in children]
    info["parent"]=dict(parent) if parent else None
    return info

def save_upload(file,kind):
    if not file or not file.filename:
        return ""
    ext=file.filename.rsplit(".",1)[-1].lower() if "." in file.filename else ""
    allowed=IMAGE_EXT if kind=="image" else AUDIO_EXT
    if ext not in allowed:
        raise ValueError("Недопустимый формат файла")
    name=secure_filename(file.filename) or ("file."+ext)
    filename=uuid.uuid4().hex[:10]+"_"+name
    file.save(UPLOAD_DIR/filename)
    return "uploads/"+filename

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login",next=request.path))
        return fn(*args,**kwargs)
    return wrapper

@app.context_processor
def inject():
    return {"groups":get_main_groups()}

@app.route("/")
def index():
    conn=db()
    featured=conn.execute(
        "SELECT * FROM materials WHERE featured=1 ORDER BY sort_order,id LIMIT 9"
    ).fetchall()
    conn.close()
    return render_template("index.html",featured=featured)

@app.route("/section/<slug>")
def section(slug):
    info=section_info(slug)
    if not info:
        abort(404)
    conn=db()
    items=conn.execute(
        "SELECT * FROM materials WHERE section_slug=? ORDER BY sort_order,id",(slug,)
    ).fetchall()
    conn.close()
    template="timeline.html" if slug=="chronicle" else "section.html"
    return render_template(template,section=info,items=items)

@app.route("/music")
def music():
    conn=db()
    tracks=conn.execute(
        "SELECT * FROM materials WHERE section_slug IN ('musical-works','in-music') ORDER BY sort_order,id"
    ).fetchall()
    conn.close()
    return render_template("music.html",tracks=tracks)

@app.route("/material/<int:material_id>")
def material(material_id):
    conn=db()
    item=conn.execute("SELECT * FROM materials WHERE id=?",(material_id,)).fetchone()
    gallery=conn.execute(
        "SELECT * FROM gallery WHERE material_id=? ORDER BY sort_order,id",(material_id,)
    ).fetchall()
    conn.close()
    if not item:
        abort(404)
    return render_template("material.html",item=item,gallery=gallery,section=section_info(item["section_slug"]))

@app.route("/tour")
def tour():
    conn=db()
    steps=conn.execute(
        """SELECT * FROM materials WHERE featured=1
           ORDER BY CASE section_slug
             WHEN 'autobiography' THEN 1 WHEN 'chronicle' THEN 2
             WHEN 'literary-works' THEN 3 WHEN 'musical-works' THEN 4
             WHEN 'archive' THEN 5 WHEN 'in-art' THEN 6 ELSE 7 END,
             sort_order,id"""
    ).fetchall()
    conn.close()
    return render_template("tour.html",steps=steps)

@app.route("/search")
def search():
    q=(request.args.get("q") or "").strip()
    rows=[]
    if q:
        conn=db()
        rows=conn.execute(
            """SELECT * FROM materials
               WHERE title LIKE ? OR subtitle LIKE ? OR body LIKE ? OR year LIKE ?
               ORDER BY featured DESC,sort_order,title""",
            tuple([f"%{q}%"]*4)
        ).fetchall()
        conn.close()
    return render_template("search.html",q=q,results=rows)

@app.route("/admin/login",methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        if request.form.get("username")==ADMIN_USER and request.form.get("password")==ADMIN_PASSWORD:
            session["admin"]=True
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("Неверный логин или пароль","danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn=db()
    items=conn.execute("SELECT * FROM materials ORDER BY section_slug,sort_order,id").fetchall()
    conn.close()
    return render_template("admin.html",items=items,sections=all_sections())

def add_gallery_files(conn,material_id):
    for idx,file in enumerate(request.files.getlist("gallery_files")):
        if not file or not file.filename:
            continue
        image=save_upload(file,"image")
        conn.execute(
            "INSERT INTO gallery(material_id,image,sort_order) VALUES(?,?,?)",
            (material_id,image,1000+idx*10)
        )

@app.route("/admin/new",methods=["GET","POST"])
@admin_required
def admin_new():
    if request.method=="POST":
        try:
            image=save_upload(request.files.get("image_file"),"image")
            audio=save_upload(request.files.get("audio_file"),"audio")
        except ValueError as e:
            flash(str(e),"danger")
            return redirect(request.url)
        conn=db()
        cur=conn.execute(
            """INSERT INTO materials(section_slug,title,subtitle,body,image,audio,year,sort_order,featured)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (request.form["section_slug"],request.form["title"].strip(),
             request.form.get("subtitle","").strip(),request.form.get("body","").strip(),
             image or request.form.get("image","").strip(),audio,
             request.form.get("year","").strip(),int(request.form.get("sort_order") or 0),
             1 if request.form.get("featured") else 0)
        )
        try:
            add_gallery_files(conn,cur.lastrowid)
        except ValueError as e:
            flash(str(e),"danger")
        conn.commit()
        conn.close()
        flash("Материал добавлен","success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_form.html",item=None,gallery=[],sections=all_sections())

@app.route("/admin/edit/<int:material_id>",methods=["GET","POST"])
@admin_required
def admin_edit(material_id):
    conn=db()
    item=conn.execute("SELECT * FROM materials WHERE id=?",(material_id,)).fetchone()
    if not item:
        conn.close()
        abort(404)
    if request.method=="POST":
        try:
            new_image=save_upload(request.files.get("image_file"),"image")
            new_audio=save_upload(request.files.get("audio_file"),"audio")
            add_gallery_files(conn,material_id)
        except ValueError as e:
            conn.close()
            flash(str(e),"danger")
            return redirect(request.url)
        image=new_image or request.form.get("image","").strip() or item["image"]
        audio=new_audio or item["audio"]
        if request.form.get("remove_audio"):
            audio=""
        conn.execute(
            """UPDATE materials SET section_slug=?,title=?,subtitle=?,body=?,image=?,audio=?,
               year=?,sort_order=?,featured=? WHERE id=?""",
            (request.form["section_slug"],request.form["title"].strip(),
             request.form.get("subtitle","").strip(),request.form.get("body","").strip(),
             image,audio,request.form.get("year","").strip(),
             int(request.form.get("sort_order") or 0),
             1 if request.form.get("featured") else 0,material_id)
        )
        conn.commit()
        conn.close()
        flash("Изменения сохранены","success")
        return redirect(url_for("admin_dashboard"))
    gallery=conn.execute(
        "SELECT * FROM gallery WHERE material_id=? ORDER BY sort_order,id",(material_id,)
    ).fetchall()
    conn.close()
    return render_template("admin_form.html",item=item,gallery=gallery,sections=all_sections())

@app.post("/admin/gallery/delete/<int:image_id>")
@admin_required
def admin_gallery_delete(image_id):
    conn=db()
    image=conn.execute("SELECT * FROM gallery WHERE id=?",(image_id,)).fetchone()
    if not image:
        conn.close()
        abort(404)
    material_id=image["material_id"]
    if image["image"].startswith("uploads/"):
        p=BASE_DIR/"static"/image["image"]
        if p.exists():
            p.unlink()
    conn.execute("DELETE FROM gallery WHERE id=?",(image_id,))
    conn.commit()
    conn.close()
    flash("Изображение удалено","success")
    return redirect(url_for("admin_edit",material_id=material_id))

@app.post("/admin/delete/<int:material_id>")
@admin_required
def admin_delete(material_id):
    conn=db()
    item=conn.execute("SELECT * FROM materials WHERE id=?",(material_id,)).fetchone()
    gallery=conn.execute("SELECT image FROM gallery WHERE material_id=?",(material_id,)).fetchall()
    if item:
        paths=[item["image"],item["audio"]]+[x["image"] for x in gallery]
        for value in paths:
            if value and value.startswith("uploads/"):
                p=STATIC_DIR/value
                if p.exists():
                    p.unlink()
        conn.execute("DELETE FROM materials WHERE id=?",(material_id,))
        conn.commit()
    conn.close()
    flash("Материал удалён","success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/sections")
@admin_required
def admin_sections():
    conn=db()
    rows=conn.execute("SELECT * FROM sections ORDER BY parent_slug,sort_order,id").fetchall()
    conn.close()
    return render_template("admin_sections.html",sections=rows)

@app.route("/admin/sections/new",methods=["GET","POST"])
@admin_required
def admin_section_new():
    if request.method=="POST":
        slug=request.form.get("slug","").strip().lower()
        title=request.form.get("title","").strip()
        if not slug or not title:
            flash("Нужны slug и название","danger")
            return redirect(request.url)
        conn=db()
        try:
            conn.execute(
                """INSERT INTO sections(slug,title,parent_slug,eyebrow,image,sort_order,visible)
                   VALUES(?,?,?,?,?,?,?)""",
                (slug,title,request.form.get("parent_slug","").strip(),
                 request.form.get("eyebrow","").strip(),
                 request.form.get("image","").strip() or "img/archive.svg",
                 int(request.form.get("sort_order") or 0),
                 1 if request.form.get("visible") else 0)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("Такой slug уже существует","danger")
            return redirect(request.url)
        conn.close()
        flash("Раздел добавлен","success")
        return redirect(url_for("admin_sections"))
    return render_template("admin_section_form.html",section=None,parents=get_main_groups())

@app.route("/admin/sections/edit/<int:section_id>",methods=["GET","POST"])
@admin_required
def admin_section_edit(section_id):
    conn=db()
    row=conn.execute("SELECT * FROM sections WHERE id=?",(section_id,)).fetchone()
    if not row:
        conn.close()
        abort(404)
    if request.method=="POST":
        old_slug=row["slug"]
        new_slug=request.form.get("slug","").strip().lower()
        title=request.form.get("title","").strip()
        if not new_slug or not title:
            conn.close()
            flash("Нужны slug и название","danger")
            return redirect(request.url)
        try:
            conn.execute(
                """UPDATE sections SET slug=?,title=?,parent_slug=?,eyebrow=?,image=?,
                   sort_order=?,visible=? WHERE id=?""",
                (new_slug,title,request.form.get("parent_slug","").strip(),
                 request.form.get("eyebrow","").strip(),
                 request.form.get("image","").strip() or "img/archive.svg",
                 int(request.form.get("sort_order") or 0),
                 1 if request.form.get("visible") else 0,section_id)
            )
            if new_slug != old_slug:
                conn.execute("UPDATE materials SET section_slug=? WHERE section_slug=?",(new_slug,old_slug))
                conn.execute("UPDATE sections SET parent_slug=? WHERE parent_slug=?",(new_slug,old_slug))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("Такой slug уже существует","danger")
            return redirect(request.url)
        conn.close()
        flash("Раздел сохранён","success")
        return redirect(url_for("admin_sections"))
    conn.close()
    return render_template("admin_section_form.html",section=row,parents=get_main_groups())

@app.post("/admin/sections/delete/<int:section_id>")
@admin_required
def admin_section_delete(section_id):
    conn=db()
    row=conn.execute("SELECT * FROM sections WHERE id=?",(section_id,)).fetchone()
    if not row:
        conn.close()
        abort(404)
    used=conn.execute("SELECT COUNT(*) n FROM materials WHERE section_slug=?",(row["slug"],)).fetchone()["n"]
    children=conn.execute("SELECT COUNT(*) n FROM sections WHERE parent_slug=?",(row["slug"],)).fetchone()["n"]
    if used or children:
        conn.close()
        flash("Нельзя удалить раздел: в нём есть материалы или подразделы","danger")
        return redirect(url_for("admin_sections"))
    conn.execute("DELETE FROM sections WHERE id=?",(section_id,))
    conn.commit()
    conn.close()
    flash("Раздел удалён","success")
    return redirect(url_for("admin_sections"))

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"),404

init_db()

if __name__=="__main__":
    from waitress import serve
    serve(app, host="127.0.0.1", port=5000, threads=8)
