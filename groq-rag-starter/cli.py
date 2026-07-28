from app.rag import answer_question


def main() -> None:
    print("\nBeginner Groq RAG Assistant")
    print("Ask a question, or type exit.\n")
    while True:
        question = input("Question: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        try:
            result = answer_question(question)
            print(f"\nAnswer:\n{result.answer}\n")
            print("Retrieved chunks:")
            for item in result.sources:
                print(
                    f"- {item['source']} page {item['page']} "
                    f"(distance {item['distance']:.3f})"
                )
            print()
        except Exception as exc:
            print(f"\nError: {exc}\n")


if __name__ == "__main__":
    main()
