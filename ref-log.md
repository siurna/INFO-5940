# Multi-agent travel planner reflection

One of the biggest challenges was getting the Reviewer Agent to actually provide updated plan, not just summarize what is wrong with the current one. The turning point came when I told it to re-create a full, improved itinerary and explain why each change made sense. That small tweak completely shifted its behavior from passive reviewer to active trip designer. Adding the internet_search tool was another game-changer. Suddenly, the agent could check things like opening hours, ticket prices, and travel times on the fly.

To move away from the typical “safe” prompt structure, I tried multiple variations where the chat would deliberately suggest more out there ideas: unusual attractions, spontaneous detours, local hidden gems. It added a layer of creativity that made the plans feel more alive and less like a checklist from Google Maps. The result felt less like a cold planning tool and more like a travel buddy that balances fun and practicality. I even baked in a bit of spontaneity. Enough structure to keep things realistic, but room for surprises that make trips memorable.

This project showed just how tricky it is to design agents that talk to each other effectively. There’s a constant balancing act between precision and creativity: too much structure, and it feels robotic; too little, and it turns into chaos.

AI tools used:
-> Claude for rewriting and iterating with the prompts, systemizing them into bullet points
