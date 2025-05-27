import datetime
import threading
from selenium.webdriver.support import expected_conditions as EC
from datetime import date
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import ElementClickInterceptedException
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


lock = threading.Lock()
matches = []


def process_channel(channel):
    local_matches = []
    driver = webdriver.Chrome(options=options)
    url = 'https://tvplus.com.tr/canli-tv/yayin-akisi/' + channel[0]
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    day = date.today()

    while True:
        if soup.find('li', class_="day-names-item active").find('div').find('span').text != str(day.day):
            button = driver.find_element(By.CSS_SELECTOR, "li.day-names-item.active")
            button = button.find_element(By.XPATH, "following-sibling::li[1]")
            button.click()
            time.sleep(0.2)
            day += datetime.timedelta(days=1)
            soup = BeautifulSoup(driver.page_source, "html.parser")

        frames = soup.find_all('li', class_="playbill-list-item")
        for frame in frames:
            if "sağlanamamaktadır" in frame.text:
                continue
            live = frame.find('div', class_="rtuk-icons-container").find('div').text
            if live == "C" and "-" in frame.find('h3').text:
                key = 0
                link = "https://tvplus.com.tr/izle/kanal/" + channel[0].split("-")[-1]
                description = frame.find('p', class_="introduce").text
                for league in leagues_set:
                    if league in description:
                        local_matches.append([str(day), frame.find('time').text.split(" ")[0],
                                              frame.find('h3').text.split('-')[0].strip(),
                                              frame.find('h3').text.split('-')[1].strip(), channel[1], league, league,
                                              link])
                        key = 1
                        break
                if key == 0:
                    league = ""
                    if channel[1] in ["ATV", "A Spor"]:
                        league = "Ziraat Türkiye Kupası"
                        description = "Ziraat Türkiye Kupası"
                    local_matches.append([str(day), frame.find('time').text.split(" ")[0],
                                          frame.find('h3').text.split('-')[0].strip(),
                                          frame.find('h3').text.split('-')[1].strip(), channel[1], league,
                                          description, link])

        try:
            button = driver.find_element(By.CSS_SELECTOR, "li.day-names-item.active")
            button = button.find_element(By.XPATH, "following-sibling::li[1]")
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(button)).click()
            time.sleep(0.2)
            day += datetime.timedelta(days=1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
        except Exception:
            break
    driver.quit()

    with lock:
        matches.extend(local_matches)


def match_merge(matches):
    combined = []
    used = [False] * len(matches)

    for i in range(len(matches)):
        if used[i]:
            continue

        tarih1, saat1, ev1, dep1, kanal1, lig1, aciklama1, link1 = matches[i]
        ev1_lower = ev1.lower()
        dep1_lower = dep1.lower()
        merged_match = {
            "tarih": tarih1,
            "saat": saat1,
            "ev": ev1,
            "dep": dep1,
            "lig": lig1,
            "aciklama": aciklama1,
            "kanallar": {kanal1},
            "linkler": {link1}
        }

        for j in range(i + 1, len(matches)):
            if used[j]:
                continue

            tarih2, saat2, ev2, dep2, kanal2, lig2, aciklama2, link2 = matches[j]
            ev2_lower = ev2.lower()
            dep2_lower = dep2.lower()

            if tarih1 == tarih2 and saat1 == saat2:
                # Benzerlik: takım ismi tam aynı veya içinde geçiyor
                if (
                    ev1_lower in ev2_lower or ev2_lower in ev1_lower or
                    dep1_lower in dep2_lower or dep2_lower in dep1_lower or
                    ev1_lower in dep2_lower or dep2_lower in ev1_lower or
                    dep1_lower in ev2_lower or ev2_lower in dep1_lower
                ):
                    merged_match["kanallar"].add(kanal2)
                    merged_match["linkler"].add(link2)
                    used[j] = True

        used[i] = True
        combined.append([
            merged_match["tarih"],
            merged_match["saat"],
            merged_match["ev"],
            merged_match["dep"],
            "_".join(sorted(merged_match["kanallar"])),
            merged_match["lig"],
            merged_match["aciklama"],
            "_".join(sorted(merged_match["linkler"]))
        ])
    return combined


leagues = ["Trendyol 1. Lig", "2. Lig", "3. Lig", "Portekiz Ligi", "İskoçya Premiership", "İtalya Kupası",
           "LALIGA", "Championship", "Eredivisie", "Belçika Pro Lig", "Serie A", "UEFA Şampiyonlar Ligi",
           "Copa Libertadores", "Copa Sudamericana", "Suudi Arabistan Pro Lig", "UEFA Avrupa Ligi",
           "İngiltere Premier Lig", "Portekiz Süper Ligi", "Almanya Bundesliga", "Almanya 2. Bundesliga",
           "Fransa Ligi", "Trendyol Süper Lig", "MLS", "NBA", "EuroLeague", "Türkiye Sigorta Basketbol Süper Ligi",
           "Formula 1", "Formula 2", "Formula 3", "Formula 4", "Formula Academy", "Fransa Lig 2", "EFL League 1",
           "EFL League 2", "Fransa Kupası"]

leagues_set = set(leagues)

channels = [["trt-spor-hd--31", "TRT Spor"], ["trt1-hd--144", "TRT 1"], ["trt-spor-yildiz--205", "TRT Spor Yıldız"],
            ["tv8-hd--134", "TV 8"], ["tv85-hd--188", "TV 8,5"], ["atv-hd--124", "ATV"], ["a-spor-hd--3", "A Spor"],
            ["ht-spor--4396", "HT Spor"], ["fb-tv--148", "FB TV"], ["tabii-spor--4399", "Tabii Spor"]]

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(process_channel, channel): channel for channel in channels}
    for _ in tqdm(as_completed(futures), total=len(futures), desc="TV+", ncols=100):
        pass

