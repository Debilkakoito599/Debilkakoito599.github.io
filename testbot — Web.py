import sqlite3,aiogram,os,shutil,aiofiles,json,logging
from aiogram.types.web_app_info import WebAppInfo
from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton,CallbackQuery
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
bot = Bot(BOT_TOKEN)
dp = Dispatcher()
operation = ''
EditingPlaylistName = ''
##############################################################################
MEDIA_FOLDER = EditingPlaylistName + "/media"  # Папка для файлов
HTML_PATH = EditingPlaylistName + "/index.html"  # Путь к HTML-файлу
PLAYLIST_FILE = "playlist.json"  # Файл для хранения списка песен

# Создаем папки
# Функции для работы с плейлистом
def load_playlist():
    """Загружает список файлов из JSON"""
    if os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_playlist(files):
    """Сохраняет список файлов в JSON"""
    with open(PLAYLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(files, f, indent=2, ensure_ascii=False)
############################################################################
@dp.message(Command('start'))
async def start(message: types.Message):
    conn = sqlite3.connect('MusicData.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS playlists (id int auto__increment primary key, playlist_name varchar(50))')
    conn.commit()
    cur.close()
    conn.close()
    markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Open WebApp',web_app=WebAppInfo(url='https://debilkakoito599.github.io/'))],
        [InlineKeyboardButton(text='Playlists Operations', callback_data='playop')],
    ]
)
    await message.answer("Welcome to Spotigramm",reply_markup=markup)
##########################################################################
@dp.message(Command("clear"))
async def clear_playlist(message: types.Message):
    # Удаляем все файлы из папки
    for file in os.listdir(MEDIA_FOLDER):
        file_path = os.path.join(MEDIA_FOLDER, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    # Очищаем плейлист
    save_playlist([])
    
    # Генерируем пустой HTML
    await generate_playlist_html()
    
    await message.answer("🗑️ Плейлист очищен!")
###########################################################################
@dp.callback_query()
async def prosess_call(callback_query: CallbackQuery):
    global operation
    if callback_query.data == 'playop':
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
            [InlineKeyboardButton(text='Delete Playlist',callback_data='deleteplaylist')],
            [InlineKeyboardButton(text='Set Playlist', callback_data='setplaylist')],
            [InlineKeyboardButton(text='Create Playlist', callback_data='newplaylist')],
            [InlineKeyboardButton(text='Edit Playlist', callback_data='editplaylist')]
    ]
)

        await callback_query.message.answer("Playlists Operations List",reply_markup=markup)

    match callback_query.data:
        case 'newplaylist':
            await callback_query.message.answer("Send new playlists name")
            operation='newplaylist'
        case 'deleteplaylist':
            await callback_query.message.answer("Send deleting playlists name")
            operation='deleteplaylist'
        case 'editplaylist':
            operation='editplaylist'
            await callback_query.message.answer("Send Editing Playlist Name")
        case 'addsong':
            operation='addsong'
            await callback_query.message.answer("Send Adding Audio")

    

@dp.message()
async def playlists_ops(message:types.Message):
    #conn = sqlite3.connect('MusicData.sql')
    #cur = conn.cursor()
    global operation
    global EditingPlaylistName
    global MEDIA_FOLDER
    global HTML_PATH
    match operation:
        case 'newplaylist':
            if message.content_type == 'text':
                NewPlaylistName = message.text.strip()
                os.makedirs(MEDIA_FOLDER, exist_ok=True)
                os.makedirs(NewPlaylistName, exist_ok=True)
                #cur.execute("INSERT INTO playlists (playlist_name) VALUES (?)",(NewPlaylistName,))
                #conn.commit()
                await message.answer(f"Playlist '{NewPlaylistName}' created successfully!")
        case 'deleteplaylist':
            if message.content_type == 'text':
                DeletePlaylistName = message.text.strip() 
                if os.path.exists(DeletePlaylistName):
                    shutil.rmtree(DeletePlaylistName)
                    await message.answer(f"Playlist '{DeletePlaylistName}' deleted successfully!")
        case 'editplaylist':
            if message.content_type == 'text':
                EditingPlaylistName = message.text.strip()
                MEDIA_FOLDER = EditingPlaylistName + "/media"
                HTML_PATH = EditingPlaylistName + "/index.html"
                markup = InlineKeyboardMarkup(
            inline_keyboard=[
            [InlineKeyboardButton(text='Add Song To Playlist',callback_data='addsong')],
            [InlineKeyboardButton(text='Delete Song From Playlist', callback_data='deletesong')],
            [InlineKeyboardButton(text='Change Playlists Name', callback_data='changenameplaylist')]
    ]
)
                await message.answer(f"Editing {EditingPlaylistName}",reply_markup=markup)
        case 'addsong':
                if message.audio:
                    file_id = message.audio.file_id
                    file = await bot.get_file(file_id)
                    downloaded = await bot.download_file(file.file_path)
                    os.makedirs(MEDIA_FOLDER, exist_ok=True)
                    os.makedirs(EditingPlaylistName, exist_ok=True)
                    if message.audio.file_name:
                        file_name = message.audio.file_name
                    else:
                        file_name = 'song_' + str(message.message_id) + '.mp3'
                    save_path = os.path.join(EditingPlaylistName + "/media", file_name)
                    f = open(save_path, 'wb')
                    f.write(downloaded.getvalue())
                    f.close()
                    #########################################
                    playlist = load_playlist()
                    playlist.append({"name": file_name, "type": "audio"})
                    save_playlist(playlist)
                    await generate_playlist_html()
                    ###############################################
                    await message.answer('Сохранено в моя_папка/' + file_name)
                
    #cur.close()
    #conn.close()
