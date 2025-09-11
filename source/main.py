import os
import requests
import urllib.parse
import urllib3
from github import Github, Auth, InputGitTreeElement
from github import GithubException
from datetime import datetime
import zoneinfo
import concurrent.futures
import threading
import re
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------------------- ЛОГИРОВАНИЕ --------------------
# Собираем сообщения по каждому номеру файла, чтобы затем вывести их в порядке 1 → N

LOGS_BY_FILE: dict[int, list[str]] = defaultdict(list)
_LOG_LOCK = threading.Lock()
changed_file_numbers = []


_GITHUBMIRROR_INDEX_RE = re.compile(r"githubmirror/mariya-(\d+)\.txt")


def _extract_index(msg: str) -> int:
    """Пытается извлечь номер файла из строки вида 'githubmirror/mariya-12.txt'.
    Если номер не найден, возвращает 0 (для общих сообщений)."""
    m = _GITHUBMIRROR_INDEX_RE.search(msg)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return 0


def log(message: str):
    """Добавляет сообщение в общий словарь логов потокобезопасно."""
    idx = _extract_index(message)
    with _LOG_LOCK:
        LOGS_BY_FILE[idx].append(message)

# Получение текущего времени по часовому поясу Европа/Варшава
zone = zoneinfo.ZoneInfo("Europe/Warsaw")
thistime = datetime.now(zone)
offset = thistime.strftime("%H:%M | %d.%m.%Y")  # Формат времени для коммитов

# Получение GitHub токена из переменных окружения
GITHUB_TOKEN = os.environ.get("MY_TOKEN")
# Имя репозитория для загрузки файлов
REPO_NAME = "sprutadm/free"

# Создаём объект Github и репозиторий один раз, чтобы не делать это при каждой загрузке
if GITHUB_TOKEN:
    g = Github(auth=Auth.Token(GITHUB_TOKEN))
else:
    g = Github()

REPO = g.get_repo(REPO_NAME)

# Проверка и создание локальной папки для хранения файлов, если она отсутствует
if not os.path.exists("githubmirror"):
    os.mkdir("githubmirror")

# Список URL-адресов для скачивания конфигов
URLS = [
    "https://istanbulsydneyhotel.com/blogs/site/sni.php?security=reality", #1
    "https://istanbulsydneyhotel.com/blogs/site/sni.php", #2
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt", #3
    "https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt", #4
    "https://raw.githubusercontent.com/AliDev-ir/FreeVPN/main/pcvpn", #5
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt", #6
    "https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/trojan.txt", #7
    "https://raw.githubusercontent.com/YasserDivaR/pr0xy/main/mycustom1.txt", #8
    "https://vpn.fail/free-proxy/v2ray", #9
    "https://raw.githubusercontent.com/Proxydaemitelegram/Proxydaemi44/refs/heads/main/Proxydaemi44", #10
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt", #11
    # "https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/all", #12
    "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/all.txt", #12
    "https://github.com/Kwinshadow/TelegramV2rayCollector/raw/refs/heads/main/sublinks/mix.txt", #13
    "https://github.com/LalatinaHub/Mineral/raw/refs/heads/master/result/nodes", #14
    "https://raw.githubusercontent.com/miladtahanian/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt", #15
    "https://github.com/freefq/free/raw/refs/heads/master/v2", #16
    "https://github.com/MhdiTaheri/V2rayCollector_Py/raw/refs/heads/main/sub/Mix/mix.txt", #17
    "https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/vmess.txt", #18
    "https://github.com/MhdiTaheri/V2rayCollector/raw/refs/heads/main/sub/mix", #19
    "https://raw.githubusercontent.com/mehran1404/Sub_Link/refs/heads/main/V2RAY-Sub.txt", #20
    "https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt", #21
    "https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/main/output/base64/mix-uri", #22
    "https://raw.githubusercontent.com/AzadNetCH/Clash/refs/heads/main/AzadNet.txt", #23
    "https://raw.githubusercontent.com/STR97/STRUGOV/refs/heads/main/STR.BYPASS#STR.BYPASS%F0%9F%91%BE", #24
    "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt", #25
]

# Пути для сохранения файлов локально и в репозитории
REMOTE_PATHS = [f"githubmirror/mariya-{i+1}.txt" for i in range(len(URLS))]
LOCAL_PATHS = [f"githubmirror/mariya-{i+1}.txt" for i in range(len(URLS))]

# Отключаем предупреждения, если будем использовать verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# UA Chrome 138 (Windows 10 x64)
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)


# Параметры пула соединений и пулов потоков
DEFAULT_MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "16"))

