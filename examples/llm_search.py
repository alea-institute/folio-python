import asyncio
import time
from pathlib import Path
from folio import FOLIO
from alea_llm_client import OpenAIModel, AnthropicModel


async def main():
    #  text to label/classify
    example_text = "review and revise license agreement"

    # set at initialization
    g = FOLIO(llm=OpenAIModel(model="gpt-4o"))

    print("gpt-4o results:")
    for x in await g.parallel_search_by_llm(
        example_text,
    ):
        print(x)

    # use a small llama model for area of law
    TOGETHER_API_KEY = (Path.home() / ".alea" / "keys" / "together").read_text().strip()
    g.llm = OpenAIModel(
        endpoint="https://api.together.xyz",
        model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        api_key=TOGETHER_API_KEY,
    )

    print("\n\nmeta-llama/Llama-3.2-3B-Instruct-Turbo results:")
    for x in await g.search_by_llm(
        example_text,
        search_set=g.get_areas_of_law(max_depth=1),
    ):
        print(x)

    # override via property
    g.llm = AnthropicModel(model="claude-3-5-haiku-20241022")

    # search specific branches
    print("\n\nclaude-3-5-haiku-20241022 results:")
    for x in await g.parallel_search_by_llm(
        example_text,
        search_sets=[
            g.get_areas_of_law(max_depth=2),
            g.get_document_artifacts(max_depth=2),
            g.get_player_actors(max_depth=3),
        ],
    ):
        print(x)


if __name__ == "__main__":
    t0 = time.time()
    asyncio.run(main())
    print(time.time() - t0)
