"""About-me profile built from portfolio content constants.

Edit `app/portfolio/content.py` to update personal details.
This module turns that content into the prompt block used by PortfolioAgent.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portfolio import content


@dataclass(frozen=True)
class AboutMeProfile:
    """Structured personal details injected into the Groq system prompt."""

    full_name: str
    title: str
    location: str
    tagline: str
    email: str
    resume_url: str
    linkedin: str
    github: str
    medium: str
    about_intro: str
    about_paragraphs: tuple[str, ...]
    about_highlight: str
    about_highlight_detail: str
    about_strength: str
    about_strength_detail: str
    exploring: tuple[str, ...]
    experience: tuple[dict, ...]
    projects: tuple[dict, ...]
    skill_categories: tuple[dict, ...]
    blogs: tuple[dict, ...]

    @classmethod
    def from_content(cls) -> AboutMeProfile:
        profile = content.PROFILE
        social = profile["social"]
        about = profile["about"]
        return cls(
            full_name=profile["full_name"],
            title=profile["title"],
            location=profile["location"],
            tagline=profile["tagline"],
            email=profile["email"],
            resume_url=profile["resume_url"],
            linkedin=social["linkedin"],
            github=social["github"],
            medium=social["medium"],
            about_intro=about["intro"],
            about_paragraphs=tuple(about["paragraphs"]),
            about_highlight=about["highlight"],
            about_highlight_detail=about["highlight_detail"],
            about_strength=about["strength"],
            about_strength_detail=about["strength_detail"],
            exploring=tuple(profile["exploring"]),
            experience=tuple(content.EXPERIENCE),
            projects=tuple(content.PROJECTS),
            skill_categories=tuple(content.SKILL_CATEGORIES),
            blogs=tuple(content.BLOGS),
        )

    def to_prompt_block(self) -> str:
        """Render a factual block the LLM must treat as ground truth."""
        lines = [
            f"Name: {self.full_name}",
            f"Title: {self.title}",
            f"Location: {self.location}",
            f"Tagline: {self.tagline}",
            "",
            "About:",
            self.about_intro,
            *self.about_paragraphs,
            f"Highlight: {self.about_highlight} {self.about_highlight_detail}",
            f"Strength: {self.about_strength} {self.about_strength_detail}",
            "",
            "Currently exploring:",
            *[f"- {item}" for item in self.exploring],
            "",
            "Contact:",
            f"- email: {self.email}",
            f"- linkedin: {self.linkedin}",
            f"- github: {self.github}",
            f"- medium: {self.medium}",
            f"- resume: {self.resume_url}",
        ]

        lines.extend(["", "Work experience:"])
        for company in self.experience:
            current = " (current)" if company.get("current") else ""
            total = company.get("total_duration")
            total_bit = f" — {total}" if total else ""
            lines.append(f"Company: {company['company']}{current}{total_bit}")
            for role in company.get("roles", []):
                work_mode = role.get("work_mode")
                mode_bit = f" | {work_mode}" if work_mode else ""
                lines.append(
                    f"  - {role['title']} ({role.get('employment_type', '')}) | "
                    f"{role.get('duration', '')} | {role.get('location', '')}{mode_bit}"
                )
                for bullet in role.get("description", []):
                    lines.append(f"    • {bullet}")
                skills = role.get("skills") or []
                if skills:
                    lines.append(f"    Skills: {', '.join(skills)}")

        lines.extend(["", "Projects:"])
        for project in self.projects:
            lines.append(
                f"- {project['title']} [{project.get('category', '')}]: "
                f"{project.get('long_description') or project.get('description', '')}"
            )
            tech = project.get("technologies") or []
            if tech:
                lines.append(f"  Tech: {', '.join(tech)}")
            if project.get("demo"):
                lines.append(f"  Demo: {project['demo']}")
            for link in project.get("github") or []:
                lines.append(f"  {link['label']}: {link['url']}")

        lines.extend(["", "Skills:"])
        for category in self.skill_categories:
            lines.append(f"{category['title']}:")
            for skill in category.get("skills", []):
                lines.append(f"  - {skill['name']} ({skill['level']})")

        if self.blogs:
            lines.extend(["", "Writing / blogs:"])
            for blog in self.blogs:
                lines.append(
                    f"- {blog['title']} ({blog.get('published_at', '')}, "
                    f"{blog.get('read_time', '')}): {blog.get('excerpt', '')}"
                )
                if blog.get("url"):
                    lines.append(f"  URL: {blog['url']}")

        return "\n".join(lines)


ABOUT_ME = AboutMeProfile.from_content()