url = "https://ssport.tv/yayin-akisi"
driver.get(url)
time.sleep(0.3)
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')
frames = (soup.find('ul', class_="uk-switcher uk-margin-small-top", id="switcher-day-s-sport")
          .find_all('ul', class_="uk-list streaming-list uk-margin-small"))
inframes = []
for frame in frames:
    inframes.append(frame.find_all('li'))
link = "https://tvplus.com.tr/izle/kanal/11"
for frames in tqdm(inframes, desc="S Sport", ncols=100):
    for frame in frames:
        if 'CANLI' not in frame.find('div', class_="uk-width-auto streaming-status uk-flex-first").text:
            continue
        program = frame.find('h3').text
        description = frame.find('p').text
        league = ""
        if '-' not in program:
            if "konferans" not in program.lower():
                continue
        for ll in leagues:
            if ll.lower() in description.lower() or ll.lower() in program.lower():
                league = ll
                break
        starttime = frame.find('time').text
        parentframe = frame.parent.parent
        date = str(parentframe.get("data-date"))
        aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım",
                 "Aralık"]
        date = "2025-" + str(aylar.index(date.split()[1]) + 1).zfill(2) + "-" + date.split()[0].zfill(2)

        if len(program.split('-')) == 1:
             matches.append([date, starttime.strip(), program.split('-')[0].strip(), "",
                        "S Sport 2", league, description, link])
        else:
             matches.append([date, starttime.strip(), program.split('-')[0].strip(), program.split('-')[1].strip(),
                        "S Sport 2", league, description, link])
wait = WebDriverWait(driver, 15)
button = wait.until(
    EC.presence_of_element_located((By.XPATH, "//img[@alt='Logo 2']/ancestor::a"))
)
try:
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//img[@alt='Logo 2']/ancestor::a")))
    button.click()
except ElementClickInterceptedException:
    driver.execute_script("arguments[0].click();", button)


page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')
frames = (soup.find('ul', class_="uk-switcher uk-margin-small-top", id="switcher-day-s-sport-2")
          .find_all('ul', class_="uk-list streaming-list uk-margin-small"))
inframes = []
link = "https://tvplus.com.tr/izle/kanal/170"
for frame in frames:
    inframes.append(frame.find_all('li'))
