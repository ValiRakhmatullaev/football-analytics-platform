"""
Digital Talent Pool — Models.
Реестр специалистов, навыки, проекты, назначения, заявки.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class Organization(models.Model):
    """Организация (ведомство)."""
    name = models.CharField("Название", max_length=255)
    code = models.SlugField("Код", max_length=64, unique=True, blank=True)
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Специалист / админ организации / центральный админ."""
    class Role(models.TextChoices):
        SPECIALIST = "specialist", "Специалист"
        ORG_ADMIN = "org_admin", "Администратор организации"
        CENTRAL_ADMIN = "central_admin", "Центральный GovTech админ"

    class Level(models.TextChoices):
        JUNIOR = "junior", "Junior"
        MIDDLE = "middle", "Middle"
        SENIOR = "senior", "Senior"
        LEAD = "lead", "Lead"

    role = models.CharField(
        "Роль",
        max_length=20,
        choices=Role.choices,
        default=Role.SPECIALIST,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Организация",
    )
    position = models.CharField("Должность", max_length=255, blank=True)
    level = models.CharField(
        "Уровень",
        max_length=20,
        choices=Level.choices,
        blank=True,
    )
    years_experience = models.PositiveIntegerField("Стаж (лет)", default=0)
    specialization = models.CharField("Специализация", max_length=255, blank=True)
    allocation_percent = models.PositiveSmallIntegerField(
        "Текущая занятость (%)",
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    available_for_projects = models.BooleanField("Доступен для проектов", default=True)
    talent_score = models.DecimalField(
        "Talent Score",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.get_full_name() or self.username


class SkillCategory(models.Model):
    """Категория навыков (Frontend, Backend, DevOps, Data Science, ...)."""
    name = models.CharField("Название", max_length=100)
    code = models.SlugField("Код", max_length=64, unique=True)

    class Meta:
        verbose_name = "Категория навыков"
        verbose_name_plural = "Категории навыков"

    def __str__(self):
        return self.name


class Skill(models.Model):
    """Навык (Python, React, Kubernetes, ...)."""
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        EXPERT = "expert", "Expert"

    name = models.CharField("Название", max_length=100)
    code = models.SlugField("Код", max_length=64, unique=True)
    category = models.ForeignKey(
        SkillCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="skills",
        verbose_name="Категория",
    )

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """Навык специалиста с уровнем (Skill Matrix)."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_skills",
        verbose_name="Специалист",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="user_skills",
        verbose_name="Навык",
    )
    level = models.CharField(
        "Уровень",
        max_length=20,
        choices=Skill.Level.choices,
    )

    class Meta:
        verbose_name = "Навык специалиста"
        verbose_name_plural = "Навыки специалистов"
        unique_together = [["user", "skill"]]

    def __str__(self):
        return f"{self.user} — {self.skill} ({self.get_level_display()})"


class Project(models.Model):
    """Государственный IT-проект (биржа проектов)."""
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="projects",
        verbose_name="Ведомство",
    )
    deadline = models.DateField("Срок", null=True, blank=True)
    priority = models.CharField(
        "Приоритет",
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    required_specialists_count = models.PositiveIntegerField(
        "Требуемое количество специалистов",
        default=1,
    )
    is_active = models.BooleanField("Активен", default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects",
        verbose_name="Создал",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    def __str__(self):
        return self.name


class ProjectRequirement(models.Model):
    """Требование проекта: навык + уровень + (опционально) роль."""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="requirements",
        verbose_name="Проект",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="project_requirements",
        verbose_name="Навык",
    )
    level = models.CharField(
        "Минимальный уровень",
        max_length=20,
        choices=Skill.Level.choices,
    )
    role_description = models.CharField("Роль", max_length=255, blank=True)

    class Meta:
        verbose_name = "Требование проекта"
        verbose_name_plural = "Требования проекта"
        unique_together = [["project", "skill"]]

    def __str__(self):
        return f"{self.project.name} — {self.skill.name} ({self.get_level_display()})"


class ProjectApplication(models.Model):
    """Заявка специалиста на участие в проекте."""
    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Одобрена"
        REJECTED = "rejected", "Отклонена"
        WITHDRAWN = "withdrawn", "Отозвана"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="project_applications",
        verbose_name="Специалист",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name="Проект",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    message = models.TextField("Сообщение", blank=True)
    matching_score = models.DecimalField(
        "Matching score (%)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заявка на проект"
        verbose_name_plural = "Заявки на проекты"
        unique_together = [["user", "project"]]

    def __str__(self):
        return f"{self.user} → {self.project} ({self.get_status_display()})"


class ProjectAssignment(models.Model):
    """Назначение специалиста на проект (allocation)."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="project_assignments",
        verbose_name="Специалист",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Проект",
    )
    allocation_percent = models.PositiveSmallIntegerField(
        "Занятость (%)",
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    role = models.CharField("Роль в проекте", max_length=255, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_others",
        verbose_name="Назначил",
    )

    class Meta:
        verbose_name = "Назначение на проект"
        verbose_name_plural = "Назначения на проекты"
        unique_together = [["user", "project"]]

    def __str__(self):
        return f"{self.user} — {self.project} ({self.allocation_percent}%)"
