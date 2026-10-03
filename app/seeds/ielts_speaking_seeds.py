"""
Seed data for IELTS Speaking Simulation Tests (3 Parts standard).
"""

from app.extensions import db
from app.backend.exams.models import IeltsSpeakingTest, IeltsSpeakingTopic


SPEAKING_TESTS_DATA = [
    {
        "title": "IELTS Speaking Test 01: Technology, Social Media & Artificial Intelligence",
        "description": "Đề thi IELTS Speaking mô phỏng 3 phần về chủ đề Công nghệ, Mạng xã hội và Trí tuệ nhân tạo (AI) trong cuộc sống tương lai.",
        "target_band": "6.5 - 8.5",
        "difficulty": "Medium",
        "duration_minutes": 15,
        "topics": [
            {
                "part": 1,
                "topic_title": "Daily Technology & Smartphone Habits",
                "cue_card_prompt": None,
                "prep_time_seconds": 0,
                "response_time_seconds": 30,
                "order": 1,
                "questions": [
                    {
                        "id": 1,
                        "question": "What electronic device do you use most frequently in your daily life?",
                        "audio_prompt": "Let's talk about technology. What electronic device do you use most frequently in your daily life?",
                        "model_answer": "Without a shadow of a doubt, it is my smartphone. I rely on it virtually around the clock for everything from communicating with colleagues to managing my daily schedule and reading digital news.",
                        "vocab_hints": ["without a shadow of a doubt", "rely on", "around the clock", "manage schedule"]
                    },
                    {
                        "id": 2,
                        "question": "Do you prefer reading physical books or e-books on a digital screen?",
                        "audio_prompt": "Do you prefer reading physical books or e-books on a digital screen?",
                        "model_answer": "To be perfectly frank, I have a strong penchant for e-books because of their sheer convenience. Having a portable digital library of hundreds of books in a lightweight tablet is truly indispensable for frequent commuters like me.",
                        "vocab_hints": ["strong penchant for", "sheer convenience", "portable library", "indispensable"]
                    },
                    {
                        "id": 3,
                        "question": "How much time do you typically spend on social media platforms each day?",
                        "audio_prompt": "How much time do you typically spend on social media platforms each day?",
                        "model_answer": "On average, I would say roughly two to three hours daily. I mostly browse through LinkedIn for professional networking and YouTube for educational documentaries during my downtime.",
                        "vocab_hints": ["on average", "browse through", "professional networking", "downtime"]
                    },
                    {
                        "id": 4,
                        "question": "Did you use much technology when you were a child?",
                        "audio_prompt": "Looking back, did you use much technology when you were a child?",
                        "model_answer": "Not particularly. Back when I was in primary school, smartphones were not ubiquitous. My childhood was predominantly centered around outdoor games, board games, and reading illustrated storybooks with friends.",
                        "vocab_hints": ["not particularly", "ubiquitous", "predominantly centered around", "illustrated storybooks"]
                    }
                ]
            },
            {
                "part": 2,
                "topic_title": "Describe a piece of technology you find difficult to live without",
                "cue_card_prompt": "Describe an electronic device or technology tool you find difficult to live without.\n\nYou should say:\n• What it is and how long you have had it\n• What you mainly use it for\n• How often you use it\n• And explain why it is so important and difficult for you to live without.",
                "prep_time_seconds": 60,
                "response_time_seconds": 120,
                "order": 2,
                "questions": [
                    {
                        "id": 5,
                        "question": "Cue Card: Describe an electronic device or technology tool you find difficult to live without.",
                        "audio_prompt": "Now, I am going to give you a topic and I would like you to speak for one to two minutes. Before you speak, you will have one minute to think about what you are going to say, and you can make notes if you wish. Here is your topic: Describe a piece of technology you find difficult to live without.",
                        "model_answer": "Today, I would like to talk about my noise-canceling laptop workstation, which I purchased about two years ago when transitioning to a hybrid working arrangement. I utilize this machine extensively for software engineering, video conferencing, and academic research. On a typical working day, I spend upwards of eight hours interacting with it. The primary reason this device has become an indispensable cornerstone of my daily life is its seamless ability to streamline complex workflows. Without it, collaborating with cross-border team members in real-time and executing demanding technical projects would be nearly insurmountable.",
                        "vocab_hints": ["hybrid working arrangement", "utilize extensively", "indispensable cornerstone", "streamline complex workflows", "insurmountable"]
                    }
                ]
            },
            {
                "part": 3,
                "topic_title": "Artificial Intelligence & Future of Society",
                "cue_card_prompt": None,
                "prep_time_seconds": 0,
                "response_time_seconds": 60,
                "order": 3,
                "questions": [
                    {
                        "id": 6,
                        "question": "In what ways do you think Artificial Intelligence will reshape the future job market?",
                        "audio_prompt": "We have been talking about technology. Let's discuss AI in more depth. In what ways do you think Artificial Intelligence will reshape the future job market?",
                        "model_answer": "From my perspective, AI will act as a double-edged sword. On one hand, it will automate mundane, repetitive tasks and significantly bolster overall productivity. On the other hand, it may cause temporary labor displacement, necessitating widespread workforce reskilling in critical thinking and creative problem-solving.",
                        "vocab_hints": ["double-edged sword", "mundane and repetitive", "bolster productivity", "labor displacement", "reskilling"]
                    },
                    {
                        "id": 7,
                        "question": "Do you believe children nowadays are overly dependent on electronic screens?",
                        "audio_prompt": "Do you believe that younger generations are becoming overly reliant on digital screens and gadgets?",
                        "model_answer": "Yes, to a considerable degree. The excessive exposure to algorithmic short-form content can lead to reduced attention spans and sedentary lifestyles. Therefore, parents and educators must implement balanced digital detox strategies and encourage physical recreation.",
                        "vocab_hints": ["to a considerable degree", "excessive exposure", "reduced attention span", "sedentary lifestyle", "digital detox"]
                    },
                    {
                        "id": 8,
                        "question": "How can governments ensure equitable access to technology across rural and urban communities?",
                        "audio_prompt": "How can governments address the digital divide between rural and urban areas?",
                        "model_answer": "Bridging the digital divide requires substantial municipal investment in high-speed broadband infrastructure, alongside government-subsidized device programs and comprehensive digital literacy workshops for underprivileged communities.",
                        "vocab_hints": ["bridge the digital divide", "municipal investment", "high-speed broadband", "subsidized programs", "digital literacy"]
                    }
                ]
            }
        ]
    },
    {
        "title": "IELTS Speaking Test 02: Environmental Protection & Sustainable Living",
        "description": "Đề thi IELTS Speaking mô phỏng 3 phần về chủ đề Bảo vệ Môi trường, Lối sống Bền vững và Biến đổi Khí hậu toàn cầu.",
        "target_band": "6.5 - 8.5",
        "difficulty": "Hard",
        "duration_minutes": 15,
        "topics": [
            {
                "part": 1,
                "topic_title": "Weather, Nature & Green Spaces",
                "cue_card_prompt": None,
                "prep_time_seconds": 0,
                "response_time_seconds": 30,
                "order": 1,
                "questions": [
                    {
                        "id": 1,
                        "question": "What is your favorite kind of weather and why?",
                        "audio_prompt": "Let's talk about nature and weather. What is your favorite kind of weather and why?",
                        "model_answer": "I have always been fond of mild, crisp autumn weather. The moderate temperature is ideal for outdoor jogging, and the serene ambiance makes it very conducive to mental relaxation.",
                        "vocab_hints": ["crisp autumn weather", "moderate temperature", "serene ambiance", "conducive to"]
                    },
                    {
                        "id": 2,
                        "question": "Do you often visit public parks or botanical gardens in your city?",
                        "audio_prompt": "Do you often visit public parks or botanical gardens in your city?",
                        "model_answer": "Yes, whenever I get a chance on weekends. Visiting green sanctuaries provides a much-needed escape from the hustle and bustle of concrete jungles and allows me to recharge my batteries.",
                        "vocab_hints": ["green sanctuaries", "hustle and bustle", "concrete jungles", "recharge batteries"]
                    },
                    {
                        "id": 3,
                        "question": "Are you conscious about recycling and reducing household waste?",
                        "audio_prompt": "Are you conscious about recycling and reducing household waste?",
                        "model_answer": "Most definitely. I make a conscious effort to segregate organic and recyclable waste, and I always carry reusable tote bags to minimize single-use plastic consumption.",
                        "vocab_hints": ["conscious effort", "segregate waste", "reusable tote bags", "single-use plastic"]
                    }
                ]
            },
            {
                "part": 2,
                "topic_title": "Describe an environmental initiative or law you support",
                "cue_card_prompt": "Describe an environmental law or green initiative you think is beneficial for the planet.\n\nYou should say:\n• What the initiative or law is\n• How you first learned about it\n• Who is involved or responsible for implementing it\n• And explain why you think this initiative is beneficial and important.",
                "prep_time_seconds": 60,
                "response_time_seconds": 120,
                "order": 2,
                "questions": [
                    {
                        "id": 4,
                        "question": "Cue Card: Describe an environmental law or green initiative you think is beneficial for the planet.",
                        "audio_prompt": "Here is your Part 2 Cue Card. You have one minute to prepare your response: Describe an environmental law or green initiative you think is beneficial for the planet.",
                        "model_answer": "I would like to shed light on the nationwide ban on single-use non-biodegradable plastics in supermarkets and food outlets. I first learned about this policy through an insightful environmental documentary broadcast on national television last year. The initiative involves stringent government regulations coupled with collaborative participation from major retail chains and everyday citizens. In my view, this measure is of paramount importance because plastic pollution poses a severe ecological threat to marine biodiversity. By incentivizing biodegradable alternatives, we can foster a circular economy and preserve our natural ecosystems for posterity.",
                        "vocab_hints": ["shed light on", "non-biodegradable plastics", "stringent regulations", "paramount importance", "marine biodiversity", "circular economy", "posterity"]
                    }
                ]
            },
            {
                "part": 3,
                "topic_title": "Global Environmental Policies & Individual Action",
                "cue_card_prompt": None,
                "prep_time_seconds": 0,
                "response_time_seconds": 60,
                "order": 3,
                "questions": [
                    {
                        "id": 5,
                        "question": "Should environmental protection be the responsibility of individuals or governments?",
                        "audio_prompt": "Let's discuss environmental policies further. Should environmental protection be primarily the responsibility of individual citizens or national governments?",
                        "model_answer": "In my estimation, it requires a concerted collective effort. While individuals can adopt eco-friendly consumer habits, national governments possess the regulatory authority and fiscal resources to enforce emissions standards and subsidize large-scale renewable energy infrastructure.",
                        "vocab_hints": ["concerted collective effort", "in my estimation", "regulatory authority", "fiscal resources", "renewable infrastructure"]
                    },
                    {
                        "id": 6,
                        "question": "How can international organizations encourage developing nations to adopt clean energy?",
                        "audio_prompt": "How can global institutions help developing countries transition to greener energy sources?",
                        "model_answer": "International institutions like the United Nations and the World Bank can facilitate technological transfers and offer preferential green financing. This ensures developing economies can grow sustainably without being penalized by exorbitant transition costs.",
                        "vocab_hints": ["technological transfer", "preferential green financing", "grow sustainably", "exorbitant transition costs"]
                    },
                    {
                        "id": 7,
                        "question": "Do you think ecotourism can genuinely help preserve fragile natural habitats?",
                        "audio_prompt": "Do you think ecotourism is effective in conserving natural habitats, or does it cause unintended damage?",
                        "model_answer": "When managed with strict ecological guidelines and carrying capacity limits, ecotourism can generate vital revenue for local conservation while raising ecological awareness among travelers. However, unchecked commercial exploitation must be vigilantly avoided.",
                        "vocab_hints": ["carrying capacity limits", "vital revenue", "ecological awareness", "commercial exploitation", "vigilantly avoided"]
                    }
                ]
            }
        ]
    },
    {
        "title": "IELTS Speaking Test 03: Higher Education, Lifelong Learning & Career Growth",
        "description": "Đề thi IELTS Speaking mô phỏng 3 phần về chủ đề Giáo dục Đại học, Kỹ năng nghề nghiệp hiện đại và Xu hướng Học tập suốt đời.",
        "target_band": "6.0 - 8.0",
        "difficulty": "Medium",
        "duration_minutes": 15,
        "topics": [
            {
                "part": 1,
                "topic_title": "Studies, Work & Learning Routines",
                "cue_card_prompt": None,
                "prep_time_seconds": 0,
                "response_time_seconds": 30,
                "order": 1,
                "questions": [
                    {
                        "id": 1,
                        "question": "Are you currently studying or working?",
                        "audio_prompt": "Let's talk about what you do. Are you currently studying or working?",
                        "model_answer": "I am currently balancing my professional career as an IT specialist while pursuing specialized online certifications in cloud architecture during my leisure time.",
                        "vocab_hints": ["balancing professional career", "specialized certifications", "leisure time"]
                    },
                    {
                        "id": 2,
                        "question": "What is the most rewarding aspect of your field?",
                        "audio_prompt": "What do you find most rewarding about your field of study or work?",
                        "model_answer": "The most gratifying aspect is undoubtedly problem-solving. Being able to devise elegant technical solutions that directly enhance user experiences provides me with an immense sense of accomplishment.",
                        "vocab_hints": ["gratifying aspect", "devise elegant solutions", "immense sense of accomplishment"]
                    },
                    {
                        "id": 3,
                        "question": "Do you find it easier to study in the morning or late at night?",
                        "audio_prompt": "Do you find it easier to concentrate on your studies in the morning or late at night?",
                        "model_answer": "I consider myself an early bird. In the quiet morning hours, my mind is exceptionally sharp and free from daily distractions, allowing for deep, uninterrupted focus.",
                        "vocab_hints": ["early bird", "exceptionally sharp", "free from distractions", "deep focus"]
                    }
                ]
            },
            {
                "part": 2,
                "topic_title": "Describe a practical skill you would like to master in the future",
                "cue_card_prompt": "Describe a practical skill or field of study you would like to master in the future.\n\nYou should say:\n• What skill or subject it is\n• How you plan to learn it\n• Why you chose this particular skill\n• And explain how mastering this skill will impact your future career or personal life.",
                "prep_time_seconds": 60,
                "response_time_seconds": 120,
                "order": 2,
                "questions": [
                    {
                        "id": 4,
                        "question": "Cue Card: Describe a practical skill or field of study you would like to master in the future.",
                        "audio_prompt": "Here is your Part 2 prompt card. You have one minute to prepare: Describe a practical skill you would like to master in the future.",
                        "model_answer": "I would like to talk about mastering advanced data analytics and machine learning modeling. My plan involves enrolling in a structured masterclass curriculum, combined with hands-on capstone projects and open-source contributions. I was drawn to this domain because data-driven decision-making has become indispensable across modern enterprise landscapes. By acquiring proficiency in predictive modeling, I will not only enhance my professional competitiveness but also position myself for high-impact leadership roles in tech innovation.",
                        "vocab_hints": ["advanced data analytics", "masterclass curriculum", "hands-on capstone projects", "data-driven decision-making", "professional competitiveness"]
                    }
                ]
            },
            {
                "part": 3,
                "topic_title": "The Evolution of Higher Education & Online Learning",
                "cue_card_prompt": None,
                "prep_time_seconds": 0,
                "response_time_seconds": 60,
                "order": 3,
                "questions": [
                    {
                        "id": 5,
                        "question": "Do you think online degree programs will ever completely replace brick-and-mortar universities?",
                        "audio_prompt": "Let's explore educational trends. Do you think online degree programs will ever completely replace traditional universities?",
                        "model_answer": "I believe online platforms will complement rather than completely replace traditional universities. While digital learning offers unparalleled flexibility, physical campuses provide irreplaceable social interactions, networking opportunities, and specialized laboratory environments.",
                        "vocab_hints": ["complement rather than replace", "unparalleled flexibility", "irreplaceable social interactions", "physical campus"]
                    },
                    {
                        "id": 6,
                        "question": "Why are soft skills increasingly valued alongside academic credentials?",
                        "audio_prompt": "Why are interpersonal and soft skills becoming just as critical as academic qualifications in the modern job market?",
                        "model_answer": "In an era of hyper-automation, technical tasks can be automated, but empathetic communication, leadership, and emotional intelligence remain uniquely human. Consequently, employers prioritize individuals who can foster team synergy and resolve nuanced conflicts.",
                        "vocab_hints": ["hyper-automation", "empathetic communication", "emotional intelligence", "foster team synergy", "nuanced conflicts"]
                    }
                ]
            }
        ]
    }
]


