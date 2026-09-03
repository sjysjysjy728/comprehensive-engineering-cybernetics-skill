import json
import sys


MAX_COUNT = 9223372036854775807


class JsonInteger:
    def __init__(self, text):
        self.value = int(text)


class JsonFloat:
    pass


class JsonObject:
    def __init__(self, pairs):
        self.pairs = pairs


def reject_constant(_text):
    raise ValueError("non-standard JSON constant")


def fail(message):
    sys.stderr.write(f"error: {message}\n")
    raise SystemExit(2)


def load_count_object(path, side):
    try:
        data = open(path, "rb").read()
    except OSError:
        fail(f"cannot read {side} input")

    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail(f"invalid UTF-8 in {side} input")

    try:
        value = json.loads(
            text,
            parse_int=JsonInteger,
            parse_float=lambda _text: JsonFloat(),
            parse_constant=reject_constant,
            object_pairs_hook=JsonObject,
        )
    except (json.JSONDecodeError, ValueError):
        fail(f"invalid JSON in {side} input")

    if not isinstance(value, JsonObject):
        fail(f"invalid count object in {side} input")

    result = {}
    for key, count in value.pairs:
        if key in result:
            fail(f"invalid count object in {side} input")
        if not isinstance(count, JsonInteger):
            fail(f"invalid count object in {side} input")
        if not 0 <= count.value <= MAX_COUNT:
            fail(f"invalid count object in {side} input")
        result[key] = count.value
    return result


def main():
    if len(sys.argv) != 3:
        fail("expected exactly two input paths")

    left = load_count_object(sys.argv[1], "left")
    right = load_count_object(sys.argv[2], "right")

    result = dict(left)
    for key, count in right.items():
        result[key] = result.get(key, 0) + count

    output = json.dumps(
        result,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    sys.stdout.write(output + "\n")


if __name__ == "__main__":
    main()
