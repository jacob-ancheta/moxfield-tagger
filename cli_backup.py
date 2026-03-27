from moxfield_tagger.main import tag_deck, save_correction
if __name__ == "__main__":
    url = input("Paste Moxfield deck URL: ")

    results = tag_deck(url)

    for r in results:
        print({
            "name": r["name"],
            "tags": r["tags"],
            "source": r["source"]
        })

    # Category totals
    category_totals = {}
    for r in results:
        for tag in r["tags"]:
            category_totals[tag] = category_totals.get(tag, 0) + 1

    print("\nCategory totals:")
    for cat, count in sorted(category_totals.items()):
        print(f"{cat}: {count}")

    # Corrections
    choice = input("\nManual corrections? (Y/N): ").strip().lower()

    if choice == "y":
        correction_count = 0

        for i, r in enumerate(results, start=1):
            print(f"{i}. {r['name']} -> {r['tags']} ({r['source']})")

        selection = input("\nEnter numbers: ").strip()

        if selection:
            indices = [int(x) for x in selection.split() if x.isdigit()]

            for idx in indices:
                if 1 <= idx <= len(results):
                    selected = results[idx - 1]

                    print(f"\n{selected['name']} | Current: {selected['tags']}")

                    user_tags = input("Correct tags: ").strip()

                    if user_tags and user_tags.lower() not in ["none", "na", "n/a"]:
                        correct_tags = [t.strip() for t in user_tags.split(",") if t.strip()]

                        if correct_tags:
                            save_correction(selected["card"], correct_tags)
                            correction_count += 1

        print(f"\nSaved {correction_count} corrections.")

    # Retrain
    retrain = input("\nRetrain model? (Y/N): ").strip().lower()

    if retrain == "y":
        from ai.train_model import train_model
        train_model()

    print("\nDone.")