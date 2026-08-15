"""Portfolio content constants — source of truth for the about-me Q&A agent.

Keep this aligned with the portfolio frontend profile / experience / projects data.
"""

from __future__ import annotations

PROFILE = {
    "first_name": "Siddhesh",
    "last_name": "Shinde",
    "full_name": "Siddhesh Shinde",
    "title": "Senior Software Engineer",
    "eyebrow": "SOFTWARE ENGINEER • AI BUILDER",
    "headline": {
        "line1": "Senior Software Engineer",
        "line2": "building useful things",
        "line3": "with code + AI.",
    },
    "tagline": (
        "5+ years of experience building scalable products, backend systems, "
        "and AI-powered applications."
    ),
    "email": "siddhesh.ss26@gmail.com",
    "location": "Navi Mumbai, Maharashtra, India",
    "resume_url": (
        "https://drive.google.com/file/d/1MwTi5GDDaPlxOTIrOEGaQzlb7CsONZm4/"
        "view?usp=sharing"
    ),
    "social": {
        "linkedin": "https://www.linkedin.com/in/siddhesh-shinde-developer/",
        "github": "https://github.com/siddhesh494",
        "medium": "https://medium.com/@siddhesh.ss26",
    },
    "about": {
        "intro": "5+ years of turning ideas into reliable software.",
        "paragraphs": [
            (
                "With 5+ years as a Senior Software Engineer, I design and ship "
                "scalable products end to end — from clean, reusable architecture "
                "to production-ready delivery. My day-to-day stack includes "
                "JavaScript, TypeScript, Node.js, ExpressJS, React, Azure, and "
                "Azure Functions, with a strong focus on code quality, thoughtful "
                "code reviews, and maintainable systems that teams can trust."
            ),
            (
                "I partner with product and engineering teams to turn requirements "
                "into reliable software, raising the bar on quality through reviews, "
                "standards, and pragmatic engineering practices."
            ),
        ],
        "highlight": "Recently focused on AI engineering.",
        "highlight_detail": (
            "LLM-powered applications, Retrieval-Augmented Generation (RAG), "
            "AI agents, and production AI systems."
        ),
        "strength": "Software engineering best practices + modern AI technologies.",
        "strength_detail": (
            "Building reliable, user-facing AI products that integrate modern LLM "
            "frameworks, vector databases, and scalable backend architectures."
        ),
    },
    "exploring": [
        "Generative AI & LLMs",
        "RAG Systems",
        "AI Agents & Workflow Automation",
        "Langchain",
    ],
    "footer_tagline": "Built with curiosity, caffeine & code.",
}