async def generate_playlist_html():
    """Генерирует HTML-страницу с плейлистом"""
    playlist = load_playlist()
    
    # Создаем элементы плейлиста для HTML
    playlist_items = ""
    if playlist:
        for idx, item in enumerate(playlist):
            file_name = item['name']
            file_type = item['type']
            icon = "🎬" if file_type == "video" else "🎵"
            playlist_items += f'''
                <div class="playlist-item" onclick="playFile('{file_name}', {idx})" data-index="{idx}">
                    <span class="icon">{icon}</span>
                    <span class="name">{file_name}</span>
                    <span class="badge">{file_type}</span>
                </div>
            '''
    else:
        playlist_items = '''
            <div class="empty-playlist">
                <p>📭 Плейлист пуст</p>
                <p style="font-size: 14px; color: #666;">Загрузите файлы через Telegram-бота</p>
            </div>
        '''
    
    html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Медиа-плейлист</title>
    <link rel= "stylesheet" href="playerstyle.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Медиа-плейлист</h1>
            <p>Управляйте своим плейлистом через Telegram-бота</p>
        </div>
        
        <div class="player-wrapper">
            <video id="videoPlayer" controls></video>
            <audio id="audioPlayer" controls></audio>
            <div id="nowPlaying" class="now-playing">Выберите файл из плейлиста</div>
            <div class="controls">
                <button onclick="prevTrack()">⏮</button>
                <button onclick="nextTrack()">⏭</button>
            </div>
        </div>
        
        <div class="playlist-container">
            <div class="playlist-header">
                <h2>📋 Плейлист</h2>
                <span class="count">{len(playlist)} файлов</span>
            </div>
            <div id="playlist">
                {playlist_items}
            </div>
        </div>
    </div>

    <script>
        const videoPlayer = document.getElementById('videoPlayer');
        const audioPlayer = document.getElementById('audioPlayer');
        const nowPlaying = document.getElementById('nowPlaying');
        let currentIndex = -1;
        let playlistItems = [];
        
        // Загружаем список файлов из HTML (генерируется сервером)
        const files = {json.dumps([item['name'] for item in playlist], ensure_ascii=False)};
        const fileTypes = {json.dumps([item['type'] for item in playlist], ensure_ascii=False)};
        
        function playFile(fileName, index) {{
            if (index < 0 || index >= files.length) return;
            
            const isVideo = fileTypes[index] === 'video';
            currentIndex = index;
            
            // Показываем нужный плеер
            if (isVideo) {{
                videoPlayer.style.display = 'block';
                audioPlayer.style.display = 'none';
                videoPlayer.src = 'media/' + encodeURIComponent(fileName);
                videoPlayer.load();
                videoPlayer.play();
            }} else {{
                audioPlayer.style.display = 'block';
                videoPlayer.style.display = 'none';
                audioPlayer.src = 'media/' + encodeURIComponent(fileName);
                audioPlayer.load();
                audioPlayer.play();
            }}
            
            // Обновляем информацию
            nowPlaying.textContent = '▶ Сейчас играет: ' + fileName;
            nowPlaying.className = 'now-playing active';
            
            // Подсветка активного элемента
            document.querySelectorAll('.playlist-item').forEach((el, i) => {{
                el.classList.toggle('active', i === index);
            }});
            
            // Обновляем URL без перезагрузки
            if (history.pushState) {{
                history.pushState(null, '', '?track=' + index);
            }}
        }}
        
        function nextTrack() {{
            if (currentIndex < files.length - 1) {{
                playFile(files[currentIndex + 1], currentIndex + 1);
            }} else if (files.length > 0) {{
                playFile(files[0], 0); // Зацикливание
            }}
        }}
        
        function prevTrack() {{
            if (currentIndex > 0) {{
                playFile(files[currentIndex - 1], currentIndex - 1);
            }} else if (files.length > 0) {{
                playFile(files[files.length - 1], files.length - 1); // Зацикливание
            }}
        }}
        
        // Автоматическое переключение на следующий трек
        videoPlayer.addEventListener('ended', nextTrack);
        audioPlayer.addEventListener('ended', nextTrack);
        
        // Горячие клавиши
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowRight' || e.key === ' ') {{
                e.preventDefault();
                nextTrack();
            }} else if (e.key === 'ArrowLeft') {{
                e.preventDefault();
                prevTrack();
            }}
        }});
        
        // Проверяем URL при загрузке
        window.addEventListener('load', function() {{
            const params = new URLSearchParams(window.location.search);
            const trackIndex = parseInt(params.get('track'));
            if (!isNaN(trackIndex) && trackIndex >= 0 && trackIndex < files.length) {{
                playFile(files[trackIndex], trackIndex);
            }} else if (files.length > 0) {{
                // Автозапуск первого трека
                playFile(files[0], 0);
            }}
        }});
        
        // Обработка навигации назад/вперед
        window.addEventListener('popstate', function() {{
            const params = new URLSearchParams(window.location.search);
            const trackIndex = parseInt(params.get('track'));
            if (!isNaN(trackIndex) && trackIndex >= 0 && trackIndex < files.length) {{
                playFile(files[trackIndex], trackIndex);
            }}
        }});
    </script>
</body>
</html>'''
    
    # Сохраняем HTML
    async with aiofiles.open(HTML_PATH, 'w', encoding='utf-8') as f:
        await f.write(html_content)
"""
markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(
                text='Open Web App', 
                web_app=WebAppInfo(url='https://debilkakoito599.github.io/')
            )]
        ],resize_keyboard=True
    )
    await message.answer("", reply_markup=markup)

"""
dp.run_polling(bot)