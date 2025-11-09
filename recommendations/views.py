from difflib import SequenceMatcher

from langchain_classic.agents import AgentType

from users.models import CustomUser
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os, json, re, logging


from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent

from sqlalchemy import create_engine
from .models import Category, GenreTag, Game


logger = logging.getLogger(__name__)

TABLES_TO_INCLUDE = [
    "recommendations_game",
    "recommendations_category",
    "recommendations_genretag",
    "recommendations_game_tags"
]

engine = create_engine("sqlite:///db.sqlite3", pool_pre_ping=True)

db = SQLDatabase.from_uri(
    "sqlite:///db.sqlite3",
    include_tables=TABLES_TO_INCLUDE
)

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

SYSTEM_PROMPT = """
Ты — игровой ассистент. Ты отвечаешь ТОЛЬКО чистым HTML-кодом, без текста вокруг.

Задача: подобрать подходящие игры по запросу пользователя через SQL.

Формат КАЖДОЙ игры (обязательно):

<div class="rec-card">
 <h4>{title}</h4>
 <p class="subtitle">{tags}</p>
 <p>{short_description}</p>
 <a href="{store_url}" target="_blank" class="btn-steam">Открыть в магазине ↗️</a>
</div>

Требования:
- никакого текста, markdown, комментариев — только HTML
- всё в одном куске HTML
- если игр нет — верни пустую строку
- {tags} — перечисление через запятую (например: хоррор, кооп, атмосферная)
- ссылки только на магазин игры

Помни:
ТЫ НЕ РАЗМЫШЛЯЕШЬ. ТЫ ТОЛЬКО ФОРМИРУЕШЬ HTML-PРЕЗЕНТАЦИЮ РЕЗУЛЬТАТА SQL.
"""


toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.OPENAI_FUNCTIONS,
    system_message=SYSTEM_PROMPT,
    agent_executor_kwargs={
        "handle_parsing_errors": True,
        "return_intermediate_steps": False,
    },
)


# === Синонимы жанров ===
def similarity(a,b):
    return SequenceMatcher(None, a, b).ratio()


def find_tags_by_synonyms(user_text: str):
    parts = [p.strip().lower() for p in re.split(r'[ ,;/.]+', user_text) if p.strip()]
    found_tags = {}

    for p in parts:
        for tag in GenreTag.objects.all():

            # прямое вхождение
            if similarity(p, tag.name.lower()) > 0.6:
                found_tags[tag.id] = tag
                continue

            # синонимы
            if tag.synonyms:
                for syn in re.split(r'[;,/]', tag.synonyms):
                    syn = syn.strip().lower()
                    if similarity(p, syn) > 0.6:
                        found_tags[tag.id] = tag
                        break

    return list(found_tags.values())


@csrf_exempt
def ask_game(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    query = data.get("query", "").strip()

    # приветствие
    if not query:
        if request.user.is_authenticated:
            name = request.user.first_name or request.user.email
            return JsonResponse({
                "answer": f"Привіт, {name}! 👋 Напиши жанр или тег – например: хоррор, кооп, выживание."
            })
        return JsonResponse({
            "answer": "Привет! Напиши любой жанр или тег – и я подскажу игру."
        })

    # парсим теги
    tags = find_tags_by_synonyms(query)
    if not tags:
        return JsonResponse({"answer": "Не нашла жанров по этому описанию 🤔"})

    try:
        result = agent_executor.invoke({
            "input": f"Поиск игр с тегами: {', '.join([t.name for t in tags])}. Запрос пользователя: {query}"
        })

        output_html = result.get("output", "").strip()
        output_html = re.sub(
            r'\[([^\]]+)\]\((https?://[^\)]+)\)',
            r'<a href="\2" target="_blank" style="color:#0d6efd;text-decoration:none;border-bottom:1px dashed #0d6efd;">\1 ↗</a>',
            output_html
        )
        if not output_html:
            return JsonResponse({"answer": "Пока ничего не нашла по этому жанру 😕"})

        # summary
        summary = llm.invoke(
            f"Сформуй 1-2 дружеских предложения-совета (рус), без повторения названий игр. Закончи 'Приятной игры! 🎮'"
        ).content.strip()

        return JsonResponse({
            "answer": output_html + f'<div class="ai-summary">{summary}</div>'
        })

    except Exception as e:
        return JsonResponse({"answer": f"⚠️ Ошибка: {str(e)}"})
