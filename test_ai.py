import ai

def test_safe_json_parse():
    # 1. Standard json
    t1 = ai.safe_json_parse('{"a": 1}')
    assert t1 == {"a": 1}, f"Failed t1: {t1}"

    # 2. Markdown wrapped json
    t2 = ai.safe_json_parse("```json\n{\"results\": [{\"subject\": \"DSA\", \"urgency_score\": 85}]}\n```")
    assert t2 == {"results": [{"subject": "DSA", "urgency_score": 85}]}, f"Failed t2: {t2}"

    # 3. Commentary around JSON
    t3 = ai.safe_json_parse("Analysis complete:\n{\"results\": []}\nHope this helps!")
    assert t3 == {"results": []}, f"Failed t3: {t3}"

    # 4. Already parsed dict
    t4 = ai.safe_json_parse({"already": "parsed"})
    assert t4 == {"already": "parsed"}, f"Failed t4: {t4}"

    # 5. Invalid input
    t5 = ai.safe_json_parse("not json at all")
    assert t5 is None, f"Failed t5: {t5}"

    print("All safe_json_parse unit tests passed!")

if __name__ == "__main__":
    test_safe_json_parse()
