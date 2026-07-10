"""Render an assembled resume dict (profile + six collections) as Markdown."""


def render_markdown(resume: dict) -> str:
    profile = resume.get("profile") or {}
    lines: list[str] = [f"# {profile.get('name', 'Resume')}"]

    if profile.get("headline"):
        lines.append(f"\n{profile['headline']}")
    if profile.get("summary"):
        lines.append(f"\n{profile['summary']}")

    contact_bits = [b for b in [profile.get("location"), profile.get("email")] if b]
    if contact_bits:
        lines.append(f"\n{' | '.join(contact_bits)}")

    links = profile.get("links") or {}
    if links:
        lines.append("\n" + " | ".join(f"[{label}]({url})" for label, url in links.items()))

    if resume.get("experience"):
        lines.append("\n## Experience")
        for exp in resume["experience"]:
            period = f"{exp.get('start_date', '')} – {exp.get('end_date') or 'Present'}"
            lines.append(f"\n### {exp.get('title')} — {exp.get('organization')}")
            meta = " | ".join(b for b in [exp.get("location"), period] if b)
            if meta:
                lines.append(meta)
            for responsibility in exp.get("responsibilities", []):
                lines.append(f"- {responsibility}")
            if exp.get("accomplishments"):
                lines.append(f"\n**Highlights:** {'; '.join(exp['accomplishments'])}")

    if resume.get("education"):
        lines.append("\n## Education")
        for edu in resume["education"]:
            period = f"{edu.get('start_date', '')} – {edu.get('end_date') or 'Present'}"
            heading = edu.get("degree", "")
            if edu.get("field_of_study"):
                heading += f", {edu['field_of_study']}"
            lines.append(f"\n### {heading}")
            lines.append(f"{edu.get('institution')} | {period}")
            if edu.get("honors"):
                lines.append(f"Honors: {edu['honors']}")

    if resume.get("skills"):
        lines.append("\n## Skills")
        by_category: dict[str, list[str]] = {}
        for skill in resume["skills"]:
            by_category.setdefault(skill.get("category", "other"), []).append(skill["name"])
        for category, names in by_category.items():
            lines.append(f"- **{category.replace('-', ' ').title()}**: {', '.join(names)}")

    if resume.get("certifications"):
        lines.append("\n## Certifications")
        for cert in resume["certifications"]:
            lines.append(
                f"- {cert.get('name')} — {cert.get('issuing_organization')} ({cert.get('issue_date')})"
            )

    if resume.get("hobbies"):
        lines.append("\n## Hobbies")
        for hobby in resume["hobbies"]:
            text = hobby.get("name", "")
            if hobby.get("description"):
                text += f": {hobby['description']}"
            lines.append(f"- {text}")

    if resume.get("goals"):
        lines.append("\n## Goals")
        for goal in resume["goals"]:
            lines.append(f"- {goal.get('description')} ({goal.get('status')})")

    return "\n".join(lines) + "\n"