EXPERIENCE = [
    {
        "id": "cogitate",
        "kind": "company",
        "company": "Cogitate",
        "current": True,
        "roles": [
            {
                "id": "cogitate-sse",
                "title": "Senior Software Engineer",
                "employment_type": "Full-time",
                "duration": "March 2026 — Present",
                "location": "Navi Mumbai, Maharashtra, India",
                "work_mode": "Hybrid",
                "description": [],
                "skills": [
                    "Software Engineering",
                    "JavaScript",
                    "TypeScript",
                    "React",
                    "Node.js",
                    "AI Engineering",
                    "Backend Development",
                    "Azure function apps",
                ],
            },
        ],
    },
    {
        "id": "servify",
        "kind": "company",
        "company": "Servify",
        "total_duration": "4 years 7 months",
        "roles": [
            {
                "id": "servify-pe2",
                "title": "Product Engineer II",
                "employment_type": "Full-time",
                "duration": "April 2024 — March 2026",
                "location": "Mumbai Metropolitan Region",
                "work_mode": "On-site",
                "description": [
                    (
                        "Worked on IVR, Chatbot and Webbot functionality that helped "
                        "users get details about their current plan and the status of "
                        "their claim. Users could also file a claim, reschedule a "
                        "request, or cancel a request using this functionality."
                    ),
                    (
                        "I delved into microservices architecture, gaining a "
                        "comprehensive understanding of how these services communicate "
                        "with each other."
                    ),
                    (
                        "Additionally, I took ownership of two projects, showcasing my "
                        "leadership, and also conducted code reviews for React and "
                        "Node-based projects, ensuring code quality."
                    ),
                ],
                "skills": [
                    "JavaScript",
                    "React.js",
                    "Node.js",
                    "Microservices",
                    "Backend Development",
                    "AI Engineering",
                ],
            },
            {
                "id": "servify-pe",
                "title": "Product Engineer",
                "employment_type": "Full-time",
                "duration": "December 2021 — April 2024",
                "location": "Maharashtra, India",
                "work_mode": "Hybrid",
                "description": [
                    (
                        "I worked in an agile environment to deliver higher-quality "
                        "software far more rapidly."
                    ),
                    (
                        "Worked on config-based UI and helped create configuration for "
                        "new client onboarding. Also created UI to automate the "
                        "onboarding process of the client from scratch, which included "
                        "Checker Maker functionality and reduced the onboarding time "
                        "by an impressive 90%."
                    ),
                    (
                        "Designed UI and API structure for onboarding new plans and "
                        "services using Checker Maker functionality and applied "
                        "feature rights."
                    ),
                    (
                        "Additionally, I took ownership of two projects, showcasing my "
                        "leadership, and also conducted code reviews for React and "
                        "Node-based projects, ensuring code quality."
                    ),
                ],
                "skills": [
                    "JavaScript",
                    "Front-End Development",
                    "React",
                    "Node.js",
                    "API Development",
                    "Agile",
                    "UI Development",
                ],
            },
            {
                "id": "servify-intern",
                "title": "Product Engineer",
                "employment_type": "Internship",
                "duration": "September 2021 — December 2021",
                "location": "Mumbai, Maharashtra, India",
                "description": [
                    (
                        "Learned about JavaScript, Node.js and Git flow and worked on "
                        "real-life projects."
                    ),
                    (
                        "Learned about the best practices for production-ready "
                        "applications."
                    ),
                ],
                "skills": [
                    "JavaScript",
                    "Node.js",
                    "Git",
                    "Software Development",
                ],
            },
        ],
    },
]

PROJECTS = [
    {
        "id": "cortex",
        "title": "Cortex",
        "category": "Multi-Agent AI",
        "description": (
            "A multi-agent AI assistant where specialized agents handle distinct "
            "jobs instead of one model doing everything."
        ),
        "long_description": (
            "Cortex is a multi-agent AI assistant. Instead of one big model doing "
            "everything, different small jobs are handled by different AI agents — "
            "like a team where each person has a clear role."
        ),
        "technologies": [
            "React",
            "TypeScript",
            "Python",
            "LLMs",
            "FastAPI",
            "RAG",
            "LangChain",
            "Pinecone",
            "Google Gemini",
            "Groq",
        ],
        "github": [
            {
                "label": "Frontend",
                "url": "https://github.com/siddhesh494/Cortex-Client",
            },
            {
                "label": "Backend",
                "url": "https://github.com/siddhesh494/Cortex-Server",
            },
        ],
        "demo": "https://cortex-client.netlify.app/",
    },
    {
        "id": "scantodine",
        "title": "ScanToDine",
        "category": "Restaurant Menu",
        "description": (
            "A digital restaurant menu app for browsing dishes with category "
            "filters, search, and live menu data."
        ),
        "long_description": (
            "ScanToDine is a restaurant menu platform with a React frontend and "
            "Express backend. Guests browse menu items with category filtering and "
            "search, while the server handles menu management, Firebase "
            "authentication, and Firestore-backed data for a seamless dining "
            "experience."
        ),
        "technologies": [
            "React",
            "Tailwind CSS",
            "Node.js",
            "Express",
            "Firebase",
        ],
        "github": [
            {
                "label": "Frontend",
                "url": "https://github.com/siddhesh494/restaurant_menu_client",
            },
            {
                "label": "Backend",
                "url": "https://github.com/siddhesh494/restaurant_menu_server",
            },
        ],
        "demo": "https://scantodine.netlify.app/",
    },
    {
        "id": "lordsdecor",
        "title": "Lord's Decor",
        "category": "Business Website",
        "description": (
            "A marketing site for a luxury home and office décor service covering "
            "Mumbai, Thane, and Navi Mumbai."
        ),
        "long_description": (
            "Lord's Decor is a client website for a décor and interior services "
            "business. It showcases work galleries, product offerings, and contact "
            "channels so customers can explore services like invisible grills, "
            "wallpaper, blinds, and more — then reach out directly."
        ),
        "technologies": ["React", "Bootstrap", "JavaScript", "React Router"],
        "github": [
            {
                "label": "GitHub",
                "url": "https://github.com/siddhesh494/lord-decor-web",
            },
        ],
        "demo": "https://www.lordsdecor.in/",
    },
    {
        "id": "logreader",
        "title": "Log Reader",
        "category": "VS Code Extension",
        "description": (
            "A VS Code extension that turns messy development logs into readable "
            "output for faster debugging."
        ),
        "long_description": (
            "Log Reader is a VS Code extension that converts unreadable development "
            "logs into clear, structured output. It helps you scan and debug faster "
            "without fighting dense raw log dumps — with a companion web demo for "
            "trying the experience outside the editor."
        ),
        "technologies": ["JavaScript", "VS Code API", "Webpack", "React"],
        "github": [
            {
                "label": "GitHub",
                "url": "https://github.com/siddhesh494/logger-extension",
            },
        ],
        "demo": "https://logger-reader.netlify.app/",
    },
    {
        "id": "tripmate",
        "title": "TripMate",
        "category": "Travel Product",
        "description": (
            "A travel-matching app that connects you with like-minded adventurers "
            "for getaways, city exploration, and group trips."
        ),
        "long_description": (
            "TripMate helps travelers find activity partners — whether for a "
            "weekend getaway, someone to show you around a new city, or planning a "
            "group trip. The product spans a marketing website, client app, and "
            "backend service that power waitlist signup and the travel-matching "
            "experience."
        ),
        "technologies": ["React", "JavaScript", "Node.js", "Express"],
        "github": [
            {
                "label": "Client",
                "url": "https://github.com/siddhesh494/tripmate-client",
            },
            {
                "label": "Server",
                "url": "https://github.com/siddhesh494/tripmate-server",
            },
            {
                "label": "Website",
                "url": "https://github.com/siddhesh494/tripmate-website",
            },
        ],
        "demo": "https://tripmate.siddheshshinde.in/",
    },
]

