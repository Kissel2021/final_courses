from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import textwrap
from difflib import SequenceMatcher
import os
from django.db.models import Q
from langchain.agents import AgentType
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
import logging
from sqlalchemy import text


import json
import re
from symspellpy import SymSpell, Verbosity
from transformers import pipeline
from .models import Tool, Material, Recommendation
from products.models import ProductSubCategory, Product
from .models import Recommendation