def seed_ielts_speaking_tests():
    """Seeds deterministic IELTS Speaking Tests and Topics if not already present."""
    if IeltsSpeakingTest.query.count() >= len(SPEAKING_TESTS_DATA):
        return

    for test_dict in SPEAKING_TESTS_DATA:
        existing = IeltsSpeakingTest.query.filter_by(title=test_dict["title"]).first()
        if existing:
            continue

        test_obj = IeltsSpeakingTest(
            title=test_dict["title"],
            description=test_dict["description"],
            target_band=test_dict["target_band"],
            difficulty=test_dict["difficulty"],
            duration_minutes=test_dict["duration_minutes"],
            is_published=True,
            is_active=True
        )
        db.session.add(test_obj)
        db.session.flush()

        for topic_dict in test_dict["topics"]:
            topic_obj = IeltsSpeakingTopic(
                test_id=test_obj.id,
                part=topic_dict["part"],
                topic_title=topic_dict["topic_title"],
                cue_card_prompt=topic_dict.get("cue_card_prompt"),
                questions=topic_dict.get("questions", []),
                prep_time_seconds=topic_dict.get("prep_time_seconds", 0),
                response_time_seconds=topic_dict.get("response_time_seconds", 30),
                order=topic_dict.get("order", 1)
            )
            db.session.add(topic_obj)

    db.session.commit()
