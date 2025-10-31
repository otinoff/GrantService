#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetic User Generator - Generate diverse user profiles for testing

Creates 20+ different profiles for autonomous night testing:
- Sports clubs (archery, football, volleyball, boxing, athletics)
- Educational projects (IT, languages, math, robotics, business)
- Social projects (elderly care, volunteers, families, rehabilitation)
- Cultural projects (theater, museum, library, music, gallery)
- Scientific projects (physics, biology, ecology, chemistry, astronomy)

Created: 2025-10-31
Iteration: 69 - Autonomous Night Testing
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """User profile for synthetic testing"""
    name: str
    type: str  # sports, education, social, cultural, scientific
    goal: str
    budget: int
    region: str
    participants: int
    duration_months: int
    organization: str
    organization_type: str  # АНО, Фонд, Ассоциация, Центр, Клуб
    experience_years: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.type,
            "goal": self.goal,
            "budget": self.budget,
            "region": self.region,
            "participants": self.participants,
            "duration_months": self.duration_months,
            "organization": self.organization,
            "organization_type": self.organization_type,
            "experience_years": self.experience_years
        }


class SyntheticUserGenerator:
    """
    Generate diverse user profiles for night testing

    Creates 20+ profile templates and generates variations
    """

    # Russian regions for diversity
    REGIONS = [
        'Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург',
        'Казань', 'Нижний Новгород', 'Красноярск', 'Челябинск',
        'Самара', 'Уфа', 'Ростов-на-Дону', 'Воронеж', 'Пермь',
        'Волгоград', 'Краснодар', 'Тюмень', 'Омск'
    ]

    # Profile templates
    PROFILES = {
        # Sports projects (5 types)
        "sports": [
            {
                "name": "Стрелковый клуб Лучник",
                "goal": "Развитие юношеской секции стрельбы из лука",
                "budget_range": (300000, 800000),
                "participants_range": (30, 100),
                "organization": "Спортивный клуб Лучник",
                "org_type": "АНО"
            },
            {
                "name": "Футбольная школа Чемпион",
                "goal": "Организация футбольной школы для детей 7-14 лет",
                "budget_range": (500000, 1200000),
                "participants_range": (50, 150),
                "organization": "Футбольная академия Чемпион",
                "org_type": "Центр"
            },
            {
                "name": "Волейбольный клуб Высота",
                "goal": "Развитие массового волейбола среди молодежи",
                "budget_range": (400000, 900000),
                "participants_range": (40, 120),
                "organization": "Волейбольный клуб Высота",
                "org_type": "Клуб"
            },
            {
                "name": "Боксерская секция Победа",
                "goal": "Обучение боксу детей из малообеспеченных семей",
                "budget_range": (350000, 750000),
                "participants_range": (25, 80),
                "organization": "Боксерский центр Победа",
                "org_type": "АНО"
            },
            {
                "name": "Секция легкой атлетики Старт",
                "goal": "Подготовка юных легкоатлетов",
                "budget_range": (300000, 700000),
                "participants_range": (30, 90),
                "organization": "Центр легкой атлетики Старт",
                "org_type": "Центр"
            }
        ],

        # Educational projects (5 types)
        "education": [
            {
                "name": "IT-буткемп Кодер",
                "goal": "Обучение Python и AI для школьников",
                "budget_range": (600000, 1500000),
                "participants_range": (40, 100),
                "organization": "Образовательный центр Кодер",
                "org_type": "АНО"
            },
            {
                "name": "Языковая школа Полиглот",
                "goal": "Бесплатное обучение английскому языку",
                "budget_range": (400000, 1000000),
                "participants_range": (50, 120),
                "organization": "Лингвистический центр Полиглот",
                "org_type": "Центр"
            },
            {
                "name": "Математический кружок Эйлер",
                "goal": "Подготовка к математическим олимпиадам",
                "budget_range": (300000, 700000),
                "participants_range": (20, 60),
                "organization": "Центр математического образования Эйлер",
                "org_type": "АНО"
            },
            {
                "name": "Робототехника для детей",
                "goal": "Обучение программированию роботов",
                "budget_range": (500000, 1200000),
                "participants_range": (30, 80),
                "organization": "Центр робототехники",
                "org_type": "Центр"
            },
            {
                "name": "Бизнес-школа Предприниматель",
                "goal": "Обучение основам предпринимательства для молодежи",
                "budget_range": (400000, 900000),
                "participants_range": (25, 70),
                "organization": "Школа бизнеса Предприниматель",
                "org_type": "АНО"
            }
        ],

        # Social projects (5 types)
        "social": [
            {
                "name": "Помощь пожилым людям",
                "goal": "Социальная поддержка и помощь пожилым гражданам",
                "budget_range": (400000, 1000000),
                "participants_range": (100, 300),
                "organization": "Фонд помощи пожилым",
                "org_type": "Фонд"
            },
            {
                "name": "Волонтерский центр Доброе дело",
                "goal": "Организация волонтерских программ для молодежи",
                "budget_range": (350000, 800000),
                "participants_range": (50, 150),
                "organization": "Волонтерский центр Доброе дело",
                "org_type": "АНО"
            },
            {
                "name": "Поддержка многодетных семей",
                "goal": "Помощь многодетным семьям в социализации детей",
                "budget_range": (500000, 1200000),
                "participants_range": (80, 200),
                "organization": "Фонд поддержки семьи",
                "org_type": "Фонд"
            },
            {
                "name": "Реабилитационный центр Надежда",
                "goal": "Реабилитация людей после травм и операций",
                "budget_range": (600000, 1500000),
                "participants_range": (40, 100),
                "organization": "Центр реабилитации Надежда",
                "org_type": "Центр"
            },
            {
                "name": "Психологическая помощь Поддержка",
                "goal": "Бесплатная психологическая помощь населению",
                "budget_range": (400000, 900000),
                "participants_range": (60, 150),
                "organization": "Центр психологической помощи",
                "org_type": "АНО"
            }
        ],

        # Cultural projects (5 types)
        "cultural": [
            {
                "name": "Театральная студия Маска",
                "goal": "Развитие детского театрального творчества",
                "budget_range": (400000, 1000000),
                "participants_range": (30, 80),
                "organization": "Театральная студия Маска",
                "org_type": "АНО"
            },
            {
                "name": "Музей истории города",
                "goal": "Создание исторического музея и экскурсионных программ",
                "budget_range": (700000, 1800000),
                "participants_range": (500, 2000),
                "organization": "Культурный фонд",
                "org_type": "Фонд"
            },
            {
                "name": "Библиотечный проект Читай-город",
                "goal": "Модернизация библиотек и развитие чтения",
                "budget_range": (500000, 1200000),
                "participants_range": (200, 800),
                "organization": "Культурный центр",
                "org_type": "Центр"
            },
            {
                "name": "Музыкальная школа Гармония",
                "goal": "Обучение игре на музыкальных инструментах",
                "budget_range": (450000, 1100000),
                "participants_range": (40, 100),
                "organization": "Музыкальная школа Гармония",
                "org_type": "АНО"
            },
            {
                "name": "Художественная галерея Палитра",
                "goal": "Организация выставок молодых художников",
                "budget_range": (300000, 800000),
                "participants_range": (50, 150),
                "organization": "Художественный фонд Палитра",
                "org_type": "Фонд"
            }
        ],

        # Scientific projects (5 types)
        "scientific": [
            {
                "name": "Лаборатория физики",
                "goal": "Исследовательские проекты по физике для школьников",
                "budget_range": (600000, 1500000),
                "participants_range": (25, 70),
                "organization": "Научный центр физики",
                "org_type": "Центр"
            },
            {
                "name": "Биологическая станция",
                "goal": "Полевые исследования и экология",
                "budget_range": (700000, 1600000),
                "participants_range": (30, 80),
                "organization": "Биологический центр",
                "org_type": "АНО"
            },
            {
                "name": "Экологический мониторинг",
                "goal": "Мониторинг экологической обстановки в регионе",
                "budget_range": (500000, 1300000),
                "participants_range": (20, 60),
                "organization": "Экологический фонд",
                "org_type": "Фонд"
            },
            {
                "name": "Химическая лаборатория",
                "goal": "Образовательные химические эксперименты",
                "budget_range": (650000, 1400000),
                "participants_range": (25, 65),
                "organization": "Центр химических наук",
                "org_type": "Центр"
            },
            {
                "name": "Астрономический клуб Звездочет",
                "goal": "Популяризация астрономии среди молодежи",
                "budget_range": (400000, 1000000),
                "participants_range": (30, 90),
                "organization": "Астрономический клуб Звездочет",
                "org_type": "Клуб"
            }
        ]
    }

    def __init__(self, random_seed: Optional[int] = None):
        """
        Initialize generator

        Args:
            random_seed: Random seed for reproducibility
        """
        if random_seed:
            random.seed(random_seed)

        logger.info(f"[SyntheticUserGenerator] Initialized with {self._count_profiles()} profile templates")

    def _count_profiles(self) -> int:
        """Count total profile templates"""
        return sum(len(profiles) for profiles in self.PROFILES.values())

    def generate_profile(
        self,
        profile_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> UserProfile:
        """
        Generate a user profile

        Args:
            profile_type: Type of profile (sports, education, social, cultural, scientific)
                          If None, random type
            region: Region (if None, random)

        Returns:
            UserProfile instance
        """
        # Select profile type
        if profile_type is None:
            profile_type = random.choice(list(self.PROFILES.keys()))

        if profile_type not in self.PROFILES:
            raise ValueError(f"Invalid profile_type: {profile_type}")

        # Select template
        template = random.choice(self.PROFILES[profile_type])

        # Generate values
        budget = random.randint(*template["budget_range"])
        participants = random.randint(*template["participants_range"])
        duration_months = random.choice([6, 9, 12, 18, 24])
        experience_years = random.randint(1, 10)

        if region is None:
            region = random.choice(self.REGIONS)

        profile = UserProfile(
            name=template["name"],
            type=profile_type,
            goal=template["goal"],
            budget=budget,
            region=region,
            participants=participants,
            duration_months=duration_months,
            organization=template["organization"],
            organization_type=template["org_type"],
            experience_years=experience_years
        )

        logger.debug(f"Generated profile: {profile.name} ({profile.type}) in {region}")

        return profile

    def generate_profiles(self, count: int = 100) -> List[UserProfile]:
        """
        Generate multiple profiles

        Args:
            count: Number of profiles to generate

        Returns:
            List of UserProfile instances
        """
        profiles = []

        # Generate balanced distribution across types
        profile_types = list(self.PROFILES.keys())

        for i in range(count):
            # Cycle through types for balance
            profile_type = profile_types[i % len(profile_types)]
            profile = self.generate_profile(profile_type=profile_type)
            profiles.append(profile)

        logger.info(f"Generated {count} profiles")

        return profiles

    def get_context_for_simulator(self, profile: UserProfile) -> Dict:
        """
        Get context dictionary for SyntheticUserSimulator

        Args:
            profile: UserProfile instance

        Returns:
            Context dictionary
        """
        return {
            "region": profile.region,
            "topic": profile.type,
            "organization": profile.organization,
            "organization_type": profile.organization_type,
            "goal": profile.goal,
            "budget": profile.budget,
            "participants": profile.participants,
            "duration_months": profile.duration_months,
            "experience_years": profile.experience_years
        }


if __name__ == "__main__":
    # Test generation
    logging.basicConfig(level=logging.INFO)

    generator = SyntheticUserGenerator()

    print("\n=== Testing Synthetic User Generator ===\n")

    # Generate 10 profiles
    profiles = generator.generate_profiles(count=10)

    for i, profile in enumerate(profiles, 1):
        print(f"\n{i}. {profile.name}")
        print(f"   Type: {profile.type}")
        print(f"   Goal: {profile.goal}")
        print(f"   Budget: {profile.budget:,} руб.")
        print(f"   Region: {profile.region}")
        print(f"   Participants: {profile.participants}")
        print(f"   Duration: {profile.duration_months} months")
        print(f"   Organization: {profile.organization} ({profile.organization_type})")
        print(f"   Experience: {profile.experience_years} years")

    print(f"\n=== Total templates: {generator._count_profiles()} ===")