SKILL_CATEGORIES = [
    {
        "id": "web",
        "title": "Web Technologies",
        "skills": [
            {"name": "Python", "level": "Intermediate"},
            {"name": "FastAPI", "level": "Intermediate"},
            {"name": "HTML", "level": "Experienced"},
            {"name": "CSS", "level": "Experienced"},
            {"name": "JavaScript", "level": "Experienced"},
            {"name": "React", "level": "Experienced"},
            {"name": "Node.js", "level": "Experienced"},
            {"name": "ExpressJS", "level": "Experienced"},
            {"name": "Redux", "level": "Experienced"},
            {"name": "TypeScript", "level": "Experienced"},
            {"name": "SASS", "level": "Intermediate"},
            {"name": "Tailwind CSS", "level": "Experienced"},
        ],
    },
    {
        "id": "other",
        "title": "Other Concepts",
        "skills": [
            {"name": "Git", "level": "Experienced"},
            {"name": "SQL", "level": "Experienced"},
            {"name": "MongoDB", "level": "Experienced"},
            {"name": "Pinecone", "level": "Intermediate"},
            {"name": "Linux", "level": "Intermediate"},
            {"name": "Developer Tools", "level": "Experienced"},
            {"name": "JIRA", "level": "Intermediate"},
            {"name": "Agile Methodology", "level": "Intermediate"},
        ],
    },
]

BLOGS = [
    {
        "id": "placeholder-1",
        "title": "Building Reliable Product Experiences with React & Node",
        "excerpt": (
            "Lessons from shipping production features — structuring APIs, keeping "
            "UI flexible, and reviewing code that lasts."
        ),
        "published_at": "2025-11-12",
        "read_time": "6 min read",
        "url": "https://medium.com/@siddhesh.ss26",
    },
    {
        "id": "placeholder-2",
        "title": "From Config UI to Faster Client Onboarding",
        "excerpt": (
            "How configuration-driven interfaces and maker-checker flows can shrink "
            "onboarding time without sacrificing control."
        ),
        "published_at": "2025-08-03",
        "read_time": "5 min read",
        "url": "https://medium.com/@siddhesh.ss26",
    },
    {
        "id": "placeholder-3",
        "title": "Growing into AI Engineering as a Product Engineer",
        "excerpt": (
            "Why strong software fundamentals matter when you start building "
            "LLM-powered features into real products."
        ),
        "published_at": "2026-02-18",
        "read_time": "7 min read",
        "url": "https://medium.com/@siddhesh.ss26",
    },
]
