import os
import sqlite3
import uuid
from pathlib import Path
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, abort
)
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "museum.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "pavlov-museum-local-change-me")
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

ALLOWED_IMAGE = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_AUDIO = {"mp3", "wav", "ogg", "m4a"}

GROUPS = [
    {
        "slug": "biography",
        "title": "Биография",
        "eyebrow": "Жизненный путь",
        "image": "img/biography.svg",
        "children": [
            ("autobiography", "Автобиография"),
            ("bibliography", "Библиография"),
            ("chronicle", "Летопись жизни и деятельности"),
        ],
    },
    {
        "slug": "heritage",
        "title": "Наследие",
        "eyebrow": "Творчество и документы",
        "image": "img/heritage.svg",
        "children": [
            ("literary-works", "Литературные произведения"),
            ("musical-works", "Музыкальные произведения"),
            ("journalism", "Публицистика"),
            ("letters", "Письма"),
            ("archive", "Архивные материалы"),
        ],
    },
    {
        "slug": "memory",
        "title": "Память",
        "eyebrow": "Павлов в культуре",
        "image": "img/memory.svg",
        "children": [
            ("in-art", "Фёдор Павлов в искусстве"),
            ("in-music", "Фёдор Павлов в музыке"),
            ("in-literature", "Фёдор Павлов в литературе"),
        ],
    },
    {
        "slug": "contemporaries",
        "title": "Современники",
        "eyebrow": "Люди эпохи",
        "image": "img/contemporaries.svg",
        "children": [
            ("stepan-maksimov", "Степан Максимов"),
            ("vasiliy-vorobyev", "Василий Воробьёв"),
            ("iosif-lyublin", "Иосиф Люблин"),
            ("sigizmund-gaber", "Сигизмунд Габер"),
            ("vladimir-krivonosov", "Владимир Кривоносов"),
            ("vladimir-ivanishin", "Владимир Иванишин"),
        ],
    },
]

