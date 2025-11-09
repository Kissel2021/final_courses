from django.db import models


class Category(models.Model):
    """Широкие жанры (Action, RPG)."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Категория игры")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class GenreTag(models.Model):
    """Детальные метки (Horror, Co-op). Используются для синонимов и детального поиска."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название метки")
    synonyms = models.TextField(blank=True, null=True, verbose_name="Синонимы для поиска")

    class Meta:
        verbose_name = "Метка"
        verbose_name_plural = "Метки"

    def __str__(self):
        return self.name


class Game(models.Model):
    """Основная информация об игре."""
    title = models.CharField(max_length=255, unique=True, verbose_name="Название игры")
    steam_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Ссылка на Steam")
    description = models.TextField(blank=True, null=True, verbose_name="Краткое описание игры")

    # СВЯЗЬ 1: Foreign Key к Category (Игра принадлежит ТОЛЬКО ОДНОЙ основной категории)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="games",
        verbose_name="Основная категория"
    )

    # СВЯЗЬ 2: Many-to-Many к GenreTag (Игра может иметь МНОГО детальных меток)
    tags = models.ManyToManyField(
        GenreTag,
        related_name="games",
        verbose_name="Детальные метки"
    )

    class Meta:
        verbose_name = "Игра"
        verbose_name_plural = "Игры"

    def __str__(self):
        return self.title
