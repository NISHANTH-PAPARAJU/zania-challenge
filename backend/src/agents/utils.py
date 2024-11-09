import os
from llama_index.core import VectorStoreIndex, load_index_from_storage, StorageContext

def create_index_cache(index: VectorStoreIndex, file):
    file_name = os.path.splitext(os.path.basename(file))[0]
    cache_path = f"./tmp/cache/{file_name}"
    print(cache_path)
    index.storage_context.persist(cache_path)

def clear_all_index_cache(folder_path):
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)  
                print(f"Deleted: {file_path}")
    else:
        print(f"The path {folder_path} is not a valid directory.")

def load_cached_index(file):
    file_name = os.path.splitext(os.path.basename(file))[0]
    cache_path = f"./tmp/cache/{file_name}"
    if os.path.exists(cache_path):
        index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir=cache_path)
        )
        return index
    return None

def is_index_cached(file):
    file_name = os.path.splitext(os.path.basename(file))[0]
    cache_path = f"./tmp/cache/{file_name}"
    if os.path.exists(cache_path):
        print("Existing Cache found")
        return True
    return False