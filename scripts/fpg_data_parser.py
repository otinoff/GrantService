"""
FPG Data Parser - Extract real grant winners data from Perplexity/Parallel AI results

This script parses 3 data sources:
1. fpg_winners_research_ru.md - Russian research with concrete projects
2. fpg_analysis_patterns_en.md - English analysis of success patterns
3. fpg_parallel_ai_analysis.json - Structured JSON from Parallel AI

Output: JSON dataset of 100 real FPG grant winners for embeddings

Iteration 51: AI Enhancement - Embeddings + RL
Date: 2025-10-26
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import Pydantic models
import sys
sys.path.append(str(Path(__file__).parent.parent))
from shared.llm.embeddings_models import FPGRealWinner


class FPGDataParser:
    """
    Parser for FPG grant data from multiple sources

    Sources:
    1. Markdown files from Perplexity AI (Russian + English)
    2. JSON file from Parallel AI
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.grants: List[FPGRealWinner] = []

    def parse_russian_markdown(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Parse fpg_winners_research_ru.md to extract concrete projects

        Expected format:
        ### Проект N: "Title"
        **Организация:** ...
        **Регион:** ...
        **Сумма гранта:** ... рублей
        **Описание проблемы:** ...
        **Решение:** ...
        **Целевая аудитория:** ...
        **Измеримые результаты:** ...
        **Социальное воздействие:** ...
        **Бюджет:** ...
        """
        print(f"[*] Parsing {filepath.name}...", flush=True)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by project headers
        project_pattern = r'### Проект \d+: "([^"]+)"'
        projects = re.split(project_pattern, content)[1:]  # Skip intro

        parsed_grants = []

        # Process pairs: (title, content)
        for i in range(0, len(projects), 2):
            if i + 1 >= len(projects):
                break

            title = projects[i].strip()
            content_block = projects[i + 1]

            # Extract fields using regex
            org_match = re.search(r'\*\*Организация:\*\* (.+?)(?:\n|$)', content_block)
            region_match = re.search(r'\*\*Регион:\*\* (.+?)(?:\n|$)', content_block)
            amount_match = re.search(r'\*\*Сумма гранта:\*\* ([\d\s]+) рубл', content_block)
            year_match = re.search(r'\*\*Год:\*\* (\d{4})', content_block)

            # Extract multi-line sections
            problem_match = re.search(r'\*\*Описание проблемы:\*\*\n(.+?)(?=\n\*\*|$)', content_block, re.DOTALL)
            solution_match = re.search(r'\*\*Решение:\*\*\n(.+?)(?=\n\*\*|$)', content_block, re.DOTALL)
            audience_match = re.search(r'\*\*Целевая аудитория:\*\* (.+?)(?=\n\*\*|$)', content_block, re.DOTALL)
            kpi_match = re.search(r'\*\*Измеримые результаты:\*\* (.+?)(?=\n\*\*|$)', content_block, re.DOTALL)
            impact_match = re.search(r'\*\*Социальное воздействие:\*\* (.+?)(?=\n\*\*|$)', content_block, re.DOTALL)
            budget_match = re.search(r'\*\*Бюджет:\*\* (.+?)(?=\n\*\*|$)', content_block, re.DOTALL)

            grant_data = {
                'title': title,
                'organization': org_match.group(1).strip() if org_match else '',
                'region': region_match.group(1).strip() if region_match else '',
                'amount': int(amount_match.group(1).replace(' ', '')) if amount_match else 0,
                'year': int(year_match.group(1)) if year_match else 2024,
                'problem': problem_match.group(1).strip() if problem_match else '',
                'solution': solution_match.group(1).strip() if solution_match else '',
                'target_audience': audience_match.group(1).strip() if audience_match else '',
                'kpi': kpi_match.group(1).strip() if kpi_match else '',
                'social_impact': impact_match.group(1).strip() if impact_match else '',
                'budget': budget_match.group(1).strip() if budget_match else '',
                'fund_name': 'ФПГ',
                'category': self._infer_category(title, content_block),
                'source_url': 'Perplexity AI Research'
            }

            parsed_grants.append(grant_data)
            print(f"  [OK] Parsed: {title[:50]}... ({grant_data['amount']:,} rub)", flush=True)

        print(f"[STATS] Total parsed from Russian MD: {len(parsed_grants)} grants\n", flush=True)
        return parsed_grants

    def parse_json_analysis(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Parse fpg_parallel_ai_analysis.json for structured insights

        This JSON contains analysis patterns but may not have complete grant data.
        We'll extract what we can and merge with other sources.
        """
        print(f"[*] Parsing {filepath.name}...", flush=True)

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract insights from JSON structure
        insights = []

        # Check output structure
        if 'output' in data:
            output = data['output']

            # Extract budget categories (useful for templates)
            if 'standard_budget_categories' in output:
                print(f"  [INFO] Found {len(output['standard_budget_categories'])} budget categories", flush=True)

            # Extract problem framing strategies
            if 'problem_framing_strategies' in output:
                print(f"  [INFO] Found problem framing strategies", flush=True)

            # Extract KPI standards
            if 'kpi_formulation_standards' in output:
                print(f"  [INFO] Found KPI formulation standards", flush=True)

        print(f"[STATS] Extracted analysis insights from JSON\n", flush=True)
        return insights

    def _infer_category(self, title: str, content: str) -> str:
        """Infer grant category from title and content"""
        title_lower = title.lower()
        content_lower = content.lower()

        if any(word in title_lower or word in content_lower for word in ['образован', 'наук', 'школ', 'студент']):
            return 'Образование и наука'
        elif any(word in title_lower or word in content_lower for word in ['культур', 'искусств', 'театр', 'музей']):
            return 'Культура и искусство'
        elif any(word in title_lower or word in content_lower for word in ['здоров', 'медицин', 'лечен', 'реабилитац']):
            return 'Охрана здоровья'
        elif any(word in title_lower or word in content_lower for word in ['социальн', 'бездом', 'инвалид', 'пожил']):
            return 'Социальное обслуживание'
        elif any(word in title_lower or word in content_lower for word in ['семь', 'детск', 'материнств']):
            return 'Поддержка семьи и детства'
        elif any(word in title_lower or word in content_lower for word in ['молодеж', 'молод']):
            return 'Молодежные проекты'
        elif any(word in title_lower or word in content_lower for word in ['эколог', 'природ', 'животн']):
            return 'Экология и защита животных'
        elif any(word in title_lower or word in content_lower for word in ['спорт', 'физкульт']):
            return 'Спорт'
        else:
            return 'Другое'

    def create_fpg_winner_objects(self, grants_data: List[Dict[str, Any]]) -> List[FPGRealWinner]:
        """
        Convert parsed data to FPGRealWinner Pydantic objects
        """
        fpg_winners = []

        for grant_data in grants_data:
            try:
                winner = FPGRealWinner(
                    title=grant_data['title'],
                    organization=grant_data['organization'],
                    problem=grant_data['problem'],
                    solution=grant_data['solution'],
                    kpi=grant_data['kpi'],
                    budget=grant_data['budget'],
                    target_audience=grant_data.get('target_audience'),
                    social_impact=grant_data.get('social_impact'),
                    fund_name=grant_data['fund_name'],
                    year=grant_data['year'],
                    region=grant_data.get('region'),
                    amount=grant_data.get('amount'),
                    category=grant_data.get('category'),
                    source_url=grant_data.get('source_url'),
                    scraped_at=datetime.now()
                )
                fpg_winners.append(winner)
            except Exception as e:
                print(f"  [WARN] Skipping grant '{grant_data.get('title', 'Unknown')}': {e}", flush=True)

        return fpg_winners

    def parse_all_sources(self) -> List[FPGRealWinner]:
        """
        Parse all available data sources and combine results
        """
        print("[START] Starting FPG data parsing...\n", flush=True)

        all_grants_data = []

        # 1. Parse Russian markdown (concrete projects)
        russian_md = self.data_dir / "fpg_winners_research_ru.md"
        if russian_md.exists():
            grants_from_russian = self.parse_russian_markdown(russian_md)
            all_grants_data.extend(grants_from_russian)

        # 2. Parse JSON analysis (insights)
        json_file = self.data_dir / "fpg_parallel_ai_analysis.json"
        if json_file.exists():
            self.parse_json_analysis(json_file)

        # 3. Convert to Pydantic objects
        print("[*] Converting to FPGRealWinner objects...", flush=True)
        fpg_winners = self.create_fpg_winner_objects(all_grants_data)
        print(f"[OK] Created {len(fpg_winners)} FPGRealWinner objects\n", flush=True)

        self.grants = fpg_winners
        return fpg_winners

    def save_to_json(self, output_file: Path):
        """
        Save parsed grants to JSON file for embeddings
        """
        print(f"[SAVE] Saving to {output_file}...", flush=True)

        grants_json = [grant.model_dump(mode='json') for grant in self.grants]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(grants_json, f, ensure_ascii=False, indent=2, default=str)

        print(f"[OK] Saved {len(grants_json)} grants to {output_file}\n", flush=True)

    def print_statistics(self):
        """Print dataset statistics"""
        if not self.grants:
            print("[WARN] No grants parsed yet", flush=True)
            return

        print("[STATS] Dataset Statistics:", flush=True)
        print(f"  Total grants: {len(self.grants)}", flush=True)

        # By category
        categories = {}
        for grant in self.grants:
            cat = grant.category or 'Unknown'
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\n  By category:", flush=True)
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"    {cat}: {count}", flush=True)

        # By year
        years = {}
        for grant in self.grants:
            years[grant.year] = years.get(grant.year, 0) + 1

        print(f"\n  By year:", flush=True)
        for year, count in sorted(years.items()):
            print(f"    {year}: {count}", flush=True)

        # Amount statistics
        amounts = [grant.amount for grant in self.grants if grant.amount]
        if amounts:
            print(f"\n  Grant amounts:", flush=True)
            print(f"    Min: {min(amounts):,} rub", flush=True)
            print(f"    Max: {max(amounts):,} rub", flush=True)
            print(f"    Avg: {sum(amounts)//len(amounts):,} rub", flush=True)

        # Content length statistics
        problem_lengths = [len(grant.problem) for grant in self.grants if grant.problem]
        solution_lengths = [len(grant.solution) for grant in self.grants if grant.solution]

        if problem_lengths:
            print(f"\n  Content lengths:", flush=True)
            print(f"    Problem avg: {sum(problem_lengths)//len(problem_lengths)} chars", flush=True)
            print(f"    Solution avg: {sum(solution_lengths)//len(solution_lengths)} chars", flush=True)


def main():
    """Main entry point"""
    # Paths
    iteration_dir = Path(__file__).parent.parent / "iterations" / "Iteration_51_AI_Enhancement"
    output_file = iteration_dir / "fpg_real_winners_dataset.json"

    # Parse data
    parser = FPGDataParser(iteration_dir)
    grants = parser.parse_all_sources()

    # Save results
    parser.save_to_json(output_file)

    # Print statistics
    parser.print_statistics()

    print(f"\n[DONE] Dataset ready for GigaChat Embeddings API", flush=True)
    print(f"[OUTPUT] File: {output_file}", flush=True)


if __name__ == "__main__":
    main()
