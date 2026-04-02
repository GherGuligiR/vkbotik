import sqlite3

conn = sqlite3.connect("dune.db")
cursor = conn.cursor()

# =========================
# 🧱 ТАБЛИЦЫ
# =========================
cursor.executescript("""
CREATE TABLE IF NOT EXISTS Scenes (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Scene TEXT UNIQUE,
    Text TEXT
);

CREATE TABLE IF NOT EXISTS Choices (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    SceneId TEXT,
    ChoiceText TEXT,
    NextScene TEXT,
    WaterEffect INTEGER DEFAULT 0,
    HealthEffect INTEGER DEFAULT 0,
    KarmaEffect INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Players (
    VkId INTEGER PRIMARY KEY,
    CurrentScene TEXT,
    Health INTEGER DEFAULT 100,
    Water INTEGER DEFAULT 50,
    Karma INTEGER DEFAULT 0
);
""")

# =========================
# 📖 РАСШИРЕННЫЙ СЮЖЕТ
# =========================
cursor.executescript("""
DELETE FROM Choices;
DELETE FROM Scenes;

INSERT INTO Scenes (Scene, Text) VALUES
('start', '🏜️ **ПУСТЫНЯ АРРАКИС** 🏜️\n\nВы прибыли на планету пустыни. Перед вами раскинулись бескрайние пески, а вдали виднеются стены города Арракина.\n\nКуда вы направитесь?'),
('city', '🏙️ **ГОРОД АРРАКИН** 🏙️\n\nВы вошли в город. Здесь пахнет специями и страхом. На улицах снуют торговцы, а в тени прячутся нищие.\n\nЧто вы сделаете?'),
('desert', '🏜️ **ГЛУБОКАЯ ПУСТЫНЯ** 🏜️\n\nВы ушли в пустыню. Песок скрипит под ногами, ветер завывает. Вдали вы замечаете движение...'),
('market', '🛍️ **РЫНОК** 🛍️\n\nВы на шумном рынке. Торговцы предлагают воду, специи и редкие артефакты. Вдруг кто-то хватает вас за руку...'),
('sietch', '🏔️ **СИЕТЧ ФРИМЕНОВ** 🏔️\n\nВы нашли убежище фрименов. Суровые пустынники с интересом разглядывают вас. Их лидер выходит вперёд.'),
('trial', '⚔️ **ИСПЫТАНИЕ** ⚔️\n\nФримены хотят проверить вашу силу духа. Вам предстоит пройти древний ритуал.'),
('worm_encounter', '🐛 **ВСТРЕЧА С ЧЕРВЁМ** 🐛\n\nИз песка поднимается гигантский песчаный червь! Земля дрожит, воздух наполняется рёвом.'),
('vision', '🔮 **ВИДЕНИЕ** 🔮\n\nВас посещает видение. Вы видите себя правителем Арракиса... или его разрушителем.'),
('final_good', '👑 **СПАСИТЕЛЬ АРРАКИСА** 👑\n\nВы объединили фрименов и принесли мир на планету. Вода течёт по каналам, народ ликует. Вы стали легендой!'),
('final_bad', '💀 **ТИРАН ПУСТЫНИ** 💀\n\nЖажда власти погубила вас. Вы стали жестоким правителем, которого боятся даже фримены. Арракис погрузился во тьму.'),
('final_worm', '🐛 **ЕДИНЫЙ С ЧЕРВЁМ** 🐛\n\nВы оседлали песчаного червя и стали частью пустыни. Легенды говорят, что вы до сих пор бродите по пескам...'),
('final_neutral', '🌵 **ИСЧЕЗНУВШИЙ В ПЕСКАХ** 🌵\n\nВы отказались от судьбы и исчезли в бескрайней пустыне. Никто не знает, что с вами случилось.');

-- СЦЕНА START
INSERT INTO Choices (SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect, KarmaEffect) VALUES
('start', 'Пойти в город Арракин', 'city', -5, 20, 0),
('start', 'Идти в пустыню', 'desert', -10, -5, 0),
('start', 'Попытаться найти фрименов', 'desert', -15, -10, 5);

-- СЦЕНА CITY
INSERT INTO Choices (SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect, KarmaEffect) VALUES
('city', 'Помочь умирающему нищему', 'market', -10, 0, 10),
('city', 'Ограбить торговца специями', 'market', 15, 0, -15),
('city', 'Искать убежище', 'sietch', -5, 5, 5);

-- СЦЕНА DESERT
INSERT INTO Choices (SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect, KarmaEffect) VALUES
('desert', 'Следовать за вибрацией в песке', 'worm_encounter', -5, -10, 0),
('desert', 'Вернуться в город', 'city', -10, -5, 0),
('desert', 'Копать в поисках воды', 'start', -20, -15, -5);

-- СЦЕНА MARKET
INSERT INTO Choices (SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect, KarmaEffect) VALUES
('market', 'Купить воду за последние деньги', 'sietch', -15, 15, 0),
('market', 'Украсть воду', 'desert', 20, -10, -20),
('market', 'Предложить свои услуги фрименам', 'sietch', -5, 0, 10);

-- СЦЕНА SIETCH
INSERT INTO Choices (SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect, KarmaEffect) VALUES
('sietch', 'Довериться фрименам', 'trial', 0, 5, 10),
('sietch', 'Попытаться сбежать', 'desert', -10, -15, -5),
('sietch', 'Предложить сделку', 'trial', 0, 0, 0);

-- СЦЕНА TRIAL
INSERT INTO Choices (SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect, KarmaEffect) VALUES
('trial', 'Пройти испытание честно', 'vision', 0, 10, 15),
('trial', 'Обмануть фрименов', 'vision', 0, 5, -15),
('trial', 'Отказаться от испытания', 'final_neutral', 0, -20, -10);

-- СЦЕНА VISION
INSERT INTO Choices (SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect, KarmaEffect) VALUES
('vision', 'Использовать силу во благо', 'final_good', 0, 20, 20),
('vision', 'Подчинить всех своей воле', 'final_bad', 0, 20, -25),
('vision', 'Вернуться в пустыню', 'final_neutral', -30, -10, 0);

-- СЦЕНА WORM_ENCOUNTER
INSERT INTO Choices (SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect, KarmaEffect) VALUES
('worm_encounter', 'Попытаться оседлать червя', 'final_worm', 0, -50, 10),
('worm_encounter', 'Бежать что есть сил', 'desert', -20, -30, -5),
('worm_encounter', 'Молиться песчаным богам', 'start', 0, -100, 0);
""")

conn.commit()
conn.close()

print("✅ База данных создана и наполнена расширенным сюжетом!")
