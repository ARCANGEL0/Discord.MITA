import json
import os
from threading import Lock

DB_FILE = "database.json"
db_lock = Lock()

class Database:
    def __init__(self, filename=DB_FILE):
        self.filename = filename
        self.data = {}
        self.load()

    def load(self):
        """Carrega o banco de dados ou cria vazio se não existir"""
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {"chats": {}}
            self.save()

    def save(self):
        """Salva o banco de dados no arquivo JSON"""
        with db_lock:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

    # -------------------
    # Chat / Server
    # -------------------
    def ensure_chat(self, chat_id):
        """Garante que o chat (servidor) exista"""
        if chat_id not in self.data["chats"]:
            self.data["chats"][chat_id] = {"users": {}}
            self.save()

    def get_chat(self, chat_id):
        self.ensure_chat(chat_id)
        return self.data["chats"][chat_id]

    # Server values
    def set_server_value(self, chat_id, key, value):
        """Define um valor no nível do servidor/chat"""
        self.ensure_chat(chat_id)
        self.data["chats"][chat_id][key] = value
        self.save()

    def get_server_value(self, chat_id, key, default=None):
        """Pega um valor do servidor/chat"""
        self.ensure_chat(chat_id)
        return self.data["chats"][chat_id].get(key, default)

    # -------------------
    # Users
    # -------------------
    def ensure_user(self, chat_id, user_id):
        """Garante que o usuário exista dentro do chat"""
        self.ensure_chat(chat_id)
        if user_id not in self.data["chats"][chat_id]["users"]:
            self.data["chats"][chat_id]["users"][user_id] = {}
            self.save()

    def get_user(self, chat_id, user_id):
        self.ensure_user(chat_id, user_id)
        return self.data["chats"][chat_id]["users"][user_id]

    def set_user_value(self, chat_id, user_id, key, value):
        self.ensure_user(chat_id, user_id)
        self.data["chats"][chat_id]["users"][user_id][key] = value
        self.save()

    def get_user_value(self, chat_id, user_id, key, default=None):
        self.ensure_user(chat_id, user_id)
        return self.data["chats"][chat_id]["users"][user_id].get(key, default)


# Inicia banco de dados
db = Database()
