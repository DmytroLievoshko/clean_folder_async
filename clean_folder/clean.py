import asyncio
import aiopath
import sys
import re
import aioshutil


async def make_new_path(path: aiopath.AsyncPath, position_of_processed_files: int, folder_name: str, unknown=False, archive=False):

    folder = path.parents[position_of_processed_files].joinpath(
        folder_name)
    if not await folder.exists():
        await folder.mkdir()

    parents_folder = path.parents[:position_of_processed_files]

    new_path = folder
    for paren in parents_folder[::-1]:
        if paren == folder:
            continue
        new_path = new_path.joinpath(await normalize(paren.stem))
        if not await new_path.exists():
            await new_path.mkdir()

    if not unknown:
        if archive:
            new_path = new_path.joinpath(await normalize(path.stem))
        else:
            new_path = new_path.joinpath(
                await normalize(path.stem) + path.suffix)
    else:
        new_path = new_path.joinpath(path.name)

    return new_path


async def mova_file(path: aiopath.AsyncPath, new_path: aiopath.Path, folder_name: str, unknown=False, archive=False):

    if archive:
        try:
            await aioshutil.unpack_archive(path, new_path)
        except FileExistsError:
            print(f'failed to extract archive {path.name}')
        else:
            await add_to_log(path.suffix, path.name, folder_name)
            try:
                await path.unlink()
            except FileExistsError:
                print(f'failed to delete file {path.name}')
    else:
        try:
            new_path = await aioshutil.move(path, new_path)
        except FileExistsError:
            print(f'failed to write file {path.name}')
        else:
            await add_to_log(path.suffix, path.name, folder_name, unknown)


async def images_processing(path: aiopath.AsyncPath, position_of_processed_files: int, folder_name: str):

    new_path = await make_new_path(
        path, position_of_processed_files, folder_name)
    await mova_file(path, new_path, folder_name)


async def video_processing(path: aiopath.AsyncPath, position_of_processed_files: int, folder_name: str):

    new_path = await make_new_path(
        path, position_of_processed_files, folder_name)
    await mova_file(path, new_path, folder_name)


async def documents_processing(path: aiopath.AsyncPath, position_of_processed_files: int, folder_name: str):

    new_path = await make_new_path(
        path, position_of_processed_files, folder_name)
    await mova_file(path, new_path, folder_name)


async def audio_processing(path: aiopath.AsyncPath, position_of_processed_files: int, folder_name: str):

    new_path = await make_new_path(
        path, position_of_processed_files, folder_name)
    await mova_file(path, new_path, folder_name)


async def archives_processing(path: aiopath.AsyncPath, position_of_processed_files: int, folder_name: str):

    new_path = await make_new_path(path, position_of_processed_files, folder_name,
                                   archive=True)
    await mova_file(path, new_path, folder_name,
                    archive=True)


async def unknown_processing(path: aiopath.AsyncPath, position_of_processed_files: int, folder_name: str):

    new_path = await make_new_path(path, position_of_processed_files, folder_name,
                                   unknown=True)
    await mova_file(path, new_path, folder_name,
                    unknown=True)


async def normalize(path_name: str) -> str:

    path_name = path_name.translate(TRANS)
    path_name = re.sub(r'\W', r'_', path_name)
    return path_name


async def add_to_log(extension: str, file_name: str, categorie: str, unknown: bool = False):

    global DICT_FILES_BY_CATEGORIES, SET_KNOWN_FILE_EXTENSIONS

    if unknown:
        SET_UNKNOWN_FILE_EXTENSIONS.add(extension.lstrip('.').upper())
    else:
        SET_KNOWN_FILE_EXTENSIONS.add(extension.lstrip('.').upper())

    DICT_FILES_BY_CATEGORIES.setdefault(categorie, []).append(file_name)


def log_print():

    str_known = f"Known file extension: {', '.join(SET_KNOWN_FILE_EXTENSIONS)}"
    str_unknown = f"Unknown file extension: {', '.join(SET_UNKNOWN_FILE_EXTENSIONS)}"
    separator_length = min(80, max(len(str_known), len(str_unknown)))
    print("="*separator_length)
    print(str_known)
    print("="*separator_length)
    print(str_unknown)
    print("="*separator_length)

    print("-"*80)
    for key, value in DICT_FILES_BY_CATEGORIES.items():

        print_str = "{:<15}| ".format(key)
        print_str += f"\n{' '*15}| ".join(value)
        print(print_str)
        print("-"*80)


async def sort_dir(path: aiopath.AsyncPath, position_of_processed_files: int = 0):

    async for sub_path in path.iterdir():

        if sub_path.name in IGNORED_FOLDERS:
            continue

        if await sub_path.is_dir():
            await sort_dir(sub_path, position_of_processed_files + 1)

        else:

            extension = sub_path.suffix.lstrip('.').upper()

            tuple_setting = SETTINGS.get(
                extension, (unknown_processing, 'unknowns'))

            await tuple_setting[0](
                sub_path, position_of_processed_files, tuple_setting[1])


async def rmdir(path: aiopath.AsyncPath):
    is_empty = True

    async for sub_path in path.iterdir():

        if sub_path.name in IGNORED_FOLDERS:
            is_empty = False
            continue

        if await sub_path.is_dir():
            await rmdir(sub_path)
        else:
            is_empty = False

    if is_empty:
        await path.rmdir()

SETTINGS = {'BMP': (images_processing, 'images'), 'JPEG': (images_processing, 'images'), 'PNG': (images_processing, 'images'), 'JPG': (images_processing, 'images'), 'SVG': (images_processing, 'images'),
            'AVI': (video_processing, 'video'), 'MP4': (video_processing, 'video'), 'MOV': (video_processing, 'video'), 'MKV': (video_processing, 'video'),
            'DOC': (documents_processing, 'documents'), 'DOCX': (documents_processing, 'documents'), 'TXT': (documents_processing, 'documents'), 'PDF': (documents_processing, 'documents'), 'XLSX': (documents_processing, 'documents'), 'PPTX': (documents_processing, 'documents'),
            'MP3': (audio_processing, 'audio'), 'OGG': (audio_processing, 'audio'), 'WAV': (audio_processing, 'audio'), 'AMR': (audio_processing, 'audio'),
            'ZIP': (archives_processing, 'archives'), 'GZ': (archives_processing, 'archives'), 'TAR': (archives_processing, 'archives')}

IGNORED_FOLDERS = [tuple_setting[1] for tuple_setting in SETTINGS.values()]
IGNORED_FOLDERS.append("unknowns")

CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", "ji", "g")

TRANS = {}
for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    TRANS[ord(c)] = l
    TRANS[ord(c.upper())] = l.title()

DICT_FILES_BY_CATEGORIES = dict()
SET_UNKNOWN_FILE_EXTENSIONS = set()
SET_KNOWN_FILE_EXTENSIONS = set()


def main():

    if len(sys.argv)-1 < 1:
        print(f'The script must take 1 argumet!')
        return

    user_path = aiopath.AsyncPath(" ".join(sys.argv[1:]))

    if user_path.exists():

        if user_path.is_dir():

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(sort_dir(user_path))
            finally:
                try:
                    loop.run_until_complete(rmdir(user_path))
                except Exception as e:
                    print(e)
                loop.close()

            log_print()
        else:
            print(f'{str(user_path.absolute())} is no directory')

    else:
        print(f'{str(user_path.absolute())} does not exist')


if __name__ == '__main__':
    main()