# Глобальная HTTP-сессия с пулом соединений для ускорения повторных запросов
def _build_session(max_pool_size: int) -> requests.Session:
    session = requests.Session()
    # Минимальные автоматические ретраи для сетевых сбоев на уровне TCP/соединения
    adapter = HTTPAdapter(
        pool_connections=max_pool_size,
        pool_maxsize=max_pool_size,
        max_retries=Retry(
            total=1,
            backoff_factor=0.2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=(
                "HEAD",
                "GET",
                "OPTIONS",
            ),
        ),
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": CHROME_UA})
    return session


REQUESTS_SESSION = _build_session(max_pool_size=max(DEFAULT_MAX_WORKERS, len(URLS))) if 'URLS' in globals() else _build_session(DEFAULT_MAX_WORKERS)


# Функция для скачивания данных по URL
def fetch_data(url: str, timeout: int = 10, max_attempts: int = 3, session: requests.Session | None = None) -> str:
    """Пытается скачать данные по URL, делая несколько попыток.

    Логика попыток:
    1. Первая попытка — как есть (verify=True).
    2. Вторая попытка — verify=False (игнорируем SSL-сертификат).
    3. Третья попытка — меняем протокол https → http и verify=False.
    """

    sess = session or REQUESTS_SESSION

    for attempt in range(1, max_attempts + 1):
        try:
            # Определяем параметры для конкретной попытки
            modified_url = url
            verify = True

            if attempt == 2:
                # Попытка 2: отключаем проверку сертификата
                verify = False
            elif attempt == 3:
                # Попытка 3: пробуем http вместо https
                parsed = urllib.parse.urlparse(url)
                if parsed.scheme == "https":
                    modified_url = parsed._replace(scheme="http").geturl()
                verify = False

            response = sess.get(modified_url, timeout=timeout, verify=verify)
            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as exc:
            last_exc = exc  # запоминаем последнюю ошибку
            # Если не последняя попытка — пробуем ещё раз
            if attempt < max_attempts:
                continue
            # Если все попытки исчерпаны — пробрасываем исключение
            raise last_exc

# Сохраняет полученные данные в локальный файл
def save_to_local_file(path, content):
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    log(f"📁 Данные сохранены локально в {path}")

# Загружает файл в репозиторий GitHub (обновляет или создаёт новый)
def upload_to_github(local_path, remote_path):
    if not os.path.exists(local_path):
        log(f"❌ Файл {local_path} не найден.")
        return None

    repo = REPO
    with open(local_path, "r", encoding="utf-8") as file:
        content = file.read()

    max_retries = 3
    for attempt in range(max_retries):
        try:
            file_in_repo = repo.get_contents(remote_path)
            remote_content = None
            if getattr(file_in_repo, "encoding", None) == "base64":
                try:
                    remote_content = file_in_repo.decoded_content.decode("utf-8")
                except Exception:
                    remote_content = None

            if remote_content is None or remote_content != content:
                # Файл изменился - возвращаем данные для коммита
                log(f"✅ Файл {remote_path} изменился")
                # Добавляем номер файла в массив измененных
                basename = os.path.basename(remote_path)
                if basename.startswith("mariya-") and basename.endswith(".txt"):
                    try:
                        num = int(basename[7:-4])  # убираем "mariya-" и ".txt"
                        changed_file_numbers.append(num)
                        print(f"🔍 DEBUG: added file number {num} to changed_file_numbers")
                    except ValueError:
                        pass
                return (local_path, remote_path, content)
            else:
                log(f"🔄 Изменений для {remote_path} нет.")
                return None
        except GithubException as e:
            if e.status == 404:
                # Файл не существует - это новый файл
                log(f"🆕 Файл {remote_path} не найден в репозитории, будет создан.")
                # Добавляем номер файла в массив измененных
                basename = os.path.basename(remote_path)
                if basename.startswith("mariya-") and basename.endswith(".txt"):
                    try:
                        num = int(basename[7:-4])  # убираем "mariya-" и ".txt"
                        changed_file_numbers.append(num)
                        print(f"🔍 DEBUG: added file number {num} to changed_file_numbers (404)")
                    except ValueError:
                        pass
                return (local_path, remote_path, content)
            elif e.status == 409 and attempt < max_retries - 1:
                # SHA conflict — повторяем попытку
                log(f"⚠️ Конфликт SHA при обновлении {remote_path}, повторяю (попытка {attempt+1})")
                continue
            else:
                log(f"⚠️ Ошибка при загрузке {remote_path}: {e.data.get('message', e)}")
                return

# Функция для параллельного скачивания и сохранения файла
def download_and_save(idx):
    url = URLS[idx]
    local_path = LOCAL_PATHS[idx]
    try:
        data = fetch_data(url)

        # Если локальный файл уже существует и содержимое не изменилось — пропускаем запись и загрузку
        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f_old:
                    old_data = f_old.read()
                if old_data == data:
                    log(f"🔄 Изменений для {local_path} нет (локально). Пропуск загрузки в GitHub.")
                    return None
            except Exception:
                # Если не удалось прочитать старый файл — просто перезапишем
                pass

        save_to_local_file(local_path, data)
        return local_path, REMOTE_PATHS[idx]
    except Exception as e:
        short_msg = str(e)
        if len(short_msg) > 200:
            short_msg = short_msg[:200] + "…"
        log(f"⚠️ Ошибка при скачивании {url}: {short_msg}")
        return None

# Основная функция: скачивает, сохраняет и загружает все конфиги
# Создает один коммит для всех измененных файлов через Git Data API
def commit_files_batch(repo, changed_files: list[tuple[str, str, str]], message: str):
    """
    changed_files: список кортежей (local_path, remote_path, content) для измененных файлов.
    """
    if not changed_files:
        return

    # 1) читаем ветку
    ref = repo.get_git_ref("heads/main")
    base_commit = repo.get_git_commit(ref.object.sha)

    # 2) формируем элементы дерева
    tree_elements: list[InputGitTreeElement] = []
    print(f"🔍 DEBUG commit_files_batch: processing {len(changed_files)} files")
    for i, (local_path, remote_path, content) in enumerate(changed_files):
        print(f"🔍 DEBUG: processing file {i}: {remote_path}")
        blob = repo.create_git_blob(content, "utf-8")
        elem = InputGitTreeElement(
            path=remote_path,
            mode="100644",
            type="blob",
            sha=blob.sha,
        )
        tree_elements.append(elem)
        print(f"🔍 DEBUG: created blob for {remote_path}, sha={blob.sha}")

    # 3) создаём дерево и коммит
    new_tree = repo.create_git_tree(tree_elements, base_commit.tree)
    commit = repo.create_git_commit(message, new_tree, [base_commit])
    ref.edit(commit.sha)

def main():
    global changed_file_numbers
    changed_file_numbers = []  # Очищаем массив измененных файлов
    
    # Параллельно скачиваем файлы и сохраняем их локально
    max_workers_download = min(DEFAULT_MAX_WORKERS, max(1, len(URLS)))

    changed_files: list[tuple[str, str, str]] = []  # <--- собираем изменённые файлы

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers_download) as download_pool:
        download_futures = [download_pool.submit(download_and_save, i) for i in range(len(URLS))]

        for future in concurrent.futures.as_completed(download_futures):
            result = future.result()
            if result:
                local_path, remote_path = result
                # Проверяем изменения и собираем измененные файлы
                changed_data = upload_to_github(local_path, remote_path)
                if changed_data:
                    changed_files.append(changed_data)

    # ЕДИНЫЙ КОММИТ ДЛЯ ВСЕХ ИЗМЕНЕНИЙ
    if changed_files:
        # ОТЛАДКА: печатаем содержимое массивов
        print(f"🔍 DEBUG: changed_file_numbers = {changed_file_numbers}")
        print(f"🔍 DEBUG: changed_files count = {len(changed_files)}")
        for i, (local_path, remote_path, content) in enumerate(changed_files):
            print(f"🔍 DEBUG: changed_files[{i}] = local='{local_path}', remote='{remote_path}', content_len={len(content)}")
        
        # Используем номера реально измененных файлов
        file_numbers = sorted(changed_file_numbers)
        numbers_str = ", ".join(map(str, file_numbers))
        message = f"Update [{numbers_str}] - Data : {offset}"
        print(f"🔍 DEBUG: commit message = '{message}'")
        try:
            commit_files_batch(REPO, changed_files, message)
            log(f"✅ Создан коммит с {len(changed_files)} измененными файлами")
        except GithubException as e:
            log(f"⚠️ Ошибка батч-коммита: {getattr(e, 'data', {}) or str(e)}")
    else:
        log("🔄 Изменений нет — коммит не требуется.")

    # -------------------- ПЕЧАТЬ СОБРАННЫХ ЛОГОВ --------------------
    ordered_keys = sorted(k for k in LOGS_BY_FILE.keys() if k != 0)

    output_lines: list[str] = []

    # Сначала выводим логи по конкретным файлам в порядке номера
    for k in ordered_keys:
        output_lines.append(f"----- {k}.txt -----")
        output_lines.extend(LOGS_BY_FILE[k])

    # Далее выводим общие/непривязанные сообщения (ключ 0)
    if LOGS_BY_FILE.get(0):
        output_lines.append("----- Общие сообщения -----")
        output_lines.extend(LOGS_BY_FILE[0])

    print("\n".join(output_lines))

# Точка входа в программу
if __name__ == "__main__":
    main()