for frames in tqdm(inframes, desc="S Sport 2", ncols=100):
    for frame in frames:
        if 'CANLI' not in frame.find('div', class_="uk-width-auto streaming-status uk-flex-first").text:
            continue
        program = frame.find('h3').text
        description = frame.find('p').text
        league = ""
        if '-' not in program:
            if "konferans" not in program.lower():
                continue
        for ll in leagues:
            if ll.lower() in description.lower() or ll.lower() in program.lower():
                league = ll
                break
        starttime = frame.find('time').text
        parentframe = frame.parent.parent
        date = str(parentframe.get("data-date"))
        aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım",
                 "Aralık"]
        date = "2025-" + str(aylar.index(date.split()[1]) + 1).zfill(2) + "-" + date.split()[0].zfill(2)
        if len(program.split('-')) == 1:
             matches.append([date, starttime.strip(), program.split('-')[0].strip(), "",
                        "S Sport 2", league, description, link])
        else:
             matches.append([date, starttime.strip(), program.split('-')[0].strip(), program.split('-')[1].strip(),
                        "S Sport 2", league, description, link])


url = 'https://www.todtv.com.tr/spor/haftanin-maclari'
driver.get(url)

time.sleep(3)
html = driver.page_source

soup = BeautifulSoup(html, 'html.parser')
bigframe = soup.find('div', class_="container weekOfMatches")
frame = bigframe.find('h2')
league = ""
while 1:
    if frame.name == "h2":
        league = frame.text.strip().replace("®", "")
    else:
        tarih = frame.find('div', class_="tod-match__time").find('span')
        if tarih.find('svg'):
            if frame.find_previous_sibling().name == "h2":
                tarih = "{} {}".format(datetime.date.today().day, aylar[datetime.date.today().month - 1])
            else:
                if frame.find_previous_sibling().find('div', class_="tod-match__time").find('span').find('svg'):
                    tarih = "{} {}".format(datetime.date.today().day, aylar[datetime.date.today().month - 1])
                else:
                    tarih = (frame.find_previous_sibling().find('div', class_="tod-match__time").find('span')
                             .text.strip())
        else:
            tarih = tarih.text.strip()
        if tarih == "Bugün":
            tarih = datetime.date.today()
            tarih = tarih.strftime("%Y-%m-%d")
        elif tarih == "Yarın":
            tarih = datetime.date.today() + datetime.timedelta(days=1)
            tarih = tarih.strftime("%Y-%m-%d")
        else:
            tarih = tarih.split()
            tarih = "2025-" + str(aylar.index(tarih[1]) + 1).zfill(2) + "-" + tarih[0].zfill(2)
        start_time = (frame.find('div', class_="tod-match__time")
                      .find('div', class_="text-center d-flex flex-row justify-content-center tod-match__time__hour")
                      .text.strip())
        teams = frame.find_all('span', class_="tod-match__club")
        if len(teams) < 2:
            teams.append(frame.find('span', class_="tod-match__practice"))
        home = teams[0].text.strip().replace("  ", " ").replace("Formula 1", "")
        home = home.replace("Formula 2", "").replace("Formula 3", "")
        away = teams[1].text.strip().replace("  ", " ")
        channel = frame.find('span', class_="match__detail--channel").text.strip()
        link = "https://www.todtv.com.tr" + frame.get("href")
        if not ("MAX" in channel or "3" in channel or "4" in channel or "5" in channel):
            channel = channel[0].upper() + channel[1:]
        if "OTT" in channel:
            channel = "ott"
        key = 0
        desc = league
        for ll in leagues:
            if ll.lower() in league.lower():
                league = ll
                key = 1
                break
        if key == 0:
            league = ""
        matches.append([tarih, start_time, home, away, channel, league, desc, link])
    frame = frame.find_next_sibling()
    if not frame:
        break

matches.sort()
matches = match_merge(matches)
matches = sorted(matches, key=lambda x: (x[0], x[1], x[4]))
outfile = open("matches.txt", "w", encoding="utf-8")
for match in matches:
    print(match[5])
    if "Almanya " in match[5] or "Fransa Ligi" in match[5] or "Fransa Lig" in match[5]:
        match[5] = match[5].replace("Almanya ", "").replace("Fransa Ligi", "Ligue 1").replace("Fransa Lig", "Ligue")
        match[6] = match[6].replace("Almanya ", "").replace("Fransa Ligi", "Ligue 1").replace("Fransa Lig", "Ligue")
    outfile.writelines(";".join(match) + "\n")