SPECIAL = {
    "excursion": {
        "slug": "excursion",
        "title": "Экскурсия",
        "eyebrow": "Маршрут по музею",
        "image": "img/excursion.svg",
        "children": [],
    }
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS materials (
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
        """
    )
    count = conn.execute("SELECT COUNT(*) AS n FROM materials").fetchone()["n"]
    if count == 0:
        seed_materials(conn)
    conn.commit()
    conn.close()


def seed_materials(conn):
    rows = [
        ("autobiography", "Фёдор Павлович Павлов", "1892–1931", 
         "Фёдор Павлович Павлов — чувашский композитор, дирижёр, педагог, драматург и фольклорист. "
         "Он родился в селе Богатырёво Ядринского уезда. Музыка вошла в его жизнь ещё в детстве: "
         "в семье знали народные песни, играли на гуслях, а позднее Павлов серьёзно занимался хоровым пением и скрипкой.\n\n"
         "В 1911 году он окончил Симбирскую чувашскую учительскую школу. В разные годы преподавал музыку, "
         "работал в сфере народного образования, собирал и обрабатывал народные песни, организовывал театральную и концертную жизнь. "
         "В 1930 году поступил на композиторское отделение Ленинградской консерватории. Его жизнь оборвалась 2 июня 1931 года в Сочи.",
         "img/pavlov.svg", "", "1892–1931", 10, 1),
        ("chronicle", "1892 — рождение", "Начало жизненного пути",
         "Фёдор Павлов родился в 1892 году в селе Богатырёво. Детство, народная песенная традиция и семейная музыкальная среда "
         "во многом определили его будущий интерес к музыке и фольклору.",
         "img/biography.svg", "", "1892", 10, 0),
        ("chronicle", "1907–1911 — Симбирская школа", "Учёба и музыкальное образование",
         "В Симбирской чувашской учительской школе Павлов изучал музыку, участвовал в хоре и инструментальных коллективах. "
         "После окончания школы преподавал пение.",
         "img/biography.svg", "", "1907–1911", 20, 0),
        ("chronicle", "1920-е — организатор музыкальной жизни", "Хор, школа, театр",
         "В 1920-е годы Павлов активно участвовал в становлении профессиональной музыкальной культуры Чувашии: "
         "преподавал, дирижировал, организовывал хоровую работу и концертную деятельность.",
         "img/heritage.svg", "", "1920-е", 30, 0),
        ("chronicle", "1930–1931 — Ленинградская консерватория", "Последний этап",
         "В 1930 году Павлов начал обучение композиции в Ленинградской государственной консерватории. "
         "Учёба была прервана болезнью. В 1931 году он умер в Сочи.",
         "img/biography.svg", "", "1930–1931", 40, 0),
        ("bibliography", "Книги и исследования о Фёдоре Павлове", "Библиографический раздел",
         "Здесь собраны сведения о книгах, статьях, исследованиях и изданиях, посвящённых Фёдору Павлову. "
         "Администратор музея может добавлять отдельные карточки для каждого издания, обложки и аннотации.",
         "img/archive.svg", "", "", 10, 0),
        ("literary-works", "«Сутра» («На суде»)", "Комедия",
         "Комедия «Сутра» («На суде») относится к ранним оригинальным произведениям чувашской драматургии. "
         "Первая редакция была показана театральной труппой в конце 1910-х годов, а произведение было опубликовано в 1919 году.",
         "img/heritage.svg", "", "1919", 10, 1),
        ("literary-works", "«Ялта» («В деревне»)", "Драма",
         "Драма «Ялта» («В деревне») была создана в начале 1920-х годов и входит в литературное наследие Павлова.",
         "img/heritage.svg", "", "1922", 20, 0),
        ("musical-works", "«Чӳк»", "Музыкальное произведение",
         "«Чӳк» («Моление чуваш») — одно из произведений, связанных с обращением Павлова к национальной музыкальной традиции. "
         "В админ-панели к этой карточке можно загрузить аудиозапись — после этого здесь появится крупный музейный плеер.",
         "img/music.svg", "", "", 10, 1),
        ("musical-works", "«Вӑйӑ»", "Музыкальное произведение",
         "«Вӑйӑ» («Хоровод») связано с фольклорными и песенными традициями. "
         "Для экспозиции можно добавить историческую запись, современное исполнение или фрагмент нот.",
         "img/music.svg", "", "", 20, 0),
        ("musical-works", "«Вӗлле хурчӗ»", "Песня",
         "Песня «Вӗлле хурчӗ» («Пчёлка») создана Павловым на собственный текст. "
         "Раздел рассчитан на воспроизведение аудио прямо с сенсорного стола.",
         "img/music.svg", "", "", 30, 0),
        ("journalism", "Публицистика", "Статьи и очерки",
         "В этом разделе размещаются публицистические тексты и материалы Павлова, посвящённые культуре, музыке, "
         "просвещению и общественной жизни.",
         "img/archive.svg", "", "", 10, 0),
        ("letters", "Письма", "Эпистолярное наследие",
         "Раздел предназначен для писем, рукописей и их расшифровок. К каждой карточке можно добавить скан документа "
         "и полный текст для удобного чтения на большом сенсорном экране.",
         "img/archive.svg", "", "", 10, 0),
        ("archive", "Архивные материалы", "Документы, рукописи, фотографии",
         "Здесь можно разместить сканы документов, афиш, нотных рукописей, фотографий и других музейных предметов.",
         "img/archive.svg", "", "", 10, 0),
        ("in-art", "Фёдор Павлов в изобразительном искусстве", "Портреты и памятные образы",
         "Раздел для портретов, памятников, художественных работ и фотографий, связанных с образом Фёдора Павлова.",
         "img/memory.svg", "", "", 10, 0),
        ("in-music", "Память в музыке", "Исполнения и посвящения",
         "Здесь могут храниться современные исполнения произведений Павлова, концертные записи и музыкальные посвящения.",
         "img/music.svg", "", "", 10, 0),
        ("in-literature", "Павлов в литературе", "Исследования и воспоминания",
         "Раздел для литературных произведений, воспоминаний и исследовательских текстов о жизни и творчестве Павлова.",
         "img/memory.svg", "", "", 10, 0),
        ("excursion", "Добро пожаловать в музей", "Интерактивная экскурсия",
         "Начните знакомство с Фёдором Павловым с биографии, затем перейдите к литературному и музыкальному наследию, "
         "посмотрите архивные документы и познакомьтесь с его современниками. Все материалы адаптированы для сенсорного стола.",
         "img/excursion.svg", "", "", 10, 1),
    ]
    people = [
        ("stepan-maksimov", "Степан Максимов"),
        ("vasiliy-vorobyev", "Василий Воробьёв"),
        ("iosif-lyublin", "Иосиф Люблин"),
        ("sigizmund-gaber", "Сигизмунд Габер"),
        ("vladimir-krivonosov", "Владимир Кривоносов"),
        ("vladimir-ivanishin", "Владимир Иванишин"),
    ]
    for i, (slug, name) in enumerate(people, start=1):
        rows.append((slug, name, "Современник Фёдора Павлова",
                     "Карточка раздела «Современники». Здесь можно разместить биографический текст, фотографии, "
                     "документы и материалы о связи этого человека с Фёдором Павловым.",
                     "img/contemporaries.svg", "", "", i * 10, 0))
    conn.executemany(
        """INSERT INTO materials
        (section_slug,title,subtitle,body,image,audio,year,sort_order,featured)
        VALUES(?,?,?,?,?,?,?,?,?)""", rows
    )


def all_sections():
    result = []
    for group in GROUPS:
        result.append((group["slug"], group["title"]))
        result.extend(group["children"])
    result.append(("excursion", "Экскурсия"))
    return result


def section_info(slug):
    for group in GROUPS:
        if group["slug"] == slug:
            return {**group, "parent": None}
        for child_slug, child_title in group["children"]:
            if child_slug == slug:
                return {
                    "slug": child_slug,
                    "title": child_title,
                    "eyebrow": group["title"],
                    "image": group["image"],
                    "children": [],
                    "parent": group,
                }
    if slug in SPECIAL:
        return {**SPECIAL[slug], "parent": None}
    return None


def save_upload(file, kind):
    if not file or not file.filename:
        return ""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed = ALLOWED_IMAGE if kind == "image" else ALLOWED_AUDIO
    if ext not in allowed:
        raise ValueError("Недопустимый формат файла")
    original = secure_filename(file.filename) or f"file.{ext}"
    filename = f"{uuid.uuid4().hex[:10]}_{original}"
    file.save(UPLOAD_DIR / filename)
    return f"uploads/{filename}"


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


@app.context_processor
def globals_for_templates():
    return {"groups": GROUPS, "special": SPECIAL}


@app.route("/")
def index():
    conn = get_db()
    featured = conn.execute(
        "SELECT * FROM materials WHERE featured=1 ORDER BY sort_order,id LIMIT 6"
    ).fetchall()
    conn.close()
    return render_template("index.html", featured=featured)


@app.route("/section/<slug>")
def section(slug):
    info = section_info(slug)
    if not info:
        abort(404)
    conn = get_db()
    items = conn.execute(
        "SELECT * FROM materials WHERE section_slug=? ORDER BY sort_order,id", (slug,)
    ).fetchall()
    conn.close()
    return render_template("section.html", section=info, items=items)


@app.route("/material/<int:material_id>")
def material(material_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM materials WHERE id=?", (material_id,)).fetchone()
    conn.close()
    if not item:
        abort(404)
    return render_template("material.html", item=item, section=section_info(item["section_slug"]))


@app.route("/search")
def search():
    q = (request.args.get("q") or "").strip()
    rows = []
    if q:
        conn = get_db()
        rows = conn.execute(
            """SELECT * FROM materials
               WHERE title LIKE ? OR subtitle LIKE ? OR body LIKE ? OR year LIKE ?
               ORDER BY featured DESC, sort_order, title""",
            tuple([f"%{q}%"] * 4),
        ).fetchall()
        conn.close()
    return render_template("search.html", q=q, results=rows)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("Неверный логин или пароль", "danger")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()
    items = conn.execute("SELECT * FROM materials ORDER BY section_slug,sort_order,id").fetchall()
    conn.close()
    return render_template("admin.html", items=items, sections=all_sections())


@app.route("/admin/new", methods=["GET", "POST"])
@admin_required
def admin_new():
    if request.method == "POST":
        try:
            image = save_upload(request.files.get("image_file"), "image")
            audio = save_upload(request.files.get("audio_file"), "audio")
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(request.url)
        conn = get_db()
        conn.execute(
            """INSERT INTO materials
            (section_slug,title,subtitle,body,image,audio,year,sort_order,featured)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                request.form["section_slug"],
                request.form["title"].strip(),
                request.form.get("subtitle", "").strip(),
                request.form.get("body", "").strip(),
                image or request.form.get("image", "").strip(),
                audio,
                request.form.get("year", "").strip(),
                int(request.form.get("sort_order") or 0),
                1 if request.form.get("featured") else 0,
            ),
        )
        conn.commit()
        conn.close()
        flash("Материал добавлен", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_form.html", item=None, sections=all_sections())


@app.route("/admin/edit/<int:material_id>", methods=["GET", "POST"])
@admin_required
def admin_edit(material_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM materials WHERE id=?", (material_id,)).fetchone()
    if not item:
        conn.close()
        abort(404)
    if request.method == "POST":
        try:
            new_image = save_upload(request.files.get("image_file"), "image")
            new_audio = save_upload(request.files.get("audio_file"), "audio")
        except ValueError as e:
            conn.close()
            flash(str(e), "danger")
            return redirect(request.url)
        image = new_image or request.form.get("image", "").strip() or item["image"]
        audio = new_audio or item["audio"]
        if request.form.get("remove_audio"):
            audio = ""
        conn.execute(
            """UPDATE materials SET
               section_slug=?,title=?,subtitle=?,body=?,image=?,audio=?,year=?,sort_order=?,featured=?
               WHERE id=?""",
            (
                request.form["section_slug"],
                request.form["title"].strip(),
                request.form.get("subtitle", "").strip(),
                request.form.get("body", "").strip(),
                image,
                audio,
                request.form.get("year", "").strip(),
                int(request.form.get("sort_order") or 0),
                1 if request.form.get("featured") else 0,
                material_id,
            ),
        )
        conn.commit()
        conn.close()
        flash("Изменения сохранены", "success")
        return redirect(url_for("admin_dashboard"))
    conn.close()
    return render_template("admin_form.html", item=item, sections=all_sections())


@app.post("/admin/delete/<int:material_id>")
@admin_required
def admin_delete(material_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM materials WHERE id=?", (material_id,)).fetchone()
    if item:
        for field in ("image", "audio"):
            value = item[field]
            if value and value.startswith("uploads/"):
                p = BASE_DIR / "static" / value
                if p.exists():
                    p.unlink()
        conn.execute("DELETE FROM materials WHERE id=?", (material_id,))
        conn.commit()
    conn.close()
    flash("Материал удалён", "success")
    return redirect(url_for("admin_dashboard"))


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
