from datetime import datetime
from datetime import timedelta
from datetime import date

football = ["1. Lig", "2. Lig", "3. Lig", "Portekiz Ligi", "İskoçya Premiership", "İtalya Kupası", "LALIGA",
            "Championship", "Eredivisie", "Belçika Pro Lig", "Serie A", "UEFA Şampiyonlar Ligi", "Copa Libertadores",
            "Copa Sudamericana", "Suudi Arabistan Pro Lig", "UEFA Avrupa Ligi", "İngiltere Premier Lig",
            "Portekiz Süper Ligi", "Trendyol 1. Lig", "Bundesliga", "2. Bundesliga", "Ligue 1",
            "Trendyol Süper Lig", "MLS", "Ziraat Türkiye Kupası", "Fransa Lig 2", "EFL League 1", "EFL League 2", "Fransa Kupası"]
basketball = ["NBA", "EuroLeague", "Türkiye Sigorta Basketbol Süper Ligi"]

infile = open("matches.txt", "r", encoding="utf-8")
outfile = open("/var/www/html/index.html", "w", encoding="utf-8")
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
day = date.today()
outfile.writelines("""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Spor Müsabakaları Yayın Takvimi</title>
    <link rel="icon" type="image/png" href="images/tv.png">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="layout">
        <aside class="sidebar">
            <div class="filters">
                <button id="toggle-filters" class="filter-button">Tümünü Temizle</button>
                <div id="sport-filter-area"></div>
            </div>
        </aside>
        <main class="container">
            <div class="date-banner">
                <span>{}</span> {} {}
            </div>

""".format(day.day, aylar[day.month - 1], gunler[day.weekday()]))

for match in infile:
    match = match.strip().split(";")
    if len(match) < 7:
        outfile = open("bos.html", "w", encoding="utf-8")
    date = datetime.strptime(match[0] + " " + match[1], "%Y-%m-%d %H:%M")
    if date + timedelta(hours=2) < datetime.now():
        continue
    else:
        color = ""
        if (match[5] in football) or ("Futbol" in match[6]) or ("futbol" in match[6]):
            color = "-green"
        elif (match[5] in basketball) or ("Basketbol" in match[6]) or ("basketbol" in match[6]):
            color = "-orange"
        elif "Formula 1" in match[6]:
            color = "-red"
        if match[0] != str(day):
            day += timedelta(days=1)
            outfile.writelines("""
            <div class="date-banner">
                <span>{}</span> {} {}
            </div>
            """.format(day.day, aylar[day.month - 1], gunler[day.weekday()]))
        start_time, home, away, channel, league, description, url = match[1:]
        key = ""
        if date < datetime.now() + timedelta(minutes=10):
            key = " live-match"
        channel = channel.split("_")
        url = url.split("_")
        outfile.writelines("""
            <div class="match">
                <div class="match-time{}{}">{}</div>
                <div class="match-logo">
                    <img src="images/{}.png" alt="{}">
                </div>
                <div class="match-info">
                    <div class="league">{}</div>
                    <h3>{} - {}</h3>
                </div>
        """.format(color, key, start_time, league, league, description, home, away))
        for i in range(len(channel)):
            outfile.writelines("""
                <div class="channel-logo">
                    <a href="{}" target="_blank">
                        <img src="images/{}.png" alt="{}">
                    </a>
                </div>""".format(url[i], channel[i], channel[i]))
        outfile.writelines("""
            </div>""")
outfile.writelines("""
        </main>
    </div>
    <script src="filters.js" defer></script>
    <footer>
        Spor Müsabakaları Yayın Takvimi
    </footer>

</body>
</html>

""")
